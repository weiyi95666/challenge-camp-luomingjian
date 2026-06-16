"""
测试三层记忆系统（不依赖外部 API）
"""
import sys
import os
import json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from memory_system import ShortTermMemory, MidTermMemory, LongTermMemory


def test_short_term_memory():
    """测试短期记忆"""
    print("\n" + "=" * 60)
    print("1. 测试短期记忆")
    print("=" * 60)
    
    stm = ShortTermMemory(max_history=5)
    print(f"- 创建短期记忆（最大长度: 5）")
    
    # 添加测试消息
    test_messages = [
        ("user", "你好"),
        ("assistant", "你好，有什么可以帮助你的？"),
        ("user", "我叫测试用户"),
        ("assistant", "很高兴认识你，测试用户！"),
        ("user", "天气怎么样？"),
        ("assistant", "今天天气很好"),
        ("user", "明天呢？"),
        ("assistant", "明天也会是晴天")
    ]
    
    for role, content in test_messages:
        stm.add_message(role, content)
        print(f"- 添加消息: {role}: {content[:30]}")
    
    # 获取历史
    history = stm.get_history()
    print(f"\n- 当前记忆中消息数: {len(history)}（应该是 5）")
    
    # 获取最近的
    recent = stm.get_recent_context(n=3)
    print(f"- 最近 3 条消息数: {len(recent)}")
    
    # 清空
    stm.clear()
    print(f"- 清空后消息数: {len(stm.get_history())}")
    
    print("✅ 短期记忆测试完成！")
    return True


def test_mid_term_memory():
    """测试中期记忆"""
    print("\n" + "=" * 60)
    print("2. 测试中期记忆")
    print("=" * 60)
    
    # 使用测试数据库
    test_db_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "test_mid_term.db"
    )
    
    # 如果存在，先删除
    if os.path.exists(test_db_path):
        os.remove(test_db_path)
    
    mtm = MidTermMemory(db_path=test_db_path)
    print(f"- 创建中期记忆（数据库: {test_db_path}）")
    
    # 测试用户偏好
    mtm.set_preference("tone", "friendly")
    mtm.set_preference("language", "Chinese")
    mtm.set_preference("detail_level", "high")
    print(f"- 设置了 3 个用户偏好")
    
    preferences = mtm.get_all_preferences()
    print(f"- 获取到偏好: {preferences}")
    
    # 测试用户事实
    mtm.add_user_fact("用户叫测试用户", category="identity")
    mtm.add_user_fact("用户喜欢蓝色", category="preference")
    mtm.add_user_fact("用户住在北京", category="location")
    print(f"- 添加了 3 个用户事实")
    
    facts = mtm.get_user_facts()
    print(f"- 获取到事实数: {len(facts)}")
    
    # 测试会话摘要
    mtm.save_session_summary("test_session_1", "测试会话摘要 1", 15)
    mtm.save_session_summary("test_session_2", "测试会话摘要 2", 8)
    print(f"- 保存了 2 个会话摘要")
    
    summaries = mtm.get_recent_summaries(limit=5)
    print(f"- 获取到摘要数: {len(summaries)}")
    
    # 测试系统提示词上下文
    context = mtm.build_system_prompt_context()
    print(f"- 系统提示词上下文:")
    print(context)
    
    # 清理
    if os.path.exists(test_db_path):
        os.remove(test_db_path)
    
    print("✅ 中期记忆测试完成！")
    return True


def test_long_term_memory():
    """测试长期记忆"""
    print("\n" + "=" * 60)
    print("3. 测试长期记忆")
    print("=" * 60)
    
    ltm = LongTermMemory()
    print(f"- 创建长期记忆")
    
    # 添加测试记忆
    test_memories = [
        ("用户叫测试用户", {"category": "identity"}),
        ("用户喜欢蓝色", {"category": "preference"}),
        ("用户住在北京", {"category": "location"}),
        ("用户的生日是1月1日", {"category": "personal"}),
        ("用户会说中文和英文", {"category": "skill"})
    ]
    
    for content, metadata in test_memories:
        memory_id = ltm.add_memory(content, metadata)
        print(f"- 添加记忆: {content} (ID: {memory_id})")
    
    # 检索测试
    print("\n- 检索测试:")
    
    test_queries = [
        "用户叫什么名字？",
        "用户喜欢什么颜色？",
        "用户住在哪里？",
        "用户会说什么语言？"
    ]
    
    for query in test_queries:
        results = ltm.search_memories(query, top_k=2)
        print(f"  查询: '{query}'")
        print(f"  找到 {len(results)} 条相关记忆")
        for result in results:
            print(f"    - {result['content']} (分数: {result['score']:.2f})")
    
    # 获取所有记忆
    all_memories = ltm.get_all_memories()
    print(f"\n- 总记忆数: {len(all_memories)}")
    
    # 测试 should_store
    test_texts = [
        "记住，我喜欢红色",
        "你好啊",
        "我叫小红",
        "今天天气真好"
    ]
    
    print("\n- 测试记忆提取判断:")
    for text in test_texts:
        should_store = ltm.should_store_to_long_term(text)
        print(f"  '{text}' -> {should_store}")
    
    print("✅ 长期记忆测试完成！")
    return True


def run_all_tests():
    """运行所有测试"""
    print("\n" + "=" * 60)
    print("三层记忆系统 - 完整测试")
    print("=" * 60)
    
    results = []
    results.append(("短期记忆", test_short_term_memory()))
    results.append(("中期记忆", test_mid_term_memory()))
    results.append(("长期记忆", test_long_term_memory()))
    
    print("\n" + "=" * 60)
    print("测试结果汇总:")
    print("=" * 60)
    
    all_passed = True
    for name, passed in results:
        status = "✅ 通过" if passed else "❌ 失败"
        print(f"- {name}: {status}")
        if not passed:
            all_passed = False
    
    if all_passed:
        print("\n🎉 所有测试通过！记忆系统运行正常！")
    else:
        print("\n⚠️  部分测试失败，请检查。")
    
    return all_passed


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
