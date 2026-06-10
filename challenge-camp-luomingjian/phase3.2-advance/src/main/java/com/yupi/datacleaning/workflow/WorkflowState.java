package com.yupi.datacleaning.workflow;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.io.Serializable;
import java.time.LocalDateTime;

/**
 * 简单的工作流状态
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class WorkflowState implements Serializable {
    
    private static final long serialVersionUID = 1L;
    
    private String taskId;
    private String sessionId;
    private String userId;
    
    private String status;
    private String message;
    private int progress;
    
    private LocalDateTime startTime;
    private LocalDateTime endTime;
}
