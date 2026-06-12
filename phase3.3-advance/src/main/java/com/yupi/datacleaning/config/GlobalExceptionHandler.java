package com.yupi.datacleaning.config;

import com.yupi.datacleaning.dto.ApiResponse;
import com.yupi.datacleaning.service.ErrorAnalysisService;
import com.yupi.datacleaning.util.MdcContextUtil;
import jakarta.servlet.http.HttpServletRequest;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.validation.BindException;
import org.springframework.validation.FieldError;
import org.springframework.web.bind.MethodArgumentNotValidException;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;
import org.springframework.web.multipart.MaxUploadSizeExceededException;

import java.util.*;

/**
 * 全局异常处理器 - 自动错误捕获、日志和修复建议
 */
@Slf4j
@RestControllerAdvice
public class GlobalExceptionHandler {
    
    @Autowired
    private ErrorAnalysisService errorAnalysisService;
    
    /**
     * 处理校验异常
     */
    @ExceptionHandler(MethodArgumentNotValidException.class)
    public ResponseEntity<ApiResponse<Map<String, String>>> handleValidationExceptions(
            MethodArgumentNotValidException ex
    ) {
        Map<String, String> errors = new HashMap<>();
        ex.getBindingResult().getAllErrors().forEach(error -> {
            String fieldName = ((FieldError) error).getField();
            String errorMessage = error.getDefaultMessage();
            errors.put(fieldName, errorMessage);
        });
        
        log.warn("参数校验失败: {}", errors);
        
        return ResponseEntity.badRequest()
            .body(ApiResponse.error("参数校验失败", errors));
    }
    
    /**
     * 处理绑定异常
     */
    @ExceptionHandler(BindException.class)
    public ResponseEntity<ApiResponse<Map<String, String>>> handleBindException(BindException ex) {
        Map<String, String> errors = new HashMap<>();
        ex.getBindingResult().getAllErrors().forEach(error -> {
            String fieldName = ((FieldError) error).getField();
            String errorMessage = error.getDefaultMessage();
            errors.put(fieldName, errorMessage);
        });
        
        return ResponseEntity.badRequest()
            .body(ApiResponse.error("参数绑定失败", errors));
    }
    
    /**
     * 处理文件大小超限异常
     */
    @ExceptionHandler(MaxUploadSizeExceededException.class)
    public ResponseEntity<ApiResponse<Void>> handleMaxSizeException(
            MaxUploadSizeExceededException ex,
            HttpServletRequest request
    ) {
        String method = getRequestInfo(request);
        logErrorContext(ex, method, null);
        
        String suggestion = errorAnalysisService.recordAndAnalyze(
            ex, method, "file upload"
        );
        
        return ResponseEntity.badRequest()
            .body(ApiResponse.error("文件大小超过限制 (最大 10MB)"));
    }
    
    /**
     * 处理参数异常
     */
    @ExceptionHandler(IllegalArgumentException.class)
    public ResponseEntity<ApiResponse<Void>> handleIllegalArgumentException(
            IllegalArgumentException ex,
            HttpServletRequest request
    ) {
        String method = getRequestInfo(request);
        logErrorContext(ex, method, null);
        
        String suggestion = errorAnalysisService.recordAndAnalyze(
            ex, method, ex.getMessage()
        );
        
        return ResponseEntity.badRequest()
            .body(ApiResponse.error(ex.getMessage()));
    }
    
    /**
     * 处理通用异常
     */
    @ExceptionHandler(Exception.class)
    public ResponseEntity<ApiResponse<Void>> handleGenericException(
            Exception ex,
            HttpServletRequest request
    ) {
        String method = getRequestInfo(request);
        String params = getRequestParams(request);
        
        logErrorContext(ex, method, params);
        
        String suggestion = errorAnalysisService.recordAndAnalyze(
            ex, method, params
        );
        
        log.error(
            "请求处理异常 | TraceId: {} | Method: {} | Error: {}",
            MdcContextUtil.getTraceId(),
            method,
            ex.getMessage()
        );
        
        ApiResponse<Void> response = ApiResponse.error(
            "服务器内部错误, 请稍后重试 (TraceId: " + MdcContextUtil.getTraceId() + ")"
        );
        
        return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
            .body(response);
    }
    
    /**
     * 记录错误上下文
     */
    private void logErrorContext(Throwable throwable, String method, String params) {
        try {
            if (MdcContextUtil.getTraceId() == null) {
                MdcContextUtil.setTraceId();
            }
            
            MdcContextUtil.setErrorContext(throwable, method, params);
            
        } catch (Exception e) {
            log.warn("记录错误上下文失败", e);
        }
    }
    
    /**
     * 获取请求信息
     */
    private String getRequestInfo(HttpServletRequest request) {
        if (request == null) return "unknown";
        return request.getMethod() + " " + request.getRequestURI();
    }
    
    /**
     * 获取请求参数
     */
    private String getRequestParams(HttpServletRequest request) {
        if (request == null) return null;
        
        Map<String, String[]> paramMap = request.getParameterMap();
        if (paramMap.isEmpty()) return null;
        
        StringBuilder sb = new StringBuilder();
        paramMap.forEach((key, values) -> {
            if (sb.length() > 0) sb.append("&");
            sb.append(key).append("=").append(Arrays.toString(values));
        });
        
        return sb.toString();
    }
}
