"""
带三层记忆系统的 API 服务器
不修改核心文件，独立运行
"""
from flask import Flask, request, jsonify, send_from_directory
import sys
import os
from datetime import datetime
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 导入带记忆的智能体
from agent_with_memory import ChatAgentWithMemory
from logger import get_logger, log_system_event, log_error

app = Flask(__name__, static_folder='static', static_url_path='')
logger = get_logger()
log_system_event("初始化带记忆系统的 API 服务器")

# 初始化带记忆的智能体
agent_with_memory = ChatAgentWithMemory()

# 联网模式配置（保持原有接口兼容）
online_mode = {
    "enabled": True,
    "description": "启用联网功能，包括天气查询、网络搜索、网页访问等"
}

# 响应模式配置（保持原有接口兼容）
response_mode_config = {
    "current": "fast",  # 'fast' 或 'deep'
    "modes": {
        "fast": {
            "name": "快速响应",
            "description": "快速回答，使用较少的搜索资源",
            "max_tokens": 1000,
            "temperature": 0.6
        },
        "deep": {
            "name": "深度搜索",
            "description": "深入搜索，使用更多的网络资源",
            "max_tokens": 2000,
            "temperature": 0.7
        }
    }
}


@app.route('/chat', methods=['POST'])
def chat():
    """聊天接口 - 使用带记忆的智能体处理"""
    try:
        data = request.get_json(force=True)
        text = data.get('text', '')
        response_mode = data.get('response_mode', 'fast')
        
        logger.info(f"收到聊天请求: {text[:50]}..., 响应模式: {response_mode}")
        
        # 更新响应模式配置
        if response_mode in response_mode_config["modes"]:
            response_mode_config["current"] = response_mode
        
        # 检测时间查询（保持原有功能）
        text_lower = text.lower()
        time_keywords = ["现在时间", "几点了", "现在几点", "当前时间", "what time", "current time"]
        if any(kw in text_lower for kw in time_keywords):
            now = datetime.now()
            year = now.year
            month = now.month
            day = now.day
            hour = now.hour
            minute = now.minute
            second = now.second
            time_str = f"{year}年{month}月{day}日 {hour:02d}:{minute:02d}:{second:02d}"
            logger.info(f"时间查询请求，返回: {time_str}")
            return jsonify({
                "response": f"现在的时间是：{time_str}",
                "tool_used": None,
                "tool_result": None
            })
        
        # 使用带记忆的智能体处理
        result = agent_with_memory.process_message(text)
        
        return jsonify({
            "response": result["response"],
            "tool_used": None,
            "tool_result": None,
            "memory_info": result.get("memory_used", {})
        })
    except Exception as e:
        log_error("API 请求错误", f"处理聊天请求时出错", e)
        return jsonify({
            "response": "抱歉，处理您的请求时发生了错误。",
            "tool_used": None,
            "tool_result": None
        }), 500


@app.route('/api/memory/status', methods=['GET'])
def get_memory_status():
    """获取记忆系统状态"""
    status = agent_with_memory.get_memory_status()
    return jsonify(status)


@app.route('/api/memory/clear-short-term', methods=['POST'])
def clear_short_term_memory():
    """清空短期记忆（开始新会话）"""
    agent_with_memory.clear_short_term_memory()
    return jsonify({"success": True, "message": "短期记忆已清空"})


@app.route('/api/memory/long-term', methods=['GET'])
def get_long_term_memories():
    """获取所有长期记忆"""
    memories = agent_with_memory.long_term.get_all_memories()
    return jsonify({"memories": memories})


@app.route('/api/memory/add-long-term', methods=['POST'])
def add_long_term_memory():
    """手动添加长期记忆"""
    data = request.get_json()
    content = data.get('content', '')
    metadata = data.get('metadata', {})
    
    if not content:
        return jsonify({"success": False, "error": "请提供内容"}), 400
    
    memory_id = agent_with_memory.long_term.add_memory(content, metadata)
    return jsonify({"success": True, "memory_id": memory_id})


@app.route('/api/memory/preferences', methods=['GET'])
def get_preferences():
    """获取用户偏好"""
    preferences = agent_with_memory.mid_term.get_all_preferences()
    return jsonify({"preferences": preferences})


@app.route('/api/memory/preferences', methods=['POST'])
def set_preference():
    """设置用户偏好"""
    data = request.get_json()
    key = data.get('key', '')
    value = data.get('value', '')
    
    if not key or not value:
        return jsonify({"success": False, "error": "请提供 key 和 value"}), 400
    
    agent_with_memory.mid_term.set_preference(key, value)
    return jsonify({"success": True})


@app.route('/api/memory/facts', methods=['GET'])
def get_user_facts():
    """获取用户事实"""
    category = request.args.get('category')
    facts = agent_with_memory.mid_term.get_user_facts(category)
    return jsonify({"facts": facts})


# ========== 保持原有 API 接口兼容 ==========
@app.route('/api/online-mode', methods=['GET'])
def get_online_mode():
    """获取当前联网模式状态（兼容接口）"""
    return jsonify(online_mode)


@app.route('/api/online-mode', methods=['POST'])
def set_online_mode():
    """设置联网模式（兼容接口）"""
    data = request.get_json()
    enabled = data.get('enabled', True)
    online_mode["enabled"] = enabled
    logger.info(f"联网模式已切换: {'启用' if enabled else '禁用'}")
    return jsonify(online_mode)


@app.route('/api/response-mode', methods=['GET'])
def get_response_mode():
    """获取当前响应模式（兼容接口）"""
    return jsonify(response_mode_config)


@app.route('/api/response-mode', methods=['POST'])
def set_response_mode():
    """设置响应模式（兼容接口）"""
    data = request.get_json()
    mode = data.get('mode', 'fast')
    
    if mode in response_mode_config["modes"]:
        response_mode_config["current"] = mode
        logger.info(f"响应模式已切换为: {mode}")
        return jsonify(response_mode_config)
    else:
        return jsonify({
            "success": False,
            "error": "无效的响应模式"
        }), 400


@app.route('/api/models', methods=['GET'])
def get_models():
    """获取模型列表（兼容接口）"""
    try:
        from config import AgentConfig
        providers = AgentConfig.get_available_providers()
        current_provider = AgentConfig.get_current_provider()
        current_model = AgentConfig.get_current_model()
        
        return jsonify({
            "providers": providers,
            "current": {
                "provider": current_provider,
                "model": current_model
            }
        })
    except:
        return jsonify({
            "providers": [],
            "current": {"provider": "None", "model": "None"}
        })


@app.route('/')
def index():
    """首页 - Web 聊天界面"""
    return send_from_directory('static', 'index.html')


if __name__ == '__main__':
    log_system_event("启动带记忆系统的 Web 服务器")
    print("=" * 60)
    print("[OK] MCP Agent + 三层记忆系统 Web 界面启动!")
    print("[OK] 访问地址: http://127.0.0.1:5002")
    print("[OK] 记忆系统状态: /api/memory/status")
    print("=" * 60)
    # 使用端口 5002 避免与原有服务器冲突
    app.run(host='127.0.0.1', port=5002, debug=False)
