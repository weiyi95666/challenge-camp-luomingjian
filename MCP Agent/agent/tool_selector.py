"""
工具选择器 - 智能决定使用哪个工具
"""
from typing import Dict, Any, List, Optional
import json


class ToolSelector:
    def __init__(self, tools_config: Dict[str, Any]):
        self.tools_config = tools_config
        self.tools = self._load_tools()
    
    def _load_tools(self) -> List[Dict[str, Any]]:
        """加载工具配置"""
        return self.tools_config.get("servers", [])
    
    def get_tool_descriptions(self) -> str:
        """获取工具的描述，用于提示 LLM"""
        descriptions = []
        for tool in self.tools:
            name = tool["name"]
            if name == "weather":
                desc = "天气查询工具 - 查询指定城市的真实天气信息"
            elif name == "writer":
                desc = "文件写入工具 - 将内容写入到文件中"
            elif name == "word":
                desc = "Word文档创建工具 - 生成Office Word文档（.docx格式），支持标题、列表、格式化内容"
            elif name == "rag":
                desc = "知识库问答工具 - 从知识库中检索信息回答问题"
            elif name == "web_search":
                desc = "网络搜索工具 - 在互联网上搜索信息"
            elif name == "webpage":
                desc = "网页访问工具 - 访问和抓取指定网页的内容"
            else:
                desc = f"{name} 工具"
            descriptions.append(f"- {name}: {desc}")
        return "\n".join(descriptions)
    
    def select_tool(self, user_input: str, llm_client=None) -> Optional[Dict[str, Any]]:
        """
        选择合适的工具
        
        参数:
            user_input: 用户输入
            llm_client: LLM 客户端（如果提供则使用 LLM 智能选择）
            
        返回:
            选中的工具配置，或 None（表示不需要工具）
        """
        # 基础规则选择（作为后备方案）
        return self._rule_based_selection(user_input)
    
    def _rule_based_selection(self, user_input: str) -> Optional[Dict[str, Any]]:
        """基于规则的工具选择"""
        user_input_lower = user_input.lower()
        
        # Word文档关键词（优先于普通写文件）
        word_keywords = ["word", "文档", "docx", "报告", "信函", "备忘录", "计划", "创建word", "生成word", "写word"]
        if any(keyword in user_input_lower for keyword in word_keywords):
            return next((t for t in self.tools if t["name"] == "word"), None)
        
        # 网页访问关键词
        webpage_keywords = ["访问", "打开", "抓取", "网页", "网站", "url", "http", "www"]
        if any(keyword in user_input_lower for keyword in webpage_keywords):
            return next((t for t in self.tools if t["name"] == "webpage"), None)
        
        # 网络搜索关键词
        search_keywords = ["搜索", "查一下", "查找", "网上", "互联网", "百度", "google", "search"]
        if any(keyword in user_input_lower for keyword in search_keywords):
            return next((t for t in self.tools if t["name"] == "web_search"), None)
        
        # 天气相关关键词
        weather_keywords = ["天气", "气温", "温度", "下雨", "晴天", "阴天", "weather"]
        if any(keyword in user_input_lower for keyword in weather_keywords):
            return next((t for t in self.tools if t["name"] == "weather"), None)
        
        # 写文件相关关键词
        write_keywords = ["写", "保存", "存储", "记录", "write", "save"]
        if any(keyword in user_input_lower for keyword in write_keywords):
            return next((t for t in self.tools if t["name"] == "writer"), None)
        
        # 默认不使用工具，让 LLM 直接回答
        return None
    
    def parse_tool_params(self, user_input: str, tool: Dict[str, Any]) -> Dict[str, Any]:
        """
        从用户输入中解析工具参数
        
        参数:
            user_input: 用户输入
            tool: 工具配置
            
        返回:
            工具参数字典
        """
        tool_name = tool["name"]
        
        if tool_name == "weather":
            # 解析城市名
            parts = user_input.split()
            city = "北京"
            if len(parts) > 1:
                city = parts[1]
            # 清理关键词
            keywords = ["天气", "查询", "查", "怎么样", "如何", "今天"]
            for kw in keywords:
                city = city.replace(kw, "")
            city = city.strip()
            if not city:
                city = "北京"
            return {"location": city}
        
        elif tool_name == "writer":
            # 解析文件名和内容
            parts = user_input.split(maxsplit=2)
            if len(parts) >= 3:
                filename = parts[1]
                content = parts[2]
            else:
                filename = "notes.txt"
                content = user_input
            return {"path": filename, "content": content}
        
        elif tool_name == "web_search":
            # 提取搜索关键词
            query = user_input
            # 清理搜索前缀
            prefixes = ["搜索", "查一下", "查找", "帮我搜", "搜一下", "网上搜", "在网上", "请问"]
            for prefix in prefixes:
                if query.startswith(prefix):
                    query = query[len(prefix):]
            query = query.strip()
            return {"query": query, "num_results": 5}
        
        elif tool_name == "webpage":
            # 提取URL
            import re
            # 简单的URL匹配
            url_pattern = r'https?://[^\s<>"\']+|www\.[^\s<>"\']+'
            urls = re.findall(url_pattern, user_input)
            if urls:
                url = urls[0]
                if not url.startswith('http'):
                    url = 'https://' + url
                return {"url": url}
            # 如果没有URL，提取可能的关键词
            return {"url": "", "hint": user_input}
        
        elif tool_name == "word":
            # 解析Word文档参数
            # 尝试提取标题、文件名和内容
            filename = "文档"
            title = "文档"
            content = user_input
            
            # 清理输入，提取关键词
            import re
            word_prefixes = ["写", "创建", "生成", "帮我写", "帮我创建", "帮我生成", "帮我做"]
            for prefix in word_prefixes:
                if user_input.startswith(prefix):
                    content = user_input[len(prefix):].strip()
            
            # 简单的文档类型识别
            doc_types = ["报告", "计划", "备忘录", "信函", "总结", "纪要"]
            for dtype in doc_types:
                if dtype in user_input:
                    title = dtype
                    filename = dtype
            
            # 尝试提取标题
            if "标题" in user_input:
                title_parts = user_input.split("标题")
                if len(title_parts) > 1:
                    possible_title = title_parts[1].split("，")[0].split(",")[0].split("。")[0].strip()
                    if possible_title:
                        title = possible_title
                        filename = possible_title
            
            return {
                "filename": filename,
                "title": title,
                "content": content
            }
        
        elif tool_name == "rag":
            return {"question": user_input}
        
        return {}
