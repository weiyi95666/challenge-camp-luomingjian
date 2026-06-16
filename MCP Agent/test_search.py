"""
测试改进后的搜索功能
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agent.core import get_agent


def test_search():
    print("="*60)
    print("🔍 测试改进后的搜索功能")
    print("="*60)
    print()
    
    agent = get_agent()
    
    test_queries = [
        "搜索 人工智能",
        "搜索 Python",
        "搜索 天气"
    ]
    
    for query in test_queries:
        print(f"📝 测试: {query}")
        print("-"*40)
        result = agent.process_message(query)
        print(f"🤖 回答: {result['response']}")
        print()


if __name__ == "__main__":
    test_search()
