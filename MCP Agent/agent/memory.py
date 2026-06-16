"""
对话记忆模块 - 管理对话历史
"""
from typing import List, Dict, Any
from datetime import datetime


class ConversationMemory:
    def __init__(self, max_history: int = 10):
        self.history: List[Dict[str, Any]] = []
        self.max_history = max_history
    
    def add_message(self, role: str, content: str, metadata: Dict[str, Any] = None):
        """添加一条消息到记忆"""
        message = {
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat(),
            "metadata": metadata or {}
        }
        self.history.append(message)
        
        # 限制历史长度
        if len(self.history) > self.max_history:
            self.history = self.history[-self.max_history:]
    
    def get_history(self) -> List[Dict[str, Any]]:
        """获取完整历史"""
        return self.history.copy()
    
    def get_recent_context(self, n: int = 5) -> List[Dict[str, Any]]:
        """获取最近的 n 条消息"""
        return self.history[-n:]
    
    def clear(self):
        """清空记忆"""
        self.history = []
    
    def to_string(self) -> str:
        """将历史转换为字符串格式"""
        result = []
        for msg in self.history:
            role_str = "用户" if msg["role"] == "user" else "助手"
            result.append(f"{role_str}: {msg['content']}")
        return "\n".join(result)
