package com.example.agent.controller;

import com.example.agent.model.ChatLog;
import com.example.agent.model.ToolResult;
import com.example.agent.model.UserPreference;
import com.example.agent.service.D4DataService;
import com.example.agent.service.KnowledgeItem;
import com.example.agent.service.KnowledgeRetriever;
import dev.langchain4j.model.chat.ChatLanguageModel;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;

import java.util.*;

/**
 * 增强版 Agent 控制器，整合 D4 阶段的所有清洗数据
 */
@RestController
@RequestMapping("/api/d4-agent")
public class D4AgentController {

    @Autowired
    private ChatLanguageModel chatLanguageModel;

    @Autowired
    private D4DataService d4DataService;

    @Autowired
    private KnowledgeRetriever knowledgeRetriever;

    private final Map<String, Map<String, String>> userPreferences = new HashMap<>();
    private final Map<String, List<Map<String, String>>> conversationHistories = new HashMap<>();
    private static final int MAX_HISTORY = 6;

    /**
     * 获取 D4 数据概览
     */
    @GetMapping("/overview")
    public Map<String, Object> getOverview() {
        Map<String, Object> result = new HashMap<>();
        result.put("success", true);
        result.put("summary", d4DataService.getD4DataSummary());
        result.put("preferences_count", d4DataService.getAllPreferences().size());
        result.put("chat_logs_count", d4DataService.getAllChatLogs().size());
        result.put("tool_results_count", d4DataService.getAllToolResults().size());
        result.put("knowledge_count", d4DataService.getAllKnowledge().size());
        return result;
    }

    /**
     * 获取所有用户偏好
     */
    @GetMapping("/preferences")
    public Map<String, Object> getAllPreferences() {
        Map<String, Object> result = new HashMap<>();
        result.put("success", true);
        result.put("data", d4DataService.getAllPreferences());
        return result;
    }

    /**
     * 获取指定用户的偏好
     */
    @GetMapping("/preferences/{userId}")
    public Map<String, Object> getUserPreferences(@PathVariable String userId) {
        Map<String, Object> result = new HashMap<>();
        List<UserPreference> prefs = d4DataService.getPreferencesByUserId(userId);
        result.put("success", true);
        result.put("user_id", userId);
        result.put("data", prefs);
        return result;
    }

    /**
     * 获取所有聊天日志
     */
    @GetMapping("/chat-logs")
    public Map<String, Object> getAllChatLogs() {
        Map<String, Object> result = new HashMap<>();
        result.put("success", true);
        result.put("data", d4DataService.getAllChatLogs());
        return result;
    }

    /**
     * 获取指定会话的聊天日志
     */
    @GetMapping("/chat-logs/{sessionId}")
    public Map<String, Object> getSessionChatLogs(@PathVariable String sessionId) {
        Map<String, Object> result = new HashMap<>();
        List<ChatLog> logs = d4DataService.getChatLogsBySessionId(sessionId);
        result.put("success", true);
        result.put("session_id", sessionId);
        result.put("data", logs);
        return result;
    }

    /**
     * 获取所有工具调用结果
     */
    @GetMapping("/tool-results")
    public Map<String, Object> getAllToolResults() {
        Map<String, Object> result = new HashMap<>();
        result.put("success", true);
        result.put("data", d4DataService.getAllToolResults());
        return result;
    }

    /**
     * 获取所有知识
     */
    @GetMapping("/knowledge")
    public Map<String, Object> getAllKnowledge() {
        Map<String, Object> result = new HashMap<>();
        result.put("success", true);
        result.put("data", d4DataService.getAllKnowledge());
        return result;
    }

    /**
     * 加载 D4 中的用户偏好到当前会话
     */
    @PostMapping("/load-preferences/{userId}")
    public Map<String, Object> loadUserPreferences(@PathVariable String userId) {
        Map<String, Object> result = new HashMap<>();
        Map<String, String> prefs = d4DataService.getPreferencesMapByUserId(userId);
        
        if (!prefs.isEmpty()) {
            userPreferences.put(userId, prefs);
            result.put("success", true);
            result.put("message", String.format("已加载用户 %s 的 %d 条偏好", userId, prefs.size()));
            result.put("preferences", prefs);
        } else {
            result.put("success", false);
            result.put("message", String.format("未找到用户 %s 的偏好数据", userId));
        }
        return result;
    }

    /**
     * 设置用户偏好
     */
    @PostMapping("/{userId}/preference")
    public Map<String, Object> setPreference(
            @PathVariable String userId,
            @RequestBody Map<String, String> request) {
        Map<String, Object> result = new HashMap<>();
        String key = request.get("key");
        String value = request.get("value");

        if (key != null && value != null) {
            userPreferences.computeIfAbsent(userId, k -> new HashMap<>()).put(key, value);
            result.put("success", true);
            result.put("message", "偏好设置成功");
            result.put("preference", Map.of(key, value));
        } else {
            result.put("success", false);
            result.put("message", "请提供 key 和 value");
        }
        return result;
    }

    /**
     * 聊天接口（支持用户偏好和对话历史）
     */
    @PostMapping("/{userId}/chat")
    public Map<String, Object> chat(
            @PathVariable String userId,
            @RequestBody Map<String, String> request) {
        String userMessage = request.get("message");

        Map<String, Object> result = new HashMap<>();
        
        if (userMessage == null || userMessage.trim().isEmpty()) {
            result.put("success", false);
            result.put("message", "请输入消息");
            return result;
        }

        conversationHistories.computeIfAbsent(userId, k -> new ArrayList<>());
        List<Map<String, String>> history = conversationHistories.get(userId);

        Map<String, String> userMsg = new HashMap<>();
        userMsg.put("role", "user");
        userMsg.put("content", userMessage);
        history.add(userMsg);

        if (history.size() > MAX_HISTORY) {
            history.remove(0);
        }

        Map<String, String> prefs = userPreferences.getOrDefault(userId, new HashMap<>());
        List<String> knowledge = knowledgeRetriever.retrieveKnowledge(userMessage);

        String prompt = buildPrompt(userMessage, prefs, knowledge, history);
        String response = chatLanguageModel.generate(prompt);

        Map<String, String> assistantMsg = new HashMap<>();
        assistantMsg.put("role", "assistant");
        assistantMsg.put("content", response);
        history.add(assistantMsg);

        if (history.size() > MAX_HISTORY) {
            history.remove(0);
        }

        result.put("success", true);
        result.put("user_id", userId);
        result.put("response", response);
        result.put("used_preferences", prefs);
        result.put("used_knowledge", knowledge);
        return result;
    }

    private String buildPrompt(String userMessage, Map<String, String> prefs, 
                                List<String> knowledge, List<Map<String, String>> history) {
        StringBuilder prompt = new StringBuilder();
        prompt.append("你是一个麒麟OS智能助手。\n\n");

        if (!prefs.isEmpty()) {
            prompt.append("用户偏好设置：\n");
            for (Map.Entry<String, String> entry : prefs.entrySet()) {
                prompt.append("- ").append(entry.getKey()).append(": ").append(entry.getValue()).append("\n");
            }
            prompt.append("\n");
        }

        if (!knowledge.isEmpty()) {
            prompt.append("参考知识库内容：\n");
            for (String k : knowledge) {
                prompt.append("- ").append(k).append("\n");
            }
            prompt.append("\n");
        }

        if (history.size() > 1) {
            prompt.append("对话历史：\n");
            for (int i = 0; i < history.size() - 1; i++) {
                Map<String, String> msg = history.get(i);
                prompt.append(msg.get("role")).append(": ").append(msg.get("content")).append("\n");
            }
            prompt.append("\n");
        }

        prompt.append("用户：").append(userMessage).append("\n");
        prompt.append("助手：");
        return prompt.toString();
    }
}
