"""测试 config 修复"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import AgentConfig
from agent.llm_client import get_llm_client

print("="*60)
print("🔧 测试配置修复")
print("="*60)
print()

print("📋 获取 API 配置:")
api_config = AgentConfig.get_api_config()
print(f"  API URL: {api_config.get('api_url')}")
print(f"  API Key: {api_config.get('api_key')[:10]}...")
print(f"  Model: {api_config.get('model')}")
print()

print("🧠 初始化 LLM 客户端...")
llm_client = get_llm_client()

print("💬 发送测试消息...")
result = llm_client.chat([
    {"role": "user", "content": "你好"}
])

print("✅ 响应:")
print(f"  {result.get('content')[:100]}")
print()

print("🎉 配置修复成功！")
print("="*60)
