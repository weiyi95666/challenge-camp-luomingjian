package com.example.agent.service;

import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.springframework.core.io.ClassPathResource;
import org.springframework.stereotype.Service;

import java.io.IOException;
import java.io.InputStream;
import java.util.ArrayList;
import java.util.List;

@Service
public class KnowledgeRetriever {

    private List<KnowledgeItem> knowledgeBase = new ArrayList<>();
    private final ObjectMapper objectMapper = new ObjectMapper();

    public KnowledgeRetriever() {
        loadKnowledgeBase();
    }

    private void loadKnowledgeBase() {
        try {
            ClassPathResource resource = new ClassPathResource("knowledge_cleaned.json");
            try (InputStream inputStream = resource.getInputStream()) {
                knowledgeBase = objectMapper.readValue(inputStream, new TypeReference<List<KnowledgeItem>>() {});
            }
        } catch (IOException e) {
            System.err.println("加载知识库失败: " + e.getMessage());
            e.printStackTrace();
        }
    }

    public boolean isSystemKnowledgeQuestion(String message) {
        String lowerMessage = message.toLowerCase();
        // 检查是否包含知识库中相关的关键词
        for (KnowledgeItem item : knowledgeBase) {
            for (String tag : item.getTags()) {
                if (lowerMessage.contains(tag.toLowerCase())) {
                    return true;
                }
            }
            if (lowerMessage.contains(item.getTitle().toLowerCase())) {
                return true;
            }
        }
        return false;
    }

    public List<String> retrieveKnowledge(String message) {
        List<String> relevant = new ArrayList<>();
        String lowerMessage = message.toLowerCase();

        for (KnowledgeItem item : knowledgeBase) {
            boolean match = false;
            
            // 检查标签
            for (String tag : item.getTags()) {
                if (lowerMessage.contains(tag.toLowerCase())) {
                    match = true;
                    break;
                }
            }
            
            // 检查标题
            if (!match && lowerMessage.contains(item.getTitle().toLowerCase())) {
                match = true;
            }
            
            // 检查内容
            if (!match && item.getContent() != null && lowerMessage.contains(item.getContent().toLowerCase())) {
                match = true;
            }

            if (match) {
                relevant.add(item.toString());
            }
        }

        return relevant;
    }
}
