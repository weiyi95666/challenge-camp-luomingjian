package com.yupi.datacleaning.service;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.yupi.datacleaning.dto.ErrorAnalysisResult;
import com.yupi.datacleaning.llm.LLMService;
import com.yupi.datacleaning.util.MdcContextUtil;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import java.time.LocalDateTime;

/**
 * 错误分析服务
 */
@Slf4j
@Service
public class ErrorAnalysisService {
    
    @Autowired
    private LLMService llmService;
    
    @Autowired
    private ObjectMapper objectMapper;
    
    @Autowired
    private ErrorRecordService errorRecordService;
    
    /**
     * 分析错误并提供修复建议
     */
    public ErrorAnalysisResult analyzeError(
            String errorType,
            String stackTrace,
            String method,
            String inputParams
    ) {
        try {
            String prompt = buildAnalysisPrompt(errorType, stackTrace, method, inputParams);
            
            log.info("开始AI错误分析...");
            String llmResponse = llmService.generate(prompt);
            
            return parseLlmResponse(llmResponse);
            
        } catch (Exception e) {
            log.warn("AI分析失败, 返回默认建议: {}", e.getMessage());
            return getDefaultSuggestion(errorType);
        }
    }
    
    /**
     * 构建分析提示词
     */
    private String buildAnalysisPrompt(
            String errorType,
            String stackTrace,
            String method,
            String inputParams
    ) {
        return String.format(
            """
            你是一位专业的Java开发和运维专家。请分析以下错误并提供修复建议。
            
            错误信息:
            - 错误类型: %s
            - 发生方法: %s
            - 输入参数: %s
            
            堆栈跟踪:
            %s
            
            请按照以下JSON格式返回分析结果:
            {
                "errorAnalysis": "错误原因分析",
                "fixSuggestion": "修复建议",
                "prevention": "预防措施",
                "relatedFiles": "相关文件路径",
                "confidence": 0.8
            }
            
            注意:
            1. 只返回JSON,不要其他内容
            2. confidence值在0-1之间
            3. 修复建议要具体可行
            """,
            errorType,
            method,
            inputParams != null ? inputParams : "N/A",
            truncateStackTrace(stackTrace)
        );
    }
    
    /**
     * 解析 LLM 响应
     */
    private ErrorAnalysisResult parseLlmResponse(String response) {
        try {
            String json = extractJson(response);
            return objectMapper.readValue(json, ErrorAnalysisResult.class);
        } catch (Exception e) {
            log.warn("解析LLM响应失败, 尝试解析为文本");
            return ErrorAnalysisResult.builder()
                .errorAnalysis("AI分析结果")
                .fixSuggestion(response)
                .prevention("请检查代码和配置")
                .relatedFiles("请查看堆栈信息")
                .confidence(0.5)
                .build();
        }
    }
    
    /**
     * 从响应中提取 JSON
     */
    private String extractJson(String response) {
        int start = response.indexOf('{');
        int end = response.lastIndexOf('}');
        
        if (start != -1 && end != -1 && end > start) {
            return response.substring(start, end + 1);
        }
        
        return "{\"errorAnalysis\":\"无法解析响应\",\"fixSuggestion\":\"" 
            + response.replace("\"", "\\\"") + "\",\"confidence\":0.3}";
    }
    
    /**
     * 获取默认建议
     */
    private ErrorAnalysisResult getDefaultSuggestion(String errorType) {
        String suggestion;
        
        switch (errorType) {
            case "NullPointerException":
                suggestion = """
                    1. 添加空值检查
                    2. 使用 Optional 代替 null
                    3. 添加防御性编程
                    """;
                break;
            case "ConnectException":
                suggestion = """
                    1. 检查网络连接
                    2. 验证目标服务是否启动
                    3. 检查防火墙配置
                    4. 增加连接超时配置
                    """;
                break;
            case "TimeoutException":
                suggestion = """
                    1. 增加超时时间配置
                    2. 实现重试机制
                    3. 考虑使用断路器模式
                    """;
                break;
            case "SQLException":
                suggestion = """
                    1. 检查SQL语法
                    2. 验证数据库连接
                    3. 检查表结构是否匹配
                    """;
                break;
            case "IllegalArgumentException":
                suggestion = """
                    1. 验证输入参数
                    2. 添加参数校验注解
                    3. 检查调用方传入的数据
                    """;
                break;
            default:
                suggestion = """
                    1. 检查详细堆栈信息
                    2. 查看相关业务代码
                    3. 验证数据格式
                    """;
        }
        
        return ErrorAnalysisResult.builder()
            .errorAnalysis("常见错误类型分析: " + errorType)
            .fixSuggestion(suggestion)
            .prevention("添加单元测试,增强错误处理")
            .relatedFiles("请查看相关业务代码")
            .confidence(0.6)
            .build();
    }
    
    /**
     * 截断堆栈信息
     */
    private String truncateStackTrace(String stackTrace) {
        if (stackTrace == null) return "N/A";
        if (stackTrace.length() > 3000) {
            return stackTrace.substring(0, 3000) + "\n...[truncated]";
        }
        return stackTrace;
    }
    
    /**
     * 记录并分析错误
     */
    public String recordAndAnalyze(
            Throwable throwable,
            String method,
            String inputParams
    ) {
        return recordAndAnalyze(throwable, method, inputParams, false);
    }
    
    /**
     * 记录并分析错误（含重试信息）
     */
    public String recordAndAnalyze(
            Throwable throwable,
            String method,
            String inputParams,
            Boolean retrySuccess
    ) {
        try {
            String traceId = MdcContextUtil.getTraceId();
            String errorType = throwable.getClass().getSimpleName();
            
            ErrorAnalysisResult analysis = analyzeError(
                errorType,
                getStackTrace(throwable),
                method,
                inputParams
            );
            
            errorRecordService.recordError(
                throwable, method, inputParams, analysis, retrySuccess
            );
            
            String suggestion = formatSuggestion(analysis);
            MdcContextUtil.setSuggestion(suggestion);
            
            log.error(
                "错误分析完成! TraceId: {}, 建议: {}", 
                traceId, suggestion
            );
            
            return suggestion;
            
        } catch (Exception e) {
            log.warn("记录和分析错误失败", e);
            return "无法生成分析建议, 请查看堆栈信息";
        }
    }
    
    /**
     * 格式化建议
     */
    private String formatSuggestion(ErrorAnalysisResult result) {
        return String.format(
            "【分析】%s | 【建议】%s | 【置信度】%.0f%%",
            result.getErrorAnalysis(),
            result.getFixSuggestion(),
            result.getConfidence() * 100
        );
    }
    
    /**
     * 获取堆栈信息
     */
    private String getStackTrace(Throwable throwable) {
        StringBuilder sb = new StringBuilder();
        sb.append(throwable.getClass().getName())
          .append(": ")
          .append(throwable.getMessage())
          .append("\n");
        
        StackTraceElement[] elements = throwable.getStackTrace();
        int limit = Math.min(elements.length, 20);
        for (int i = 0; i < limit; i++) {
            sb.append("  at ").append(elements[i]).append("\n");
        }
        
        return sb.toString();
    }
}
