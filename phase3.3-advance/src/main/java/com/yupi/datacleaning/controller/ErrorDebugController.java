package com.yupi.datacleaning.controller;

import com.yupi.datacleaning.annotation.AutoRetry;
import com.yupi.datacleaning.dto.ApiResponse;
import com.yupi.datacleaning.entity.ErrorAnalysisRecord;
import com.yupi.datacleaning.service.ErrorRecordService;
import com.yupi.datacleaning.util.MdcContextUtil;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;

import java.util.List;

/**
 * 错误调试控制器 - 示例使用
 */
@Slf4j
@RestController
@RequestMapping("/api/debug")
public class ErrorDebugController {
    
    @Autowired
    private ErrorRecordService errorRecordService;
    
    /**
     * 测试空指针异常
     */
    @GetMapping("/npe")
    public ApiResponse<String> testNPE() {
        String data = null;
        int length = data.length(); // 会抛出NPE
        return ApiResponse.success("ok");
    }
    
    /**
     * 测试参数异常
     */
    @GetMapping("/illegal")
    public ApiResponse<String> testIllegal(@RequestParam String value) {
        if ("error".equals(value)) {
            throw new IllegalArgumentException("无效的参数值");
        }
        return ApiResponse.success("ok");
    }
    
    /**
     * 测试自动重试的方法
     */
    @GetMapping("/retry-test")
    @AutoRetry
    public ApiResponse<String> testRetry() {
        log.info("执行重试测试方法");
        throw new RuntimeException("模拟连接异常");
    }
    
    /**
     * 获取所有错误记录
     */
    @GetMapping("/errors")
    public ApiResponse<List<ErrorAnalysisRecord>> getAllErrors() {
        return ApiResponse.success(
            errorRecordService.getPendingErrors()
        );
    }
    
    /**
     * 通过traceId查询错误
     */
    @GetMapping("/errors/{traceId}")
    public ApiResponse<ErrorAnalysisRecord> getErrorByTraceId(
            @PathVariable String traceId
    ) {
        return errorRecordService.getByTraceId(traceId)
            .map(ApiResponse::success)
            .orElse(ApiResponse.error("未找到错误记录"));
    }
    
    /**
     * 统计错误类型
     */
    @GetMapping("/statistics")
    public ApiResponse<List<Object[]>> getStatistics() {
        return ApiResponse.success(
            errorRecordService.getErrorTypeStatistics()
        );
    }
}
