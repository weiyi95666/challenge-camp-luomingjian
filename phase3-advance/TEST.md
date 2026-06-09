# 麒麟 OS Agent 测试用例 (D4 完整整合版)

---

## 📋 测试总览

本测试用例完整覆盖：
- ✅ 任务一：LangChain4j 基础聊天
- ✅ 任务二：知识库检索 + 意图识别
- ✅ 任务三：记忆 + 偏好 + 检索（基于 D4 清洗数据

---

## 1. 启动项目初始化

### 1.1 启动 Spring Boot 项目
```bash
cd phase3-advance
.\mvnw.cmd spring-boot:run
```

---

## 2. D4 清洗数据验证

### 2.1 查看 D4 数据概览
```bash
curl http://localhost:8080/api/d4-agent/overview
```
**预期**：显示 4 类数据的统计信息

### 2.2 查看所有用户偏好
```bash
curl http://localhost:8080/api/d4-agent/preferences
```
**预期**：显示 U001-U006 的 7 条用户偏好

### 2.3 查看知识库
```bash
curl http://localhost:8080/api/d4-agent/knowledge
```
**预期**：显示 5 条知识库内容

### 2.4 查看 U003 用户的偏好（驱动更新相关）
```bash
curl http://localhost:8080/api/d4-agent/preferences/U003
```
**预期**：显示 search_scope 和 driver_update_entry 两条偏好

### 2.5 查看聊天日志（会话 S102）
```bash
curl http://localhost:8080/api/d4-agent/chat-logs/S102
```

---

## 3. 任务一测试：LangChain4j 基础聊天

### 3.1 普通聊天
```bash
curl -X POST http://localhost:8080/api/chat -H "Content-Type: application/json" -d "{\"message\": \"你好\"}"
```

---

## 4. 任务二测试：知识库检索 + 意图识别

### 4.1 系统知识问题 - 安装 deb 包（触发知识库检索）
```bash
curl -X POST http://localhost:8080/api/chat -H "Content-Type: application/json" -d "{\"message\": \"如何在麒麟上离线安装 deb 包？\"}"
```

### 4.2 系统知识问题 - 驱动更新（触发知识库检索）
```bash
curl -X POST http://localhost:8080/api/chat -H "Content-Type: application/json" -d "{\"message\": \"麒麟系统怎么更新驱动？\"}"
```

### 4.3 普通聊天问题（不触发知识库检索）
```bash
curl -X POST http://localhost:8080/api/chat -H "Content-Type: application/json" -d "{\"message\": \"今天天气怎么样？\"}"
```

---

## 5. 任务三测试：记忆 + 偏好 + 检索（D4 增强接口）

### 5.1 场景 1：U003 用户 + 驱动更新偏好
```bash
# 步骤1: 加载 D4 中 U003 的偏好
curl -X POST http://localhost:8080/api/d4-agent/load-preferences/U003

# 步骤2: 询问驱动更新（结合用户偏好 + 知识库检索）
curl -X POST http://localhost:8080/api/d4-agent/U003/chat -H "Content-Type: application/json" -d "{\"message\": \"麒麟系统怎么更新驱动？\"}"
```

### 5.2 场景 2：U001 用户 + 简洁风格偏好
```bash
# 步骤1: 加载 D4 中 U001 的偏好（简洁、少废话）
curl -X POST http://localhost:8080/api/d4-agent/load-preferences/U001

# 步骤2: 询问会议纪要（结合用户偏好 + 知识库检索）
curl -X POST http://localhost:8080/api/d4-agent/U001/chat -H "Content-Type: application/json" -d "{\"message\": \"给我个会议纪要模板\"}"
```

### 5.3 场景 3：记忆功能测试（多轮对话）
```bash
# 步骤1: 加载 U003 偏好
curl -X POST http://localhost:8080/api/d4-agent/load-preferences/U003

# 步骤2: 第一轮对话 - 自我介绍
curl -X POST http://localhost:8080/api/d4-agent/U003/chat -H "Content-Type: application/json" -d "{\"message\": \"我叫测试用户\"}"

# 步骤3: 第二轮对话 - 测试记忆
curl -X POST http://localhost:8080/api/d4-agent/U003/chat -H "Content-Type: application/json" -d "{\"message\": \"我叫什么名字？\"}"
```

### 5.4 场景 4：U005 用户 + 会议纪要偏好
```bash
# 步骤1: 加载 D4 中 U005 的偏好
curl -X POST http://localhost:8080/api/d4-agent/load-preferences/U005

# 步骤2: 询问会议纪要
curl -X POST http://localhost:8080/api/d4-agent/U005/chat -H "Content-Type: application/json" -d "{\"message\": \"帮我写个会议纪要\"}"
```

### 5.5 自定义偏好设置
```bash
# 给 U003 设置自定义偏好
curl -X POST http://localhost:8080/api/d4-agent/U003/preference -H "Content-Type: application/json" -d "{\"key\": \"language\", \"value\": \"中文\"}"

# 验证自定义偏好生效
curl -X POST http://localhost:8080/api/d4-agent/U003/chat -H "Content-Type: application/json" -d "{\"message\": \"你好\"}"
```

---

## 6. 其他数据查看

### 6.1 查看工具调用结果
```bash
curl http://localhost:8080/api/d4-agent/tool-results
```

---

## 📊 D4 数据使用说明

本项目使用的 D4 清洗数据：

| 数据类型 | 文件 | 数量 | 用途 |
|---------|------|------|------|
| 知识库 | knowledge_cleaned.json | 5条 | 知识检索 |
| 用户偏好 | preferences_cleaned.json | 7条 | 个性化回复 |
| 聊天日志 | chat_logs_cleaned.json | 15条 | 参考对话 |
| 工具结果 | tool_result_cleaned.json | 7条 | 工具调用记录 |

| 用户 ID | 主要偏好 |
|---------|---------|
| U001 | output_style: 简洁、少废话 |
| U002 | emoji_policy: 允许少量 emoji |
| U003 | search_scope: 麒麟系统/驱动；driver_update_entry: 驱动管理器 |
| U005 | meeting_minutes_format: bullet 列表 |
| U006 | privacy_policy: 不保存测试手机号 |
