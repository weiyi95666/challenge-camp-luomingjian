package com.yupi.datacleaning.entity;

import jakarta.persistence.*;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;
import org.hibernate.annotations.CreationTimestamp;

import java.time.LocalDateTime;

/**
 * 错误分析记录实体
 */
@Entity
@Table(name = "error_analysis_records")
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class ErrorAnalysisRecord {
    
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;
    
    @Column(unique = true, nullable = false, length = 64)
    private String traceId;
    
    @Column(name = "error_type", length = 100)
    private String errorType;
    
    @Column(name = "method_name", length = 200)
    private String methodName;
    
    @Column(name = "stack_trace", columnDefinition = "TEXT")
    private String stackTrace;
    
    @Column(name = "input_params", columnDefinition = "TEXT")
    private String inputParams;
    
    @Column(name = "error_analysis", columnDefinition = "TEXT")
    private String errorAnalysis;
    
    @Column(name = "fix_suggestion", columnDefinition = "TEXT")
    private String fixSuggestion;
    
    @Column(name = "prevention", columnDefinition = "TEXT")
    private String prevention;
    
    @Column(name = "related_files", columnDefinition = "TEXT")
    private String relatedFiles;
    
    @Column(name = "confidence")
    private Double confidence;
    
    @Column(name = "retry_success")
    private Boolean retrySuccess;
    
    @Column(name = "resolution_status")
    @Enumerated(EnumType.STRING)
    private ResolutionStatus resolutionStatus;
    
    @Column(name = "created_at")
    @CreationTimestamp
    private LocalDateTime createdAt;
}
