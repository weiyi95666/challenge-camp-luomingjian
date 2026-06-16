"""
LLM 客户端接口 - 支持 OpenAI 兼容 API
"""
from typing import Dict, Any, Optional
import json
import sys
import os
import re

# 添加项目根目录以导入 config
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from logger import get_logger, log_api_call, log_error

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False


def clean_text(text: str) -> str:
    """
    清理文本，去除乱码、重复和多余字符
    
    参数:
        text: 原始文本
        
    返回:
        清理后的文本
    """
    if not text:
        return text
    
    # 去除多余的空格和换行
    text = re.sub(r'\s+', ' ', text)
    
    # 去除重复的引号和特殊字符
    text = re.sub(r'["]{2,}', '"', text)
    text = re.sub(r"[']{2,}", "'", text)
    
    # 去除连续的相同字符（3个以上）
    text = re.sub(r'(.)\1{2,}', r'\1', text)
    
    # 去除乱码和不可打印字符（保留中文、英文、数字、常见标点）
    text = re.sub(r'[^\u4e00-\u9fa5a-zA-Z0-9\s\.,!?;:''""()\[\]<>]', '', text)
    
    # 去除多余的空格
    text = ' '.join(text.split())
    
    return text.strip()


def remove_duplicate_sentences(text: str) -> str:
    """
    去除重复的句子
    
    参数:
        text: 原始文本
        
    返回:
        去除重复后的文本
    """
    sentences = re.split(r'[。！？.!?]', text)
    seen = set()
    result = []
    
    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence:
            continue
        
        # 去除句子中的空格用于比较
        normalized = sentence.replace(' ', '')
        
        if normalized not in seen:
            seen.add(normalized)
            result.append(sentence)
    
    # 重新组合文本
    return '。'.join(result) + '。' if result else text


class LLMClient:
    """大语言模型客户端"""
    
    def __init__(self, api_url: str = None, api_key: str = None, model_name: str = None):
        self._api_url = api_url
        self._api_key = api_key
        self._model_name = model_name
        self.logger = get_logger()
        # 不预先设置 is_configured，每次动态检查
    
    def _get_config(self):
        """动态获取当前配置"""
        try:
            from config import AgentConfig
            api_config = AgentConfig.get_api_config()
            return {
                "api_url": self._api_url or api_config.get("api_url"),
                "api_key": self._api_key or api_config.get("api_key"),
                "model_name": self._model_name or api_config.get("model")
            }
        except:
            return {
                "api_url": self._api_url,
                "api_key": self._api_key,
                "model_name": self._model_name or "gpt-3.5-turbo"
            }
    
    def chat(self, messages: list, **kwargs) -> Dict[str, Any]:
        """
        调用 LLM 聊天接口
        
        参数:
            messages: 消息列表，格式为 [{"role": "user", "content": "..."}]
            **kwargs: 其他参数
            
        返回:
            LLM 响应
        """
        config = self._get_config()
        api_url = config.get("api_url")
        api_key = config.get("api_key")
        model_name = config.get("model_name")
        
        self.logger.info(f"准备调用 LLM API - 模型: {model_name}, 消息数: {len(messages)}")
        
        if not api_url or not api_key:
            self.logger.warning("API 未配置，使用模拟响应")
            return self._mock_response(messages)
        
        if not HAS_REQUESTS:
            self.logger.warning("requests 库未安装，使用模拟响应")
            return self._mock_response(messages)
        
        try:
            temperature = kwargs.get("temperature", 0.7)
            max_tokens = kwargs.get("max_tokens", 1500)
            
            # 构建请求头
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}"
            }
            
            # 构建请求体
            payload = {
                "model": model_name,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens
            }
            
            self.logger.debug(f"发送请求到: {api_url}")
            
            # 发送请求 - 禁用代理
            response = requests.post(api_url, headers=headers, json=payload, timeout=45, proxies={"http": None, "https": None})
            response.raise_for_status()
            result = response.json()
            
            # 解析响应
            if "choices" in result and len(result["choices"]) > 0:
                choice = result["choices"][0]
                message = choice.get("message", {})
                content = message.get("content", "")
                
                # 清理文本
                cleaned_content = clean_text(content)
                if cleaned_content:
                    content = cleaned_content
                
                response_data = {
                    "role": message.get("role", "assistant"),
                    "content": content,
                    "tool_calls": message.get("tool_calls")
                }
                log_api_call(api_url, model_name, messages, response_data)
                return response_data
            else:
                error_msg = "API 返回格式异常"
                log_api_call(api_url, model_name, messages, None, error_msg)
                return {
                    "role": "assistant",
                    "content": "抱歉，我遇到了一些问题，请稍后再试。",
                    "tool_calls": None
                }
                
        except Exception as e:
            error_msg = str(e)
            log_error("API 调用错误", error_msg, e)
            return {
                "role": "assistant",
                "content": f"抱歉，我连接 API 时遇到了问题: {error_msg}",
                "tool_calls": None
            }
    
    def _mock_response(self, messages: list) -> Dict[str, Any]:
        """模拟 LLM 响应（用于开发测试）"""
        last_user_msg = next((m for m in reversed(messages) if m["role"] == "user"), None)
        user_content = last_user_msg["content"] if last_user_msg else "你好"
        
        return {
            "role": "assistant",
            "content": f"这是对 '{user_content}' 的模拟回复。您的 API 已配置，正在尝试连接...",
            "tool_calls": None
        }
    
    def generate_tool_calls(self, user_input: str, tools_desc: str, history: str = "") -> Optional[Dict[str, Any]]:
        """
        让 LLM 决定是否需要调用工具
        
        参数:
            user_input: 用户输入
            tools_desc: 工具描述
            history: 对话历史
            
        返回:
            工具调用信息，或 None
        """
        config = self._get_config()
        if not config.get("api_url") or not config.get("api_key"):
            return None
        
        # 暂时返回 None，使用规则驱动的工具选择
        return None


# 单例模式
_llm_client: Optional[LLMClient] = None


def get_llm_client() -> LLMClient:
    """获取 LLM 客户端实例"""
    global _llm_client
    # 每次都重新创建客户端，以确保使用最新配置
    try:
        from config import AgentConfig
        api_config = AgentConfig.get_api_config()
        _llm_client = LLMClient(
            api_config.get("api_url"),
            api_config.get("api_key"),
            api_config.get("model")
        )
    except:
        _llm_client = LLMClient()
    return _llm_client


def reset_llm_client():
    """重置 LLM 客户端单例"""
    global _llm_client
    _llm_client = None


def configure_llm(api_url: str, api_key: str, model_name: str = None):
    """配置 LLM 客户端"""
    global _llm_client
    _llm_client = LLMClient(api_url, api_key, model_name)
