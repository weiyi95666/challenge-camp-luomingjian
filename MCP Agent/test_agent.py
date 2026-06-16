"""
测试 MCP Agent 智能体
"""
import sys
import os

# 添加项目根目录
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agent.core import get_agent


def test_agent():
    print("=" * 60)
    print("🤖 测试 MCP Agent 智能体")
    print("=" * 60)
    print()
    
    agent = get_agent()
    
    # 测试 1: 天气查询
    print("📋 测试 1: 天气查询")
    print("-" * 40)
    result = agent.process_message("天气 北京")
    print(f"用户: 天气 北京")
    print(f"助手: {result['response']}")
    print(f"使用工具: {result['tool_used']}")
    print()
    
    # 测试 2: 写文件
    print("📋 测试 2: 写文件")
    print("-" * 40)
    result = agent.process_message("写 test_note.txt 这是一条测试笔记")
    print(f"用户: 写 test_note.txt 这是一条测试笔记")
    print(f"助手: {result['response']}")
    print(f"使用工具: {result['tool_used']}")
    print()
    
    # 测试 3: RAG 查询
    print("📋 测试 3: RAG 查询")
    print("-" * 40)
    result = agent.process_message("什么是人工智能？")
    print(f"用户: 什么是人工智能？")
    print(f"助手: {result['response']}")
    print(f"使用工具: {result['tool_used']}")
    print()
    
    # 测试 4: 对话历史
    print("📋 测试 4: 对话历史")
    print("-" * 40)
    history = agent.get_conversation_history()
    print(f"历史消息数: {len(history)}")
    for msg in history:
        role = "👤 用户" if msg["role"] == "user" else "🤖 助手"
        print(f"  {role}: {msg['content']}")
    print()
    
    # 测试 5: 清空记忆
    print("📋 测试 5: 清空记忆")
    print("-" * 40)
    agent.clear_memory()
    history = agent.get_conversation_history()
    print(f"清空后历史消息数: {len(history)}")
    print()
    
    print("=" * 60)
    print("✅ 所有测试完成！")
    print("=" * 60)
    print()
    print("📝 说明:")
    print("  - 当前使用模板化回复")
    print("  - 请提供 API 来启用真实的 LLM 功能")
    print("  - 详见 '智能体架构说明.md'")
    print()


if __name__ == "__main__":
    test_agent()
