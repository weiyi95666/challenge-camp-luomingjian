package com.yupi.datacleaning.llm;

import reactor.core.publisher.Flux;

/**
 * LLM 提供者接口 - 支持多种模型接入
 * 包括：Ollama 本地模型、OpenAI API、Azure OpenAI、Anthropic Claude 等
 */
public interface LLMProvider {

    /**
     * 获取提供者名称
     */
    String getName();

    /**
     * 检查提供者是否可用
     */
    boolean isAvailable();

    /**
     * 生成完整响应（非流式）
     */
    String generate(String prompt);

    /**
     * 生成流式响应（打字机效果）
     */
    default Flux<String> generateStream(String prompt) {
        // 默认实现：先生成完整响应，然后逐字返回
        String fullResponse = generate(prompt);
        return Flux.fromArray(fullResponse.split(""))
                .delayElements(java.time.Duration.ofMillis(30));
    }

    /**
     * 获取配置的模型名称
     */
    String getModelName();

    /**
     * 健康检查
     */
    default boolean healthCheck() {
        try {
            String test = generate("Hello");
            return test != null && !test.isEmpty();
        } catch (Exception e) {
            return false;
        }
    }
}
