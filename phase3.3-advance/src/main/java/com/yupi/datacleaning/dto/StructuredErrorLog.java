package com.yupi.datacleaning.dto;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.time.LocalDateTime;

/**
 * 结构化错误日志 DTO
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class StructuredErrorLog {
    
    /**
     * 时间戳
     */
    private LocalDateTime timestamp;
    
    /**
     * 追踪 ID
     */
    private String traceId;
    
    /**
     * 错误类型
     */
    private String errorType;
    
    /**
     * 堆栈跟踪
     */
    private String stackTrace;
    
    /**
     * 发生方法
     */
    private String method;
    
    /**
     * 输入参数
     */
    private String inputParams;
    
    /**
     * 用户 ID
     */
    private String userId;
    
    /**
     * 是否重试成功
     */
    private Boolean retrySuccess;
    
    /**
     * AI 修复建议
     */
    private String suggestion;
}
