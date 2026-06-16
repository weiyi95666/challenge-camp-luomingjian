"""智能体 CLI 客户端 - 使用 MCP Agent 处理用户输入"""
import json
import sys
from typing import Dict, Any
from agent.core import get_agent


def process_with_agent(text: str) -> Dict[str, Any]:
    """使用智能体处理用户输入"""
    agent = get_agent()
    result = agent.process_message(text)
    return result

def main():
    if len(sys.argv) > 1:
        text = ' '.join(sys.argv[1:])
        res = process_with_agent(text)
        print(f"\n🤖 助手: {res['response']}\n")
        if res.get('tool_used'):
            print(f"   使用工具: {res['tool_used']}")
        return
    
    print('🤖 MCP Agent 智能体已启动！')
    print('输入您的问题，或输入 /clear 清空对话，Ctrl-C 退出。\n')
    
    agent = get_agent()
    
    try:
        while True:
            text = input('👤 您: ')
            
            if text.strip() == '/clear':
                agent.clear_memory()
                print('🧹 对话记忆已清空\n')
                continue
            
            if not text.strip():
                continue
            
            res = process_with_agent(text)
            print(f"\n🤖 助手: {res['response']}\n")
            
            if res.get('tool_used'):
                print(f"   🔧 使用工具: {res['tool_used']}")
                if res.get('tool_result'):
                    print(f"   📊 工具结果: {json.dumps(res['tool_result'], ensure_ascii=False)}\n")
            
    except KeyboardInterrupt:
        print('\n\n👋 再见！')

if __name__ == '__main__':
    main()
