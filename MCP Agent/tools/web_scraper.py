"""
网页访问/抓取工具
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mcp_framework import tool
from typing import Dict, Any
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin


def is_valid_url(url: str) -> bool:
    """验证URL是否有效"""
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except:
        return False


@tool("fetch_webpage")
def fetch_webpage(params: Dict[str, Any]) -> Dict[str, Any]:
    """
    访问/抓取网页内容
    
    参数:
        url: 网页地址
        max_length: 返回内容的最大长度 (默认 2000)
    
    返回:
        网页内容摘要
    """
    url = params.get("url", "")
    max_length = params.get("max_length", 2000)
    
    if not url:
        return {"error": "请提供网页地址"}
    
    if not is_valid_url(url):
        return {"error": "无效的URL格式，请确保包含 http:// 或 https://"}
    
    try:
        # 设置请求头，模拟浏览器
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        
        response = requests.get(url, headers=headers, timeout=15, proxies={"http": None, "https": None})
        response.raise_for_status()
        
        # 解析HTML
        soup = BeautifulSoup(response.content, 'lxml')
        
        # 获取页面标题
        title = soup.title.string.strip() if soup.title else "无标题"
        
        # 移除脚本和样式元素
        for script in soup(["script", "style"]):
            script.decompose()
        
        # 获取文本内容
        text = soup.get_text()
        
        # 清理文本
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = '\n'.join(chunk for chunk in chunks if chunk)
        
        # 截取内容
        if len(text) > max_length:
            text = text[:max_length] + "...\n\n[内容已截断]"
        
        # 获取主要链接
        links = []
        for a in soup.find_all('a', href=True)[:10]:
            href = a['href']
            if href and not href.startswith('#'):
                full_url = urljoin(url, href)
                link_text = a.get_text(strip=True)
                if link_text:
                    links.append({
                        "text": link_text[:50],
                        "url": full_url
                    })
        
        return {
            "success": True,
            "url": url,
            "title": title,
            "content": text,
            "links": links,
            "content_length": len(text),
            "status_code": response.status_code
        }
        
    except requests.RequestException as e:
        return {
            "error": f"网页访问失败: {str(e)}",
            "url": url
        }
    except Exception as e:
        return {
            "error": f"处理网页时出错: {str(e)}",
            "url": url
        }


if __name__ == "__main__":
    from mcp_framework import serve
    serve()
