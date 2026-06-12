# 自动错误捕获、日志分析和修复建议系统

## 概述

本系统为 Spring Boot 项目提供完整的自动错误处理解决方案：

- **结构化日志**：JSON 格式，包含 traceId、堆栈信息、输入参数等
- **自动重试**：对瞬时错误进行指数退避重试
- **AI 分析**：集成 Ollama 分析错误并提供修复建议
- **持久化**：存储错误分析记录到数据库
- **全局异常处理**：统一的错误处理和响应

## 目录结构

```
src/main/java/com/yupi/datacleaning/
├── annotation/
│   └── AutoRetry.java          # 自动重试注解
├── aspect/
│   └── AutoRetryAspect.java    # 重试切面
├── config/
│   ├── GlobalExceptionHandler.java  # 全局异常处理
│   ├── RetryConfig.java            # 重试配置
│   └── TraceIdFilter.java          # TraceId 过滤器
├── dto/
│   ├── ErrorAnalysisResult.java    # 分析结果DTO
│   └── StructuredErrorLog.java     # 结构化日志DTO
├── entity/
│   ├── ErrorAnalysisRecord.java    # 错误记录实体
│   └── ResolutionStatus.java       # 解决状态枚举
├── repository/
│   └── ErrorAnalysisRepository.java # 数据访问层
├── service/
│   ├── ErrorAnalysisService.java   # 错误分析服务
│   └── ErrorRecordService.java     # 错误记录服务
└── util/
    └── MdcContextUtil.java         # MDC工具类
```

## 快速开始

### 1. 添加依赖（已添加）

```xml
<!-- Spring Retry -->
<dependency>
    <groupId>org.springframework.retry</groupId>
    <artifactId>spring-retry</artifactId>
</dependency>

<!-- Spring AOP -->
<dependency>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-starter-aop</artifactId>
</dependency>

<!-- Logback JSON encoder -->
<dependency>
    <groupId>net.logstash.logback</groupId>
    <artifactId>logstash-logback-encoder</artifactId>
    <version>7.4</version>
</dependency>
```

### 2. 配置日志（已创建）

`logback-spring.xml` 已配置，无需修改。

### 3. 使用自动重试

```java
import com.yupi.datacleaning.annotation.AutoRetry;
import org.springframework.stereotype.Service;

@Service
public class MyService {
    
    // 使用默认配置
    @AutoRetry
    public void doSomething() {
        // 业务逻辑
    }
    
    // 自定义配置
    @AutoRetry(
        maxAttempts = 5,
        initialInterval = 2000,
        multiplier = 1.5,
        maxInterval = 8000
    )
    public String callExternalApi() {
        // 调用外部API
    }
}
```

### 4. 手动设置上下文

```java
import com.yupi.datacleaning.util.MdcContextUtil;

public void myMethod() {
    // 设置TraceId
    MdcContextUtil.setTraceId();
    
    // 设置用户ID
    MdcContextUtil.setUserId("user123");
    
    // 设置方法名
    MdcContextUtil.setMethod("MyService.myMethod");
    
    // 设置输入参数
    MdcContextUtil.setInputParams("{\"name\":\"test\"}");
    
    try {
        // 业务逻辑
    } catch (Exception ex) {
        // 设置错误上下文
        MdcContextUtil.setErrorContext(ex, "myMethod", "params");
        throw ex;
    }
}
```

## 功能特性

### 1. 结构化日志

所有错误日志自动记录以下字段：

```json
{
  "timestamp": "2024-01-15T10:30:45.123+08:00",
  "level": "ERROR",
  "logger": "com.yupi.datacleaning.service.MyService",
  "traceId": "abc123...",
  "userId": "user123",
  "errorType": "NullPointerException",
  "method": "MyService.doSomething",
  "stackTrace": "java.lang.NullPointerException: ...",
  "inputParams": "{\"id\":123}",
  "retrySuccess": false,
  "suggestion": "【分析】... | 【建议】..."
}
```

日志文件位置：`logs/`

### 2. 自动重试机制

- **可重试异常**：`ConnectException`、`SocketTimeoutException`、`TimeoutException`等
- **重试策略**：最多 3 次，指数退避（1s → 2s → 4s）
- **成功标记**：`retrySuccess: true`

### 3. AI 错误分析

当错误发生时，系统自动：

1. 提取堆栈信息和上下文
2. 调用 Ollama 分析错误原因
3. 生成修复建议
4. 持久化到数据库
5. 记录到日志中

分析结果包含：
- 错误原因分析
- 修复建议
- 预防措施
- 相关文件
- 置信度（0-1）

### 4. 测试 API

可以使用以下 API 测试系统：

| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/debug/npe` | GET | 测试空指针异常 |
| `/api/debug/illegal?value=error` | GET | 测试参数异常 |
| `/api/debug/retry-test` | GET | 测试自动重试 |
| `/api/debug/errors` | GET | 获取错误记录列表 |
| `/api/debug/errors/{traceId}` | GET | 通过traceId查询详情 |
| `/api/debug/statistics` | GET | 获取错误统计 |

## 数据库表

系统自动创建 `error_analysis_records` 表：

```sql
CREATE TABLE error_analysis_records (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    trace_id VARCHAR(64) UNIQUE NOT NULL,
    error_type VARCHAR(100),
    method_name VARCHAR(200),
    stack_trace TEXT,
    input_params TEXT,
    error_analysis TEXT,
    fix_suggestion TEXT,
    prevention TEXT,
    related_files TEXT,
    confidence DOUBLE,
    retry_success BOOLEAN,
    resolution_status VARCHAR(20),
    created_at TIMESTAMP
);
```

## 配置说明

### application.yml

```yaml
# 日志配置
logging:
  file:
    path: logs

# 数据源（使用H2或MySQL）
spring:
  datasource:
    url: jdbc:h2:mem:testdb
    driver-class-name: org.h2.Driver
  h2:
    console:
      enabled: true
  jpa:
    hibernate:
      ddl-auto: update
```

## 使用示例

### 示例 1：基础使用

```java
@RestController
public class MyController {
    
    @GetMapping("/api/data")
    public ApiResponse<String> fetchData() {
        // 自动捕获异常
        String data = null;
        return ApiResponse.success(data.toUpperCase());
    }
}
```

### 示例 2：带重试的服务

```java
@Service
public class ExternalService {
    
    @Autowired
    private WebClient webClient;
    
    @AutoRetry(maxAttempts = 3)
    public String callThirdPartyApi(String param) {
        return webClient.get()
            .uri("https://api.example.com/data")
            .retrieve()
            .bodyToMono(String.class)
            .block();
    }
}
```

### 示例 3：手动记录错误

```java
@Service
public class DataService {
    
    @Autowired
    private ErrorAnalysisService analysisService;
    
    public void processData(String data) {
        try {
            validate(data);
        } catch (ValidationException ex) {
            String suggestion = analysisService.recordAndAnalyze(
                ex, 
                "DataService.processData", 
                data
            );
            log.warn("验证失败: {}", suggestion);
            throw ex;
        }
    }
}
```

## 监控和查询

### 查看日志

```bash
# 应用日志
tail -f logs/data-cleaning-agent.log

# 错误日志
tail -f logs/data-cleaning-agent-error.log

# 错误分析日志
tail -f logs/data-cleaning-agent-error-analysis.log
```

### 查询数据库

如果使用 H2 控制台：

1. 访问：`http://localhost:8080/h2-console`
2. JDBC URL：`jdbc:h2:mem:testdb`
3. 执行：`SELECT * FROM error_analysis_records ORDER BY created_at DESC`

## 最佳实践

1. **总是设置 TraceId**：在异步任务、定时任务中手动设置
2. **合理使用重试**：只对瞬时错误启用重试
3. **参数长度限制**：避免记录过大的输入参数（已自动截断）
4. **检查置信度**：AI 建议置信度低时需要人工审核
5. **定期清理**：清理已解决的历史错误记录

## 扩展和自定义

### 自定义提示词

修改 `ErrorAnalysisService.buildAnalysisPrompt()`

### 自定义可重试异常

修改 `AutoRetryAspect` 中的 `DEFAULT_RETRYABLE`

### 添加更多错误建议

扩展 `ErrorAnalysisService.getDefaultSuggestion()`

## 故障排查

### Ollama 连接失败

确保 Ollama 正在运行并且模型已下载：

```bash
ollama run gemma4:2b
```

### 日志未生成

检查 `logback-spring.xml` 配置是否正确，确认日志目录权限。

### 数据库表未创建

确保 JPA 的 `ddl-auto` 设置为 `update` 或 `create`。
