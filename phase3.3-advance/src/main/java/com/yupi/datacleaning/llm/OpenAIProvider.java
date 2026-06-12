package com.yupi.datacleaning.llm;

import com.fasterxml.jackson.annotation.JsonProperty;
import com.fasterxml.jackson.databind.ObjectMapper;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.*;
import org.springframework.web.client.RestTemplate;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

/**
 * OpenAI API 提供者
 * 支持标准 OpenAI API 格式，兼容所有 OpenAI、DeepSeek、通义千问等
 */
@Slf4j
public class OpenAIProvider implements LLMProvider {

    private final LLMProviderConfig.OpenAIConfig config;
    private final RestTemplate restTemplate;
    private final ObjectMapper objectMapper;
    private boolean available = false;

    public OpenAIProvider(LLMProviderConfig.OpenAIConfig config) {
        this.config = config;
        this.restTemplate = new RestTemplate();
        this.objectMapper = new ObjectMapper();
        init();
    }

    private void init() {
        if (!config.isEnabled()) {
            log.info("OpenAI provider is disabled");
            return;
        }
        if (config.getApiKey() == null || config.getApiKey().isEmpty() || 
            config.getApiKey().equals("your-api-key-here")) {
            log.warn("OpenAI API key is not configured");
            return;
        }
        log.info("Initializing OpenAI provider with model: {}", config.getModelName());
        this.available = true;
    }

    @Override
    public String getName() {
        return "OpenAI";
    }

    @Override
    public boolean isAvailable() {
        return available && config.isEnabled();
    }

    @Override
    public String generate(String prompt) {
        if (!isAvailable()) {
            throw new IllegalStateException("OpenAI provider is not available");
        }

        try {
            log.info("Generating response from OpenAI...");

            HttpHeaders headers = new HttpHeaders();
            headers.setContentType(MediaType.APPLICATION_JSON);
            headers.setBearerAuth(config.getApiKey());

            Map<String, Object> message = new HashMap<>();
            message.put("role", "user");
            message.put("content", prompt);

            List<Map<String, Object>> messages = new ArrayList<>();
            messages.add(message);

            Map<String, Object> requestBody = new HashMap<>();
            requestBody.put("model", config.getModelName());
            requestBody.put("messages", messages);
            requestBody.put("temperature", 0.7);
            requestBody.put("max_tokens", 2000);

            HttpEntity<Map<String, Object>> entity = new HttpEntity<>(requestBody, headers);

            ResponseEntity<OpenAIResponse> response = restTemplate.postForEntity(
                config.getBaseUrl() + "/chat/completions",
                entity,
                OpenAIResponse.class
            );

            if (response.getBody() != null && !response.getBody().getChoices().isEmpty()) {
                String result = response.getBody().getChoices().get(0).getMessage().getContent();
                log.info("✅ OpenAI response generated successfully");
                return result;
            }

            throw new RuntimeException("Empty response from OpenAI");
        } catch (Exception e) {
            log.error("❌ OpenAI API error: {}", e.getMessage());
            throw new RuntimeException("OpenAI API call failed", e);
        }
    }

    @Override
    public String getModelName() {
        return config.getModelName();
    }

    // OpenAI API Response Classes
    @lombok.Data
    public static class OpenAIResponse {
        private List<Choice> choices;
    }

    @lombok.Data
    public static class Choice {
        private Message message;
    }

    @lombok.Data
    public static class Message {
        private String content;
    }
}
