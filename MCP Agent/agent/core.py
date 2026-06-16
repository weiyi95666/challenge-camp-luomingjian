"""
智能体核心 - 将所有组件整合在一起
"""
from typing import Dict, Any, Optional
import json
import sys
import os
from datetime import datetime

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agent.memory import ConversationMemory
from agent.tool_selector import ToolSelector
from agent.llm_client import LLMClient, get_llm_client
from utils import load_config, run_tool
from logger import get_logger, log_user_message, log_agent_response, log_tool_use, log_error, log_system_event


class MCPAgent:
    """MCP 智能体核心类"""
    
    def __init__(self, config_path: str = None):
        self.logger = get_logger()
        log_system_event("初始化智能体")
        
        # 加载配置
        if config_path is None:
            config_path = os.path.join(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                "servers_config.json"
            )
        
        self.config = load_config()
        self.logger.info(f"配置加载完成，工具数量: {len(self.config.get('servers', []))}")
        
        # 初始化组件
        self.memory = ConversationMemory(max_history=20)
        self.tool_selector = ToolSelector(self.config)
        
        # 不保存 LLM 客户端的引用，每次动态获取最新配置
        self._llm = None
        
        # 联网模式配置
        self.online_mode_enabled = True
        log_system_event("智能体初始化完成")
    
    @property
    def llm(self):
        """获取最新的 LLM 客户端"""
        return get_llm_client()
    
    def set_online_mode(self, enabled):
        """设置联网模式"""
        self.online_mode_enabled = enabled
        self.logger.info(f"智能体重联网模式: {'启用' if enabled else '禁用'}")
    
    def get_online_mode(self):
        """获取联网模式状态"""
        return self.online_mode_enabled
    
    def process_message(self, user_input: str) -> Dict[str, Any]:
        """
        处理用户消息，返回智能体响应
        
        参数:
            user_input: 用户输入
            
        返回:
            响应字典
        """
        log_user_message(user_input)
        
        try:
            # 0. 检测时间查询（优先处理）
            text_lower = user_input.lower()
            time_keywords = ["现在时间", "几点了", "现在几点", "当前时间", "what time", "current time"]
            if any(kw in text_lower for kw in time_keywords):
                now = datetime.now()
                # 安全的时间格式化方式，避免 Windows 编码问题
                year = now.year
                month = now.month
                day = now.day
                hour = now.hour
                minute = now.minute
                second = now.second
                time_str = f"{year}年{month}月{day}日 {hour:02d}:{minute:02d}:{second:02d}"
                self.logger.info(f"时间查询请求，返回: {time_str}")
                response = f"现在的时间是：{time_str}"
                self.memory.add_message("user", user_input)
                self.memory.add_message("assistant", response, {
                    "tool_used": None,
                    "tool_result": None
                })
                log_agent_response(response)
                return {
                    "response": response,
                    "tool_used": None,
                    "tool_result": None
                }
            
            # 1. 添加用户消息到记忆
            self.memory.add_message("user", user_input)
            
            # 2. 选择工具
            selected_tool = self.tool_selector.select_tool(user_input, self.llm)
            
            # 联网工具列表
            online_tools = ["weather", "web_search", "webpage"]
            
            tool_result = None
            if selected_tool:
                # 检查是否在联网模式禁用时使用了联网工具
                if not self.online_mode_enabled and selected_tool["name"] in online_tools:
                    self.logger.info(f"联网模式已禁用，跳过工具: {selected_tool['name']}")
                    selected_tool = None
                else:
                    self.logger.info(f"选择工具: {selected_tool['name']}")
                    
                    # 3. 解析工具参数
                    params = self.tool_selector.parse_tool_params(user_input, selected_tool)
                    self.logger.info(f"工具参数: {params}")
                    
                    # 4. 调用工具
                    try:
                        tool_response = run_tool(
                            selected_tool["script"],
                            selected_tool["tool"],
                            params
                        )
                        tool_result = tool_response.get("result") or tool_response
                        log_tool_use(selected_tool['name'], params, tool_result)
                    except Exception as e:
                        log_error("工具调用错误", f"工具 {selected_tool['name']} 调用失败", e)
                        tool_result = {"error": str(e)}
            
            # 5. 生成回复
            response = self._generate_response(user_input, tool_result, selected_tool)
            
            # 6. 添加助手回复到记忆
            self.memory.add_message("assistant", response, {
                "tool_used": selected_tool["name"] if selected_tool else None,
                "tool_result": tool_result
            })
            
            log_agent_response(response, selected_tool["name"] if selected_tool else None)
            
            return {
                "response": response,
                "tool_used": selected_tool["name"] if selected_tool else None,
                "tool_result": tool_result
            }
            
        except Exception as e:
            log_error("消息处理错误", f"处理用户消息时发生错误", e)
            error_response = "抱歉，处理您的消息时发生了错误，请稍后再试。"
            log_agent_response(error_response)
            return {
                "response": error_response,
                "tool_used": None,
                "tool_result": None
            }
    
    def _generate_response(self, user_input: str, tool_result: Any, used_tool: Optional[Dict[str, Any]]) -> str:
        """
        生成自然语言回复
        
        参数:
            user_input: 用户输入
            tool_result: 工具执行结果
            used_tool: 使用的工具
            
        返回:
            自然语言回复
        """
        # 总是尝试使用 LLM 生成回复（新的架构会动态检查配置）
        return self._generate_with_llm(user_input, tool_result, used_tool)
    
    def _generate_with_llm(self, user_input: str, tool_result: Any, used_tool: Optional[Dict[str, Any]]) -> str:
        """使用 LLM 生成回复"""
        try:
            # 构建消息
            messages = []
            
            # 系统提示词（MCP 智能出行助手）
            system_prompt = """你是"MCP 智能出行助手"，基于高德地图、天气查询、文件写入等工具，为用户提供出行规划、天气查询、信息保存等服务。

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
            messages.append({"role": "system", "content": system_prompt})
            
            # 添加历史对话
            history = self.memory.get_history()
            for msg in history[-5:]:  # 只取最近5条
                if msg["role"] in ["user", "assistant"]:
                    messages.append({"role": msg["role"], "content": msg["content"]})
            
            # 构建当前提示
            if tool_result and used_tool:
                # 如果有工具结果，加入提示
                tool_name = used_tool["name"]
                
                if tool_name == "weather":
                    # 天气查询，直接使用模板回复
                    return self._generate_template_response(user_input, tool_result, used_tool)
                
                elif tool_name == "web_search":
                    # 检查是否有 Tavily 提供的直接答案
                    if isinstance(tool_result, dict) and tool_result.get("answer"):
                        answer = tool_result.get("answer", "")
                        if answer and len(answer) > 10:
                            return answer
                    
                    # 否则让 LLM 处理搜索结果
                    search_results = tool_result.get("results", []) if isinstance(tool_result, dict) else []
                    
                    prompt = f"""用户问题：{user_input}

搜索结果：
{json.dumps(search_results, ensure_ascii=False, indent=2)}

请基于搜索结果，给用户一个简洁、准确的回答。只回答问题本身，不要添加额外的格式或符号。"""
                
                elif tool_name == "writer":
                    # 文件写入，直接使用模板
                    return self._generate_template_response(user_input, tool_result, used_tool)
                
                else:
                    prompt = f"""用户问题：{user_input}

工具结果：
{json.dumps(tool_result, ensure_ascii=False, indent=2)}

请根据信息回复用户。"""
            
            else:
                # 没有使用工具，直接回复
                prompt = user_input
            
            messages.append({"role": "user", "content": prompt})
            
            # 调用 LLM，使用更低的温度获得更稳定的输出
            response = self.llm.chat(messages, temperature=0.6, max_tokens=1500)
            
            if "content" in response:
                content = response["content"]
                # 清理文本
                from agent.llm_client import clean_text
                content = clean_text(content)
                if content:
                    return content
            
            # 如果 LLM 失败，回退到模板
            return self._generate_template_response(user_input, tool_result, used_tool)
                
        except Exception as e:
            log_error("LLM 生成失败", str(e), e)
            # 出错时回退到模板
            return self._generate_template_response(user_input, tool_result, used_tool)
    
    def _generate_template_response(self, user_input: str, tool_result: Any, 
                                   used_tool: Optional[Dict[str, Any]]) -> str:
        """模板化回复（后备方案）"""
        if not used_tool:
            return "我理解了您的问题，但还需要更多信息才能帮助您。"
        
        tool_name = used_tool["name"]
        
        if tool_name == "weather" and tool_result:
            if tool_result.get("success"):
                location = tool_result.get("location", "未知")
                weather = tool_result.get("weather", "未知")
                temp = tool_result.get("temperature", "未知")
                humidity = tool_result.get("humidity", "")
                wind = tool_result.get("wind_speed", "")
                source = tool_result.get("data_source", "")
                
                response = f"🌤️ {location}的天气：\n"
                response += f"• 天气状况：{weather}\n"
                response += f"• 温度：{temp}\n"
                if humidity:
                    response += f"• 湿度：{humidity}\n"
                if wind:
                    response += f"• 风速：{wind}\n"
                if source:
                    response += f"\n数据来源：{source}"
                return response
            elif tool_result.get("fallback"):
                fallback = tool_result["fallback"]
                location = tool_result.get("location", "未知")
                return f"⚠️ 网络请求失败，使用模拟数据：\n{location}的天气是{fallback.get('weather')}，温度{fallback.get('temperature')}"
            else:
                return f"抱歉，天气查询失败：{tool_result.get('error', '未知错误')}"
        
        elif tool_name == "writer" and tool_result:
            path = tool_result.get("path", "文件")
            return f"✅ 好的，我已经将内容保存到了 {path}。"
        
        elif tool_name == "rag" and tool_result:
            answer = tool_result.get("answer", "")
            return answer
        
        elif tool_name == "web_search" and tool_result:
            if tool_result.get("success"):
                query = tool_result.get("query", "")
                results = tool_result.get("results", [])
                answer = tool_result.get("answer", "")
                source = tool_result.get("source", "")
                
                # 如果 Tavily 提供了直接答案，优先使用
                if answer and source == "Tavily":
                    response = f"🔍 关于 '{query}' 的信息：\n\n"
                    response += f"{answer}\n\n"
                    
                    if results:
                        response += "---\n📚 参考来源：\n"
                        for i, result in enumerate(results[:3], 1):
                            title = result.get("title", "")
                            url = result.get("url", "")
                            if title:
                                response += f"{i}. {title}"
                                if url:
                                    response += f" ({url})"
                                response += "\n"
                    return response
                
                # 否则显示搜索结果列表
                if not results:
                    return tool_result.get("message", f"未找到关于 '{query}' 的搜索结果。")
                
                response = f"🔍 关于 '{query}' 的搜索结果：\n\n"
                for i, result in enumerate(results[:5], 1):
                    title = result.get("title", "")
                    snippet = result.get("snippet", "")
                    url = result.get("url", "")
                    response += f"{i}. {title}\n"
                    if snippet:
                        response += f"   {snippet[:150]}...\n"
                    if url:
                        response += f"   {url}\n"
                    response += "\n"
                return response
            else:
                return f"抱歉，搜索失败：{tool_result.get('error', '未知错误')}"
        
        elif tool_name == "webpage" and tool_result:
            if tool_result.get("success"):
                url = tool_result.get("url", "")
                title = tool_result.get("title", "")
                content = tool_result.get("content", "")
                
                response = f"📄 网页访问成功！\n"
                response += f"标题：{title}\n"
                response += f"地址：{url}\n\n"
                response += "内容摘要：\n"
                response += content[:500]
                if len(content) > 500:
                    response += "..."
                return response
            else:
                return f"抱歉，网页访问失败：{tool_result.get('error', '未知错误')}"
        
        return "好的，我已经帮您处理了。"
    
    def clear_memory(self):
        """清空对话记忆"""
        self.memory.clear()
    
    def get_conversation_history(self):
        """获取对话历史"""
        return self.memory.get_history()


# 单例模式
_agent_instance: Optional[MCPAgent] = None


def get_agent() -> MCPAgent:
    """获取智能体实例"""
    global _agent_instance
    if _agent_instance is None:
        _agent_instance = MCPAgent()
    return _agent_instance
