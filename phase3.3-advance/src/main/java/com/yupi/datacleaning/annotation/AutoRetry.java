package com.yupi.datacleaning.annotation;

import java.lang.annotation.*;

/**
 * 自动重试注解
 */
@Target(ElementType.METHOD)
@Retention(RetentionPolicy.RUNTIME)
@Documented
public @interface AutoRetry {
    
    /**
     * 最大重试次数 (默认3次)
     */
    int maxAttempts() default 3;
    
    /**
     * 初始退避时间 (毫秒，默认1秒)
     */
    long initialInterval() default 1000;
    
    /**
     * 退避倍数 (默认2倍)
     */
    double multiplier() default 2.0;
    
    /**
     * 最大退避时间 (毫秒，默认4秒)
     */
    long maxInterval() default 4000;
    
    /**
     * 可重试的异常类型
     */
    Class<? extends Throwable>[] retryFor() default {};
}
