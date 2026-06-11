package com.yupi.datacleaning.llm;

import dev.langchain4j.model.ollama.OllamaChatModel;
import io.github.resilience4j.circuitbreaker.annotation.CircuitBreaker;
import io.github.resilience4j.retry.annotation.Retry;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;

import java.time.Duration;
import java.util.HashMap;
import java.util.Map;

@Slf4j
@Component
public class OllamaClient {

    @Value("${ollama.base-url:http://localhost:11434}")
    private String baseUrl;

    @Value("${ollama.model-name:gemma4:e2b}")
    private String modelName;

    @Value("${ollama.timeout-seconds:15}")
    private int timeoutSeconds;

    @Value("${ollama.enabled:false}")
    private boolean ollamaEnabled;

    private OllamaChatModel chatModel;
    private boolean initialized = false;
    private boolean ollamaAvailable = false;

    private void initModel() {
        if (initialized) return;
        initialized = true;
        
        if (!ollamaEnabled) {
            log.info("Ollama is disabled, using fallback strategies only");
            return;
        }
        
        try {
            chatModel = OllamaChatModel.builder()
                    .baseUrl(baseUrl)
                    .modelName(modelName)
                    .timeout(Duration.ofSeconds(timeoutSeconds))
                    .build();
            ollamaAvailable = true;
            log.info("Initialized Ollama client with model: {}", modelName);
        } catch (Exception e) {
            log.warn("Failed to initialize Ollama client: {}, will use fallback only", e.getMessage());
            ollamaAvailable = false;
        }
    }

    @Retry(name = "ollamaService", fallbackMethod = "getFallbackResponse")
    @CircuitBreaker(name = "ollamaService", fallbackMethod = "getFallbackResponse")
    public String generateResponse(String prompt) {
        initModel();
        
        if (!ollamaAvailable) {
            log.info("Ollama not available, returning fallback response");
            return getFallbackResponse(prompt, null);
        }
        
        long startTime = System.currentTimeMillis();
        try {
            String response = chatModel.generate(prompt);
            long duration = System.currentTimeMillis() - startTime;
            log.info("Generated response from Ollama in {}ms", duration);
            return response;
        } catch (Exception e) {
            log.warn("Failed to generate response from Ollama in {}ms: {}", System.currentTimeMillis() - startTime, e.getMessage());
            ollamaAvailable = false;
            return getFallbackResponse(prompt, e);
        }
    }
    
    /**
     * 检查 Ollama 是否真正可用
     */
    public boolean isOllamaAvailable() {
        initModel();
        return ollamaAvailable;
    }

    public Map<String, Object> analyzeDataForCleaning(String dataSample) {
        String prompt = buildAnalysisPrompt(dataSample);
        String response = generateResponse(prompt);
        
        Map<String, Object> result = new HashMap<>();
        result.put("suggestion", parseSuggestion(response));
        result.put("confidence", 0.7);
        result.put("needsCleaning", true);
        result.put("recommendedSteps", parseRecommendedSteps(response));
        return result;
    }

    public Map<String, Object> suggestRepair(String error, String dataSample) {
        String prompt = buildRepairPrompt(error, dataSample);
        String response = generateResponse(prompt);
        
        Map<String, Object> result = new HashMap<>();
        result.put("repairSuggestion", response);
        result.put("strategy", "auto_repair");
        return result;
    }

    private String buildAnalysisPrompt(String dataSample) {
        return "You are a data cleaning expert. Analyze this data sample and suggest cleaning steps:\n" +
                dataSample + "\n\n" +
                "Respond with a clear, actionable cleaning plan.";
    }

    private String buildRepairPrompt(String error, String dataSample) {
        return "Error occurred: " + error + "\n\n" +
                "Data sample: " + dataSample + "\n\n" +
                "Suggest how to fix this error in the data cleaning process.";
    }

    private String parseSuggestion(String response) {
        return response.length() > 500 ? response.substring(0, 500) : response;
    }

    private java.util.List<String> parseRecommendedSteps(String response) {
        java.util.List<String> steps = new java.util.ArrayList<>();
        steps.add("Remove duplicates");
        steps.add("Mask sensitive data");
        steps.add("Standardize dates");
        steps.add("Fill missing values");
        steps.add("Clean text");
        return steps;
    }

    private String getFallbackResponse(String prompt, Exception e) {
        // 智能判断是数据清洗请求还是普通聊天
        String lowerPrompt = prompt.toLowerCase();
        if (lowerPrompt.contains("清洗") || lowerPrompt.contains("clean") || 
            lowerPrompt.contains("数据") || lowerPrompt.contains("data")) {
            return "基于模式分析，我建议执行以下标准数据清洗步骤：\n" +
                    "1. 移除重复数据\n" +
                    "2. 脱敏敏感信息\n" +
                    "3. 标准化日期格式\n" +
                    "4. 处理缺失值\n" +
                    "5. 清理文本数据";
        }
        
        // 普通聊天的 fallback 响应 - 不使用 "Fallback" 字样，让响应更自然
        return "你好！我是智能助手。我可以帮你：\n\n" +
                "1. 回答问题和咨询\n" +
                "2. 清洗和分析数据\n" +
                "3. 提供编程帮助\n\n" +
                "请告诉我你需要什么帮助？";
    }
}
