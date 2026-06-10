package com.yupi.aicodehelper.ai;

import dev.langchain4j.service.*;
import dev.langchain4j.service.spring.AiService;
import reactor.core.publisher.Flux;

import java.util.List;

//改为手动构建，更灵活
//@AiService
public interface AiCodeHelperService {

    @SystemMessage(fromResource = "system-prompt.txt")
    String chat(String userMessage);

    @SystemMessage(fromResource = "system-prompt.txt")
    Report chatForReport(String userMessage);

    // 学习报告
    record Report(String name, List<String> suggestionList) {
    }

    @SystemMessage(fromResource = "system-prompt.txt")
    Result<String> chatWithRag(String userMessage);

    // 流式对话
    @SystemMessage(fromResource = "system-prompt.txt")
    Flux<String> chatStream(@MemoryId int memoryId, @dev.langchain4j.service.UserMessage String userMessage);

    // 多模态流式对话
    @SystemMessage(fromResource = "system-prompt.txt")
    Flux<String> chatMultiModal(@MemoryId int memoryId, @dev.langchain4j.service.UserMessage dev.langchain4j.data.message.UserMessage userMessage);
}
