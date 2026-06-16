"""测试 Web API"""
import requests
import json
import time

print("="*60)
print("🔍 测试 Web API")
print("="*60)
print()

BASE_URL = "http://127.0.0.1:5001"

print(f"🌐 连接到: {BASE_URL}")
print()

# 测试1: 获取当前模型
print("📝 测试1: 获取当前模型...")
try:
    response = requests.get(f"{BASE_URL}/api/models/current", timeout=5)
    print(f"  状态码: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"  当前模型: {data.get('model')}")
        print(f"  提供商: {data.get('provider')}")
        print(f"  ✅ 成功！")
except Exception as e:
    print(f"  ❌ 错误: {e}")
print()

# 测试2: 发送聊天消息
print("💬 测试2: 发送聊天消息...")
try:
    test_text = "你好，你能做什么？"
    response = requests.post(
        f"{BASE_URL}/chat",
        json={"text": test_text},
        timeout=30
    )
    print(f"  状态码: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"  回复: {data.get('response')[:100]}...")
        print(f"  使用工具: {data.get('tool_used')}")
        print(f"  ✅ 成功！")
except Exception as e:
    print(f"  ❌ 错误: {e}")
print()

print("="*60)
print("✅ Web API 测试完成！")
print("="*60)
