package com.yupi.datacleaning.config;

import com.yupi.datacleaning.util.MdcContextUtil;
import jakarta.servlet.*;
import jakarta.servlet.annotation.WebFilter;
import lombok.extern.slf4j.Slf4j;
import org.springframework.core.annotation.Order;
import org.springframework.stereotype.Component;

import java.io.IOException;

/**
 * TraceId 过滤器
 */
@Slf4j
@Component
@WebFilter(urlPatterns = "/*")
@Order(1)
public class TraceIdFilter implements Filter {
    
    @Override
    public void doFilter(ServletRequest request, ServletResponse response, FilterChain chain)
            throws IOException, ServletException {
        try {
            String existingTraceId = request.getParameter("traceId");
            
            if (existingTraceId != null && !existingTraceId.isEmpty()) {
                MdcContextUtil.setTraceId(existingTraceId);
            } else {
                MdcContextUtil.setTraceId();
            }
            
            chain.doFilter(request, response);
            
        } finally {
            MdcContextUtil.clear();
        }
    }
    
    @Override
    public void init(FilterConfig filterConfig) throws ServletException {
        log.info("TraceIdFilter initialized");
    }
    
    @Override
    public void destroy() {
        log.info("TraceIdFilter destroyed");
    }
}
