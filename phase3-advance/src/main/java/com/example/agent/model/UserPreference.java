package com.example.agent.model;

/**
 * 用户偏好数据模型（来自 D4 清洗数据）
 */
public class UserPreference {
    private String user_id;
    private String pref_key;
    private String pref_value;
    private String preference_type;

    public UserPreference() {
    }

    public UserPreference(String user_id, String pref_key, String pref_value, String preference_type) {
        this.user_id = user_id;
        this.pref_key = pref_key;
        this.pref_value = pref_value;
        this.preference_type = preference_type;
    }

    public String getUser_id() {
        return user_id;
    }

    public void setUser_id(String user_id) {
        this.user_id = user_id;
    }

    public String getPref_key() {
        return pref_key;
    }

    public void setPref_key(String pref_key) {
        this.pref_key = pref_key;
    }

    public String getPref_value() {
        return pref_value;
    }

    public void setPref_value(String pref_value) {
        this.pref_value = pref_value;
    }

    public String getPreference_type() {
        return preference_type;
    }

    public void setPreference_type(String preference_type) {
        this.preference_type = preference_type;
    }
}
