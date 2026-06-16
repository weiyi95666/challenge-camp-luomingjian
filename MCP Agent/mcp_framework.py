import sys
import json
import argparse
from functools import wraps
from typing import Dict, Any, Callable, Optional

_TOOLS: Dict[str, Callable[[Dict[str, Any]], Any]] = {}


def tool(name: Optional[str] = None) -> Callable[[Callable], Callable]:
    def decorator(fn: Callable) -> Callable:
        key = name or fn.__name__
        _TOOLS[key] = fn

        @wraps(fn)
        def wrapper(params: Dict[str, Any]) -> Any:
            return fn(params)

        return wrapper
    return decorator


def serve() -> None:
    """简单的 stdio MCP 风格服务：通过命令行参数 --tool <name> 调用注册的工具。
    从 stdin 读取 JSON 参数，向 stdout 输出 JSON 结果。
    """
    parser = argparse.ArgumentParser()
    parser.add_argument('--tool', required=True, help='tool name to run')
    args = parser.parse_args()
    tool_name = args.tool

    if tool_name not in _TOOLS:
        print(json.dumps({'error': f"tool '{tool_name}' not found"}))
        sys.exit(1)

    raw = sys.stdin.read()
    try:
        params = json.loads(raw) if raw.strip() else {}
    except Exception:
        params = {}

    try:
        result = _TOOLS[tool_name](params)
        print(json.dumps({'result': result}, ensure_ascii=False))
    except Exception as e:
        print(json.dumps({'error': str(e)}))


def get_tools() -> Dict[str, Callable[[Dict[str, Any]], Any]]:
    """获取所有已注册的工具"""
    return _TOOLS.copy()


if __name__ == '__main__':
    serve()
