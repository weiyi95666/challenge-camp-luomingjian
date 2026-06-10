package com.yupi.aicodehelper.ai;

import com.yupi.aicodehelper.ai.guardrail.SafeInputGuardrail;
import com.yupi.aicodehelper.ai.tools.DataCleaningTool;
import com.yupi.aicodehelper.ai.tools.InterviewQuestionTool;
import com.yupi.aicodehelper.ai.tools.OfficeTool;
import dev.langchain4j.memory.chat.MessageWindowChatMemory;
import dev.langchain4j.model.chat.ChatLanguageModel;
import dev.langchain4j.model.chat.StreamingChatLanguageModel;
import dev.langchain4j.rag.content.retriever.ContentRetriever;
import dev.langchain4j.service.AiServices;
import jakarta.annotation.Resource;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

@Configuration
public class AiCodeHelperServiceFactory {

    @Resource(name = "ollamaChatModel")
    private ChatLanguageModel myChatModel;

    @Resource(name = "ollamaStreamingChatModel")
    private StreamingChatLanguageModel myStreamingChatModel;

    @Resource
    private ContentRetriever contentRetriever;

    @Bean
    public AiCodeHelperService aiCodeHelperService() {
        // 构造 AI Service，使用 LangChain4j 技术实现
        return AiServices.builder(AiCodeHelperService.class)
                .chatLanguageModel(myChatModel)
                .streamingChatLanguageModel(myStreamingChatModel)
                // 启用上下文检索 (RAG)
                .contentRetriever(contentRetriever)
                // 启用短期记忆功能，通过 @MemoryId 实现会话隔离，保持 20 条消息上下文
                .chatMemoryProvider(memoryId -> MessageWindowChatMemory.withMaxMessages(20))
                // 绑定工具
                .tools(new InterviewQuestionTool(), new OfficeTool(), new DataCleaningTool())
                .build();
    }
}
