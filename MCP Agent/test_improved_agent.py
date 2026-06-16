"""
测试改进后的智能体
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agent.core import get_agent
from logger import get_logger, log_system_event


def test_improved_agent():
    """测试改进后的智能体"""
    print("=" * 70)
    print("[测试] 改进后的智能体 - DeepSeek-V3 + 文本清理")
    print("=" * 70)
    print()
    
    logger = get_logger()
    log_system_event("开始改进版智能体测试")
    
    agent = get_agent()
    
    # 测试用例
    test_cases = [
        "你好，请介绍一下你自己",
        "搜索 人工智能是什么",
        "天气 广州",
        "现在几点了",
    ]
    
    for i, query in enumerate(test_cases, 1):
        print()
        print("-" * 50)
        print(f"[测试 {i}] {query}")
        print("-" * 50)
        
        try:
            result = agent.process_message(query)
            response = result["response"]
            tool_used = result.get("tool_used")
            
            print(f"[回复] {response}")
            if tool_used:
                print(f"[工具] 使用了: {tool_used}")
            
            # 检查回复质量
            if len(response) > 10 and "抱歉" not in response:
                print("[质量] OK 回复质量良好")
            else:
                print("[质量] WARN 需要检查")
                
        except Exception as e:
            print(f"[错误] {e}")
    
    print()
    print("=" * 70)
    print("[完成] 测试完成！")
    print("=" * 70)


if __name__ == "__main__":
    test_improved_agent()
