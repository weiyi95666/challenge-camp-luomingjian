"""
测试模型对接功能
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import AgentConfig
from agent.llm_client import get_llm_client
from logger import get_logger, log_system_event


def test_model_integration():
    """测试模型对接"""
    print("=" * 70)
    print("[测试] 模型对接功能验证")
    print("=" * 70)
    print()
    
    logger = get_logger()
    log_system_event("开始模型对接测试")
    
    # 1. 检查配置加载
    print("[1] 检查模型配置加载...")
    api_config = AgentConfig.get_api_config()
    print(f"    提供商: {api_config.get('provider')}")
    print(f"    模型: {api_config.get('model')}")
    print(f"    API URL: {api_config.get('api_url')}")
    print(f"    API Key: {'已设置' if api_config.get('api_key') else '未设置'}")
    print()
    
    # 2. 获取 LLM 客户端
    print("[2] 初始化 LLM 客户端...")
    llm_client = get_llm_client()
    print("    OK")
    print()
    
    # 3. 简单测试对话
    print("[3] 测试简单对话...")
    messages = [
        {"role": "system", "content": "你是一个简单的AI助手，用简短的中文回答问题。"},
        {"role": "user", "content": "你好，请用一句话介绍你自己。"}
    ]
    
    try:
        response = llm_client.chat(messages, temperature=0.7, max_tokens=200)
        print(f"    AI 回复: {response.get('content', '无回复')}")
        print("    OK")
    except Exception as e:
        print(f"    错误: {e}")
    print()
    
    # 4. 测试模型切换
    print("[4] 测试模型切换...")
    print(f"    当前模型: {AgentConfig.get_current_model()}")
    
    # 切换到 Qwen 模型
    AgentConfig.set_current_model("SiliconFlow", "Qwen/Qwen2.5-7B-Instruct")
    print(f"    切换到: Qwen/Qwen2.5-7B-Instruct")
    
    # 重新获取 LLM 客户端
    llm_client_new = get_llm_client()
    
    # 测试新模型
    try:
        response = llm_client_new.chat(messages, temperature=0.7, max_tokens=200)
        print(f"    AI 回复: {response.get('content', '无回复')}")
        print("    OK - 模型切换工作正常!")
    except Exception as e:
        print(f"    错误: {e}")
    print()
    
    # 切回默认模型
    AgentConfig.set_current_model("SiliconFlow", "deepseek-ai/DeepSeek-V3")
    
    print("=" * 70)
    print("[OK] 模型对接测试完成!")
    print("=" * 70)


if __name__ == "__main__":
    test_model_integration()
