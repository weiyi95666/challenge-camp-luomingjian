package com.yupi.datacleaning.model;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.time.LocalDateTime;

@Data
@NoArgsConstructor
@AllArgsConstructor
public class ChatMessage {
    private String id;
    private String conversationId;
    private String role; // "user" or "assistant"
    private String content;
    private String thinkingProcess; // for deep thinking mode
    private LocalDateTime timestamp;
}
