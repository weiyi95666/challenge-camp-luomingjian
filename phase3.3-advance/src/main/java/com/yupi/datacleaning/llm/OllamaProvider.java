package com.yupi.datacleaning.llm;

import dev.langchain4j.model.ollama.OllamaChatModel;
import lombok.extern.slf4j.Slf4j;

import java.time.Duration;

/**
 * Ollama 本地模型提供者
 * 支持本地运行的各种大模型
 */
@Slf4j
public class OllamaProvider implements LLMProvider {

    private final LLMProviderConfig.OllamaConfig config;
    private OllamaChatModel chatModel;
    private boolean available = false;

    public OllamaProvider(LLMProviderConfig.OllamaConfig config) {
        this.config = config;
        init();
    }

    private void init() {
        if (!config.isEnabled()) {
            log.info("Ollama provider is disabled");
            return;
        }

        try {
            log.info("Initializing Ollama provider - baseUrl: {}, model: {}", 
                     config.getBaseUrl(), config.getModelName());

            chatModel = OllamaChatModel.builder()
                    .baseUrl(config.getBaseUrl())
                    .modelName(config.getModelName())
                    .timeout(Duration.ofSeconds(config.getTimeoutSeconds()))
                    .build();

            // 测试连接
            String testResponse = chatModel.generate("Hello, respond with 'OK' only");
            log.info("✅ Ollama connection test successful: {}", testResponse);
            this.available = true;
        } catch (Exception e) {
            log.warn("❌ Ollama initialization failed: {} - Will use fallback if available", 
                     e.getMessage());
            this.available = false;
        }
    }

    @Override
    public String getName() {
        return "Ollama";
    }

    @Override
    public boolean isAvailable() {
        return available && config.isEnabled();
    }

    @Override
    public String generate(String prompt) {
        if (!isAvailable()) {
            throw new IllegalStateException("Ollama is not available");
        }

        try {
            log.info("Generating response from Ollama (model: {})...", config.getModelName());
            long startTime = System.currentTimeMillis();

            String response = chatModel.generate(prompt);

            long duration = System.currentTimeMillis() - startTime;
            log.info("✅ Ollama response generated in {}ms", duration);

            return response;
        } catch (Exception e) {
            log.error("❌ Ollama generation error: {}", e.getMessage());
            this.available = false; // 标记为不可用，下次会尝试重新初始化
            throw new RuntimeException("Ollama generation failed", e);
        }
    }

    @Override
    public String getModelName() {
        return config.getModelName();
    }
}
