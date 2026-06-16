"""简单的 VectorRetriever 模拟实现。
真实 RAG 需配合 Milvus 和嵌入服务，见 README。
"""


class VectorRetriever:
    def __init__(self) -> None:
        pass

    def answer_question(self, question: str) -> str:
        if not question:
            return '未提供问题。'
        return f'（模拟RAG回答）关于“{question}”：知识库暂无真实向量检索，返回模拟答案。'
