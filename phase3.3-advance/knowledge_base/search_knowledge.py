#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据清洗知识库搜索脚本
"""

import sys
from pymilvus import MilvusClient
from sentence_transformers import SentenceTransformer

# 配置
MILVUS_DB_PATH = "./milvus.db"
COLLECTION_NAME = "data_cleaning_knowledge"
MODEL_NAME = "shibing624/text2vec-base-chinese"


def search_knowledge(query: str, top_k: int = 3):
    """
    搜索知识库
    
    Args:
        query: 用户查询
        top_k: 返回结果数量
    
    Returns:
        搜索结果列表
    """
    # 1. 连接 Milvus
    client = MilvusClient(MILVUS_DB_PATH)
    
    # 2. 加载模型
    print(f"加载嵌入模型: {MODEL_NAME}")
    model = SentenceTransformer(MODEL_NAME)
    
    # 3. 生成查询向量
    print(f"正在编码查询: {query}")
    query_embedding = model.encode([query])[0]
    
    # 4. 执行搜索
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


def print_results(results):
    """格式化打印搜索结果"""
    print("\n" + "=" * 70)
    print(f"搜索结果 (Top {len(results)})")
    print("=" * 70)
    
    for i, result in enumerate(results, 1):
        entity = result['entity']
        score = result['distance']
        
        print(f"\n【结果 {i}】")
        print(f"标题: {entity['title']}")
        print(f"分类: {entity['category']}")
        print(f"标签: {entity['tags']}")
        print(f"相似度: {score:.4f}")
        print("-" * 70)
        
        text = entity['text']
        # 截取内容预览
        if len(text) > 500:
            text = text[:500] + "...\n[内容截断]"
        print(text)
        print("-" * 70)


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="数据清洗知识库搜索")
    parser.add_argument("query", help="搜索查询", nargs="?")
    parser.add_argument("--topk", type=int, default=3, help="返回结果数量")
    args = parser.parse_args()
    
    if args.query:
        query = args.query
    else:
        # 交互式输入
        print("数据清洗知识库搜索")
        print("=" * 70)
        query = input("请输入您的查询: ").strip()
        if not query:
            print("查询不能为空！")
            return
    
    # 搜索
    results = search_knowledge(query, top_k=args.topk)
    
    # 打印结果
    print_results(results)


if __name__ == "__main__":
    main()
