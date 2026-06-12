package com.yupi.datacleaning.util;

import org.slf4j.MDC;

import java.util.UUID;

/**
 * MDC 上下文工具类
 */
public class MdcContextUtil {
    
    private static final String TRACE_ID = "traceId";
    private static final String USER_ID = "userId";
    private static final String ERROR_TYPE = "errorType";
    private static final String METHOD = "method";
    private static final String STACK_TRACE = "stackTrace";
    private static final String INPUT_PARAMS = "inputParams";
    private static final String RETRY_SUCCESS = "retrySuccess";
    private static final String SUGGESTION = "suggestion";
    
    /**
     * 生成并设置 traceId
     */
    public static String setTraceId() {
        String traceId = UUID.randomUUID().toString().replace("-", "");
        MDC.put(TRACE_ID, traceId);
        return traceId;
    }
    
    /**
     * 获取当前 traceId
     */
    public static String getTraceId() {
        return MDC.get(TRACE_ID);
    }
    
    /**
     * 设置 traceId
     */
    public static void setTraceId(String traceId) {
        MDC.put(TRACE_ID, traceId);
    }
    
    /**
     * 设置用户 ID
     */
    public static void setUserId(String userId) {
        MDC.put(USER_ID, userId);
    }
    
    /**
     * 设置方法名
     */
    public static void setMethod(String method) {
        MDC.put(METHOD, method);
    }
    
    /**
     * 设置输入参数（JSON 格式）
     */
    public static void setInputParams(String params) {
        if (params != null && params.length() > 1000) {
            params = params.substring(0, 1000) + "...[truncated]";
        }
        MDC.put(INPUT_PARAMS, params);
    }
    
    /**
     * 设置错误信息
     */
    public static void setErrorContext(Throwable throwable, String methodName, String params) {
        MDC.put(ERROR_TYPE, throwable.getClass().getSimpleName());
        MDC.put(METHOD, methodName);
        MDC.put(STACK_TRACE, getStackTraceAsString(throwable));
        if (params != null) {
            setInputParams(params);
        }
    }
    
    /**
     * 标记重试成功
     */
    public static void markRetrySuccess() {
        MDC.put(RETRY_SUCCESS, "true");
    }
    
    /**
     * 设置 AI 建议
     */
    public static void setSuggestion(String suggestion) {
        if (suggestion != null && suggestion.length() > 2000) {
            suggestion = suggestion.substring(0, 2000) + "...";
        }
        MDC.put(SUGGESTION, suggestion);
    }
    
    /**
     * 获取堆栈跟踪为字符串
     */
    private static String getStackTraceAsString(Throwable throwable) {
        StringBuilder sb = new StringBuilder();
        sb.append(throwable.getClass().getName()).append(": ")
          .append(throwable.getMessage()).append("\n");
        
        StackTraceElement[] elements = throwable.getStackTrace();
        int limit = Math.min(elements.length, 50);
        for (int i = 0; i < limit; i++) {
            sb.append("  at ").append(elements[i]).append("\n");
        }
        
        if (elements.length > 50) {
            sb.append("  ... [").append(elements.length - 50).append(" more]");
        }
        
        return sb.toString().trim();
    }
    
    /**
     * 清除上下文
     */
    public static void clear() {
        MDC.clear();
    }
    
    /**
     * 获取完整的错误日志
     */
    public static String getFullErrorContext() {
        return String.format(
            "TraceId: %s, ErrorType: %s, Method: %s, Input: %s",
            MDC.get(TRACE_ID),
            MDC.get(ERROR_TYPE),
            MDC.get(METHOD),
            MDC.get(INPUT_PARAMS)
        );
    }
}
