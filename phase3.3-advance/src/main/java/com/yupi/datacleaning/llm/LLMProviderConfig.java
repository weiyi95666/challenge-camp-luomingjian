package com.yupi.datacleaning.llm;

import lombok.Data;
import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.context.annotation.Configuration;

import java.util.ArrayList;
import java.util.List;

/**
 * LLM 提供者配置
 * 支持配置多个模型提供者，按优先级选择
 */
@Data
@Configuration
@ConfigurationProperties(prefix = "llm")
public class LLMProviderConfig {

    /**
     * 启用的提供者列表（按优先级排序）
     */
    private List<String> providers = new ArrayList<>();

    /**
     * Ollama 配置
     */
    private OllamaConfig ollama = new OllamaConfig();

    /**
     * OpenAI 配置
     */
    private OpenAIConfig openai = new OpenAIConfig();

    /**
     * Azure OpenAI 配置
     */
    private AzureOpenAIConfig azure = new AzureOpenAIConfig();

    /**
     * Claude 配置
     */
    private ClaudeConfig claude = new ClaudeConfig();

    /**
     * 兜底响应配置
     */
    private FallbackConfig fallback = new FallbackConfig();

    @Data
    public static class OllamaConfig {
        private boolean enabled = true;
        private String baseUrl = "http://localhost:11434";
        private String modelName = "gemma2:2b";
        private int timeoutSeconds = 60;
    }

    @Data
    public static class OpenAIConfig {
        private boolean enabled = false;
        private String apiKey = "";
        private String baseUrl = "https://api.openai.com/v1";
        private String modelName = "gpt-3.5-turbo";
        private int timeoutSeconds = 60;
    }

    @Data
    public static class AzureOpenAIConfig {
        private boolean enabled = false;
        private String apiKey = "";
        private String endpoint = "";
        private String deploymentName = "";
        private String apiVersion = "2024-02-15-preview";
        private int timeoutSeconds = 60;
    }

    @Data
    public static class ClaudeConfig {
        private boolean enabled = false;
        private String apiKey = "";
        private String baseUrl = "https://api.anthropic.com/v1";
        private String modelName = "claude-3-sonnet-20240229";
        private int timeoutSeconds = 60;
    }

    @Data
    public static class FallbackConfig {
        private boolean enabled = true;
        private String defaultResponse = "我是智能助手，正在为你服务！";
    }
}
