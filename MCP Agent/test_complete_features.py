"""
全面测试智能体功能
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agent.core import get_agent
from logger import get_logger, log_system_event

def test_weather():
    """测试天气查询"""
    print("\n" + "="*50)
    print("测试天气查询功能")
    print("="*50)
    
    agent = get_agent()
    test_queries = ["天气 北京", "天气 上海"]
    
    for query in test_queries:
        print(f"\n测试: '{query}'")
        result = agent.process_message(query)
        print(f"回复: {result['response'][:100]}...")
        print(f"使用工具: {result['tool_used']}")

def test_search():
    """测试网络搜索"""
    print("\n" + "="*50)
    print("测试网络搜索功能")
    print("="*50)
    
    agent = get_agent()
    test_queries = ["搜索 Python", "搜索 人工智能"]
    
    for query in test_queries:
        print(f"\n测试: '{query}'")
        result = agent.process_message(query)
        print(f"回复: {result['response'][:100]}...")
        print(f"使用工具: {result['tool_used']}")

def test_general_chat():
    """测试普通聊天"""
    print("\n" + "="*50)
    print("测试普通聊天功能")
    print("="*50)
    
    agent = get_agent()
    test_queries = ["你好", "介绍一下你自己"]
    
    for query in test_queries:
        print(f"\n测试: '{query}'")
        result = agent.process_message(query)
        print(f"回复: {result['response']}")
        print(f"使用工具: {result['tool_used']}")

def main():
    """运行所有测试"""
    logger = get_logger()
    log_system_event("开始完整功能测试")
    
    print("\n" + "="*60)
    print("开始 MCP Agent 完整功能测试")
    print("="*60)
    
    # 测试时间查询
    print("\n[1/4] 测试时间查询...")
    agent = get_agent()
    result = agent.process_message("现在时间多少")
    print(f"  查询: '现在时间多少'")
    print(f"  回复: {result['response']}")
    if "现在的时间是：" in result['response']:
        print("  [OK] 时间查询功能正常")
    else:
        print("  [FAIL] 时间查询功能异常")
    
    # 测试天气
    test_weather()
    
    # 测试搜索
    test_search()
    
    # 测试普通聊天
    test_general_chat()
    
    print("\n" + "="*60)
    print("测试完成！")
    print("="*60)

if __name__ == "__main__":
    main()
