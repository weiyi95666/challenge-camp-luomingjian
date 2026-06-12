package com.yupi.datacleaning.aspect;

import com.yupi.datacleaning.annotation.AutoRetry;
import com.yupi.datacleaning.util.MdcContextUtil;
import lombok.extern.slf4j.Slf4j;
import org.aspectj.lang.ProceedingJoinPoint;
import org.aspectj.lang.annotation.Around;
import org.aspectj.lang.annotation.Aspect;
import org.aspectj.lang.reflect.MethodSignature;
import org.springframework.stereotype.Component;

import java.io.PrintWriter;
import java.io.StringWriter;
import java.util.Arrays;
import java.util.HashSet;
import java.util.Set;
import java.util.concurrent.TimeUnit;

/**
 * 自动重试切面
 */
@Slf4j
@Aspect
@Component
public class AutoRetryAspect {
    
    private static final Set<Class<? extends Throwable>> DEFAULT_RETRYABLE = new HashSet<>(
        Arrays.asList(
            java.net.ConnectException.class,
            java.net.SocketTimeoutException.class,
            java.util.concurrent.TimeoutException.class,
            org.springframework.web.client.ResourceAccessException.class,
            org.springframework.web.client.HttpServerErrorException.class
        )
    );
    
    @Around("@annotation(autoRetry)")
    public Object around(ProceedingJoinPoint joinPoint, AutoRetry autoRetry) throws Throwable {
        MethodSignature signature = (MethodSignature) joinPoint.getSignature();
        String methodName = signature.getDeclaringTypeName() + "." + signature.getName();
        
        Set<Class<? extends Throwable>> retryableExceptions = new HashSet<>(DEFAULT_RETRYABLE);
        if (autoRetry.retryFor().length > 0) {
            retryableExceptions.addAll(Arrays.asList(autoRetry.retryFor()));
        }
        
        int maxAttempts = autoRetry.maxAttempts();
        long currentDelay = autoRetry.initialInterval();
        
        Throwable lastException = null;
        
        for (int attempt = 1; attempt <= maxAttempts; attempt++) {
            try {
                if (attempt > 1) {
                    log.info("第{}次重试执行方法: {}, 等待: {}ms", attempt, methodName, currentDelay);
                }
                
                Object result = joinPoint.proceed();
                
                if (attempt > 1) {
                    log.info("重试成功! 方法: {}, 第{}次成功", methodName, attempt);
                    MdcContextUtil.markRetrySuccess();
                }
                
                return result;
                
            } catch (Throwable e) {
                lastException = e;
                
                if (!isRetryable(e, retryableExceptions)) {
                    log.warn("不可重试的异常: {}, 方法: {}", e.getClass().getSimpleName(), methodName);
                    throw e;
                }
                
                if (attempt >= maxAttempts) {
                    log.error("所有重试失败! 方法: {}, 已尝试{}次", methodName, maxAttempts);
                    break;
                }
                
                log.warn("方法执行失败, 准备重试: {}/{} - 异常: {}", 
                    attempt, maxAttempts, e.getMessage());
                
                try {
                    TimeUnit.MILLISECONDS.sleep(currentDelay);
                } catch (InterruptedException ie) {
                    Thread.currentThread().interrupt();
                    throw e;
                }
                
                currentDelay = (long) (currentDelay * autoRetry.multiplier());
                currentDelay = Math.min(currentDelay, autoRetry.maxInterval());
            }
        }
        
        throw lastException;
    }
    
    private boolean isRetryable(Throwable e, Set<Class<? extends Throwable>> retryable) {
        if (e == null) return false;
        
        for (Class<? extends Throwable> ex : retryable) {
            if (ex.isInstance(e)) {
                return true;
            }
        }
        
        Throwable cause = e.getCause();
        if (cause != null && cause != e) {
            return isRetryable(cause, retryable);
        }
        
        return false;
    }
}
