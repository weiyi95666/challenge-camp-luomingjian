# 数据清洗智能体 + 聊天助手 - 完整项目文档

## 📋 项目概览

这是一个集数据清洗和智能对话于一体的Web应用，包含两套核心功能：

1. **数据清洗智能体**：自动清洗CSV/Excel数据文件，支持去重、脱敏、日期标准化、缺失值填充等
2. **智能对话助手**：类似DeepSeek的聊天界面，支持深度思考、联网搜索、文件上传等

## 🚀 快速开始

### 前置要求

- **Java 17+**
- **Maven 3.8+**
- **Node.js 18+**
- **Ollama**（可选，用于本地大模型）

### 1. 安装 Ollama（可选但推荐）

```bash
# 下载安装 Ollama
# https://ollama.ai/download

# 拉取 gemma 或其他模型
ollama pull gemma2:2b

# 启动服务
ollama serve
```

### 2. 启动后端服务

```bash
cd phase3.2-advance

# 编译项目
mvn clean compile

# 运行项目
mvn spring-boot:run
```

后端将在 `http://localhost:8080` 启动

### 3. 启动前端服务

```bash
cd ai-code-helper-frontend

# 安装依赖
npm install

# 开发模式启动
npm run dev
```

前端将在 `http://localhost:5173` 或类似地址启动

## 🎯 功能特性

### 数据清洗功能

| 功能 | 说明
|--------|------
| 📁 文件上传 | 支持 CSV、Excel、JSON 文件拖拽上传
| 📊 数据预览 | 显示文件概览和数据样本
| 🧹 数据清洗 | 自动去重、脱敏、标准化、填充
| 📋 清洗报告 | 详细的清洗统计和结果下载

### 智能对话功能

| 功能 | 说明
|------|------
| 💬 智能对话 | 与AI助手自然语言对话
| 🧠 深度思考 | 可切换深度思考/快速回答模式
| 🔍 联网搜索 | 可选联网搜索能力（模拟实现）
| 📎 文件上传 | 支持附件上传功能
| 📜 历史对话 | 对话历史管理（新建/重命名/删除/切换）
| 📝 Markdown | 支持Markdown渲染和代码高亮
| 📱 响应式设计 | 美观的渐变深色主题

## 📁 项目结构

```
phase3.2-advance/
├── src/main/java/com/yupi/datacleaning/
│   ├── DataCleaningAgentApplication.java    # 主入口
│   ├── cleaning/
│   │   ├── DataCleaner.java                  # 数据清洗核心
│   │   └── CleaningReport.java                # 清洗报告
│   ├── controller/
│   │   ├── CleaningController.java         # 数据清洗API
│   │   └── ChatController.java            # 聊天API
│   ├── model/
│   │   ├── ChatMessage.java
│   │   └── Conversation.java
│   ├── service/
│   │   ├── ChatService.java
│   │   └── SearchService.java
│   ├── memory/
│   │   ├── LongTermMemoryService.java      # 长期记忆
│   │   └── ShortTermMemoryService.java    # 短期记忆
│   └── llm/
│       └── OllamaClient.java                # Ollama客户端
├── ai-code-helper-frontend/
│   └── src/
│       ├── App.vue                        # 主应用
│       └── components/
│           └── DataCleaningView.vue        # 数据清洗页面
└── src/main/resources/
    └── application.yml                      # 配置文件
```

## 🔧 API 接口

### 聊天 API (`/api/chat`)

| 方法 | 路径 | 功能
|------|--------|------
| POST | `/conversations` | 创建新对话
| GET | `/conversations` | 获取所有对话
| GET | `/conversations/{id}` | 获取对话详情
| PUT | `/conversations/{id}` | 更新对话（重命名）
| DELETE | `/conversations/{id}` | 删除对话
| POST | `/send` | 发送消息
| POST | `/upload` | 上传附件

### 数据清洗 API (`/api/clean`)

| 方法 | 路径 | 功能
|------|--------|------
| POST | `/upload` | 上传文件
| POST | `/start/{taskId}` | 开始清洗
| GET | `/status/{taskId}` | 查询进度
| GET | `/download/{taskId}` | 下载结果

## 📝 配置说明

在 `application.yml` 中配置 Ollama：

```yaml
ollama:
  base-url: http://localhost:11434
  model-name: gemma2:2b
  timeout-seconds: 60
  enabled: true
```

## 🎨 界面展示

### 对话界面
- 左侧：对话历史侧边栏
- 右侧：聊天消息区域
- 底部：聊天输入和模式选择
- 支持深色主题，美观渐变

### 数据清洗界面
- 文件拖拽上传
- 数据预览表格
- 清洗报告展示

## 📊 数据清洗能力

- **去重：自动移除重复行
- **脱敏：手机号、邮箱、身份证号脱敏处理
- **日期标准化：多种格式统一
- **缺失值填充：均值填充数值，空值填充文本
- **文本清洗：去除空格和格式化

## 🛠️ 技术栈

### 后端
- Spring Boot 3.2
- Tablesaw（数据处理）
- LangChain4j + Ollama

### 前端
- Vue 3
- Vite
- Axios
- Marked (Markdown)

## 🧪 测试数据

项目包含 `test_data.csv` 用于测试数据清洗功能。

## 📄 许可证

MIT License

