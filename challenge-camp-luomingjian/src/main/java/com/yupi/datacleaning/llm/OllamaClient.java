package com.yupi.datacleaning.llm;

import dev.langchain4j.model.ollama.OllamaChatModel;
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

    public String generateResponse(String prompt) {
        initModel();
        
        if (!ollamaAvailable) {
            return getFallbackResponse(prompt);
        }
        
        long startTime = System.currentTimeMillis();
        try {
            String response = chatModel.generate(prompt);
            long duration = System.currentTimeMillis() - startTime;
            log.info("Generated response from Ollama in {}ms", duration);
            return response;
        } catch (Exception e) {
            log.warn("Failed to generate response in {}ms: {}", System.currentTimeMillis() - startTime, e.getMessage());
            ollamaAvailable = false;
            return getFallbackResponse(prompt);
        }
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

    private String getFallbackResponse(String prompt) {
        return "Fallback: Based on pattern analysis, I suggest performing standard data cleaning steps:\n" +
                "1. Remove duplicates\n" +
                "2. Mask sensitive information\n" +
                "3. Standardize date formats\n" +
                "4. Handle missing values\n" +
                "5. Clean text data";
    }
}
