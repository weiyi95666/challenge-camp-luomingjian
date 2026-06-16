# MCP Agent 项目变更日志

## [2.0.0] - 2026-06-15
### 重大更新
- ✅ 完成 LLM API 集成
- ✅ 创建现代化 Web 聊天界面
- ✅ 升级为完整的智能体架构

### 新增功能
- `agent/llm_client.py` - 新增 LLM 客户端，支持 OpenAI 兼容 API
- `agent/core.py` - 智能体核心升级，支持 LLM 生成回复
- `static/` 目录 - 全新的 Web 前端界面
  - `index.html` - 主页面
  - `style.css` - 现代化样式
  - `app.js` - 交互逻辑
- `api_server.py` - 新增 Web 界面路由
- `.env` - 配置文件，支持 API Key 管理
- `config.py` - 配置管理模块
- `test_api_connection.py` - API 连接测试脚本
- `test_llm.py` - LLM 集成测试脚本
- `API_对接指南.md` - API 对接文档
- `CHANGELOG.md` - 本变更日志

### 改进
- `tools/web_search.py` - 改进网络搜索，添加备用方案和智能知识库
- `requirements.txt` - 更新依赖列表

---

## [1.1.0] - 2026-06-15
### 新增功能
- `tools/weather_api.py` - 真实天气查询（Open-Meteo API）
- `tools/web_search.py` - 网络搜索工具
- `tools/webpage.py` - 网页访问工具
- `agent/` 目录 - 新增智能体架构
  - `memory.py` - 对话记忆系统
  - `tool_selector.py` - 工具选择器
  - `llm_client.py` - LLM 客户端框架
  - `core.py` - 智能体核心
- `utils.py` - 共享工具函数，消除重复代码
- `快速开始.md` - 中文使用文档
- `联网功能说明.md` - 联网功能说明
- `test_internet.py` - 联网功能测试

### 改进
- `weather_server.py` - 增强为支持真实 API 和备用方案
- `client.py` - 简化，使用共享函数
- `api_server.py` - 新增多个 API 端点（/history, /clear）
- `write_server.py` - 改进安全性，防止路径遍历
- `desktop_chat.py` - 保持桌面应用功能
- 所有模块完善类型注解

---

## [1.0.0] - 2026-06-15 (初始版本)
### 基础功能
- `mcp_framework.py` - MCP 工具注册与调用框架
- `weather_server.py` - 模拟天气查询工具
- `write_server.py` - 文件写入工具
- `rag_server.py` - RAG 查询工具（模拟）
- `client.py` - 命令行客户端
- `api_server.py` - Flask API 服务器
- `desktop_chat.py` - Tkinter 桌面聊天应用
- `vector_retriever.py` - 向量检索框架
- `servers_config.json` - 工具配置文件
- `requirements.txt` - 项目依赖
- `start_all.bat`, `start_all.ps1` - 启动脚本
