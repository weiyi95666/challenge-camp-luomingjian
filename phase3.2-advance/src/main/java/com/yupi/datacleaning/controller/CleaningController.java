package com.yupi.datacleaning.controller;

import com.yupi.datacleaning.audit.AuditService;
import com.yupi.datacleaning.cleaning.CleaningReport;
import com.yupi.datacleaning.cleaning.DataCleaner;
import com.yupi.datacleaning.llm.OllamaClient;
import com.yupi.datacleaning.memory.ShortTermMemoryService;
import com.yupi.datacleaning.memory.LongTermMemoryService;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.slf4j.MDC;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;
import tech.tablesaw.api.Table;

import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.*;
import java.util.concurrent.ConcurrentHashMap;

@Slf4j
@RestController
@RequestMapping("/api/clean")
@RequiredArgsConstructor
@CrossOrigin(origins = "*")
public class CleaningController {

    private final DataCleaner dataCleaner;
    private final OllamaClient ollamaClient;
    private final ShortTermMemoryService shortTermMemory;
    private final LongTermMemoryService longTermMemory;
    private final AuditService auditService;

    private final Map<String, CleaningTask> tasks = new ConcurrentHashMap<>();

    @PostMapping("/upload")
    public Map<String, Object> uploadFile(@RequestParam("file") MultipartFile file,
                                         @RequestParam(value = "userId", defaultValue = "default") String userId) {
        String traceId = UUID.randomUUID().toString();
        MDC.put("traceId", traceId);
        
        try {
            String taskId = UUID.randomUUID().toString();
            String sessionId = UUID.randomUUID().toString();
            
            // Audit log
            Map<String, Object> auditParams = new HashMap<>();
            auditParams.put("taskId", taskId);
            auditParams.put("fileName", file.getOriginalFilename());
            auditParams.put("fileSize", file.getSize());
            auditService.logAudit(userId, "UPLOAD_FILE", auditParams);
            
            Path tempDir = Paths.get("temp");
            Files.createDirectories(tempDir);
            
            String filePath = tempDir.resolve(taskId + "_" + file.getOriginalFilename()).toString();
            Files.write(Paths.get(filePath), file.getBytes());
            
            Table table = Table.read().file(filePath);
            
            CleaningTask task = new CleaningTask();
            task.setTaskId(taskId);
            task.setSessionId(sessionId);
            task.setUserId(userId);
            task.setOriginalFilePath(filePath);
            task.setStatus("uploaded");
            task.setRowCount(table.rowCount());
            task.setColumnCount(table.columnCount());
            tasks.put(taskId, task);
            
            shortTermMemory.addChatHistory(sessionId, "User uploaded file: " + file.getOriginalFilename());
            
            Map<String, Object> analysis = dataCleaner.analyzeData(table);
            
            Map<String, Object> result = new HashMap<>();
            result.put("taskId", taskId);
            result.put("sessionId", sessionId);
            result.put("status", "uploaded");
            result.put("analysis", analysis);
            result.put("sample", getSampleData(table));
            
            return result;
        } catch (Exception e) {
            log.error("Error uploading file", e);
            return Map.of("error", e.getMessage(), "status", "error");
        } finally {
            MDC.clear();
        }
    }

    @PostMapping("/start/{taskId}")
    public Map<String, Object> startCleaning(@PathVariable String taskId,
                                             @RequestBody Map<String, Object> request) {
        String traceId = UUID.randomUUID().toString();
        MDC.put("traceId", traceId);
        
        try {
            long startTime = System.currentTimeMillis();
            CleaningTask task = tasks.get(taskId);
            if (task == null) {
                return Map.of("error", "Task not found", "status", "error");
            }
            
            // Audit log
            Map<String, Object> auditParams = new HashMap<>();
            auditParams.put("taskId", taskId);
            auditParams.put("userId", task.getUserId());
            auditService.logAudit(task.getUserId(), "START_CLEANING", auditParams);
            
            task.setStatus("running");
            task.setProgress(20);
            
            // 读取文件
            log.info("Reading file: {}", task.getOriginalFilePath());
            Table table = Table.read().file(task.getOriginalFilePath());
            log.info("Read {} rows", table.rowCount());
            task.setProgress(40);
            
            // 执行清洗并获取报告
            log.info("Starting auto-clean...");
            CleaningReport report = dataCleaner.autoCleanWithReport(table);
            Table cleanedTable = report.getFinalTable();
            log.info("Cleaned to {} rows", cleanedTable.rowCount());
            task.setProgress(80);
            
            // 保存输出
            Path outputDir = Paths.get("outputs");
            Files.createDirectories(outputDir);
            
            String outputPath = outputDir.resolve(taskId + "_cleaned.csv").toString();
            log.info("Writing output to: {}", outputPath);
            cleanedTable.write().csv(outputPath);
            
            // 完成
            task.setCleanedFilePath(outputPath);
            task.setProgress(100);
            task.setStatus("success");
            
            long duration = System.currentTimeMillis() - startTime;
            log.info("Cleaning completed in {}ms", duration);
            
            // 添加详细的清洗报告
            Map<String, Object> cleaningReport = new HashMap<>();
            cleaningReport.put("removedDuplicates", report.getRemovedDuplicates());
            cleaningReport.put("standardizedDates", report.getStandardizedDates());
            cleaningReport.put("filledMissingValues", report.getFilledMissingValues());
            cleaningReport.put("maskedSensitiveData", report.getMaskedSensitiveData());
            cleaningReport.put("cleanedTextEntries", report.getCleanedTextEntries());
            cleaningReport.put("handledOutliers", report.getHandledOutliers());
            cleaningReport.put("originalRowCount", report.getOriginalRowCount());
            cleaningReport.put("finalRowCount", report.getFinalRowCount());
            cleaningReport.put("columnStats", report.getColumnStats());
            
            task.setCleaningReport(cleaningReport);
            
            Map<String, Object> result = new HashMap<>();
            result.put("taskId", taskId);
            result.put("status", "success");
            result.put("cleanedRowCount", cleanedTable.rowCount());
            result.put("durationMs", duration);
            result.put("message", "Cleaning completed in " + (duration / 1000.0) + "s");
            result.put("cleaningReport", cleaningReport);
            return result;
        } catch (Exception e) {
            log.error("Cleaning failed", e);
            CleaningTask task = tasks.get(taskId);
            if (task != null) {
                task.setStatus("failed");
                task.setError(e.getMessage());
            }
            return Map.of("error", e.getMessage(), "status", "error");
        } finally {
            MDC.clear();
        }
    }

    @GetMapping("/status/{taskId}")
    public Map<String, Object> getStatus(@PathVariable String taskId) {
        CleaningTask task = tasks.get(taskId);
        if (task == null) {
            return Map.of("error", "Task not found", "status", "error");
        }
        Map<String, Object> result = new HashMap<>();
        result.put("taskId", task.getTaskId());
        result.put("status", task.getStatus());
        result.put("progress", task.getProgress());
        if (task.getLlmSuggestion() != null) {
            result.put("llmSuggestion", task.getLlmSuggestion());
        }
        if (task.getError() != null) {
            result.put("error", task.getError());
        }
        if (task.getCleaningReport() != null) {
            result.put("cleaningReport", task.getCleaningReport());
        }
        return result;
    }

    @GetMapping("/health")
    public Map<String, Object> healthCheck() {
        return Map.of("status", "ok");
    }

    @GetMapping("/download/{taskId}")
    public org.springframework.http.ResponseEntity<org.springframework.core.io.Resource> downloadResult(@PathVariable String taskId) {
        CleaningTask task = tasks.get(taskId);
        if (task == null || task.getCleanedFilePath() == null) {
            return org.springframework.http.ResponseEntity.notFound().build();
        }
        
        try {
            Path path = Paths.get(task.getCleanedFilePath());
            org.springframework.core.io.Resource resource = 
                new org.springframework.core.io.UrlResource(path.toUri());
            
            return org.springframework.http.ResponseEntity.ok()
                    .header(org.springframework.http.HttpHeaders.CONTENT_DISPOSITION, 
                           "attachment; filename=\"" + path.getFileName() + "\"")
                    .body(resource);
        } catch (Exception e) {
            return org.springframework.http.ResponseEntity.internalServerError().build();
        }
    }
    
    @PostMapping("/open-folder/{taskId}")
    public Map<String, Object> openFolder(@PathVariable String taskId) {
        CleaningTask task = tasks.get(taskId);
        if (task == null || task.getCleanedFilePath() == null) {
            return Map.of("success", false, "message", "Task not found");
        }
        
        try {
            Path filePath = Paths.get(task.getCleanedFilePath());
            Path folderPath = filePath.getParent();
            
            // 打开文件夹
            String os = System.getProperty("os.name").toLowerCase();
            ProcessBuilder pb;
            if (os.contains("win")) {
                pb = new ProcessBuilder("explorer.exe", folderPath.toString());
            } else if (os.contains("mac")) {
                pb = new ProcessBuilder("open", folderPath.toString());
            } else {
                pb = new ProcessBuilder("xdg-open", folderPath.toString());
            }
            
            pb.start();
            
            return Map.of("success", true, "folderPath", folderPath.toString());
        } catch (Exception e) {
            log.error("Failed to open folder", e);
            return Map.of("success", false, "message", e.getMessage());
        }
    }

    private List<Map<String, String>> getSampleData(Table table) {
        List<Map<String, String>> sample = new ArrayList<>();
        int sampleSize = Math.min(5, table.rowCount());
        
        for (int i = 0; i < sampleSize; i++) {
            Map<String, String> row = new HashMap<>();
            for (String col : table.columnNames()) {
                row.put(col, table.getString(i, col));
            }
            sample.add(row);
        }
        return sample;
    }

    @Data
    @NoArgsConstructor
    @AllArgsConstructor
    private static class CleaningTask {
        private String taskId;
        private String sessionId;
        private String userId;
        private String originalFilePath;
        private String cleanedFilePath;
        private String status;
        private int progress;
        private int rowCount;
        private int columnCount;
        private String error;
        private Map<String, Object> llmSuggestion;
        private Map<String, Object> cleaningReport;
    }
}
