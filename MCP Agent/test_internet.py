"""
测试智能体的联网功能
"""
import sys
import os

# 添加项目根目录
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agent.core import get_agent


def test_internet_features():
    print("=" * 70)
    print("🌐 测试 MCP Agent 联网功能")
    print("=" * 70)
    print()
    
    agent = get_agent()
    
    # 测试1：真实天气查询
    print("📋 测试1：真实天气查询（上海）")
    print("-" * 50)
    result = agent.process_message("天气 上海")
    print(result["response"])
    print()
    
    # 测试2：网络搜索
    print("📋 测试2：网络搜索（人工智能）")
    print("-" * 50)
    result = agent.process_message("搜索 人工智能")
    print(result["response"])
    print()
    
    # 测试3：再查一个城市
    print("📋 测试3：真实天气查询（北京）")
    print("-" * 50)
    result = agent.process_message("北京天气怎么样")
    print(result["response"])
    print()
    
    print("=" * 70)
    print("✅ 联网功能测试完成！")
    print("=" * 70)
    print()
    print("💡 使用提示：")
    print("  • 说 '天气 [城市名]' 来查询天气")
    print("  • 说 '搜索 [关键词]' 来进行网络搜索")
    print("  • 说 '访问 [网址]' 来抓取网页内容")
    print("  • 运行 'python client.py' 来进行交互式对话")
    print()


if __name__ == "__main__":
    test_internet_features()
