from mcp_framework import tool
from vector_retriever import VectorRetriever
from typing import Dict, Any


@tool('query_rag')
def query_rag(params: Dict[str, Any]) -> Dict[str, str]:
    """RAG 查询工具。params: {question: str} 返回: {answer: str}"""
    question = params.get('question', '')
    vr = VectorRetriever()
    answer = vr.answer_question(question)
    return {'answer': answer}


if __name__ == '__main__':
    from mcp_framework import serve
    serve()
