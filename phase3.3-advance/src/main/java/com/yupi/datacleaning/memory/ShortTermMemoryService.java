package com.yupi.datacleaning.memory;

import com.github.benmanes.caffeine.cache.Caffeine;
import com.github.benmanes.caffeine.cache.Cache;
import lombok.Data;
import lombok.AllArgsConstructor;
import lombok.NoArgsConstructor;
import org.springframework.stereotype.Service;

import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.concurrent.TimeUnit;

@Service
public class ShortTermMemoryService {

    private final Cache<String, SessionMemory> cache;

    public ShortTermMemoryService() {
        this.cache = Caffeine.newBuilder()
                .expireAfterWrite(30, TimeUnit.MINUTES)
                .maximumSize(1000)
                .build();
    }

    public void saveSession(String sessionId, SessionMemory memory) {
        cache.put(sessionId, memory);
    }

    public SessionMemory getSession(String sessionId) {
        return cache.getIfPresent(sessionId);
    }

    public void addChatHistory(String sessionId, String message) {
        SessionMemory memory = getSession(sessionId);
        if (memory == null) {
            memory = new SessionMemory();
            memory.setSessionId(sessionId);
        }
        if (memory.getChatHistory() == null) {
            memory.setChatHistory(new ArrayList<>());
        }
        memory.getChatHistory().add(message);
        if (memory.getChatHistory().size() > 10) {
            memory.getChatHistory().remove(0);
        }
        cache.put(sessionId, memory);
    }

    public void saveRecentLlmSuggestion(String sessionId, String suggestion) {
        SessionMemory memory = getSession(sessionId);
        if (memory == null) {
            memory = new SessionMemory();
            memory.setSessionId(sessionId);
        }
        memory.setRecentLlmSuggestion(suggestion);
        cache.put(sessionId, memory);
    }

    public void addCleaningStep(String sessionId, String step) {
        SessionMemory memory = getSession(sessionId);
        if (memory == null) {
            memory = new SessionMemory();
            memory.setSessionId(sessionId);
        }
        if (memory.getCleaningSteps() == null) {
            memory.setCleaningSteps(new ArrayList<>());
        }
        memory.getCleaningSteps().add(step);
        cache.put(sessionId, memory);
    }

    public void clearSession(String sessionId) {
        cache.invalidate(sessionId);
    }

    @Data
    @NoArgsConstructor
    @AllArgsConstructor
    public static class SessionMemory {
        private String sessionId;
        private List<String> chatHistory;
        private List<String> cleaningSteps;
        private String recentLlmSuggestion;
        private String intermediateDataPath;
    }
}
