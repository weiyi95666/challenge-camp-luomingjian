import json
import os
import sys
import subprocess
from typing import Dict, Any, Optional

ROOT = os.path.dirname(os.path.abspath(__file__))
CONFIG = os.path.join(ROOT, 'servers_config.json')


def load_config() -> Dict[str, Any]:
    with open(CONFIG, 'r', encoding='utf-8') as f:
        return json.load(f)


def run_tool(script: str, tool_name: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    path = os.path.join(ROOT, script)
    proc = subprocess.run(
        [sys.executable, path, '--tool', tool_name],
        input=json.dumps(payload, ensure_ascii=False),
        text=True,
        capture_output=True
    )
    out = proc.stdout
    if not out:
        return {'error': proc.stderr}
    try:
        return json.loads(out)
    except Exception:
        return {'raw': out}


def process_input(text: str, config: Dict[str, Any]) -> Dict[str, Any]:
    text = text.strip()
    if '天气' in text:
        parts = text.split()
        city = parts[1] if len(parts) > 1 else '北京'
        srv = next(s for s in config['servers'] if s['name'] == 'weather')
        return run_tool(srv['script'], srv['tool'], {'location': city})
    if '写' in text or '保存' in text:
        parts = text.split(maxsplit=2)
        if len(parts) < 3:
            return {'error': '写命令格式：写 <path> <content>'}
        path = parts[1]
        content = parts[2]
        srv = next(s for s in config['servers'] if s['name'] == 'writer')
        return run_tool(srv['script'], srv['tool'], {'path': path, 'content': content})
    srv = next(s for s in config['servers'] if s['name'] == 'rag')
    return run_tool(srv['script'], srv['tool'], {'question': text})
