package com.yupi.datacleaning.config;

import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.retry.annotation.EnableRetry;
import org.springframework.retry.backoff.ExponentialBackOffPolicy;
import org.springframework.retry.policy.SimpleRetryPolicy;
import org.springframework.retry.support.RetryTemplate;

import java.util.HashMap;
import java.util.Map;

/**
 * 自动重试配置
 */
@Configuration
@EnableRetry
public class RetryConfig {
    
    /**
     * 可重试的异常类型
     */
    private static final Map<Class<? extends Throwable>, Boolean> RETRYABLE_EXCEPTIONS = new HashMap<>();
    
    static {
        RETRYABLE_EXCEPTIONS.put(java.net.ConnectException.class, true);
        RETRYABLE_EXCEPTIONS.put(java.net.SocketTimeoutException.class, true);
        RETRYABLE_EXCEPTIONS.put(java.util.concurrent.TimeoutException.class, true);
        RETRYABLE_EXCEPTIONS.put(org.springframework.web.client.ResourceAccessException.class, true);
        RETRYABLE_EXCEPTIONS.put(org.springframework.web.client.HttpServerErrorException.class, true);
    }
    
    @Bean
    public RetryTemplate retryTemplate() {
        RetryTemplate retryTemplate = new RetryTemplate();
        
        // 重试策略：最多3次，使用构造函数指定可重试异常
        SimpleRetryPolicy retryPolicy = new SimpleRetryPolicy(3, RETRYABLE_EXCEPTIONS);
        retryTemplate.setRetryPolicy(retryPolicy);
        
        // 退避策略：指数退避 (1s, 2s, 4s)
        ExponentialBackOffPolicy backOffPolicy = new ExponentialBackOffPolicy();
        backOffPolicy.setInitialInterval(1000);
        backOffPolicy.setMultiplier(2.0);
        backOffPolicy.setMaxInterval(4000);
        retryTemplate.setBackOffPolicy(backOffPolicy);
        
        return retryTemplate;
    }
}
