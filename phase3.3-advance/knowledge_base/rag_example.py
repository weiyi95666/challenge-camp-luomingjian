#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据清洗知识库 RAG（检索增强生成）示例
集成本地 Ollama 大模型
"""

import requests
import json
from typing import List, Dict, Any
from pymilvus import MilvusClient
from sentence_transformers import SentenceTransformer

# 配置
MILVUS_DB_PATH = "./milvus.db"
COLLECTION_NAME = "data_cleaning_knowledge"
MODEL_NAME = "shibing624/text2vec-base-chinese"
OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "gemma4:e2b"  # 或您使用的模型


def search_knowledge(query: str, top_k: int = 3) -> List[Dict]:
    """
    搜索知识库
    
    Args:
        query: 用户查询
        top_k: 返回结果数量
    
    Returns:
        搜索结果列表
    """
    # 连接 Milvus
    client = MilvusClient(MILVUS_DB_PATH)
    
    # 加载模型
    model = SentenceTransformer(MODEL_NAME)
    
    # 编码查询
    query_embedding = model.encode([query])[0]
    
    # 搜索
    search_params = {
        "metric_type": "COSINE",
        "params": {"nprobe": 10}
    }
    
    results = client.search(
        collection_name=COLLECTION_NAME,
        data=[query_embedding],
        limit=top_k,
        search_params=search_params,
        output_fields=["id", "title", "category", "text", "tags"]
    )
    
    return results[0]


def build_rag_prompt(query: str, retrieved_knowledge: List[Dict]) -> str:
    """
    构建 RAG 提示词
    
    Args:
        query: 用户问题
        retrieved_knowledge: 检索到的知识
    
    Returns:
        完整提示词
    """
    knowledge_text = ""
    for i, result in enumerate(retrieved_knowledge, 1):
        entity = result['entity']
        knowledge_text += f"\n=== 知识片段 {i} ===\n"
        knowledge_text += f"标题: {entity['title']}\n"
        knowledge_text += f"分类: {entity['category']}\n"
        knowledge_text += f"内容: {entity['text']}\n"
    
    prompt = f"""你是一位专业的数据清洗专家。请根据用户问题和提供的知识片段，给出详细的回答。

请参考以下知识片段（按相关性排序）：
{knowledge_text}

用户问题: {query}

请基于提供的知识片段，回答用户问题。如果知识片段不足以回答问题，请基于你的专业知识补充。
请用中文回答，结构清晰，包含：
1. 方法概述
2. 适用场景
3. 代码示例（如果有）
4. 注意事项
"""
    return prompt


def query_ollama(prompt: str, model: str = OLLAMA_MODEL) -> str:
    """
    调用本地 Ollama
    
    Args:
        prompt: 提示词
        model: 模型名称
    
    Returns:
        模型响应
    """
    try:
        response = requests.post(
            OLLAMA_URL,
            json={
                "model": model,
                "prompt": prompt,
                "stream": False,
                "temperature": 0.7,
                "top_p": 0.9,
                "max_tokens": 2000
            },
            timeout=120
        )
        response.raise_for_status()
        return response.json().get("response", "没有返回内容")
    except Exception as e:
        print(f"Ollama 调用失败: {e}")
        print("请确保 Ollama 正在运行，并已安装模型")
        return None


def rag_query(user_question: str, top_k: int = 3):
    """
    完整 RAG 查询流程
    
    Args:
        user_question: 用户问题
        top_k: 检索数量
    
    Returns:
        最终回答
    """
    print("=" * 70)
    print("数据清洗 RAG 助手")
    print("=" * 70)
    
    # 1. 检索知识
    print(f"\n[1/3] 正在检索知识库 (Top {top_k})...")
    retrieved = search_knowledge(user_question, top_k=top_k)
    
    print("\n检索到的知识片段:")
    for i, r in enumerate(retrieved, 1):
        print(f"  {i}. {r['entity']['title']} (相似度: {r['distance']:.4f})")
    
    # 2. 构建提示词
    print("\n[2/3] 构建 RAG 提示词...")
    prompt = build_rag_prompt(user_question, retrieved)
    
    # 3. 调用大模型
    print("\n[3/3] 正在调用大模型...")
    print("-" * 70)
    answer = query_ollama(prompt)
    
    if answer:
        print(answer)
        print("-" * 70)
        return answer
    else:
        print("\n提示词内容预览:")
        print(prompt[:500] + "...")
        return None


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="数据清洗 RAG 助手")
    parser.add_argument("question", help="用户问题", nargs="?")
    parser.add_argument("--topk", type=int, default=3, help="检索数量")
    args = parser.parse_args()
    
    if args.question:
        question = args.question
    else:
        print("数据清洗 RAG 助手")
        print("=" * 70)
        question = input("请输入您的问题: ").strip()
        if not question:
            print("问题不能为空！")
            return
    
    rag_query(question, top_k=args.topk)


if __name__ == "__main__":
    main()
