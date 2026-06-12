package com.yupi.datacleaning.dto;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

/**
 * 错误分析结果 DTO
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class ErrorAnalysisResult {
    
    /**
     * 错误原因分析
     */
    private String errorAnalysis;
    
    /**
     * 修复建议
     */
    private String fixSuggestion;
    
    /**
     * 预防措施
     */
    private String prevention;
    
    /**
     * 相关代码文件
     */
    private String relatedFiles;
    
    /**
     * 置信度 (0-1)
     */
    private Double confidence;
}
