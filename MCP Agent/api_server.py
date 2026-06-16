from flask import Flask, request, jsonify, send_from_directory
import sys
import os
from datetime import datetime
from agent.core import get_agent
from config import AgentConfig
from logger import get_logger, log_system_event, log_error

app = Flask(__name__, static_folder='static', static_url_path='')
logger = get_logger()
log_system_event("初始化 API 服务器")
agent = get_agent()

# 输出目录
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'outputs')

# 联网模式配置
online_mode = {
    "enabled": True,
    "description": "启用联网功能，包括天气查询、网络搜索、网页访问等"
}

# 响应模式配置
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
            "name": "深度思考",
            "description": "深度思考，使用更多的推理步骤，提供更周全的回答",
            "max_tokens": 2000,
            "temperature": 0.7
        }
    }
}


@app.route('/chat', methods=['POST'])
def chat():
    """聊天接口 - 使用智能体处理"""
    try:
        data = request.get_json(force=True)
        text = data.get('text', '')
        response_mode = data.get('response_mode', 'fast')
        
        logger.info(f"收到聊天请求: {text[:50]}..., 响应模式: {response_mode}")
        
        # 更新响应模式配置
        if response_mode in response_mode_config["modes"]:
            response_mode_config["current"] = response_mode
        
        # 同步 API 服务器和智能体的联网模式
        agent.set_online_mode(online_mode["enabled"])
        
        # 检测时间查询
        text_lower = text.lower()
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
            logger.info(f"时间查询请求，返回: {time_str}")
            return jsonify({
                "response": f"现在的时间是：{time_str}",
                "tool_used": None,
                "tool_result": None,
                "thinking_process": None
            })
        
        # 检测联网模式禁用时的联网请求
        if not online_mode["enabled"]:
            online_keywords = ["天气", "搜索", "查找", "访问", "打开网页", "weather", "search"]
            if any(kw in text_lower for kw in online_keywords):
                return jsonify({
                    "response": "联网功能已禁用，请先在界面右上角启用联网模式后再试。",
                    "tool_used": None,
                    "tool_result": None,
                    "thinking_process": None
                })
        
        # 生成思考过程（深度思考模式）
        thinking_process = None
        if response_mode == "deep":
            thinking_process = generate_thinking_process(text)
        
        result = agent.process_message(text)
        return jsonify({
            "response": result["response"],
            "tool_used": result["tool_used"],
            "tool_result": result["tool_result"],
            "thinking_process": thinking_process
        })
    except Exception as e:
        log_error("API 请求错误", f"处理聊天请求时出错", e)
        return jsonify({
            "response": "抱歉，处理您的请求时发生了错误。",
            "tool_used": None,
            "tool_result": None,
            "thinking_process": None
        }), 500


def generate_thinking_process(query):
    """生成深度思考过程"""
    import time
    import random
    
    # 模拟思考步骤
    steps = [
        f"🤔 正在理解您的问题: \"{query}\"",
        "📚 检索相关知识和上下文",
        "🔍 分析问题的多个角度",
        "💡 生成初步的解决方案",
        "⚖️ 评估不同方案的优劣",
        "🎯 筛选最佳答案并组织语言"
    ]
    
    # 添加一些随机的思考细节
    details = [
        "考虑不同的可能性...",
        "检查逻辑一致性...",
        "确保信息准确性...",
        "优化表达方式..."
    ]
    
    # 构建思考过程
    thinking = []
    for i, step in enumerate(steps):
        thinking.append(step)
        if random.random() > 0.5 and i < len(steps) - 1:
            thinking.append(f"   ⏳ {random.choice(details)}")
        time.sleep(0.1)  # 模拟思考时间
    
    return thinking


@app.route('/history', methods=['GET'])
def get_history():
    """获取对话历史"""
    history = agent.get_conversation_history()
    return jsonify({"history": history})


@app.route('/clear', methods=['POST'])
def clear_memory():
    """清空对话记忆"""
    agent.clear_memory()
    return jsonify({"success": True})


@app.route('/api/online-mode', methods=['GET'])
def get_online_mode():
    """获取当前联网模式状态"""
    return jsonify(online_mode)


@app.route('/api/online-mode', methods=['POST'])
def set_online_mode():
    """设置联网模式"""
    data = request.get_json()
    enabled = data.get('enabled', True)
    online_mode["enabled"] = enabled
    agent.set_online_mode(enabled)
    logger.info(f"联网模式已切换: {'启用' if enabled else '禁用'}")
    return jsonify(online_mode)


@app.route('/api/models', methods=['GET'])
def get_models():
    """获取所有可用的模型"""
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


@app.route('/api/models/select', methods=['POST'])
def select_model():
    """选择使用的模型"""
    data = request.get_json()
    provider_name = data.get('provider')
    model_id = data.get('model')
    
    if not provider_name or not model_id:
        return jsonify({"success": False, "error": "请提供 provider 和 model"}), 400
    
    AgentConfig.set_current_model(provider_name, model_id)
    
    # 重置智能体中的 LLM 客户端
    try:
        from agent.core import get_agent
        agent_instance = get_agent()
        # 更新智能体中的 LLM 客户端（如果有引用）
        if hasattr(agent_instance, 'llm'):
            from agent.llm_client import reset_llm_client
            reset_llm_client()
            # 重新获取
            from agent.llm_client import get_llm_client
            agent_instance.llm = get_llm_client()
    except Exception as e:
        logger.warning(f"重置 LLM 客户端时出错: {e}")
    
    logger.info(f"模型已切换为: {provider_name}/{model_id}")
    
    return jsonify({
        "success": True,
        "current": {
            "provider": provider_name,
            "model": model_id
        }
    })


@app.route('/api/response-mode', methods=['GET'])
def get_response_mode():
    """获取当前响应模式"""
    return jsonify(response_mode_config)


@app.route('/api/response-mode', methods=['POST'])
def set_response_mode():
    """设置响应模式"""
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


@app.route('/api/models/current', methods=['GET'])
def get_current_model():
    """获取当前使用的模型"""
    current_provider = AgentConfig.get_current_provider()
    current_model = AgentConfig.get_current_model()
    
    provider_config = AgentConfig.get_provider_config(current_provider)
    display_name = None
    if provider_config:
        for model in provider_config.get('models', []):
            if model.get('id') == current_model:
                display_name = model.get('display_name')
                break
    
    return jsonify({
        "provider": current_provider,
        "model": current_model,
        "display_name": display_name or current_model
    })


@app.route('/')
def index():
    """首页 - Web 聊天界面"""
    return send_from_directory('static', 'index.html')

@app.route('/api/files', methods=['GET'])
def list_files():
    """列出所有输出文件"""
    try:
        if not os.path.exists(OUTPUT_DIR):
            return jsonify({"files": []})
        
        files = []
        for filename in os.listdir(OUTPUT_DIR):
            filepath = os.path.join(OUTPUT_DIR, filename)
            if os.path.isfile(filepath):
                stat = os.stat(filepath)
                files.append({
                    "name": filename,
                    "size": stat.st_size,
                    "created": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                    "modified": datetime.fromtimestamp(stat.st_mtime).isoformat()
                })
        
        # 按修改时间倒序排列
        files.sort(key=lambda x: x["modified"], reverse=True)
        return jsonify({"files": files})
    except Exception as e:
        log_error("文件列表错误", "获取文件列表失败", e)
        return jsonify({"error": str(e)}), 500

@app.route('/api/files/<filename>', methods=['GET'])
def download_file(filename):
    """下载文件"""
    try:
        return send_from_directory(OUTPUT_DIR, filename, as_attachment=True)
    except Exception as e:
        log_error("文件下载错误", f"下载文件 {filename} 失败", e)
        return jsonify({"error": "文件不存在"}), 404

@app.route('/api/files/preview/<filename>', methods=['GET'])
def preview_file(filename):
    """预览文件内容（仅文本文件）"""
    try:
        filepath = os.path.join(OUTPUT_DIR, filename)
        if not os.path.exists(filepath):
            return jsonify({"error": "文件不存在"}), 404
        
        # 检查文件类型
        text_extensions = ['.txt', '.md', '.json', '.csv', '.py', '.js', '.html', '.css']
        ext = os.path.splitext(filename)[1].lower()
        
        if ext in text_extensions:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            return jsonify({
                "name": filename,
                "content": content,
                "type": "text"
            })
        elif ext == '.docx':
            # 尝试读取Word文档内容
            try:
                from docx import Document
                doc = Document(filepath)
                content = '\n'.join([para.text for para in doc.paragraphs])
                return jsonify({
                    "name": filename,
                    "content": content,
                    "type": "docx"
                })
            except Exception as e:
                logger.warning(f"无法读取Word文档内容: {e}")
                return jsonify({
                    "name": filename,
                    "content": "Word文档预览不可用，请下载查看",
                    "type": "docx"
                })
        else:
            return jsonify({
                "name": filename,
                "content": "该文件类型不支持预览，请下载查看",
                "type": "binary"
            })
    except Exception as e:
        log_error("文件预览错误", f"预览文件 {filename} 失败", e)
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    log_system_event("启动 Web 服务器")
    print("[OK] MCP Agent Web 界面启动!")
    print("[OK] 访问地址: http://127.0.0.1:5001")
    print("="*50)
    app.run(host='127.0.0.1', port=5001, debug=False)
