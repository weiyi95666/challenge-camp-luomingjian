package com.example.agent.model;

/**
 * 聊天日志数据模型（来自 D4 清洗数据）
 */
public class ChatLog {
    private String session_id;
    private String user_id;
    private String role;
    private String text;
    private String timestamp;

    public ChatLog() {
    }

    public ChatLog(String session_id, String user_id, String role, String text, String timestamp) {
        this.session_id = session_id;
        this.user_id = user_id;
        this.role = role;
        this.text = text;
        this.timestamp = timestamp;
    }

    public String getSession_id() {
        return session_id;
    }

    public void setSession_id(String session_id) {
        this.session_id = session_id;
    }

    public String getUser_id() {
        return user_id;
    }

    public void setUser_id(String user_id) {
        this.user_id = user_id;
    }

    public String getRole() {
        return role;
    }

    public void setRole(String role) {
        this.role = role;
    }

    public String getText() {
        return text;
    }

    public void setText(String text) {
        this.text = text;
    }

    public String getTimestamp() {
        return timestamp;
    }

    public void setTimestamp(String timestamp) {
        this.timestamp = timestamp;
    }
}
