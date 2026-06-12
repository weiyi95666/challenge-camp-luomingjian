package com.yupi.datacleaning.repository;

import com.yupi.datacleaning.entity.ErrorAnalysisRecord;
import com.yupi.datacleaning.entity.ResolutionStatus;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;

import java.time.LocalDateTime;
import java.util.List;
import java.util.Optional;

/**
 * 错误分析记录仓库
 */
@Repository
public interface ErrorAnalysisRepository extends JpaRepository<ErrorAnalysisRecord, Long> {
    
    /**
     * 通过 traceId 查找
     */
    Optional<ErrorAnalysisRecord> findByTraceId(String traceId);
    
    /**
     * 查找待解决的错误
     */
    List<ErrorAnalysisRecord> findByResolutionStatusOrderByCreatedAtDesc(
        ResolutionStatus status
    );
    
    /**
     * 查找特定类型的错误
     */
    List<ErrorAnalysisRecord> findByErrorTypeOrderByCreatedAtDesc(String errorType);
    
    /**
     * 统计错误类型数量
     */
    @Query("SELECT e.errorType, COUNT(e) FROM ErrorAnalysisRecord e GROUP BY e.errorType")
    List<Object[]> countByErrorType();
    
    /**
     * 查询时间范围内的错误
     */
    List<ErrorAnalysisRecord> findByCreatedAtBetweenOrderByCreatedAtDesc(
        LocalDateTime start, LocalDateTime end
    );
    
    /**
     * 查找置信度高的错误分析
     */
    List<ErrorAnalysisRecord> findByConfidenceGreaterThanEqualOrderByCreatedAtDesc(
        Double confidence
    );
}
