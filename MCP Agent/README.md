# MCP Agent + RAG (示例项目)

说明：本示例将 RAG 功能封装为一个 MCP 风格的 stdio 工具（`rag_server.py`），并提供了天气与写文件两个示例工具。

快速开始：

1. 创建并激活虚拟环境，安装依赖：

```bash
python -m venv .venv
.
# Windows
.venv\Scripts\activate
pip install -r requirements.txt
```

2. 运行 CLI：

```bash
python client.py
# 示例：输入 `天气 上海` 或 `写 outputs/test.txt 这是测试内容` 或任意问题（默认走RAG）
```

3. 运行 API：

```bash
python api_server.py
# POST /chat JSON: {"text":"你的问题"}
```

4. 运行桌面聊天前端：

```bash
python desktop_chat.py
```

如果希望先单独启动后端，也可以先运行 `python api_server.py`，然后再打开 `python desktop_chat.py`。

启用真实 RAG：
- 启动 Milvus：

```bash
docker run -d --name milvus -p 19530:19530 milvusdb/milvus:latest
```

- 用真实向量化与 Milvus 存储文档，替换 `vector_retriever.py` 中的模拟实现为真实 Milvus 客户端逻辑（参见 RAG 项目流程：chunk_size=500, 嵌入 model=text-embedding-v1 1536 维）。

## 一步启动（Windows）

在 PowerShell 中运行：

```powershell
cd "c:\Users\weiyi\Desktop\challenge-camp-luomingjian-main\MCP Agent"
.\.venv\Scripts\activate
start_all.bat
```
