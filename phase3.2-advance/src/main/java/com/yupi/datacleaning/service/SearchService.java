package com.yupi.datacleaning.service;

import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

@Slf4j
@Service
public class SearchService {

    // Mock search results for demonstration
    public List<Map<String, String>> search(String query) {
        log.info("Searching for: {}", query);
        
        List<Map<String, String>> results = new ArrayList<>();
        
        // Mock search results
        Map<String, String> result1 = new HashMap<>();
        result1.put("title", "关于 " + query + " 的简介");
        result1.put("snippet", "这是关于 " + query + " 的综合介绍，涵盖了主要概念和应用场景。");
        result1.put("url", "https://example.com/intro");
        results.add(result1);
        
        Map<String, String> result2 = new HashMap<>();
        result2.put("title", query + " - 详细教程");
        result2.put("snippet", "一步步学习如何使用 " + query + "，包含实际示例和最佳实践。");
        result2.put("url", "https://example.com/tutorial");
        results.add(result2);
        
        Map<String, String> result3 = new HashMap<>();
        result3.put("title", query + " 最新动态");
        result3.put("snippet", "了解 " + query + " 的最新发展和行业应用。");
        result3.put("url", "https://example.com/news");
        results.add(result3);
        
        return results;
    }

    public String formatSearchResults(List<Map<String, String>> results) {
        if (results == null || results.isEmpty()) {
            return "";
        }
        
        StringBuilder sb = new StringBuilder();
        for (int i = 0; i < results.size(); i++) {
            Map<String, String> result = results.get(i);
            sb.append((i + 1)).append(". ").append(result.get("title")).append("\n");
            sb.append("   ").append(result.get("snippet")).append("\n");
            sb.append("   链接: ").append(result.get("url")).append("\n\n");
        }
        return sb.toString();
    }
}
