package com.yupi.aicodehelper.ai.model;

import dev.langchain4j.model.chat.ChatLanguageModel;
import dev.langchain4j.model.chat.StreamingChatLanguageModel;
import dev.langchain4j.model.chat.listener.ChatModelListener;
import dev.langchain4j.model.openai.OpenAiChatModel;
import dev.langchain4j.model.openai.OpenAiStreamingChatModel;
import jakarta.annotation.Resource;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

import java.time.Duration;
import java.util.List;

@Configuration
public class OllamaModelConfig {

    @Value("${langchain4j.ollama.chat-model.base-url}")
    private String baseUrl;

    @Value("${langchain4j.ollama.chat-model.model-name}")
    private String modelName;

    @Resource
    private ChatModelListener chatModelListener;

    @Bean
    public ChatLanguageModel ollamaChatModel() {
        return OpenAiChatModel.builder()
                .baseUrl(baseUrl + "/v1")
                .apiKey("ollama")
                .modelName(modelName)
                .timeout(Duration.ofMinutes(1))
                .maxRetries(0) // 减少重试等待
                .listeners(List.of(chatModelListener))
                .build();
    }

    @Bean
    public StreamingChatLanguageModel ollamaStreamingChatModel() {
        return OpenAiStreamingChatModel.builder()
                .baseUrl(baseUrl + "/v1")
                .apiKey("ollama")
                .modelName(modelName)
                .timeout(Duration.ofMinutes(1))
                .listeners(List.of(chatModelListener))
                .build();
    }
}
