"""
三层记忆系统 - 短期、中期、长期记忆
兼容 Python 3.7，不依赖 LangChain
"""
import sys
import os
import sqlite3
import json
import hashlib
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from collections import deque
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


class ShortTermMemory:
    """
    短期记忆 - 基于 deque 实现
    保存当前会话的最近 N 轮对话，仅在内存中
    """
    
    def __init__(self, max_history: int = 10):
        self.max_history = max_history
        self.memory = deque(maxlen=max_history)
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    def add_message(self, role: str, content: str, metadata: Dict[str, Any] = None) -> None:
        """添加一条消息到短期记忆"""
        message = {
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat(),
            "metadata": metadata or {}
        }
        self.memory.append(message)
    
    def get_history(self) -> List[Dict[str, Any]]:
        """获取完整的短期记忆"""
        return list(self.memory)
    
    def get_recent_context(self, n: int = 5) -> List[Dict[str, Any]]:
        """获取最近的 n 条消息"""
        return list(self.memory)[-n:]
    
    def clear(self) -> None:
        """清空短期记忆"""
        self.memory.clear()
    
    def get_session_summary(self) -> str:
        """获取会话摘要（用于保存到中期记忆）"""
        if not self.memory:
            return "空会话"
        
        messages = list(self.memory)
        user_messages = [m for m in messages if m["role"] == "user"]
        
        if not user_messages:
            return "无用户消息的会话"
        
        first_msg = user_messages[0]["content"][:50] if user_messages else ""
        return f"会话主题: {first_msg}... (共{len(messages)}条消息)"


class MidTermMemory:
    """
    中期记忆 - 基于 SQLite 实现
    保存跨会话的用户偏好、对话摘要等
    """
    
    def __init__(self, db_path: str = None):
        if db_path is None:
            db_path = os.path.join(
                os.path.dirname(os.path.abspath(__file__)),
                "mid_term_memory.db"
            )
        self.db_path = db_path
        self._init_database()
    
    def _init_database(self) -> None:
        """初始化数据库表结构"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 用户偏好表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_preferences (
                key TEXT PRIMARY KEY,
                value TEXT,
                updated_at TEXT
            )
        """)
        
        # 会话摘要表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS session_summaries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT,
                summary TEXT,
                created_at TEXT,
                messages_count INTEGER
            )
        """)
        
        # 用户事实表（记住的重要信息）
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_facts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                fact TEXT,
                category TEXT,
                created_at TEXT,
                confidence REAL
            )
        """)
        
        conn.commit()
        conn.close()
    
    # ========== 用户偏好管理 ==========
    def set_preference(self, key: str, value: str) -> None:
        """设置用户偏好"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT OR REPLACE INTO user_preferences (key, value, updated_at)
            VALUES (?, ?, ?)
        """, (key, value, datetime.now().isoformat()))
        
        conn.commit()
        conn.close()
    
    def get_preference(self, key: str, default: str = None) -> Optional[str]:
        """获取用户偏好"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT value FROM user_preferences WHERE key = ?", (key,))
        result = cursor.fetchone()
        
        conn.close()
        
        return result[0] if result else default
    
    def get_all_preferences(self) -> Dict[str, str]:
        """获取所有用户偏好"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT key, value FROM user_preferences")
        results = cursor.fetchall()
        
        conn.close()
        
        return {key: value for key, value in results}
    
    # ========== 会话摘要管理 ==========
    def save_session_summary(self, session_id: str, summary: str, messages_count: int) -> None:
        """保存会话摘要"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO session_summaries (session_id, summary, created_at, messages_count)
            VALUES (?, ?, ?, ?)
        """, (session_id, summary, datetime.now().isoformat(), messages_count))
        
        conn.commit()
        conn.close()
    
    def get_recent_summaries(self, limit: int = 10) -> List[Dict[str, Any]]:
        """获取最近的会话摘要"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT session_id, summary, created_at, messages_count
            FROM session_summaries
            ORDER BY created_at DESC
            LIMIT ?
        """, (limit,))
        
        results = cursor.fetchall()
        conn.close()
        
        return [
            {
                "session_id": r[0],
                "summary": r[1],
                "created_at": r[2],
                "messages_count": r[3]
            }
            for r in results
        ]
    
    # ========== 用户事实管理 ==========
    def add_user_fact(self, fact: str, category: str = "general", confidence: float = 0.8) -> None:
        """添加用户事实（如"用户名叫小明"）"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO user_facts (fact, category, created_at, confidence)
            VALUES (?, ?, ?, ?)
        """, (fact, category, datetime.now().isoformat(), confidence))
        
        conn.commit()
        conn.close()
    
    def get_user_facts(self, category: str = None) -> List[Dict[str, Any]]:
        """获取用户事实"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        if category:
            cursor.execute("""
                SELECT id, fact, category, created_at, confidence
                FROM user_facts
                WHERE category = ?
                ORDER BY created_at DESC
            """, (category,))
        else:
            cursor.execute("""
                SELECT id, fact, category, created_at, confidence
                FROM user_facts
                ORDER BY created_at DESC
            """)
        
        results = cursor.fetchall()
        conn.close()
        
        return [
            {
                "id": r[0],
                "fact": r[1],
                "category": r[2],
                "created_at": r[3],
                "confidence": r[4]
            }
            for r in results
        ]
    
    def build_system_prompt_context(self) -> str:
        """构建用于 LLM 的系统提示词上下文"""
        preferences = self.get_all_preferences()
        facts = self.get_user_facts()
        
        parts = []
        
        if preferences:
            parts.append("【用户偏好】")
            for key, value in preferences.items():
                parts.append(f"- {key}: {value}")
        
        if facts:
            parts.append("\n【已知用户事实】")
            for fact in facts[:10]:  # 限制数量
                parts.append(f"- {fact['fact']}")
        
        return "\n".join(parts) if parts else ""


class LongTermMemory:
    """
    长期记忆 - 基于向量检索实现
    保存重要事实性知识，支持语义检索
    """
    
    def __init__(self):
        self.vector_dim = 1536  # DashScope text-embedding-v2 的维度
        self.collection_name = "long_term_memory"
        
        # 尝试初始化 Milvus，如果不可用则使用简单的本地存储
        self.use_milvus = self._init_milvus()
        
        if not self.use_milvus:
            # 使用简单的本地存储作为 fallback
            self._init_local_storage()
    
    def _init_milvus(self) -> bool:
        """尝试初始化 Milvus 连接"""
        try:
            # 检查是否有 Milvus 相关的导入和配置
            # 由于这是模拟实现，我们先检查是否有相关依赖
            # 在实际项目中，这里应该是真实的 Milvus 连接代码
            return False  # 默认使用本地存储
        except Exception as e:
            print(f"Milvus 初始化失败，使用本地存储: {e}")
            return False
    
    def _init_local_storage(self) -> None:
        """初始化本地存储作为 long-term memory 的 fallback"""
        self.local_memory_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "long_term_memory.json"
        )
        
        if not os.path.exists(self.local_memory_path):
            with open(self.local_memory_path, 'w', encoding='utf-8') as f:
                json.dump([], f)
    
    def _compute_simple_hash(self, text: str) -> str:
        """计算简单的文本哈希（替代向量）"""
        return hashlib.md5(text.encode('utf-8')).hexdigest()
    
    def _simple_similarity_score(self, text1: str, text2: str) -> float:
        """简单的相似度评分（基于关键词重叠）"""
        # 中文分词处理（简单实现）
        def tokenize(text):
            tokens = []
            text_lower = text.lower()
            
            # 常用关键词
            keywords = ["名字", "叫", "喜欢", "颜色", "住", "哪里", "生日", "语言", "会说",
                       "用户", "我", "什么", "是", "的", "吗", "呢", "啊"]
            
            # 先按空格分割
            words = text_lower.split()
            
            # 对于每个词，检查是否包含关键词
            for word in words:
                tokens.append(word)
                for kw in keywords:
                    if kw in word:
                        tokens.append(kw)
            
            # 也添加单个字符（中文）
            for char in text_lower:
                if '\u4e00' <= char <= '\u9fff':  # 中文字符范围
                    tokens.append(char)
            
            return set(tokens)
        
        words1 = tokenize(text1)
        words2 = tokenize(text2)
        
        if not words1 or not words2:
            return 0.0
        
        intersection = words1 & words2
        
        # 计算 Jaccard 相似度
        if not intersection:
            return 0.0
        
        # 使用更灵活的评分
        score = len(intersection) / min(len(words1), len(words2))
        return min(score, 1.0)
    
    def add_memory(self, content: str, metadata: Dict[str, Any] = None) -> str:
        """添加长期记忆"""
        memory_id = self._compute_simple_hash(content)
        memory_item = {
            "id": memory_id,
            "content": content,
            "metadata": metadata or {},
            "created_at": datetime.now().isoformat()
        }
        
        # 保存到本地存储
        if os.path.exists(self.local_memory_path):
            with open(self.local_memory_path, 'r', encoding='utf-8') as f:
                memories = json.load(f)
        else:
            memories = []
        
        # 检查是否已存在
        existing_ids = [m["id"] for m in memories]
        if memory_id not in existing_ids:
            memories.append(memory_item)
            
            with open(self.local_memory_path, 'w', encoding='utf-8') as f:
                json.dump(memories, f, ensure_ascii=False, indent=2)
        
        return memory_id
    
    def search_memories(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """检索相关的长期记忆"""
        if not os.path.exists(self.local_memory_path):
            return []
        
        with open(self.local_memory_path, 'r', encoding='utf-8') as f:
            memories = json.load(f)
        
        # 简单的相似度排序
        scored_memories = []
        for memory in memories:
            score = self._simple_similarity_score(query, memory["content"])
            scored_memories.append((score, memory))
        
        # 按分数排序
        scored_memories.sort(key=lambda x: x[0], reverse=True)
        
        # 返回 top_k 结果
        return [
            {
                "content": m[1]["content"],
                "metadata": m[1]["metadata"],
                "score": m[0]
            }
            for m in scored_memories[:top_k] if m[0] > 0.05
        ]
    
    def get_all_memories(self) -> List[Dict[str, Any]]:
        """获取所有长期记忆"""
        if not os.path.exists(self.local_memory_path):
            return []
        
        with open(self.local_memory_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def should_store_to_long_term(self, text: str) -> bool:
        """判断是否应该存储到长期记忆"""
        # 简单的启发式规则
        keywords = ["记住", "记得", "我的名字", "我叫", "我喜欢", "我不喜欢", "我住", "我工作"]
        return any(keyword in text for keyword in keywords)


if __name__ == "__main__":
    # 简单的测试
    print("测试短期记忆...")
    stm = ShortTermMemory(max_history=5)
    stm.add_message("user", "你好")
    stm.add_message("assistant", "你好，有什么可以帮助你的？")
    print(f"短期记忆: {stm.get_history()}")
    
    print("\n测试中期记忆...")
    mtm = MidTermMemory()
    mtm.set_preference("tone", "friendly")
    mtm.add_user_fact("用户叫小明", category="identity")
    print(f"用户偏好: {mtm.get_all_preferences()}")
    print(f"用户事实: {mtm.get_user_facts()}")
    
    print("\n测试长期记忆...")
    ltm = LongTermMemory()
    ltm.add_memory("用户喜欢蓝色", metadata={"category": "preference"})
    ltm.add_memory("用户住在北京", metadata={"category": "location"})
    results = ltm.search_memories("用户住在哪里")
    print(f"检索结果: {results}")
    
    print("\n所有测试完成！")
