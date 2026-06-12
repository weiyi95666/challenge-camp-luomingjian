package com.yupi.datacleaning.memory;

import lombok.Data;
import lombok.AllArgsConstructor;
import lombok.NoArgsConstructor;
import org.springframework.stereotype.Service;

import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.ConcurrentHashMap;
import java.util.Map;

@Service
public class LongTermMemoryService {

    private final Map<String, UserPreferences> userPreferencesMap = new ConcurrentHashMap<>();

    public UserPreferences getUserPreferences(String userId) {
        return userPreferencesMap.computeIfAbsent(userId, k -> {
            UserPreferences prefs = new UserPreferences();
            prefs.setUserId(userId);
            prefs.setDefaultFillMethod("mean");
            prefs.setDefaultMaskingStrategy("partial");
            prefs.setFavoriteSteps(new ArrayList<>());
            return prefs;
        });
    }

    public void saveUserPreferences(String userId, UserPreferences preferences) {
        preferences.setUserId(userId);
        userPreferencesMap.put(userId, preferences);
    }

    public void addFavoriteStep(String userId, String step) {
        UserPreferences prefs = getUserPreferences(userId);
        if (!prefs.getFavoriteSteps().contains(step)) {
            prefs.getFavoriteSteps().add(step);
        }
    }

    @Data
    @NoArgsConstructor
    @AllArgsConstructor
    public static class UserPreferences {
        private String userId;
        private String defaultFillMethod;
        private String defaultMaskingStrategy;
        private List<String> favoriteSteps;
    }
}
