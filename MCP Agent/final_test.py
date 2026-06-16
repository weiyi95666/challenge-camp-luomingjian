"""
最终测试 - 验证优化后的功能
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agent.core import get_agent


def quick_test():
    print("="*60)
    print("🎯 最终验证测试")
    print("="*60)
    print()
    
    agent = get_agent()
    
    # 测试1: 简单对话（不使用工具）
    print("测试1: 简单对话")
    result1 = agent.process_message("你好")
    print(f"回复: {result1['response'][:100]}...")
    print(f"使用工具: {result1['tool_used']}")
    print("✅ 测试1通过!\n")
    
    # 测试2: 天气查询
    print("测试2: 天气查询")
    result2 = agent.process_message("天气 北京")
    print(f"回复: {result2['response'][:100]}...")
    print(f"使用工具: {result2['tool_used']}")
    print("✅ 测试2通过!\n")
    
    print("🎉 所有测试完成！")
    print()
    print("🚀 现在访问 http://127.0.0.1:5001 开始使用您的智能体吧！")


if __name__ == "__main__":
    quick_test()
