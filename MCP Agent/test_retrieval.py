"""
测试长期记忆的检索效果
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from memory_system import LongTermMemory


def test_retrieval():
    """测试检索功能"""
    print("=" * 60)
    print("长期记忆检索测试")
    print("=" * 60)
    
    ltm = LongTermMemory()
    
    # 清空现有测试数据
    test_file = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "long_term_memory.json"
    )
    if os.path.exists(test_file):
        os.remove(test_file)
    
    # 重新初始化
    ltm = LongTermMemory()
    
    # 添加测试记忆
    print("\n1. 添加测试记忆:")
    test_memories = [
        ("用户叫测试用户", {"category": "identity"}),
        ("用户喜欢蓝色", {"category": "preference"}),
        ("用户住在北京", {"category": "location"}),
        ("用户的生日是1月1日", {"category": "personal"}),
        ("用户会说中文和英文", {"category": "skill"})
    ]
    
    for content, metadata in test_memories:
        memory_id = ltm.add_memory(content, metadata)
        print(f"   ✅ {content}")
    
    # 测试检索
    print("\n2. 测试检索:")
    test_queries = [
        "用户叫什么名字？",
        "用户喜欢什么颜色？",
        "用户住在哪里？",
        "用户的生日是什么时候？",
        "用户会说什么语言？"
    ]
    
    for query in test_queries:
        results = ltm.search_memories(query, top_k=2)
        print(f"\n   🔍 查询: '{query}'")
        if results:
            for i, result in enumerate(results, 1):
                print(f"      {i}. {result['content']} (分数: {result['score']:.2f})")
        else:
            print(f"      ❌ 未找到相关记忆")
    
    # 显示所有记忆
    print("\n3. 所有存储的记忆:")
    all_memories = ltm.get_all_memories()
    for memory in all_memories:
        print(f"   📝 {memory['content']}")
    
    print("\n" + "=" * 60)
    print("测试完成！")


if __name__ == "__main__":
    test_retrieval()
