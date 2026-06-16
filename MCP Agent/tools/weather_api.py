"""
真实天气查询工具 - 使用 Open-Meteo 免费 API
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mcp_framework import tool
from typing import Dict, Any
import requests


# 城市坐标映射（简化版）
CITY_COORDINATES = {
    "北京": (39.9042, 116.4074),
    "上海": (31.2304, 121.4737),
    "广州": (23.1291, 113.2644),
    "深圳": (22.5431, 114.0579),
    "杭州": (30.2741, 120.1551),
    "成都": (30.5728, 104.0668),
    "武汉": (30.5928, 114.3055),
    "西安": (34.3416, 108.9398),
    "重庆": (29.4316, 106.9123),
    "南京": (32.0603, 118.7969),
    "天津": (39.0842, 117.2008),
    "苏州": (31.2989, 120.5853),
    "长沙": (28.2282, 112.9388),
    "沈阳": (41.8045, 123.4315),
    "青岛": (36.0671, 120.3826),
}


def get_coordinates(city_name: str) -> tuple:
    """获取城市坐标"""
    city_name = city_name.strip()
    
    # 直接匹配
    if city_name in CITY_COORDINATES:
        return CITY_COORDINATES[city_name]
    
    # 部分匹配
    for city, coords in CITY_COORDINATES.items():
        if city_name in city or city in city_name:
            return coords
    
    # 默认返回北京
    return CITY_COORDINATES["北京"]


def weather_code_to_text(code: int) -> str:
    """天气代码转文字"""
    weather_codes = {
        0: "晴朗",
        1: "大部晴朗", 2: "局部多云", 3: "多云",
        45: "雾", 48: "雾凇",
        51: "小毛毛雨", 53: "毛毛雨", 55: "大毛毛雨",
        56: "冻毛毛雨", 57: "大冻毛毛雨",
        61: "小雨", 63: "中雨", 65: "大雨",
        66: "冻雨", 67: "大冻雨",
        71: "小雪", 73: "中雪", 75: "大雪",
        77: "雪粒",
        80: "小阵雨", 81: "阵雨", 82: "大阵雨",
        85: "小阵雪", 86: "大阵雪",
        95: "雷暴",
        96: "雷暴伴小冰雹", 99: "雷暴伴大冰雹"
    }
    return weather_codes.get(code, "未知天气")


@tool("get_weather_real")
def get_weather_real(params: Dict[str, Any]) -> Dict[str, Any]:
    """
    真实天气查询工具 - 使用 Open-Meteo API
    
    参数:
        location: 城市名称
        
    返回:
        真实天气信息
    """
    location = params.get("location", "北京")
    
    try:
        # 获取城市坐标
        lat, lon = get_coordinates(location)
        
        # 调用 Open-Meteo API
        url = "https://api.open-meteo.com/v1/forecast"
        params_api = {
            "latitude": lat,
            "longitude": lon,
            "current": ["temperature_2m", "relative_humidity_2m", "weather_code", "wind_speed_10m"],
            "timezone": "Asia/Shanghai",
            "forecast_days": 1
        }
        
        response = requests.get(url, params=params_api, timeout=10, proxies={"http": None, "https": None})
        response.raise_for_status()
        data = response.json()
        
        # 解析天气数据
        current = data.get("current", {})
        
        temperature = current.get("temperature_2m", "N/A")
        humidity = current.get("relative_humidity_2m", "N/A")
        weather_code = current.get("weather_code", 0)
        wind_speed = current.get("wind_speed_10m", "N/A")
        
        weather_desc = weather_code_to_text(weather_code)
        
        # 获取温度单位
        temp_unit = data.get("current_units", {}).get("temperature_2m", "°C")
        wind_unit = data.get("current_units", {}).get("wind_speed_10m", "km/h")
        
        return {
            "success": True,
            "location": location,
            "coordinates": {"latitude": lat, "longitude": lon},
            "weather": weather_desc,
            "temperature": f"{temperature}{temp_unit}",
            "humidity": f"{humidity}%",
            "wind_speed": f"{wind_speed}{wind_unit}",
            "data_source": "Open-Meteo"
        }
        
    except requests.RequestException as e:
        return {
            "error": f"天气查询失败: {str(e)}",
            "location": location,
            "fallback": {
                "weather": "晴",
                "temperature": "25°C",
                "note": "使用模拟数据（网络请求失败）"
            }
        }
    except Exception as e:
        return {
            "error": f"发生错误: {str(e)}"
        }


if __name__ == "__main__":
    from mcp_framework import serve
    serve()
