package com.example.agent.memory;

import org.springframework.stereotype.Service;

import java.util.*;

@Service
public class MemoryService {

    private final Map<String, String> preferences = new HashMap<>();
    private final List<Map<String, String>> conversationHistory = new ArrayList<>();
    private static final int MAX_HISTORY = 6;

    public MemoryService() {
        preferences.put("tech_level", "beginner");
        preferences.put("response_style", "simple");
    }

    public void setPreference(String key, String value) {
        preferences.put(key, value);
    }

    public Map<String, String> getPreferences() {
        return new HashMap<>(preferences);
    }

    public void addToHistory(String role, String content) {
        Map<String, String> message = new HashMap<>();
        message.put("role", role);
        message.put("content", content);
        conversationHistory.add(message);

        if (conversationHistory.size() > MAX_HISTORY) {
            conversationHistory.remove(0);
        }
    }

    public List<Map<String, String>> getConversationHistory() {
        return new ArrayList<>(conversationHistory);
    }

    public String getFormattedHistory() {
        StringBuilder sb = new StringBuilder();
        for (Map<String, String> msg : conversationHistory) {
            sb.append(msg.get("role")).append(": ").append(msg.get("content")).append("\n");
        }
        return sb.toString();
    }

    public String buildPromptWithPreferences(String userMessage, String knowledgeContext) {
        String techLevel = preferences.get("tech_level");
        String responseStyle = preferences.get("response_style");

        StringBuilder prompt = new StringBuilder();
        
        prompt.append("你是一个麒麟OS智能助手。\n\n");
        
        prompt.append("用户技术水平: ").append(techLevel).append("\n");
        prompt.append("回复风格: ").append(responseStyle).append("\n\n");

        if (!knowledgeContext.isEmpty()) {
            prompt.append("参考知识库内容:\n").append(knowledgeContext).append("\n\n");
        }

        if (!conversationHistory.isEmpty()) {
            prompt.append("对话历史:\n").append(getFormattedHistory()).append("\n");
        }

        prompt.append("用户: ").append(userMessage).append("\n");
        prompt.append("助手:");

        return prompt.toString();
    }
}
