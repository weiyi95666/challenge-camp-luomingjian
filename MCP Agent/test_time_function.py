"""
测试时间查询功能
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agent.core import get_agent
from logger import get_logger, log_system_event

def test_time_query():
    """测试时间查询功能"""
    print("="*50)
    print("测试智能体时间查询功能")
    print("="*50)
    
    logger = get_logger()
    log_system_event("开始测试")
    
    agent = get_agent()
    
    # 测试不同的时间查询关键词
    test_queries = [
        "现在时间多少",
        "几点了",
        "现在几点了",
        "当前时间",
        "what time is it"
    ]
    
    all_passed = True
    
    for query in test_queries:
        print(f"\n测试查询: '{query}'")
        result = agent.process_message(query)
        print(f"回复: {result['response']}")
        print(f"使用工具: {result['tool_used']}")
        
        # 验证回复
        if "现在的时间是：" in result['response']:
            print("[OK] 时间查询测试通过")
        else:
            print("[FAIL] 时间查询测试失败")
            all_passed = False
    
    print("\n" + "="*50)
    if all_passed:
        print("所有测试通过！")
    else:
        print("部分测试失败！")
    print("="*50)

if __name__ == "__main__":
    test_time_query()
