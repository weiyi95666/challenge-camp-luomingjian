"""
日志模块 - 为智能体提供全面的日志记录功能
"""
import logging
import os
from datetime import datetime
from typing import Any, Dict, Optional


def setup_logger(name: str = "mcp_agent", log_level: int = logging.INFO) -> logging.Logger:
    """
    设置并配置日志记录器
    
    参数:
        name: 日志记录器名称
        log_level: 日志级别
        
    返回:
        配置好的日志记录器
    """
    logger = logging.getLogger(name)
    
    # 如果已经配置过，直接返回
    if logger.handlers:
        return logger
    
    logger.setLevel(log_level)
    
    # 日志格式
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # 控制台日志
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # 文件日志 - 确保日志目录存在
    log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'logs')
    os.makedirs(log_dir, exist_ok=True)
    
    # 按日期命名的日志文件
    log_filename = os.path.join(log_dir, f'mcp_agent_{datetime.now().strftime("%Y%m%d")}.log')
    file_handler = logging.FileHandler(log_filename, encoding='utf-8')
    file_handler.setLevel(log_level)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    return logger


# 全局日志记录器
_logger: Optional[logging.Logger] = None


def get_logger() -> logging.Logger:
    """获取全局日志记录器"""
    global _logger
    if _logger is None:
        _logger = setup_logger()
    return _logger


def log_api_call(api_url: str, model: str, messages: list, response: Any, error: Optional[str] = None):
    """记录 API 调用日志"""
    logger = get_logger()
    log_data = {
        "timestamp": datetime.now().isoformat(),
        "type": "api_call",
        "api_url": api_url,
        "model": model,
        "messages_count": len(messages),
        "success": error is None
    }
    if error:
        log_data["error"] = error
        logger.error(f"API 调用失败: {error}")
    else:
        log_data["response_length"] = len(str(response))
        logger.info(f"API 调用成功: {api_url} (模型: {model})")


def log_tool_use(tool_name: str, params: Dict[str, Any], result: Any, error: Optional[str] = None):
    """记录工具使用日志"""
    logger = get_logger()
    if error:
        logger.error(f"工具调用失败 - {tool_name}: {error}")
    else:
        logger.info(f"工具调用成功 - {tool_name}")


def log_user_message(user_input: str, message_id: Optional[str] = None):
    """记录用户消息"""
    logger = get_logger()
    logger.info(f"收到用户消息: {user_input[:100]}{'...' if len(user_input) > 100 else ''}")


def log_agent_response(response: str, tool_used: Optional[str] = None):
    """记录智能体回复"""
    logger = get_logger()
    if tool_used:
        logger.info(f"智能体回复 (使用工具: {tool_used}): {response[:100]}{'...' if len(response) > 100 else ''}")
    else:
        logger.info(f"智能体回复: {response[:100]}{'...' if len(response) > 100 else ''}")


def log_error(error_type: str, error_message: str, exception: Optional[Exception] = None):
    """记录错误日志"""
    logger = get_logger()
    if exception:
        logger.error(f"{error_type}: {error_message}", exc_info=exception)
    else:
        logger.error(f"{error_type}: {error_message}")


def log_system_event(event_type: str, details: Optional[Dict[str, Any]] = None):
    """记录系统事件"""
    logger = get_logger()
    if details:
        logger.info(f"系统事件: {event_type} - {details}")
    else:
        logger.info(f"系统事件: {event_type}")
