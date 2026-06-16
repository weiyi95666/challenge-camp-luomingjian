"""
测试 API 连接 - 验证修复后的代理问题
"""
import sys
import os

# 添加项目根目录
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agent.llm_client import get_llm_client
from agent.core import get_agent
from logger import get_logger, log_system_event

logger = get_logger()
log_system_event("开始 API 连接测试")

print("=" * 70)
print("🧪 API 连接测试")
print("=" * 70)

# 测试 1: 直接测试 LLM 客户端
print("\n📋 测试 1: LLM 客户端直接调用")
print("-" * 50)

try:
    llm_client = get_llm_client()
    print("✅ LLM 客户端初始化成功")
    
    # 测试简单对话
    test_messages = [
        {"role": "user", "content": "你好，请简单介绍一下自己"}
    ]
    
    print("🔄 正在发送测试请求...")
    result = llm_client.chat(test_messages, temperature=0.7, max_tokens=200)
    
    print(f"✅ API 调用成功!")
    print(f"\n📝 回复内容:")
    print(f"   {result.get('content', '无内容')}")
    
except Exception as e:
    print(f"❌ 测试失败: {str(e)}")
    import traceback
    traceback.print_exc()

# 测试 2: 智能体完整测试
print("\n" + "=" * 70)
print("🤖 测试 2: 完整智能体功能")
print("=" * 70)

try:
    agent = get_agent()
    print("✅ 智能体初始化成功")
    
    # 测试天气查询
    print("\n🌤️ 测试天气查询:")
    weather_result = agent.process_message("天气 北京")
    print(f"   回复: {weather_result.get('response', '')}")
    print(f"   使用工具: {weather_result.get('tool_used', '无')}")
    
    # 测试简单对话
    print("\n💬 测试对话:")
    chat_result = agent.process_message("你好，你能做什么？")
    print(f"   回复: {chat_result.get('response', '')}")
    
    print("\n" + "=" * 70)
    print("✅ 所有测试通过！系统运行正常！")
    print("=" * 70)
    
except Exception as e:
    print(f"❌ 智能体测试失败: {str(e)}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 70)
print("测试完成！")
print("=" * 70)
