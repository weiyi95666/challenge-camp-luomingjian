package com.yupi.datacleaning.service;

import com.yupi.datacleaning.dto.ErrorAnalysisResult;
import com.yupi.datacleaning.entity.ErrorAnalysisRecord;
import com.yupi.datacleaning.entity.ResolutionStatus;
import com.yupi.datacleaning.repository.ErrorAnalysisRepository;
import com.yupi.datacleaning.util.MdcContextUtil;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;
import java.util.Optional;

/**
 * 错误记录服务
 */
@Slf4j
@Service
public class ErrorRecordService {
    
    @Autowired
    private ErrorAnalysisRepository repository;
    
    /**
     * 记录错误分析结果
     */
    @Transactional
    public ErrorAnalysisRecord recordError(
            Throwable throwable,
            String methodName,
            String inputParams,
            ErrorAnalysisResult analysis,
            Boolean retrySuccess
    ) {
        try {
            String traceId = MdcContextUtil.getTraceId();
            if (traceId == null) {
                traceId = MdcContextUtil.setTraceId();
            }
            
            ErrorAnalysisRecord record = ErrorAnalysisRecord.builder()
                .traceId(traceId)
                .errorType(throwable.getClass().getSimpleName())
                .methodName(methodName)
                .stackTrace(getStackTrace(throwable))
                .inputParams(inputParams)
                .errorAnalysis(analysis.getErrorAnalysis())
                .fixSuggestion(analysis.getFixSuggestion())
                .prevention(analysis.getPrevention())
                .relatedFiles(analysis.getRelatedFiles())
                .confidence(analysis.getConfidence())
                .retrySuccess(retrySuccess)
                .resolutionStatus(ResolutionStatus.ANALYZED)
                .build();
            
            ErrorAnalysisRecord saved = repository.save(record);
            log.info("错误记录已保存, TraceId: {}, ID: {}", traceId, saved.getId());
            
            return saved;
            
        } catch (Exception e) {
            log.warn("保存错误记录失败", e);
            return null;
        }
    }
    
    /**
     * 获取错误记录
     */
    public Optional<ErrorAnalysisRecord> getByTraceId(String traceId) {
        return repository.findByTraceId(traceId);
    }
    
    /**
     * 获取待解决的错误
     */
    public List<ErrorAnalysisRecord> getPendingErrors() {
        return repository.findByResolutionStatusOrderByCreatedAtDesc(
            ResolutionStatus.PENDING
        );
    }
    
    /**
     * 更新解决状态
     */
    @Transactional
    public Optional<ErrorAnalysisRecord> updateStatus(Long id, ResolutionStatus status) {
        return repository.findById(id).map(record -> {
            record.setResolutionStatus(status);
            return repository.save(record);
        });
    }
    
    /**
     * 统计错误类型
     */
    public List<Object[]> getErrorTypeStatistics() {
        return repository.countByErrorType();
    }
    
    /**
     * 获取堆栈信息
     */
    private String getStackTrace(Throwable throwable) {
        StringBuilder sb = new StringBuilder();
        sb.append(throwable.getClass().getName())
          .append(": ")
          .append(throwable.getMessage())
          .append("\n");
        
        StackTraceElement[] elements = throwable.getStackTrace();
        int limit = Math.min(elements.length, 30);
        for (int i = 0; i < limit; i++) {
            sb.append("  at ").append(elements[i]).append("\n");
        }
        
        if (elements.length > 30) {
            sb.append("  ... [").append(elements.length - 30).append(" more]");
        }
        
        return sb.toString();
    }
}
