package com.example.agent.controller;

import com.example.agent.memory.MemoryService;
import com.example.agent.service.KnowledgeRetriever;
import dev.langchain4j.model.chat.ChatLanguageModel;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;

import java.util.HashMap;
import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/api/agent")
public class AgentController {

    @Autowired
    private ChatLanguageModel chatLanguageModel;

    @Autowired
    private MemoryService memoryService;

    @Autowired
    private KnowledgeRetriever knowledgeRetriever;

    @PostMapping("/chat")
    public String agentChat(@RequestBody Map<String, String> request) {
        String userMessage = request.get("message");

        if (userMessage == null || userMessage.trim().isEmpty()) {
            return "请输入消息";
        }

        memoryService.addToHistory("用户", userMessage);

        List<String> knowledge = knowledgeRetriever.retrieveKnowledge(userMessage);
        String knowledgeContext = String.join("\n", knowledge);

        String prompt = memoryService.buildPromptWithPreferences(userMessage, knowledgeContext);
        String response = chatLanguageModel.generate(prompt);

        memoryService.addToHistory("助手", response);

        return response;
    }

    @PostMapping("/preference")
    public Map<String, Object> setPreference(@RequestBody Map<String, String> request) {
        String key = request.get("key");
        String value = request.get("value");
        Map<String, Object> result = new HashMap<>();

        if (key != null && value != null) {
            memoryService.setPreference(key, value);
            result.put("success", true);
            result.put("message", "偏好设置成功");
            result.put("preference", Map.of(key, value));
        } else {
            result.put("success", false);
            result.put("message", "请提供 key 和 value");
        }

        return result;
    }

    @GetMapping("/preferences")
    public Map<String, Object> getPreferences() {
        Map<String, Object> result = new HashMap<>();
        result.put("success", true);
        result.put("preferences", memoryService.getPreferences());
        result.put("conversation_history", memoryService.getConversationHistory());
        return result;
    }
}
