package com.example.agent.controller;

import com.example.agent.service.KnowledgeRetriever;
import dev.langchain4j.model.chat.ChatLanguageModel;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/api")
public class ChatController {

    @Autowired
    private ChatLanguageModel chatLanguageModel;

    @Autowired
    private KnowledgeRetriever knowledgeRetriever;

    @PostMapping("/chat")
    public String chat(@RequestBody Map<String, String> request) {
        String userMessage = request.get("message");

        if (userMessage == null || userMessage.trim().isEmpty()) {
            return "请输入消息";
        }

        return processChatWorkflow(userMessage);
    }

    private String processChatWorkflow(String userMessage) {
        String intent = classifyIntent(userMessage);
        String response;

        if ("system_knowledge".equals(intent)) {
            List<String> knowledge = knowledgeRetriever.retrieveKnowledge(userMessage);
            String context = String.join("\n", knowledge);
            response = generateResponseWithContext(userMessage, context);
        } else {
            response = generateSimpleResponse(userMessage);
        }

        return response;
    }

    private String classifyIntent(String message) {
        if (knowledgeRetriever.isSystemKnowledgeQuestion(message)) {
            return "system_knowledge";
        }
        return "normal_chat";
    }

    private String generateResponseWithContext(String userMessage, String context) {
        String prompt = "你是一个麒麟OS智能助手。\n\n" +
                "参考知识库内容：\n" + context + "\n\n" +
                "用户问题：" + userMessage + "\n" +
                "请根据知识库内容回答用户问题。";
        return chatLanguageModel.generate(prompt);
    }

    private String generateSimpleResponse(String userMessage) {
        return chatLanguageModel.generate(userMessage);
    }
}
