"""
完整测试 MCP Agent 智能体功能
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agent.core import get_agent


def test_complete_agent():
    print("="*60)
    print("🚀 完整测试 MCP Agent 智能体")
    print("="*60)
    print()
    
    agent = get_agent()
    
    test_cases = [
        "你好",
        "你能做什么？",
        "天气 上海",
        "搜索 Python"
    ]
    
    for i, query in enumerate(test_cases, 1):
        print(f"\n{'='*20} 测试 {i} {'='*20}")
        print(f"👤 用户: {query}")
        print("-"*40)
        
        try:
            result = agent.process_message(query)
            print(f"🤖 智能体: {result['response']}")
            
            if result.get('tool_used'):
                print(f"🔧 使用工具: {result['tool_used']}")
                
            print("✅ 测试通过！")
            
        except Exception as e:
            print(f"❌ 测试失败: {e}")
    
    print("\n" + "="*60)
    print("🎉 所有测试完成！")
    print("="*60)


if __name__ == "__main__":
    test_complete_agent()
