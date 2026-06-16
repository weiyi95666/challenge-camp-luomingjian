from mcp_framework import tool
from typing import Dict, Any


@tool('get_weather')
def get_weather(params: Dict[str, Any]) -> Dict[str, str]:
    """返回模拟天气信息。params: {location: str}"""
    location = params.get('location', '北京')
    return {
        'location': location,
        'weather': '晴',
        'temperature': '25°C',
    }


if __name__ == '__main__':
    from mcp_framework import serve
    serve()
