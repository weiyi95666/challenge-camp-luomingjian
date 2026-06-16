"""
带三层记忆系统的智能体
集成了短期、中期、长期记忆功能
"""
import sys
import os
import json
from typing import Dict, Any, Optional
from datetime import datetime
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 导入记忆系统
from memory_system import ShortTermMemory, MidTermMemory, LongTermMemory

# 导入原有的核心组件（不修改这些文件）
try:
    from vector_retriever import VectorRetriever
except ImportError:
    # 如果没有 VectorRetriever，使用简单的模拟实现
    class VectorRetriever:
        def answer_question(self, question: str) -> str:
            return f"关于\"{question}\"：知识库暂无内容。"

try:
    from agent.llm_client import LLMClient, get_llm_client
except ImportError:
    # 如果没有 LLMClient，创建简单的模拟
    def get_llm_client():
        return LLMClient()
    
    class LLMClient:
        def chat(self, messages: list) -> str:
            return "这是模拟的LLM回复。"

from logger import get_logger, log_user_message, log_agent_response


class ChatAgentWithMemory:
    """
    带三层记忆系统的对话智能体
    """
    
    def __init__(self):
        self.logger = get_logger()
        
        # 初始化三层记忆
        self.short_term = ShortTermMemory(max_history=15)
        self.mid_term = MidTermMemory()
        self.long_term = LongTermMemory()
        
        # 初始化原有的 RAG 检索器
        try:
            self.vector_retriever = VectorRetriever()
        except Exception as e:
            self.logger.warning(f"RAG 检索器初始化失败: {e}")
            self.vector_retriever = None
        
        # 对话计数器（用于定期保存摘要）
        self.message_count = 0
        self.summary_interval = 10  # 每 10 条消息保存一次摘要
    
    def _build_system_prompt(self) -> str:
        """构建包含中期记忆的系统提示词"""
        base_prompt = """你是"MCP 智能出行助手"，基于高德地图、天气查询、文件写入等工具，为用户提供出行规划、天气查询、信息保存等服务。

## 核心能力
- 使用高德地图MCP工具查询路线、规划出行。
- 使用天气MCP工具查询实时天气。
- 使用文件写入MCP工具将信息保存到本地文件。

## 回答格式要求（非常重要）

当用户询问**路线规划**（如"广州到深圳驾车路线"）时，你必须按照以下**固定格式**输出：

### 1. 路线概览
从起点到终点，全程xx公里，预计xx小时xx分钟。

### 2. 主要行驶路线（分步骤列出）
1. 从起点出发 → 沿xx路/高速
2. ...
（列出5-9个关键节点）

### 3. 分段行程亮点
- 高速路段特点
- 隧道/桥梁注意事项
- 收费站提示
- 市区路段提示

### 4. 出行建议
- 最佳出行时间
- 加油/充电提示
- 导航工具建议
- 天气提醒

### 5. 主动询问
在回答末尾，**必须主动询问**："是否需要我为你生成一份可保存的文本文件？或者查看沿途加油站、餐饮服务点？"

## 文件保存功能
如果用户要求保存内容到文件，你需要：
1. 调用 `write_file` 工具。
2. 确认保存成功后，回复："已将内容保存到本地文件：`[文件路径]`"并展示内容摘要。

## 天气查询
如果用户询问天气，使用 `query_weather` 工具返回结果，并主动询问是否需要将天气信息保存到文件。

## 其他注意事项
- 回答必须使用中文，语言亲切专业。
- 不要编造数据，所有路线、时间、距离必须从高德MCP工具获取。
- 如果用户没有提供具体地点，主动询问起点和终点。"""
        
        # 添加中期记忆中的上下文
        memory_context = self.mid_term.build_system_prompt_context()
        
        if memory_context:
            return f"{base_prompt}\n\n{memory_context}"
        return base_prompt
    
    def _retrieve_long_term_memory(self, query: str) -> str:
        """从长期记忆中检索相关信息"""
        relevant_memories = self.long_term.search_memories(query, top_k=3)
        
        if not relevant_memories:
            return ""
        
        context_parts = ["【相关背景信息】"]
        for memory in relevant_memories:
            context_parts.append(f"- {memory['content']}")
        
        return "\n".join(context_parts)
    
    def _extract_memory_from_text(self, text: str) -> Optional[str]:
        """从文本中提取可能需要长期记忆的信息"""
        # 简单的规则提取
        if "记住" in text or "记得" in text:
            # 尝试提取"记住"后面的内容
            keywords = ["记住", "记得"]
            for keyword in keywords:
                if keyword in text:
                    idx = text.index(keyword)
                    content = text[idx + len(keyword):].strip()
                    if content:
                        # 清理标点符号
                        content = content.rstrip("。！？.！?")
                        return content
        
        # 其他启发式规则
        if "我叫" in text:
            return text
        if "我的名字是" in text:
            return text
        if "我喜欢" in text:
            return text
        
        return None
    
    def _should_save_summary(self) -> bool:
        """判断是否应该保存会话摘要"""
        return self.message_count > 0 and self.message_count % self.summary_interval == 0
    
    def process_message(self, user_input: str) -> Dict[str, Any]:
        """
        处理用户消息的主函数
        """
        log_user_message(user_input)
        self.message_count += 1
        
        try:
            # 1. 添加用户消息到短期记忆
            self.short_term.add_message("user", user_input)
            
            # 2. 从长期记忆中检索相关信息
            long_term_context = self._retrieve_long_term_memory(user_input)
            
            # 3. 构建消息列表
            messages = []
            
            # 系统提示词（包含中期记忆）
            system_prompt = self._build_system_prompt()
            messages.append({"role": "system", "content": system_prompt})
            
            # 添加短期记忆中的历史对话
            recent_history = self.short_term.get_recent_context(n=10)
            for msg in recent_history[:-1]:  # 排除当前用户消息
                messages.append({
                    "role": msg["role"],
                    "content": msg["content"]
                })
            
            # 构建最终的用户消息（加入长期记忆上下文）
            final_user_msg = user_input
            if long_term_context:
                final_user_msg = f"{long_term_context}\n\n用户问题：{user_input}"
            
            messages.append({"role": "user", "content": final_user_msg})
            
            # 4. 调用 RAG（如果可用）
            rag_answer = ""
            if self.vector_retriever:
                try:
                    rag_answer = self.vector_retriever.answer_question(user_input)
                except Exception as e:
                    self.logger.warning(f"RAG 检索失败: {e}")
            
            # 5. 调用 LLM
            llm_client = get_llm_client()
            response = llm_client.chat(messages)
            
            # 6. 确保 response 是字符串
            if not isinstance(response, str):
                response = str(response)
            
            # 7. 处理并添加助手回复到短期记忆
            self.short_term.add_message("assistant", response)
            
            # 8. 检查是否需要提取长期记忆
            memory_to_store = self._extract_memory_from_text(user_input)
            if memory_to_store:
                self.long_term.add_memory(
                    memory_to_store,
                    metadata={
                        "source": "user_direct",
                        "session_id": self.short_term.session_id
                    }
                )
                # 也保存到中期记忆的用户事实中
                self.mid_term.add_user_fact(memory_to_store, category="user_mentioned")
            
            # 9. 定期保存会话摘要到中期记忆
            if self._should_save_summary():
                summary = self.short_term.get_session_summary()
                self.mid_term.save_session_summary(
                    self.short_term.session_id,
                    summary,
                    self.message_count
                )
            
            log_agent_response(response)
            
            return {
                "response": response,
                "memory_used": {
                    "short_term_count": len(self.short_term.get_history()),
                    "long_term_relevant": bool(long_term_context)
                }
            }
            
        except Exception as e:
            self.logger.error(f"处理消息时出错: {e}", exc_info=True)
            error_response = "抱歉，处理您的消息时发生了错误，请稍后再试。"
            log_agent_response(error_response)
            return {
                "response": error_response,
                "error": str(e)
            }
    
    def clear_short_term_memory(self):
        """清空短期记忆（开始新会话）"""
        # 保存当前会话的摘要
        if len(self.short_term.get_history()) > 0:
            summary = self.short_term.get_session_summary()
            self.mid_term.save_session_summary(
                self.short_term.session_id,
                summary,
                self.message_count
            )
        
        # 重置短期记忆
        self.short_term.clear()
        self.short_term.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.message_count = 0
    
    def get_memory_status(self) -> Dict[str, Any]:
        """获取当前记忆状态"""
        return {
            "short_term": {
                "count": len(self.short_term.get_history()),
                "session_id": self.short_term.session_id
            },
            "mid_term": {
                "preferences_count": len(self.mid_term.get_all_preferences()),
                "facts_count": len(self.mid_term.get_user_facts()),
                "sessions_count": len(self.mid_term.get_recent_summaries(limit=100))
            },
            "long_term": {
                "count": len(self.long_term.get_all_memories())
            }
        }


# ========== 简单的测试函数 ==========
def test_agent_with_memory():
    """测试带记忆的智能体"""
    print("=" * 60)
    print("测试带三层记忆系统的智能体")
    print("=" * 60)
    
    agent = ChatAgentWithMemory()
    
    print("\n1. 初始记忆状态:")
    print(json.dumps(agent.get_memory_status(), indent=2, ensure_ascii=False))
    
    print("\n2. 第一次对话:")
    result1 = agent.process_message("你好，我叫小明")
    print(f"回复: {result1['response']}")
    
    print("\n3. 第二次对话（应该记住名字）:")
    result2 = agent.process_message("我叫什么名字？")
    print(f"回复: {result2['response']}")
    
    print("\n4. 测试记住信息:")
    result3 = agent.process_message("记住，我喜欢蓝色")
    print(f"回复: {result3['response']}")
    
    print("\n5. 再次询问（应该从长期记忆检索）:")
    result4 = agent.process_message("我喜欢什么颜色？")
    print(f"回复: {result4['response']}")
    
    print("\n6. 当前记忆状态:")
    print(json.dumps(agent.get_memory_status(), indent=2, ensure_ascii=False))
    
    print("\n测试完成！")


if __name__ == "__main__":
    test_agent_with_memory()
