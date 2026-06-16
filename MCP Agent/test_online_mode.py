"""
测试联网模式切换功能
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agent.core import get_agent
from logger import get_logger, log_system_event


def test_online_mode():
    """测试联网模式功能"""
    print("=" * 70)
    print("[测试] 联网模式切换功能")
    print("=" * 70)
    print()
    
    logger = get_logger()
    log_system_event("开始联网模式测试")
    
    agent = get_agent()
    
    # 测试1：启用联网模式
    print("[1] 启用联网模式...")
    agent.set_online_mode(True)
    print(f"    当前状态: {agent.get_online_mode()}")
    print()
    
    # 测试2：查询天气
    print("[2] 测试天气查询（联网模式启用）...")
    result = agent.process_message("天气 北京")
    # 避免编码问题，只打印ASCII部分
    safe_response = ''.join(c for c in result['response'] if ord(c) < 128)
    print(f"    结果: {safe_response[:80]}...")
    print(f"    使用工具: {result.get('tool_used')}")
    print()
    
    # 测试3：禁用联网模式
    print("[3] 禁用联网模式...")
    agent.set_online_mode(False)
    print(f"    当前状态: {agent.get_online_mode()}")
    print()
    
    # 测试4：查询天气（禁用联网）
    print("[4] 测试天气查询（联网模式禁用）...")
    result = agent.process_message("天气 北京")
    print(f"    结果: {result['response']}")
    print(f"    使用工具: {result.get('tool_used')}")
    print()
    
    # 测试5：重新启用
    print("[5] 重新启用联网模式...")
    agent.set_online_mode(True)
    print(f"    当前状态: {agent.get_online_mode()}")
    print()
    
    print("=" * 70)
    print("[OK] 联网模式测试完成！")
    print("=" * 70)


if __name__ == "__main__":
    test_online_mode()
