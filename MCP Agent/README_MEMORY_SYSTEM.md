# 三层记忆系统

为 MCP Agent 智能体增加的短期、中期、长期记忆功能。

## 📋 项目概述

在不修改原有核心文件的前提下，为现有智能体系统添加完整的记忆功能。

### ⚙️ 系统要求
- Python 3.7+
- Flask
- 不需要额外的向量数据库（使用本地存储作为 fallback）

### 📁 新增文件

| 文件名 | 说明 |
|--------|------|
| `memory_system.py` | 三层记忆系统的核心实现 |
| `agent_with_memory.py` | 集成了记忆系统的智能体 |
| `api_server_with_memory.py` | 带记忆功能的 API 服务器 |
| `test_memory_system.py` | 记忆系统测试文件 |
| `README_MEMORY_SYSTEM.md` | 本文档 |

## 🧠 记忆系统架构

### 1. 短期记忆 (Short-Term Memory)
- **存储位置**: 内存（deque）
- **特点**: 
  - 当前会话的最近 N 轮对话
  - 会话结束后自动清空
  - 默认最大长度：15 条消息
- **用途**: 上下文理解、连续对话

### 2. 中期记忆 (Mid-Term Memory)
- **存储位置**: SQLite 数据库 (`mid_term_memory.db`)
- **特点**: 
  - 跨会话持久化
  - 存储用户偏好设置
  - 存储用户事实信息
  - 存储会话摘要
- **用途**: 个性化设置、用户档案

### 3. 长期记忆 (Long-Term Memory)
- **存储位置**: 本地 JSON 文件 (`long_term_memory.json`)
- **特点**: 
  - 重要事实性知识
  - 支持语义检索
  - 可扩展支持 Milvus 向量数据库
- **用途**: 事实召回、知识库

## 🚀 快速开始

### 1. 运行测试
```bash
cd MCP Agent
.venv/Scripts/python.exe test_memory_system.py
```

### 2. 启动带记忆的 API 服务器
```bash
cd MCP Agent
.venv/Scripts/python.exe api_server_with_memory.py
```

服务器将在 `http://127.0.0.1:5002` 启动（端口 5002，避免与原有服务冲突）

### 3. 使用原有 API 服务器（也可以）

如果需要在原有 API 服务器中使用记忆功能，您可以修改 `api_server.py`，替换智能体实例。

## 🔌 API 接口

### 聊天接口
```
POST /chat
Content-Type: application/json

{
  "text": "你好，我叫小明",
  "response_mode": "fast"
}
```

### 记忆系统状态
```
GET /api/memory/status
```

### 清空短期记忆
```
POST /api/memory/clear-short-term
```

### 管理长期记忆
```
GET /api/memory/long-term
POST /api/memory/add-long-term
```

### 管理用户偏好
```
GET /api/memory/preferences
POST /api/memory/preferences
```

### 管理用户事实
```
GET /api/memory/facts?category=identity
```

## 💡 使用示例

### Python 直接使用

```python
from agent_with_memory import ChatAgentWithMemory

# 创建智能体
agent = ChatAgentWithMemory()

# 对话
response = agent.process_message("你好，我叫测试用户")
print(response)

response = agent.process_message("记住，我喜欢蓝色")
print(response)

response = agent.process_message("我喜欢什么颜色？")
print(response)

# 获取记忆状态
status = agent.get_memory_status()
print(status)
```

### 记忆触发关键词

当用户消息包含以下关键词时，会自动存入长期记忆：
- "记住"、"记得"
- "我叫"、"我的名字是"
- "我喜欢"、"我不喜欢"
- "我住"、"我的生日是"
- 等等

## 🔧 扩展开发

### 集成 Milvus 向量数据库

在 `memory_system.py` 的 `LongTermMemory` 类中：

```python
def _init_milvus(self) -> bool:
    """初始化 Milvus 连接"""
    # 在这里实现真实的 Milvus 连接
    # 参考原有 RAG 系统的实现
    pass
```

### 自定义 Embedding 模型

修改 `LongTermMemory` 类，添加真实的 Embedding 调用：

```python
def _get_embedding(self, text: str) -> List[float]:
    """获取文本的 Embedding 向量"""
    # 调用 DashScope 或其他 Embedding API
    pass
```

## 📊 数据文件

- `mid_term_memory.db`: SQLite 数据库（中期记忆）
- `long_term_memory.json`: JSON 文件（长期记忆）

**注意**: 这些文件会自动创建，不需要手动管理。

## 🔐 兼容性

- ✅ 完全兼容原有 API 接口
- ✅ 不修改任何核心文件
- ✅ 可独立运行，也可集成到现有系统
- ✅ Python 3.7 友好

## 📝 注意事项

1. **端口冲突**: 新的 API 服务器使用端口 5002，避免与原有服务的 5001 冲突
2. **网络连接**: 如果代理连接有问题，请检查网络设置
3. **数据备份**: 建议定期备份 `*.db` 和 `*.json` 文件

## 🎯 下一步

- [ ] 集成真实的 Milvus 向量数据库
- [ ] 添加更高级的 Embedding 模型
- [ ] 实现记忆的重要性评分和淘汰策略
- [ ] 添加记忆编辑和管理界面
- [ ] 实现对话摘要自动生成

---

**祝你使用愉快！** 🎉
