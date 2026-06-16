from mcp_framework import tool
import os
from typing import Dict, Any

ROOT = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(ROOT, 'outputs')


@tool('write_file')
def write_file(params: Dict[str, Any]) -> Dict[str, Any]:
    """写文件工具。params: {path: str, content: str}"""
    path = params.get('path')
    content = params.get('content', '')
    if not path:
        return {'error': 'missing path'}
    
    base_name = os.path.basename(path)
    safe_path = os.path.normpath(os.path.join(OUTPUT_DIR, base_name))
    os.makedirs(os.path.dirname(safe_path), exist_ok=True)
    
    with open(safe_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    return {'ok': True, 'path': safe_path}


if __name__ == '__main__':
    from mcp_framework import serve
    serve()
