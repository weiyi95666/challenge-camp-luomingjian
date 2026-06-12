# 数据清洗向量知识库

基于 Milvus 的专业数据清洗知识向量数据库，支持 RAG 检索增强生成。

## 功能特点

- ✨ **25条高质量数据清洗知识点
- 📚 涵盖缺失值、重复值、异常值等完整知识
- 🧠 sentence-transformers 嵌入模型
- 🔍 向量相似度搜索
- 🤖 可集成本地 Ollama RAG
- 🚀 Milvus Lite 本地运行

## 快速开始

### 1. 安装依赖

```bash
cd knowledge_base
pip install -r requirements.txt
```

### 2. 创建知识库

```bash
python create_knowledge_base.py
```

### 3. 搜索知识

```bash
# 交互式
python search_knowledge.py "如何处理缺失值"

# 指定返回 Top 5
python search_knowledge.py "如何处理缺失值" --topk 5
```

### 4. RAG 集成 (需要 Ollama)

```bash
python rag_example.py "如何处理缺失值"
```

## 知识库内容

包含的主题：

| 分类 | 数量 |
|------|------|
| 缺失值处理 | 4 |
| 重复数据处理 | 2 |
| 异常值检测 | 3 |
| 数据类型转换 | 2 |
| 文本清洗 | 4 |
| 敏感信息处理 | 2 |
| 数据标准化 | 2 |
| 最佳实践 | 3 |
| 编码问题 | 1 |
| 分箱/邮箱标准化 | 2 |

## 使用示例

### 查询：缺失值处理
```python
# 搜索示例
python search_knowledge.py "缺失值处理方法"
```

### 模糊去重
```python
python search_knowledge.py "如何去除重复数据"
```

### RAG 查询
```python
python rag_example.py "数据清洗完整流程"
```

## 技术栈

- **Milvus Lite**: 向量数据库
- **sentence-transformers**: 文本嵌入
- **pymilvus: Milvus 客户端
- **Ollama**: 本地大模型

## 目录结构

```
knowledge_base/
├── create_knowledge_base.py  # 构建知识库
├── search_knowledge.py     # 搜索脚本
├── rag_example.py          # RAG 集成示例
├── requirements.txt        # 依赖
└── README.md           # 本文档
```

## 常见问题

### 如何修改嵌入模型

修改脚本中的 `MODEL_NAME` 变量：

```python
# 使用英文模型
MODEL_NAME = "all-MiniLM-L6-v2"
# 或中文模型
MODEL_NAME = "shibing624/text2vec-base-chinese"
```

### 使用 Docker 版本的 Milvus

修改连接

如需使用 Docker 版本的 Milvus：

替换连接方式：

```python
from pymilvus import connections, utility
connections.connect("default", host="localhost", port="19530")
```

## 许可证
