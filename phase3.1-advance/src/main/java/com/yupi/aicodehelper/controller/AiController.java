package com.yupi.aicodehelper.controller;

import com.yupi.aicodehelper.ai.AiCodeHelperService;
import dev.langchain4j.data.message.ImageContent;
import dev.langchain4j.data.message.TextContent;
import dev.langchain4j.data.message.UserMessage;
import lombok.extern.slf4j.Slf4j;
import org.springframework.core.io.UrlResource;
import org.springframework.http.HttpHeaders;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.http.codec.ServerSentEvent;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;
import reactor.core.publisher.Flux;

import java.io.File;
import java.io.IOException;
import java.net.MalformedURLException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.ArrayList;
import java.util.Base64;
import java.util.List;

@RestController
@RequestMapping("/ai")
@Slf4j
public class AiController {

    @jakarta.annotation.Resource
    private AiCodeHelperService aiCodeHelperService;

    @jakarta.annotation.Resource
    private dev.langchain4j.store.embedding.EmbeddingStore<dev.langchain4j.data.segment.TextSegment> embeddingStore;

    @jakarta.annotation.Resource
    private dev.langchain4j.model.embedding.EmbeddingModel embeddingModel;

    private static final String UPLOAD_DIR = "outputs";

    @GetMapping("/chat")
    public Flux<ServerSentEvent<String>> chat(int memoryId, String message) {
        return aiCodeHelperService.chatStream(memoryId, message)
                .map(chunk -> ServerSentEvent.<String>builder()
                        .data(chunk)
                        .build());
    }

    /**
     * 多模态对话（支持多图片和其他多文件上传，并自动向量化以供检索）
     */
    @PostMapping(value = "/chat/multimodal", consumes = MediaType.MULTIPART_FORM_DATA_VALUE)
    public Flux<ServerSentEvent<String>> chatMultiModal(
            @RequestParam("memoryId") int memoryId,
            @RequestParam("message") String message,
            @RequestParam(value = "images", required = false) MultipartFile[] images) throws IOException {

        List<dev.langchain4j.data.message.Content> contents = new ArrayList<>();
        contents.add(dev.langchain4j.data.message.TextContent.from(message));

        StringBuilder fileInfos = new StringBuilder();
        
        if (images != null && images.length > 0) {
            for (MultipartFile file : images) {
                if (file.isEmpty()) continue;
                
                String contentType = file.getContentType();
                if (contentType != null && contentType.startsWith("image/")) {
                    String base64Image = Base64.getEncoder().encodeToString(file.getBytes());
                    contents.add(dev.langchain4j.data.message.ImageContent.from(base64Image, contentType));
                } else {
                    // 处理非图片文件
                    Path uploadPath = Paths.get(UPLOAD_DIR);
                    if (!Files.exists(uploadPath)) {
                        Files.createDirectories(uploadPath);
                    }
                    String originalFilename = file.getOriginalFilename();
                    Path filePath = uploadPath.resolve(originalFilename);
                    file.transferTo(filePath.toFile());
                    fileInfos.append(String.format("\n[用户上传了文件: %s, 已保存到: %s]", originalFilename, filePath.toAbsolutePath()));

                    // --- 增强型全格式向量化 ---
                    try {
                        String fileContent;
                        if (originalFilename.toLowerCase().endsWith(".docx")) {
                             try (java.io.InputStream is = file.getInputStream();
                                  org.apache.poi.xwpf.usermodel.XWPFDocument doc = new org.apache.poi.xwpf.usermodel.XWPFDocument(is)) {
                                 org.apache.poi.xwpf.extractor.XWPFWordExtractor extractor = new org.apache.poi.xwpf.extractor.XWPFWordExtractor(doc);
                                 fileContent = extractor.getText();
                             }
                        } else if (originalFilename.toLowerCase().endsWith(".xlsx") || originalFilename.toLowerCase().endsWith(".xls")) {
                            StringBuilder sb = new StringBuilder();
                            try (java.io.InputStream is = file.getInputStream();
                                 org.apache.poi.ss.usermodel.Workbook workbook = org.apache.poi.ss.usermodel.WorkbookFactory.create(is)) {
                                org.apache.poi.ss.usermodel.Sheet sheet = workbook.getSheetAt(0);
                                for (org.apache.poi.ss.usermodel.Row row : sheet) {
                                    for (org.apache.poi.ss.usermodel.Cell cell : row) {
                                        sb.append(cell.toString()).append(" ");
                                    }
                                    sb.append("\n");
                                }
                            }
                            fileContent = sb.toString();
                        } else {
                            fileContent = new String(file.getBytes(), StandardCharsets.UTF_8);
                        }

                        if (fileContent != null && !fileContent.trim().isEmpty()) {
                            dev.langchain4j.data.document.Document document = dev.langchain4j.data.document.Document.from(fileContent);
                            document.metadata().add("file_name", originalFilename);
                            document.metadata().add("upload_time", String.valueOf(System.currentTimeMillis()));
                            
                            dev.langchain4j.store.embedding.EmbeddingStoreIngestor.builder()
                                    .embeddingModel(embeddingModel)
                                    .embeddingStore(embeddingStore)
                                    .build()
                                    .ingest(document);
                            log.info("【RAG系统】文件 {} 内容已深度解析并存入向量库，字节数: {}", originalFilename, fileContent.length());
                        }
                    } catch (Exception e) {
                        log.error("【RAG系统】文件解析或向量化失败: {}", e.getMessage());
                    }
                }
            }
        }

        if (fileInfos.length() > 0) {
            contents.set(0, dev.langchain4j.data.message.TextContent.from(message + fileInfos.toString() + "\n请务必参考以上上传文件的内容进行回答，我已将它们存入你的上下文检索库中。"));
        }

        UserMessage userMessage = UserMessage.from(contents);

        return aiCodeHelperService.chatMultiModal(memoryId, userMessage)
                .map(chunk -> ServerSentEvent.<String>builder()
                        .data(chunk)
                        .build());
    }

    /**
     * 文件下载/预览接口
     */
    @GetMapping("/files/download")
    public ResponseEntity<org.springframework.core.io.Resource> downloadFile(@RequestParam String path) throws MalformedURLException {
        Path filePath = Paths.get(path);
        if (!Files.exists(filePath)) {
            return ResponseEntity.notFound().build();
        }

        org.springframework.core.io.Resource resource = new UrlResource(filePath.toUri());
        String contentType = "application/octet-stream";
        try {
            contentType = Files.probeContentType(filePath);
        } catch (IOException e) {
            // ignore
        }

        return ResponseEntity.ok()
                .contentType(MediaType.parseMediaType(contentType))
                .header(HttpHeaders.CONTENT_DISPOSITION, "inline; filename=\"" + filePath.getFileName().toString() + "\"")
                .body(resource);
    }
}
