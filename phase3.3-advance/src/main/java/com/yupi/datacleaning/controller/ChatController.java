package com.yupi.datacleaning.controller;

import com.yupi.datacleaning.llm.LLMService;
import com.yupi.datacleaning.model.ChatMessage;
import com.yupi.datacleaning.model.Conversation;
import com.yupi.datacleaning.service.ChatService;
import com.yupi.datacleaning.service.SearchService;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;
import reactor.core.publisher.Flux;
import reactor.core.publisher.SignalType;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.time.Duration;
import java.util.*;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.atomic.AtomicReference;

@Slf4j
@RestController
@RequestMapping("/api/chat")
@RequiredArgsConstructor
@CrossOrigin(origins = "*")
public class ChatController {

    private final ChatService chatService;
    private final SearchService searchService;
    private final LLMService llmService;

    // ==================== Conversation APIs ====================

    @GetMapping("/conversations")
    public ResponseEntity<List<Conversation>> getConversations() {
        return ResponseEntity.ok(chatService.getAllConversations());
    }

    @GetMapping("/conversations/{id}")
    public ResponseEntity<Conversation> getConversation(@PathVariable String id) {
        Conversation conversation = chatService.getConversation(id);
        if (conversation == null) {
            return ResponseEntity.notFound().build();
        }
        return ResponseEntity.ok(conversation);
    }

    @PostMapping("/conversations")
    public ResponseEntity<Conversation> createConversation(@RequestBody Map<String, String> request) {
        String title = request.get("title");
        return ResponseEntity.ok(chatService.createConversation(title));
    }

    @PutMapping("/conversations/{id}")
    public ResponseEntity<Conversation> updateConversation(@PathVariable String id, @RequestBody Map<String, String> request) {
        String title = request.get("title");
        Conversation conversation = chatService.updateConversationTitle(id, title);
        if (conversation == null) {
            return ResponseEntity.notFound().build();
        }
        return ResponseEntity.ok(conversation);
    }

    @DeleteMapping("/conversations/{id}")
    public ResponseEntity<Void> deleteConversation(@PathVariable String id) {
        chatService.deleteConversation(id);
        return ResponseEntity.ok().build();
    }

    // ==================== Chat APIs ====================

    @PostMapping("/send")
    public ResponseEntity<Map<String, Object>> sendMessage(@RequestBody ChatRequest request) {
        try {
            if (request.getMessage() == null || request.getMessage().trim().isEmpty()) {
                Map<String, Object> error = new HashMap<>();
                error.put("error", "Message cannot be empty");
                return ResponseEntity.badRequest().body(error);
            }

            String conversationId = request.getConversationId();
            if (conversationId == null || conversationId.isEmpty()) {
                Conversation conversation = chatService.createConversation(null);
                conversationId = conversation.getId();
            }

            chatService.addMessage(conversationId, "user", request.getMessage(), null);

            String searchResults = "";
            if (request.isWebSearchEnabled()) {
                List<Map<String, String>> results = searchService.search(request.getMessage());
                searchResults = searchService.formatSearchResults(results);
            }

            String rawResponse = chatService.generateResponse(
                request.getMessage(),
                request.isDeepThinking(),
                request.isWebSearchEnabled(),
                searchResults
            );

            String thinkingProcess = null;
            String assistantContent = rawResponse;

            if (request.isDeepThinking()) {
                Map<String, String> parsed = chatService.parseDeepThinkingResponse(rawResponse);
                thinkingProcess = parsed.get("thinking");
                assistantContent = parsed.get("answer");
            }

            ChatMessage assistantMessage = chatService.addMessage(
                conversationId,
                "assistant",
                assistantContent,
                thinkingProcess
            );

            Map<String, Object> result = new HashMap<>();
            result.put("conversationId", conversationId);
            result.put("message", assistantMessage);
            result.put("searchResults", searchResults);
            result.put("provider", llmService.getCurrentProvider().getName());

            return ResponseEntity.ok(result);

        } catch (Exception e) {
            log.error("Error processing chat message", e);
            Map<String, Object> error = new HashMap<>();
            error.put("error", e.getMessage());
            return ResponseEntity.internalServerError().body(error);
        }
    }

    // ==================== Streaming Chat - 修复版 ====================

    @GetMapping(value = "/stream", produces = MediaType.TEXT_EVENT_STREAM_VALUE)
    public Flux<String> streamChat(
            @RequestParam String message,
            @RequestParam(required = false) String conversationId,
            @RequestParam(defaultValue = "false") boolean deepThinking,
            @RequestParam(defaultValue = "false") boolean webSearchEnabled) {

        log.info("📡 Starting streaming chat...");

        try {
            String searchResults = "";
            if (webSearchEnabled) {
                log.info("🔍 Performing web search for streaming...");
                List<Map<String, String>> results = searchService.search(message);
                searchResults = searchService.formatSearchResults(results);
                if (!searchResults.isEmpty()) {
                    log.info("✅ Search completed, {} results", results.size());
                }
            }

            String systemPrompt = deepThinking 
                ? "你是一个聪明的AI助手。请直接回答用户的问题。" 
                : "你是一个聪明的AI助手。请直接回答用户的问题，简洁明了。";

            String prompt = systemPrompt + "\n\n用户问题：" + message;

            if (webSearchEnabled && !searchResults.isEmpty()) {
                prompt += "\n\n" + searchResults;
            }

            // 使用 LLM 服务生成完整响应
            String fullResponse = llmService.generate(prompt);

            log.info("✅ Full response generated ({} chars), starting streaming...", fullResponse.length());

            // 逐字流式返回，模拟打字效果
            return Flux.fromArray(fullResponse.split(""))
                    .delayElements(Duration.ofMillis(25))
                    .doOnComplete(() -> {
                        log.info("✅ Streaming completed");
                        saveToConversation(conversationId, message, fullResponse);
                    })
                    .doOnError(error -> log.error("❌ Streaming error: {}", error.getMessage()));

        } catch (Exception e) {
            log.error("❌ Error in streaming chat", e);
            String errorMsg = "抱歉，发生了错误：" + e.getMessage();
            return Flux.just(errorMsg);
        }
    }

    private void saveToConversation(String conversationId, String userMessage, String assistantResponse) {
        try {
            if (conversationId == null || conversationId.isEmpty()) {
                Conversation conversation = chatService.createConversation(null);
                conversationId = conversation.getId();
            }
            chatService.addMessage(conversationId, "user", userMessage, null);
            chatService.addMessage(conversationId, "assistant", assistantResponse, null);
            log.info("💾 Conversation saved: {}", conversationId);
        } catch (Exception e) {
            log.warn("⚠️ Failed to save conversation", e);
        }
    }

    // ==================== LLM Service Status API ====================

    @GetMapping("/status")
    public ResponseEntity<LLMService.ServiceStatus> getLLMStatus() {
        return ResponseEntity.ok(llmService.getStatus());
    }

    @PostMapping("/reinitialize")
    public ResponseEntity<Map<String, Object>> reinitializeLLM() {
        llmService.reinitialize();
        Map<String, Object> result = new HashMap<>();
        result.put("success", true);
        result.put("status", llmService.getStatus());
        return ResponseEntity.ok(result);
    }

    // ==================== File Upload ====================

    @PostMapping("/upload")
    public ResponseEntity<Map<String, String>> uploadFile(@RequestParam("file") MultipartFile file) {
        try {
            Path uploadDir = Paths.get("uploads");
            Files.createDirectories(uploadDir);

            String fileId = UUID.randomUUID().toString();
            String originalFilename = file.getOriginalFilename();
            String extension = originalFilename != null
                ? originalFilename.substring(originalFilename.lastIndexOf("."))
                : "";
            String savedFilename = fileId + extension;

            Path filePath = uploadDir.resolve(savedFilename);
            Files.write(filePath, file.getBytes());

            Map<String, String> result = new HashMap<>();
            result.put("fileId", fileId);
            result.put("filename", originalFilename);
            result.put("savedFilename", savedFilename);
            result.put("size", String.valueOf(file.getSize()));

            return ResponseEntity.ok(result);

        } catch (IOException e) {
            log.error("Error uploading file", e);
            Map<String, String> error = new HashMap<>();
            error.put("error", e.getMessage());
            return ResponseEntity.internalServerError().body(error);
        }
    }

    // ==================== Conversation Search ====================

    @GetMapping("/conversations/search")
    public ResponseEntity<List<Conversation>> searchConversations(@RequestParam String q) {
        List<Conversation> allConversations = chatService.getAllConversations();
        String query = q.toLowerCase();

        List<Conversation> filtered = allConversations.stream()
                .filter(conv -> conv.getTitle().toLowerCase().contains(query))
                .toList();

        return ResponseEntity.ok(filtered);
    }

    @Data
    @NoArgsConstructor
    @AllArgsConstructor
    public static class ChatRequest {
        private String conversationId;
        private String message;
        private boolean deepThinking;
        private boolean webSearchEnabled;
    }
}
