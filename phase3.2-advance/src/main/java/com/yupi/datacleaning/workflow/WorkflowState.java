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
    
    // Budget control fields
    private int tokenCount;
    private int executionSteps;
    private int maxTokenCount;
    private int maxExecutionSteps;
    
    public void incrementTokenCount(int tokens) {
        this.tokenCount += tokens;
        checkBudget();
    }
    
    public void incrementExecutionSteps() {
        this.executionSteps++;
        checkBudget();
    }
    
    private void checkBudget() {
        if (maxTokenCount > 0 && tokenCount > maxTokenCount) {
            throw new BudgetExceededException("Token budget exceeded: " + tokenCount + " > " + maxTokenCount);
        }
        if (maxExecutionSteps > 0 && executionSteps > maxExecutionSteps) {
            throw new BudgetExceededException("Execution steps budget exceeded: " + executionSteps + " > " + maxExecutionSteps);
        }
    }
}
