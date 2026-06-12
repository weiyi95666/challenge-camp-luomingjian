package com.yupi.datacleaning.llm;

import lombok.extern.slf4j.Slf4j;

/**
 * 兜底提供者 - 当其他所有模型都不可用时使用
 * 提供智能的规则化响应
 */
@Slf4j
public class FallbackProvider implements LLMProvider {

    private final LLMProviderConfig.FallbackConfig config;

    public FallbackProvider(LLMProviderConfig.FallbackConfig config) {
        this.config = config;
    }

    @Override
    public String getName() {
        return "Fallback";
    }

    @Override
    public boolean isAvailable() {
        return config.isEnabled();
    }

    @Override
    public String generate(String prompt) {
        log.info("Using fallback provider for prompt: {}", prompt.substring(0, Math.min(50, prompt.length())));
        return generateSmartResponse(prompt);
    }

    private String generateSmartResponse(String prompt) {
        String lowerPrompt = prompt.toLowerCase();

        // 问候
        if (lowerPrompt.contains("你好") || lowerPrompt.contains("hi") || lowerPrompt.contains("hello")) {
            return "你好！很高兴见到你！我是智能助手。\n\n" +
                   "虽然我现在使用的是模拟响应模式，但我依然可以帮你：\n" +
                   "1. 回答常见问题\n" +
                   "2. 提供数据清洗功能\n" +
                   "3. 文件处理和预览\n\n" +
                   "如需完整 AI 功能，请配置 Ollama 或 OpenAI API！";
        }

        // 数据清洗相关
        if (lowerPrompt.contains("清洗") || lowerPrompt.contains("clean") || 
            lowerPrompt.contains("数据") || lowerPrompt.contains("data")) {
            return "关于数据清洗，我可以帮你：\n\n" +
                    "1. 移除重复数据\n" +
                    "2. 脱敏敏感信息（手机号、邮箱、身份证等）\n" +
                    "3. 标准化日期格式\n" +
                    "4. 智能填充缺失值\n" +
                    "5. 清理文本格式\n\n" +
                    "你可以上传文件到\"数据清洗\"标签页开始使用！";
        }

        // 帮助
        if (lowerPrompt.contains("帮助") || lowerPrompt.contains("help")) {
            return "📚 我可以帮你：\n\n" +
                    "1. 💬 聊天对话 - 发送任何问题\n" +
                    "2. 🧹 数据清洗 - 上传文件进行清洗\n" +
                    "3. 📁 文件管理 - 查看和下载文件\n\n" +
                    "切换到顶部的标签页来使用不同功能！\n\n" +
                    "💡 提示：启用 Ollama 或 OpenAI 可以获得更强大的 AI 能力。";
        }

        // 编程相关
        if (lowerPrompt.contains("代码") || lowerPrompt.contains("code") || 
            lowerPrompt.contains("编程") || lowerPrompt.contains("java") ||
            lowerPrompt.contains("python")) {
            return "关于编程问题，我建议：\n\n" +
                    "1. 查阅官方文档\n" +
                    "2. 在 StackOverflow 搜索\n" +
                    "3. 使用 GitHub Copilot\n\n" +
                    "配置 Ollama 或 OpenAI 后，我可以直接帮你写代码！";
        }

        // 默认响应
        return "收到你的消息了！\n\n" +
               "当前使用的是模拟响应模式。\n\n" +
               "🚀 如需完整 AI 功能，请：\n" +
               "1. 安装 Ollama（https://ollama.com）\n" +
               "2. 拉取模型：`ollama pull gemma2:2b`\n" +
               "3. 或者配置 OpenAI API Key\n\n" +
               "你问的是：\"" + prompt + "\"";
    }

    @Override
    public String getModelName() {
        return "fallback";
    }
}
