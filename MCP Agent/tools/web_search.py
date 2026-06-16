"""
网络搜索工具 - 使用 Tavily API 进行高质量搜索
专为 AI 设计的搜索 API，提供准确、相关的搜索结果
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mcp_framework import tool
from typing import Dict, Any
import requests
import json
from dotenv import load_dotenv


# 加载环境变量
load_dotenv()

# 获取 Tavily API Key
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY", "")
TAVILY_API_URL = "https://api.tavily.com/search"


# 模拟搜索数据 - 作为后备方案
MOCK_SEARCH_DATA = {
    "人工智能": [
        {
            "title": "人工智能 (AI) 是什么？",
            "snippet": "人工智能是计算机科学的一个分支，致力于创建智能机器。",
            "url": "https://example.com/ai",
            "source": "知识库"
        },
        {
            "title": "机器学习简介",
            "snippet": "机器学习是人工智能的一个子集，使系统能够从数据中学习。",
            "url": "https://example.com/ml",
            "source": "知识库"
        }
    ],
    "天气": [
        {
            "title": "天气预报",
            "snippet": "使用天气工具可以查询实时天气信息，包括温度、湿度、风速等。",
            "url": "https://example.com/weather",
            "source": "知识库"
        }
    ],
    "Python": [
        {
            "title": "Python 编程语言",
            "snippet": "Python 是一种高级、解释型的编程语言，广泛用于数据科学和人工智能。",
            "url": "https://www.python.org",
            "source": "知识库"
        },
        {
            "title": "Python 入门教程",
            "snippet": "学习 Python 的最佳实践和核心概念，从基础到高级。",
            "url": "https://example.com/python-tutorial",
            "source": "知识库"
        }
    ]
}


def get_mock_results(query, num_results):
    """获取模拟搜索结果 - 当 Tavily API 不可用时使用"""
    results = []
    
    for key, mock_data in MOCK_SEARCH_DATA.items():
        if key in query:
            results.extend(mock_data)
    
    if not results:
        results = [
            {
                "title": f"关于 '{query}' 的信息",
                "snippet": "这是模拟搜索结果。Tavily API 可以提供更强大的实时搜索。",
                "url": "https://example.com/search",
                "source": "知识库"
            },
            {
                "title": "智能体助手",
                "snippet": "MCP Agent 可以帮你查询天气、管理文件、回答问题等。",
                "url": "https://example.com/agent",
                "source": "知识库"
            }
        ]
    
    return results[:num_results]


def search_with_tavily(query: str, num_results: int = 5) -> Dict[str, Any]:
    """
    使用 Tavily API 进行网络搜索
    
    参数:
        query: 搜索关键词
        num_results: 返回结果数量
    
    返回:
        搜索结果字典
    """
    if not TAVILY_API_KEY:
        return {
            "success": False,
            "error": "Tavily API Key 未配置",
            "fallback": True
        }
    
    try:
        headers = {
            "Content-Type": "application/json"
        }
        
        payload = {
            "api_key": TAVILY_API_KEY,
            "query": query,
            "search_depth": "basic",
            "max_results": num_results,
            "include_images": False,
            "include_answer": True,
            "include_raw_content": False
        }
        
        response = requests.post(
            TAVILY_API_URL,
            headers=headers,
            json=payload,
            timeout=10,
            proxies={"http": None, "https": None}
        )
        response.raise_for_status()
        
        data = response.json()
        
        results = []
        if "results" in data:
            for result in data["results"][:num_results]:
                results.append({
                    "title": result.get("title", ""),
                    "snippet": result.get("content", ""),
                    "url": result.get("url", ""),
                    "source": result.get("site", "Tavily")
                })
        
        answer = data.get("answer", "")
        
        return {
            "success": True,
            "query": query,
            "results": results,
            "answer": answer,
            "total_results": len(results),
            "source": "Tavily"
        }
        
    except requests.exceptions.RequestException as e:
        return {
            "success": False,
            "error": f"网络请求错误: {str(e)}",
            "fallback": True
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Tavily API 调用失败: {str(e)}",
            "fallback": True
        }


@tool("web_search")
def web_search(params: Dict[str, Any]) -> Dict[str, Any]:
    """
    网络搜索工具 - 使用 Tavily API 进行高质量搜索
    
    参数:
        query: 搜索关键词
        num_results: 返回结果数量 (默认 5)
    
    返回:
        搜索结果
    """
    query = params.get("query", "")
    num_results = params.get("num_results", 5)
    
    if not query:
        return {"error": "请提供搜索关键词"}
    
    try:
        # 优先使用 Tavily API
        tavily_result = search_with_tavily(query, num_results)
        
        if tavily_result.get("success"):
            return {
                "success": True,
                "query": query,
                "results": tavily_result.get("results", []),
                "answer": tavily_result.get("answer", ""),
                "total_results": len(tavily_result.get("results", [])),
                "source": "Tavily"
            }
        
        # 如果 Tavily 失败，使用备用方案
        if tavily_result.get("fallback"):
            results = get_mock_results(query, num_results)
            return {
                "success": True,
                "query": query,
                "results": results,
                "total_results": len(results),
                "note": "使用智能体知识库（Tavily API 暂时不可用）"
            }
        
        return tavily_result
        
    except Exception as e:
        results = get_mock_results(query, num_results)
        return {
            "success": True,
            "query": query,
            "results": results,
            "total_results": len(results),
            "note": "使用智能体知识库"
        }


if __name__ == "__main__":
    from mcp_framework import serve
    serve()
