package com.yupi.datacleaning.service;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.HttpHeaders;
import org.springframework.http.MediaType;
import org.springframework.stereotype.Service;
import org.springframework.web.reactive.function.client.WebClient;
import org.springframework.web.reactive.function.client.WebClientResponseException;
import reactor.core.publisher.Mono;
import reactor.util.retry.Retry;

import java.time.Duration;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

@Slf4j
@Service
public class BraveSearchService {

    private static final String BRAVE_SEARCH_API = "https://api.search.brave.com/res/v1/web/search";
    private static final int DEFAULT_COUNT = 5;
    private static final Duration TIMEOUT = Duration.ofSeconds(5);

    private final WebClient webClient;
    private final ObjectMapper objectMapper;
    private final boolean isEnabled;

    public BraveSearchService(
            @Value("${brave.search.api.key:}") String apiKey,
            ObjectMapper objectMapper) {
        this.objectMapper = objectMapper;
        this.isEnabled = apiKey != null && !apiKey.trim().isEmpty();

        if (isEnabled) {
            log.info("✅ Brave Search API initialized");
            this.webClient = WebClient.builder()
                    .baseUrl(BRAVE_SEARCH_API)
                    .defaultHeader(HttpHeaders.ACCEPT, MediaType.APPLICATION_JSON_VALUE)
                    .defaultHeader("X-Subscription-Token", apiKey)
                    .build();
        } else {
            log.warn("⚠️ Brave Search API not configured (missing BRAVE_API_KEY)");
            this.webClient = null;
        }
    }

    public boolean isAvailable() {
        return isEnabled;
    }

    public List<Map<String, String>> search(String query) {
        if (!isEnabled) {
            log.warn("⚠️ Brave Search not available, returning empty results");
            return new ArrayList<>();
        }

        try {
            log.info("🔍 Searching Brave for: {}", query);
            
            String response = webClient.get()
                    .uri(uriBuilder -> uriBuilder
                            .queryParam("q", query)
                            .queryParam("count", DEFAULT_COUNT)
                            .build())
                    .retrieve()
                    .bodyToMono(String.class)
                    .timeout(TIMEOUT)
                    .retryWhen(Retry.backoff(2, Duration.ofMillis(500)))
                    .block();

            if (response != null) {
                List<Map<String, String>> results = parseResponse(response);
                log.info("✅ Found {} results from Brave Search", results.size());
                return results;
            }

            return new ArrayList<>();

        } catch (WebClientResponseException e) {
            log.error("❌ Brave Search API error: {} - {}", e.getStatusCode(), e.getResponseBodyAsString());
            return new ArrayList<>();
        } catch (Exception e) {
            log.error("❌ Brave Search error: {}", e.getMessage());
            return new ArrayList<>();
        }
    }

    private List<Map<String, String>> parseResponse(String response) {
        List<Map<String, String>> results = new ArrayList<>();
        try {
            JsonNode root = objectMapper.readTree(response);
            JsonNode webNode = root.get("web");
            
            if (webNode != null && webNode.has("results")) {
                JsonNode resultsNode = webNode.get("results");
                
                for (JsonNode resultNode : resultsNode) {
                    Map<String, String> result = new HashMap<>();
                    
                    if (resultNode.has("title")) {
                        result.put("title", resultNode.get("title").asText());
                    }
                    if (resultNode.has("description")) {
                        result.put("snippet", resultNode.get("description").asText());
                    }
                    if (resultNode.has("url")) {
                        result.put("url", resultNode.get("url").asText());
                    }
                    
                    if (!result.isEmpty()) {
                        results.add(result);
                    }
                }
            }
        } catch (Exception e) {
            log.error("❌ Failed to parse Brave Search response: {}", e.getMessage());
        }
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
