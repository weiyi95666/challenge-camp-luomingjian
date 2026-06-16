"""
测试 Tavily 搜索 API 集成
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agent.core import get_agent
from logger import get_logger, log_system_event


def test_tavily_search():
    """测试 Tavily 搜索功能"""
    print("=" * 70)
    print("[搜索] 测试 Tavily 搜索 API 集成")
    print("=" * 70)
    print()
    
    logger = get_logger()
    log_system_event("开始 Tavily 搜索测试")
    
    agent = get_agent()
    
    # 测试搜索查询
    test_queries = [
        "搜索 人工智能最新进展",
        "搜索 Python 编程技巧",
        "搜索 今天的天气怎么样"
    ]
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n[测试] 测试 {i}: {query}")
        print("-" * 50)
        
        try:
            result = agent.process_message(query)
            print(f"[智能体] 回应:\n{result['response']}")
            print(f"\n[工具] 使用工具: {result.get('tool_used')}")
            print("[OK] 测试通过!")
        except Exception as e:
            print(f"[错误] 错误: {e}")
            log_error("Tavily 测试错误", f"查询 '{query}' 失败", e)
    
    print()
    print("=" * 70)
    print("[OK] Tavily 搜索测试完成!")
    print("=" * 70)
    print()
    print("[提示] 提示:")
    print("  * 说 '搜索 [关键词]' 来使用 Tavily 进行网络搜索")
    print("  * Tavily 提供高质量、AI 优化的搜索结果")
    print("  * 还可以查询天气、访问网页等")
    print()


if __name__ == "__main__":
    test_tavily_search()
