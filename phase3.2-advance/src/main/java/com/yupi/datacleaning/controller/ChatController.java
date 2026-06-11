package com.yupi.datacleaning.controller;

import com.yupi.datacleaning.model.ChatMessage;
import com.yupi.datacleaning.model.Conversation;
import com.yupi.datacleaning.service.ChatService;
import com.yupi.datacleaning.service.SearchService;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.UUID;

@Slf4j
@RestController
@RequestMapping("/api/chat")
@RequiredArgsConstructor
@CrossOrigin(origins = "*")
public class ChatController {

    private final ChatService chatService;
    private final SearchService searchService;

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
            String conversationId = request.getConversationId();
            if (conversationId == null || conversationId.isEmpty()) {
                Conversation conversation = chatService.createConversation(null);
                conversationId = conversation.getId();
            }

            // Add user message
            chatService.addMessage(conversationId, "user", request.getMessage(), null);

            // Perform search if enabled
            String searchResults = "";
            if (request.isWebSearchEnabled()) {
                List<Map<String, String>> results = searchService.search(request.getMessage());
                searchResults = searchService.formatSearchResults(results);
            }

            // Generate response
            boolean deepThinking = request.isDeepThinking();
            String rawResponse = chatService.generateResponse(
                request.getMessage(), 
                deepThinking, 
                request.isWebSearchEnabled(), 
                searchResults
            );

            String thinkingProcess = null;
            String assistantContent = rawResponse;

            if (deepThinking) {
                Map<String, String> parsed = chatService.parseDeepThinkingResponse(rawResponse);
                thinkingProcess = parsed.get("thinking");
                assistantContent = parsed.get("answer");
            }

            // Add assistant message
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

            return ResponseEntity.ok(result);

        } catch (Exception e) {
            log.error("Error processing chat message", e);
            Map<String, Object> error = new HashMap<>();
            error.put("error", e.getMessage());
            return ResponseEntity.internalServerError().body(error);
        }
    }

    // ==================== File Upload ====================
    
    @PostMapping("/upload")
    public ResponseEntity<Map<String, String>> uploadFile(@RequestParam("file") MultipartFile file) {
        try {
            Path uploadDir = Paths.get("uploads");
            Files.createDirectories(uploadDir);
            
            String fileId = UUID.randomUUID().toString();
            String originalFilename = file.getOriginalFilename();
            String extension = originalFilename != null ? 
                originalFilename.substring(originalFilename.lastIndexOf(".")) : "";
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
