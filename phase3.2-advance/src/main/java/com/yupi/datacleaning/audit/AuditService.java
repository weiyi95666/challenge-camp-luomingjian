package com.yupi.datacleaning.audit;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;

import java.time.LocalDateTime;
import java.util.HashMap;
import java.util.Map;
import java.util.UUID;

@Slf4j
@Service
public class AuditService {

    private final ObjectMapper objectMapper;

    public AuditService(ObjectMapper objectMapper) {
        this.objectMapper = objectMapper;
    }

    public void logAudit(String userId, String action, Map<String, Object> requestParams) {
        Map<String, Object> auditLog = new HashMap<>();
        auditLog.put("traceId", UUID.randomUUID().toString());
        auditLog.put("userId", userId);
        auditLog.put("action", action);
        auditLog.put("timestamp", LocalDateTime.now().toString());
        auditLog.put("requestParams", requestParams);
        
        try {
            String logString = objectMapper.writeValueAsString(auditLog);
            log.info("AUDIT: {}", logString);
        } catch (JsonProcessingException e) {
            log.warn("Failed to serialize audit log", e);
            log.info("AUDIT: {}", auditLog);
        }
    }
}
