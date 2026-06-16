"""
测试 LLM API 集成
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agent.core import get_agent
from config import AgentConfig


def test_llm_integration():
    print("="*60)
    print("🤖 测试 LLM API 集成")
    print("="*60)
    print()
    
    # 检查配置
    print("📋 配置检查:")
    print(f"  API URL: {'已配置' if AgentConfig.API_URL else '未配置'}")
    print(f"  API Key: {'已配置' if AgentConfig.API_KEY else '未配置'}")
    print(f"  Model: {AgentConfig.MODEL_NAME}")
    print()
    
    if not AgentConfig.is_api_configured():
        print("⚠️  API 未配置，无法测试 LLM")
        return
    
    agent = get_agent()
    
    # 测试简单对话
    test_queries = [
        "你好",
        "你能做什么？",
        "天气 北京",
        "搜索 人工智能"
    ]
    
    for query in test_queries:
        print(f"\n📝 用户: {query}")
        print("-"*40)
        
        try:
            result = agent.process_message(query)
            print(f"🤖 智能体: {result['response']}")
            if result.get('tool_used'):
                print(f"🔧 使用工具: {result['tool_used']}")
        except Exception as e:
            print(f"❌ 错误: {e}")


if __name__ == "__main__":
    test_llm_integration()
