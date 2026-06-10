# 数据清洗智能体

一个基于 Spring Boot、LangChain4j 和本地 Ollama 模型的数据清洗智能体系统，具备完整的记忆、学习和自动修复能力。

## 核心功能

### 数据清洗能力
- **数据去重** - 自动识别并移除重复行
- **敏感信息处理** - 自动检测并脱敏手机号、身份证号、邮箱等
- **日期标准化** - 识别多种日期格式并统一标准化
- **缺失值处理** - 智能填充或删除缺失值
- **文本清洗** - 去除空格、统一格式
- **异常值检测** - 检测并处理异常数据

### 智能特性
- **本地 Ollama 集成** - 使用本地模型，无需云端 API
- **短期记忆** - 会话级别的上下文记忆（Caffeine 缓存）
- **长期记忆** - 用户偏好记忆（JPA 存储）
- **工作流引擎** - 基于 LangGraph 概念的工作流
- **自动修复** - 遇到错误时自动修复并继续
- **结构化日志** - 完整的清洗过程记录

## 技术栈

- **后端框架**: Spring Boot 3.2
- **数据处理**: Tablesaw (Java 版 pandas)
- **LLM 集成**: LangChain4j + Ollama
- **缓存**: Caffeine (短期记忆)
- **持久化**: Spring Data JPA
- **日志**: SLF4J + Logback

## 快速开始

### 前置要求

1. **Java 17 或更高版本**
2. **Maven 3.8+**
3. **Ollama 服务** (必须本地运行)

### 安装 Ollama

```bash
# 下载并安装 Ollama
# https://ollama.ai/download

# 启动 Ollama 服务
ollama serve

# 拉取 gemma4 模型
ollama pull gemma4:e2b
```

### 运行项目

```bash
# 1. 进入项目目录
cd phase3.2-advance

# 2. 编译项目
mvn clean compile

# 3. 运行项目
mvn spring-boot:run

# 或者直接运行打包后的 JAR
mvn clean package
java -jar target/data-cleaning-agent-1.0.0.jar
```

### 访问应用

启动成功后，在浏览器中访问：

- **Web 界面**: http://localhost:8080
- **健康检查**: http://localhost:8080/api/clean/health

## 使用指南

### 1. 上传数据文件

在 Web 界面上点击上传区域，或拖拽文件到页面上。支持格式：
- CSV (.csv)
- Excel (.xlsx, .xls)
- JSON (.json)

### 2. 查看数据预览

上传完成后，系统会自动：
- 分析数据结构
- 显示数据样本
- 提供统计信息

### 3. 开始清洗

点击「开始清洗」按钮，系统会：
1. 调用 Ollama 分析数据
2. 应用清洗规则
3. 执行数据清洗
4. 显示进度和 LLM 建议

### 4. 查看结果

清洗完成后，可以查看：
- 清洗进度详情
- Ollama 的清洗建议
- 数据变化统计
- 完整的日志记录

## API 接口

### 上传文件

```http
POST /api/clean/upload
Content-Type: multipart/form-data

file: [文件]
userId: [可选用户ID]
```

响应示例：
```json
{
  "taskId": "uuid",
  "sessionId": "uuid",
  "status": "uploaded",
  "analysis": {
    "rowCount": 100,
    "columnCount": 10,
    "columns": [...]
  },
  "sample": [...]
}
```

### 开始清洗

```http
POST /api/clean/start/{taskId}
Content-Type: application/json

{
  "autoAcceptLlm": true,
  "rules": [...]
}
```

### 查询状态

```http
GET /api/clean/status/{taskId}
```

响应示例：
```json
{
  "taskId": "uuid",
  "status": "running",
  "progress": 50,
  "llmSuggestion": {
    "suggestion": "建议对手机号列进行脱敏",
    "confidence": 0.8
  }
}
```

### 健康检查

```http
GET /api/clean/health
```

## 配置说明

在 `application.yml` 中配置：

```yaml
ollama:
  base-url: http://localhost:11434  # Ollama 服务地址
  model-name: gemma4:e2b             # 使用的模型
  timeout-seconds: 60                # 超时时间

server:
  port: 8080

spring:
  servlet:
    multipart:
      max-file-size: 100MB          # 最大文件大小
```

## 项目结构

```
phase3.2-advance/
├── src/main/java/com/yupi/datacleaning/
│   ├── DataCleaningAgentApplication.java    # 主应用
│   ├── cleaning/
│   │   └── DataCleaner.java                  # 数据清洗核心
│   ├── controller/
│   │   ├── CleaningController.java           # 清洗控制器
│   │   └── HomeController.java               # 主页控制器
│   ├── llm/
│   │   └── OllamaClient.java                 # Ollama 客户端
│   ├── memory/
│   │   ├── ShortTermMemoryService.java       # 短期记忆
│   │   └── LongTermMemoryService.java        # 长期记忆
│   └── workflow/                              # LangGraph 工作流
│       ├── Node.java
│       ├── StateGraph.java
│       ├── WorkflowState.java
│       ├── ConditionalEdge.java
│       └── WorkflowExecutor.java
├── src/main/resources/
│   ├── static/
│   │   └── index.html                        # 前端界面
│   └── application.yml                       # 配置文件
├── test_data.csv                             # 测试数据
├── pom.xml                                   # Maven 配置
└── README.md                                 # 本文档
```

## 测试数据

项目包含测试数据文件 `test_data.csv`，包含以下问题场景：
- 重复数据行
- 敏感信息（手机号、邮箱）
- 多种日期格式
- 缺失值
- 格式不一致

## 记忆系统

### 短期记忆
- 存储会话上下文
- 保存最近的对话历史
- 记录 LLM 建议
- 30分钟过期
- 使用 Caffeine 缓存

### 长期记忆
- 用户偏好存储
- 常用清洗步骤
- 配置记忆
- 跨会话持久化

## 清洗步骤

系统自动执行的清洗流程：
1. **数据加载** - 读取并解析文件
2. **数据去重** - 移除重复行
3. **文本清洗** - 去除空格、统一格式
4. **敏感信息处理** - 脱敏手机号、邮箱等
5. **日期标准化** - 统一日期格式
6. **缺失值处理** - 智能填充缺失值
7. **结果保存** - 输出清洗后的数据

## 故障排除

### Ollama 连接失败

确保 Ollama 服务正在运行：
```bash
ollama serve
```

检查模型是否已下载：
```bash
ollama list
```

### 编译错误

确保使用 Java 17：
```bash
java -version
```

### 内存不足

大文件处理时，可以增加 JVM 内存：
```bash
java -Xms2g -Xmx8g -jar target/data-cleaning-agent-1.0.0.jar
```

## 许可证

MIT License

## 贡献

欢迎提交 Issue 和 Pull Request！
