package com.yupi.datacleaning.llm;

import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import reactor.core.publisher.Flux;

import jakarta.annotation.PostConstruct;
import java.util.ArrayList;
import java.util.List;

/**
 * 智能 LLM 服务
 * 自动选择可用的模型提供者，支持故障转移
 */
@Slf4j
@Service
public class LLMService {

    private final LLMProviderConfig config;
    private final List<LLMProvider> providers = new ArrayList<>();
    private LLMProvider currentProvider;

    public LLMService(LLMProviderConfig config) {
        this.config = config;
    }

    @PostConstruct
    public void init() {
        log.info("🚀 Initializing LLM Service...");

        // 按配置顺序初始化提供者
        initializeProviders();

        // 选择第一个可用的提供者
        selectProvider();

        log.info("✅ LLM Service initialized. Active provider: {}", 
                 currentProvider != null ? currentProvider.getName() : "None");
    }

    private void initializeProviders() {
        log.info("Initializing LLM providers in order: {}", config.getProviders());

        for (String providerName : config.getProviders()) {
            try {
                LLMProvider provider = createProvider(providerName);
                if (provider != null) {
                    providers.add(provider);
                    log.info("✅ Loaded provider: {} (available: {})", 
                             provider.getName(), provider.isAvailable());
                }
            } catch (Exception e) {
                log.error("❌ Failed to initialize provider: {}", providerName, e);
            }
        }

        // 始终添加兜底提供者
        providers.add(new FallbackProvider(config.getFallback()));
        log.info("✅ Fallback provider added");
    }

    private LLMProvider createProvider(String name) {
        return switch (name.toLowerCase()) {
            case "ollama" -> new OllamaProvider(config.getOllama());
            case "openai" -> new OpenAIProvider(config.getOpenai());
            // 可以继续添加 azure, claude 等
            default -> {
                log.warn("Unknown provider: {}", name);
                yield null;
            }
        };
    }

    private void selectProvider() {
        for (LLMProvider provider : providers) {
            if (provider.isAvailable()) {
                this.currentProvider = provider;
                log.info("🎯 Selected provider: {} (model: {})", 
                         provider.getName(), provider.getModelName());
                return;
            }
        }
        log.warn("⚠️  No available providers, using fallback");
        this.currentProvider = providers.get(providers.size() - 1); // 兜底
    }

    /**
     * 获取当前活动的提供者
     */
    public LLMProvider getCurrentProvider() {
        return currentProvider;
    }

    /**
     * 获取所有可用的提供者列表
     */
    public List<LLMProvider> getAllProviders() {
        return new ArrayList<>(providers);
    }

    /**
     * 生成响应（自动故障转移）
     */
    public String generate(String prompt) {
        if (currentProvider == null) {
            selectProvider();
        }

        try {
            return currentProvider.generate(prompt);
        } catch (Exception e) {
            log.warn("⚠️ Provider {} failed, trying next...", currentProvider.getName());
            return tryNextProvider(prompt);
        }
    }

    /**
     * 尝试下一个可用的提供者
     */
    private String tryNextProvider(String prompt) {
        int currentIndex = providers.indexOf(currentProvider);
        for (int i = currentIndex + 1; i < providers.size(); i++) {
            LLMProvider next = providers.get(i);
            if (next.isAvailable()) {
                try {
                    log.info("🔄 Switching to provider: {}", next.getName());
                    String response = next.generate(prompt);
                    this.currentProvider = next;
                    return response;
                } catch (Exception e) {
                    log.warn("Provider {} also failed", next.getName());
                }
            }
        }
        throw new RuntimeException("All providers failed");
    }

    /**
     * 流式生成响应
     */
    public Flux<String> generateStream(String prompt) {
        if (currentProvider == null) {
            selectProvider();
        }

        try {
            return currentProvider.generateStream(prompt);
        } catch (Exception e) {
            log.warn("⚠️ Streaming from {} failed, trying fallback", currentProvider.getName());
            return Flux.just(tryNextProvider(prompt))
                    .flatMap(response -> Flux.fromArray(response.split(""))
                    .delayElements(java.time.Duration.ofMillis(30)));
        }
    }

    /**
     * 重新初始化所有提供者
     */
    public void reinitialize() {
        log.info("🔄 Reinitializing LLM providers...");
        providers.clear();
        initializeProviders();
        selectProvider();
    }

    /**
     * 获取服务状态
     */
    public ServiceStatus getStatus() {
        return new ServiceStatus(
            currentProvider != null ? currentProvider.getName() : "none",
            currentProvider != null ? currentProvider.getModelName() : "none",
            currentProvider != null && currentProvider.isAvailable(),
            providers.stream().map(p -> new ProviderStatus(p.getName(), p.isAvailable())).toList()
        );
    }

    public record ServiceStatus(
        String activeProvider,
        String activeModel,
        boolean isHealthy,
        List<ProviderStatus> providers
    ) {}

    public record ProviderStatus(String name, boolean available) {}
}
