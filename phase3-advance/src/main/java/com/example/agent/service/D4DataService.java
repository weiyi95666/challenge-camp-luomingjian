package com.example.agent.service;

import com.example.agent.model.ChatLog;
import com.example.agent.model.ToolResult;
import com.example.agent.model.UserPreference;
import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.springframework.core.io.ClassPathResource;
import org.springframework.stereotype.Service;

import jakarta.annotation.PostConstruct;
import java.io.IOException;
import java.io.InputStream;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.stream.Collectors;

/**
 * D4 阶段清洗数据加载服务
 */
@Service
public class D4DataService {

    private List<UserPreference> preferences = new ArrayList<>();
    private List<ChatLog> chatLogs = new ArrayList<>();
    private List<ToolResult> toolResults = new ArrayList<>();
    private List<KnowledgeItem> knowledge = new ArrayList<>();
    
    private final ObjectMapper objectMapper = new ObjectMapper();

    @PostConstruct
    public void init() {
        loadPreferences();
        loadChatLogs();
        loadToolResults();
        loadKnowledge();
    }

    private void loadPreferences() {
        try {
            ClassPathResource resource = new ClassPathResource("preferences_cleaned.json");
            try (InputStream inputStream = resource.getInputStream()) {
                preferences = objectMapper.readValue(inputStream, new TypeReference<List<UserPreference>>() {});
            }
        } catch (IOException e) {
            System.err.println("加载 preferences 失败: " + e.getMessage());
            e.printStackTrace();
        }
    }

    private void loadChatLogs() {
        try {
            ClassPathResource resource = new ClassPathResource("chat_logs_cleaned.json");
            try (InputStream inputStream = resource.getInputStream()) {
                chatLogs = objectMapper.readValue(inputStream, new TypeReference<List<ChatLog>>() {});
            }
        } catch (IOException e) {
            System.err.println("加载 chat_logs 失败: " + e.getMessage());
            e.printStackTrace();
        }
    }

    private void loadToolResults() {
        try {
            ClassPathResource resource = new ClassPathResource("tool_result_cleaned.json");
            try (InputStream inputStream = resource.getInputStream()) {
                toolResults = objectMapper.readValue(inputStream, new TypeReference<List<ToolResult>>() {});
            }
        } catch (IOException e) {
            System.err.println("加载 tool_result 失败: " + e.getMessage());
            e.printStackTrace();
        }
    }

    private void loadKnowledge() {
        try {
            ClassPathResource resource = new ClassPathResource("knowledge_cleaned.json");
            try (InputStream inputStream = resource.getInputStream()) {
                knowledge = objectMapper.readValue(inputStream, new TypeReference<List<KnowledgeItem>>() {});
            }
        } catch (IOException e) {
            System.err.println("加载 knowledge 失败: " + e.getMessage());
            e.printStackTrace();
        }
    }

    public List<UserPreference> getAllPreferences() {
        return new ArrayList<>(preferences);
    }

    public List<UserPreference> getPreferencesByUserId(String userId) {
        return preferences.stream()
                .filter(p -> userId.equals(p.getUser_id()))
                .collect(Collectors.toList());
    }

    public Map<String, String> getPreferencesMapByUserId(String userId) {
        Map<String, String> result = new HashMap<>();
        for (UserPreference pref : preferences) {
            if (userId.equals(pref.getUser_id())) {
                result.put(pref.getPref_key(), pref.getPref_value());
            }
        }
        return result;
    }

    public List<ChatLog> getAllChatLogs() {
        return new ArrayList<>(chatLogs);
    }

    public List<ChatLog> getChatLogsBySessionId(String sessionId) {
        return chatLogs.stream()
                .filter(c -> sessionId.equals(c.getSession_id()))
                .collect(Collectors.toList());
    }

    public List<ToolResult> getAllToolResults() {
        return new ArrayList<>(toolResults);
    }

    public List<KnowledgeItem> getAllKnowledge() {
        return new ArrayList<>(knowledge);
    }

    public String getD4DataSummary() {
        return String.format("D4 清洗数据统计:\n" +
                "- 用户偏好: %d 条\n" +
                "- 聊天日志: %d 条\n" +
                "- 工具结果: %d 条\n" +
                "- 知识库: %d 条",
                preferences.size(), chatLogs.size(), toolResults.size(), knowledge.size());
    }
}
