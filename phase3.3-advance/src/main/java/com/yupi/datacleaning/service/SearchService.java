package com.yupi.datacleaning.service;

import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;

import java.net.URLEncoder;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

@Slf4j
@Service
public class SearchService {

    private final BraveSearchService braveSearchService;

    public SearchService(BraveSearchService braveSearchService) {
        this.braveSearchService = braveSearchService;
    }

    public List<Map<String, String>> search(String query) {
        // 跳过不需要搜索的简单问题
        if (shouldSkipSearch(query)) {
            log.info("⏭️ 跳过搜索：{}", query);
            return new ArrayList<>();
        }
        
        // 优先使用 Brave Search
        if (braveSearchService.isAvailable()) {
            log.info("🔍 Using Brave Search for: {}", query);
            List<Map<String, String>> results = braveSearchService.search(query);
            if (!results.isEmpty()) {
                return results;
            }
            log.warn("⚠️ Brave Search returned no results, using fallback");
        }
        
        log.warn("⚠️ Search not available, using fallback results");
        return getFallbackResults(query);
    }

    private boolean shouldSkipSearch(String query) {
        if (query == null || query.trim().isEmpty()) {
            return true;
        }
        
        String lowerQuery = query.toLowerCase().trim();
        
        // 简单问候
        String[] greetings = {"你好", "您好", "hi", "hello", "hey", "早上好", "下午好", "晚上好"};
        for (String g : greetings) {
            if (lowerQuery.equals(g) || lowerQuery.startsWith(g)) {
                return true;
            }
        }
        
        // 问时间
        if (lowerQuery.contains("时间") || lowerQuery.contains("几点") || 
            lowerQuery.contains("日期") || lowerQuery.contains("今天") ||
            lowerQuery.contains("现在") || lowerQuery.contains("时刻")) {
            return true;
        }
        
        // 简单对话
        if (lowerQuery.equals("谢谢") || lowerQuery.equals("好的") || 
            lowerQuery.equals("ok") || lowerQuery.equals("嗯")) {
            return true;
        }
        
        return false;
    }

    private List<Map<String, String>> getFallbackResults(String query) {
        log.info("⚠️ Using fallback search results for: {}", query);
        List<Map<String, String>> results = new ArrayList<>();
        
        Map<String, String> result1 = new HashMap<>();
        result1.put("title", "关于 " + query + " 的综合介绍");
        result1.put("snippet", "这是关于 " + query + " 的综合介绍，涵盖了主要概念和应用场景。");
        result1.put("url", "https://search.brave.com/search?q=" + URLEncoder.encode(query, StandardCharsets.UTF_8));
        results.add(result1);
        
        Map<String, String> result2 = new HashMap<>();
        result2.put("title", query + " - 相关资源和教程");
        result2.put("snippet", "查找 " + query + " 的相关教程、文档和学习资源。");
        result2.put("url", "https://search.brave.com/search?q=" + URLEncoder.encode(query, StandardCharsets.UTF_8));
        results.add(result2);
        
        return results;
    }

    public String formatSearchResults(List<Map<String, String>> results) {
        if (results == null || results.isEmpty()) {
            return "";
        }
        
        StringBuilder sb = new StringBuilder();
        sb.append("【搜索结果】\n\n");
        for (int i = 0; i < results.size(); i++) {
            Map<String, String> result = results.get(i);
            sb.append((i + 1)).append(". ").append(result.getOrDefault("title", "")).append("\n");
            sb.append("   ").append(result.getOrDefault("snippet", "")).append("\n");
            sb.append("   链接: ").append(result.getOrDefault("url", "")).append("\n\n");
        }
        return sb.toString();
    }
}
