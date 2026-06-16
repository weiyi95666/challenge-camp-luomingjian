"""
向量存储模块 - 为未来集成PyMilvus等向量数据库做准备
提供向量存储和检索的基础架构
"""

import json
import os
from typing import List, Dict, Any, Optional
from abc import ABC, abstractmethod


class VectorStore(ABC):
    """向量存储抽象基类"""
    
    @abstractmethod
    def add_documents(self, documents: List[Dict[str, Any]]) -> bool:
        """添加文档到向量存储"""
        pass
    
    @abstractmethod
    def search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """搜索相关文档"""
        pass
    
    @abstractmethod
    def delete_collection(self) -> bool:
        """删除整个集合"""
        pass


class LocalVectorStore(VectorStore):
    """本地向量存储实现（基于文件）"""
    
    def __init__(self, storage_path: str = "./vector_data"):
        self.storage_path = storage_path
        self.documents_file = os.path.join(storage_path, "documents.json")
        self.documents = self._load_documents()
        
        os.makedirs(storage_path, exist_ok=True)
    
    def _load_documents(self) -> List[Dict[str, Any]]:
        """从文件加载文档"""
        if os.path.exists(self.documents_file):
            try:
                with open(self.documents_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return []
        return []
    
    def _save_documents(self) -> bool:
        """保存文档到文件"""
        try:
            with open(self.documents_file, 'w', encoding='utf-8') as f:
                json.dump(self.documents, f, ensure_ascii=False, indent=2)
            return True
        except:
            return False
    
    def add_documents(self, documents: List[Dict[str, Any]]) -> bool:
        """添加文档到存储"""
        for doc in documents:
            if 'id' not in doc:
                doc['id'] = str(len(self.documents) + 1)
            doc['created_at'] = doc.get('created_at', self._get_timestamp())
            self.documents.append(doc)
        return self._save_documents()
    
    def search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """简单的关键词搜索（为未来的向量搜索做准备）"""
        results = []
        query_lower = query.lower()
        
        for doc in self.documents:
            content = doc.get('content', '').lower()
            title = doc.get('title', '').lower()
            if query_lower in content or query_lower in title:
                results.append(doc)
        
        return results[:top_k]
    
    def delete_collection(self) -> bool:
        """删除所有文档"""
        self.documents = []
        return self._save_documents()
    
    def _get_timestamp(self) -> str:
        """获取当前时间戳"""
        from datetime import datetime
        return datetime.now().isoformat()


class RAGEngine:
    """检索增强生成引擎"""
    
    def __init__(self, vector_store: Optional[VectorStore] = None):
        self.vector_store = vector_store or LocalVectorStore()
        self.system_prompt = """你是一个基于检索增强生成（RAG）的AI助手。
当用户提问时，请优先使用检索到的相关文档内容来回答。
如果没有找到相关文档，请基于你已有的知识回答。
请确保你的回答准确、有帮助。"""
    
    def query(self, user_query: str, top_k: int = 3) -> Dict[str, Any]:
        """执行RAG查询"""
        # 检索相关文档
        relevant_docs = self.vector_store.search(user_query, top_k)
        
        # 构建上下文
        context = self._build_context(relevant_docs)
        
        return {
            'query': user_query,
            'context': context,
            'relevant_docs': relevant_docs,
            'has_relevant_docs': len(relevant_docs) > 0
        }
    
    def _build_context(self, documents: List[Dict[str, Any]]) -> str:
        """从文档构建上下文"""
        context_parts = []
        for i, doc in enumerate(documents, 1):
            title = doc.get('title', f'文档 {i}')
            content = doc.get('content', '')
            context_parts.append(f"【{title}】\n{content}")
        
        return '\n\n'.join(context_parts) if context_parts else ''
    
    def add_document(self, title: str, content: str, metadata: Optional[Dict] = None) -> bool:
        """添加文档"""
        doc = {
            'title': title,
            'content': content,
            'metadata': metadata or {}
        }
        return self.vector_store.add_documents([doc])


# 全局实例
_vector_store: Optional[VectorStore] = None
_rag_engine: Optional[RAGEngine] = None


def get_vector_store() -> VectorStore:
    """获取向量存储实例"""
    global _vector_store
    if _vector_store is None:
        _vector_store = LocalVectorStore()
    return _vector_store


def get_rag_engine() -> RAGEngine:
    """获取RAG引擎实例"""
    global _rag_engine
    if _rag_engine is None:
        _rag_engine = RAGEngine(get_vector_store())
    return _rag_engine


if __name__ == "__main__":
    # 简单测试
    rag = get_rag_engine()
    
    # 添加示例文档
    rag.add_document(
        "MCP Agent 简介",
        "MCP Agent 是一个智能助手，支持联网搜索、天气查询等功能。"
    )
    
    # 测试查询
    result = rag.query("MCP Agent 是什么")
    print("检索结果:", result)
