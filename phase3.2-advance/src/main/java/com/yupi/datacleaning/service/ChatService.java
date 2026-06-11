package com.yupi.datacleaning.service;

import com.yupi.datacleaning.llm.OllamaClient;
import com.yupi.datacleaning.model.ChatMessage;
import com.yupi.datacleaning.model.Conversation;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;

import java.time.LocalDateTime;
import java.util.*;
import java.util.concurrent.ConcurrentHashMap;

@Slf4j
@Service
@RequiredArgsConstructor
public class ChatService {

    private final OllamaClient ollamaClient;
    
    // In-memory storage for conversations
    private final Map<String, Conversation> conversations = new ConcurrentHashMap<>();
    
    // Deep thinking system prompt
    private static final String DEEP_THINKING_PROMPT = 
        "你是一个聪明的AI助手。请你：\n" +
        "1. 首先，逐步分析用户的问题\n" +
        "2. 然后，仔细思考问题的各个方面\n" +
        "3. 接着，组织你的思路\n" +
        "4. 最后，给出完整的答案\n" +
        "请用 '### 思考过程 ###' 标记你的思考过程，然后用 '### 答案 ###' 给出答案。";
    
    private static final String QUICK_THINKING_PROMPT = 
        "你是一个聪明的AI助手。请直接回答用户的问题，简洁明了。";

    public Conversation createConversation(String title) {
        String id = UUID.randomUUID().toString();
        Conversation conversation = new Conversation();
        conversation.setId(id);
        conversation.setTitle(title != null ? title : "新对话");
        conversation.setCreatedAt(LocalDateTime.now());
        conversation.setUpdatedAt(LocalDateTime.now());
        conversation.setMessages(new ArrayList<>());
        conversations.put(id, conversation);
        log.info("Created new conversation: {}", id);
        return conversation;
    }

    public List<Conversation> getAllConversations() {
        return new ArrayList<>(conversations.values());
    }

    public Conversation getConversation(String id) {
        return conversations.get(id);
    }

    public Conversation updateConversationTitle(String id, String title) {
        Conversation conversation = conversations.get(id);
        if (conversation != null) {
            conversation.setTitle(title);
            conversation.setUpdatedAt(LocalDateTime.now());
        }
        return conversation;
    }

    public void deleteConversation(String id) {
        conversations.remove(id);
        log.info("Deleted conversation: {}", id);
    }

    public ChatMessage addMessage(String conversationId, String role, String content, String thinkingProcess) {
        Conversation conversation = conversations.get(conversationId);
        if (conversation == null) {
            conversation = createConversation("新对话");
        }
        
        ChatMessage message = new ChatMessage();
        message.setId(UUID.randomUUID().toString());
        message.setConversationId(conversationId);
        message.setRole(role);
        message.setContent(content);
        message.setThinkingProcess(thinkingProcess);
        message.setTimestamp(LocalDateTime.now());
        
        conversation.getMessages().add(message);
        conversation.setUpdatedAt(LocalDateTime.now());
        
        return message;
    }

    public String generateResponse(String userMessage, boolean deepThinking, boolean webSearchEnabled, String searchResults) {
        try {
            // 优先尝试使用 Ollama 本地模型
            String systemPrompt = deepThinking ? DEEP_THINKING_PROMPT : QUICK_THINKING_PROMPT;
            
            String prompt = systemPrompt + "\n\n用户问题：" + userMessage;
            
            if (webSearchEnabled && searchResults != null && !searchResults.isEmpty()) {
                prompt += "\n\n搜索结果：" + searchResults;
            }
            
            // 直接调用 Ollama，它会内部处理是否可用的逻辑
            String response = ollamaClient.generateResponse(prompt);
            
            log.info("Response generated successfully");
            return response;
        } catch (Exception e) {
            log.error("Error generating response", e);
            return generateSmartFallbackResponse(userMessage, deepThinking, webSearchEnabled, searchResults);
        }
    }
    
    private String generateSmartFallbackResponse(String userMessage, boolean deepThinking, boolean webSearchEnabled, String searchResults) {
        String lowerMsg = userMessage.toLowerCase();
        
        // 深度思考模式的响应
        if (deepThinking) {
            String thinking = "让我分析一下这个问题...\n\n" +
                            "1. 首先理解用户的需求\n" +
                            "2. 分析问题的各个方面\n" +
                            "3. 组织思路\n" +
                            "4. 给出建议";
            
            String answer = generateSimpleAnswer(userMessage);
            
            return "### 思考过程 ###\n" + thinking + "\n\n### 答案 ###\n" + answer;
        }
        
        // 快速模式的响应
        return generateSimpleAnswer(userMessage);
    }
    
    private String generateSimpleAnswer(String userMessage) {
        String lowerMsg = userMessage.toLowerCase();
        
        // 问候
        if (lowerMsg.contains("你好") || lowerMsg.contains("hi") || lowerMsg.contains("hello")) {
            return "你好！很高兴见到你！我是智能助手，有什么可以帮你的吗？";
        }
        
        // 数据清洗相关
        if (lowerMsg.contains("清洗") || lowerMsg.contains("clean") || lowerMsg.contains("数据")) {
            return "关于数据清洗，我可以帮你：\n\n" +
                    "1. 移除重复数据\n" +
                    "2. 脱敏敏感信息（手机号、邮箱等）\n" +
                    "3. 标准化日期格式\n" +
                    "4. 填充缺失值\n" +
                    "5. 清理文本数据\n\n" +
                    "你可以上传文件到\"数据清洗\"标签页开始使用！";
        }
        
        // 帮助
        if (lowerMsg.contains("帮助") || lowerMsg.contains("help")) {
            return "我可以帮你：\n\n" +
                    "1. 回答问题和聊天\n" +
                    "2. 数据清洗和分析\n" +
                    "3. 文件处理\n\n" +
                    "切换到顶部的标签页来使用不同功能！";
        }
        
        // 默认响应
        return "收到你的消息了！这是一个模拟响应（Ollama 未启用或连接失败）。\n\n" +
                "如需完整功能，请：\n" +
                "1. 安装并启动 Ollama\n" +
                "2. 下载模型（如 gemma2:2b）\n" +
                "3. 在 application.yml 中启用 Ollama";
    }

    // Parse thinking process from response (for deep thinking mode)
    public Map<String, String> parseDeepThinkingResponse(String response) {
        Map<String, String> result = new HashMap<>();
        String thinking = "";
        String answer = response;
        
        if (response.contains("### 思考过程 ###")) {
            String[] parts = response.split("### 思考过程 ###|### 答案 ###");
            if (parts.length > 1) {
                thinking = parts[1].trim();
            }
            if (parts.length > 2) {
                answer = parts[2].trim();
            }
        }
        
        result.put("thinking", thinking);
        result.put("answer", answer);
        return result;
    }
}
