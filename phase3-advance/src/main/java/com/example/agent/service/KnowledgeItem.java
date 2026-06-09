package com.example.agent.service;

import java.util.List;

public class KnowledgeItem {
    private String title;
    private List<String> tags;
    private String content;

    public KnowledgeItem() {
    }

    public KnowledgeItem(String title, List<String> tags, String content) {
        this.title = title;
        this.tags = tags;
        this.content = content;
    }

    public String getTitle() {
        return title;
    }

    public void setTitle(String title) {
        this.title = title;
    }

    public List<String> getTags() {
        return tags;
    }

    public void setTags(List<String> tags) {
        this.tags = tags;
    }

    public String getContent() {
        return content;
    }

    public void setContent(String content) {
        this.content = content;
    }

    @Override
    public String toString() {
        return "标题：" + title + "\n内容：" + content;
    }
}
