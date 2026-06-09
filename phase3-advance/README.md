# 麒麟 OS Agent - Spring Boot 项目 (D4 完整整合版)

## 📚 项目介绍

本项目完整整合了 **D4 阶段**的所有清洗结果作为知识源，包括：
- 用户偏好数据
- 聊天日志
- 工具调用结果
- 知识库

## 🔧 环境要求

- Java 17 或更高版本
- Ollama 正在运行，模型为 gemma4:e2b

## 📦 D4 数据源

项目使用的 D4 清洗数据包括：

| 文件 | 说明 | 数量 |
|------|------|------|
| knowledge_cleaned.json | 知识库 | 5 条 |
| preferences_cleaned.json | 用户偏好 | 7 条 |
| chat_logs_cleaned.json | 聊天日志 | 15 条 |
| tool_result_cleaned.json | 工具调用结果 | 7 条 |

## 🚀 快速开始

### 1. 确保 Ollama 正在运行
```bash
ollama run gemma4:e2b
```

### 2. 启动项目（无需安装 Maven）
在项目根目录下运行：
```bash
.\mvnw.cmd spring-boot:run
```

第一次运行会自动下载 Maven 和所需依赖，请耐心等待。

## 📡 API 接口

### 基础接口（任务一、二）

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | /api/chat | 基础聊天 + 知识库检索 |

### D4 增强接口（任务三 + D4 完整数据）

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /api/d4-agent/overview | 获取 D4 数据概览 |
| GET | /api/d4-agent/preferences | 获取所有用户偏好 |
| GET | /api/d4-agent/preferences/{userId} | 获取指定用户的偏好 |
| GET | /api/d4-agent/chat-logs | 获取所有聊天日志 |
| GET | /api/d4-agent/chat-logs/{sessionId} | 获取指定会话的聊天日志 |
| GET | /api/d4-agent/tool-results | 获取所有工具调用结果 |
| GET | /api/d4-agent/knowledge | 获取所有知识 |
| POST | /api/d4-agent/load-preferences/{userId} | 加载 D4 中用户的偏好数据 |
| POST | /api/d4-agent/{userId}/preference | 设置用户偏好 |
| POST | /api/d4-agent/{userId}/chat | 带记忆和偏好的聊天 |

## 🧪 测试命令

### 基础测试

```bash
# 查看 D4 数据概览
curl http://localhost:8080/api/d4-agent/overview

# 查看所有用户偏好
curl http://localhost:8080/api/d4-agent/preferences

# 查看 U003 用户的偏好（驱动更新相关）
curl http://localhost:8080/api/d4-agent/preferences/U003

# 查看所有知识
curl http://localhost:8080/api/d4-agent/knowledge
```

### 加载 D4 用户偏好并聊天

```bash
# 加载 U003 用户的偏好（驱动更新相关）
curl -X POST http://localhost:8080/api/d4-agent/load-preferences/U003

# 用 U003 用户身份聊天（会自动应用该用户的偏好）
curl -X POST http://localhost:8080/api/d4-agent/U003/chat -H "Content-Type: application/json" -d "{\"message\": \"麒麟系统怎么更新驱动？\"}"

# 加载 U001 用户的偏好（简洁风格）
curl -X POST http://localhost:8080/api/d4-agent/load-preferences/U001

# 用 U001 用户身份聊天
curl -X POST http://localhost:8080/api/d4-agent/U001/chat -H "Content-Type: application/json" -d "{\"message\": \"给我个会议纪要模板\"}"
```

### 传统接口（保持兼容）

```bash
# 基础聊天
curl -X POST http://localhost:8080/api/chat -H "Content-Type: application/json" -d "{\"message\": \"你好\"}"

# 知识库检索
curl -X POST http://localhost:8080/api/chat -H "Content-Type: application/json" -d "{\"message\": \"如何在麒麟上离线安装 deb 包？\"}"
```

## 📂 项目结构

```
phase3-advance/
├── pom.xml
├── mvnw.cmd
├── README.md
├── TEST.md
├── 录屏操作步骤.txt
└── src/main/
    ├── java/com/example/agent/
    │   ├── AgentApplication.java
    │   ├── config/
    │   │   └── LLMConfig.java
    │   ├── controller/
    │   │   ├── ChatController.java       (基础接口)
    │   │   ├── AgentController.java      (原Agent接口)
    │   │   └── D4AgentController.java    (D4增强接口)
    │   ├── model/                        (D4数据模型)
    │   │   ├── UserPreference.java
    │   │   ├── ChatLog.java
    │   │   └── ToolResult.java
    │   ├── service/
    │   │   ├── KnowledgeItem.java
    │   │   ├── KnowledgeRetriever.java
    │   │   └── D4DataService.java        (D4数据加载服务)
    │   └── memory/
    │       └── MemoryService.java
    └── resources/
        ├── application.yml
        ├── knowledge_cleaned.json        (D4知识库)
        ├── preferences_cleaned.json      (D4用户偏好)
        ├── chat_logs_cleaned.json        (D4聊天日志)
        └── tool_result_cleaned.json      (D4工具结果)
```

## 🎯 D4 数据中的用户

| 用户 ID | 主要偏好 |
|---------|---------|
| U001 | output_style: 简洁、少废话 |
| U002 | emoji_policy: 允许少量 emoji |
| U003 | search_scope: 麒麟系统/驱动；driver_update_entry: 驱动管理器 |
| U005 | meeting_minutes_format: bullet 列表 |
| U006 | privacy_policy: 不保存测试手机号 |
