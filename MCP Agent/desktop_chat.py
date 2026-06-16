import json
import os
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.request
import tkinter as tk
from tkinter import scrolledtext, messagebox
from typing import Optional, Dict, Any

ROOT = os.path.dirname(__file__)
API_HOST = '127.0.0.1'
API_PORT = 5001
API_URL = f'http://{API_HOST}:{API_PORT}/chat'
API_SERVER_SCRIPT = os.path.join(ROOT, 'api_server.py')

backend_process: Optional[subprocess.Popen] = None


def post_chat(text: str) -> Dict[str, Any]:
    data = json.dumps({'text': text}, ensure_ascii=False).encode('utf-8')
    req = urllib.request.Request(API_URL, data=data, method='POST')
    req.add_header('Content-Type', 'application/json; charset=utf-8')

    with urllib.request.urlopen(req, timeout=10) as resp:
        body = resp.read().decode('utf-8')
        return json.loads(body)


def is_backend_running() -> bool:
    try:
        data = json.dumps({'text': 'ping'}, ensure_ascii=False).encode('utf-8')
        req = urllib.request.Request(API_URL, data=data, method='POST')
        req.add_header('Content-Type', 'application/json; charset=utf-8')
        with urllib.request.urlopen(req, timeout=3):
            return True
    except Exception:
        return False


def start_backend() -> bool:
    global backend_process
    if is_backend_running():
        return True
    if not os.path.exists(API_SERVER_SCRIPT):
        return False
    backend_process = subprocess.Popen(
        [sys.executable, API_SERVER_SCRIPT],
        cwd=ROOT,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    for _ in range(20):
        if is_backend_running():
            return True
        if backend_process.poll() is not None:
            return False
        time.sleep(0.3)
    return is_backend_running()


def stop_backend() -> None:
    global backend_process
    if backend_process and backend_process.poll() is None:
        backend_process.terminate()
        try:
            backend_process.wait(timeout=3)
        except subprocess.TimeoutExpired:
            backend_process.kill()
    backend_process = None


def safe_request(text: str) -> Dict[str, Any]:
    try:
        return post_chat(text)
    except urllib.error.URLError as exc:
        return {'error': f'无法连接到后端: {exc}'}
    except Exception as exc:
        return {'error': str(exc)}


class DesktopChatApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        root.title('MCP Agent 桌面对话')
        root.geometry('700x500')

        self.chat_display = scrolledtext.ScrolledText(
            root, wrap='word', state='disabled', font=('微软雅黑', 10)
        )
        self.chat_display.pack(fill='both', expand=True, padx=10, pady=(10, 0))

        entry_frame = tk.Frame(root)
        entry_frame.pack(fill='x', padx=10, pady=10)

        self.input_var = tk.StringVar()
        self.input_entry = tk.Entry(
            entry_frame, textvariable=self.input_var, font=('微软雅黑', 10)
        )
        self.input_entry.pack(side='left', fill='x', expand=True, padx=(0, 8))
        self.input_entry.bind('<Return>', self.on_send)

        self.send_button = tk.Button(entry_frame, text='发送', width=10, command=self.on_send)
        self.send_button.pack(side='left')

        status_frame = tk.Frame(root)
        status_frame.pack(fill='x', padx=10, pady=(0, 10))

        self.status_label = tk.Label(status_frame, text='正在启动后端...', anchor='w')
        self.status_label.pack(fill='x')

        self.append_chat('系统', '桌面聊天已启动。正在检查后端服务...')
        self.initialize_backend()

    def append_chat(self, sender: str, message: str) -> None:
        self.chat_display.config(state='normal')
        self.chat_display.insert('end', f'{sender}: {message}\n')
        self.chat_display.see('end')
        self.chat_display.config(state='disabled')

    def initialize_backend(self) -> None:
        def worker() -> None:
            success = start_backend()
            if success:
                status = f'后端已启动：{API_URL}'
            else:
                status = '后端启动失败，请先运行 api_server.py 或检查网络/Python 环境。'
            self.status_label.config(text=status)
            if not success:
                messagebox.showerror('后端启动失败', status)
                self.send_button.config(state='disabled')

        threading.Thread(target=worker, daemon=True).start()

    def on_send(self, event: Optional[tk.Event] = None) -> None:
        text = self.input_var.get().strip()
        if not text:
            return
        self.input_var.set('')
        self.append_chat('你', text)
        self.send_button.config(state='disabled')

        def worker() -> None:
            result = safe_request(text)
            if 'error' in result:
                self.append_chat('错误', result['error'])
            else:
                reply = result.get('result') or result
                if isinstance(reply, dict):
                    self.append_chat('机器人', json.dumps(reply, ensure_ascii=False))
                else:
                    self.append_chat('机器人', str(reply))
            self.send_button.config(state='normal')

        threading.Thread(target=worker, daemon=True).start()


def main() -> None:
    root = tk.Tk()
    app = DesktopChatApp(root)
    root.protocol('WM_DELETE_WINDOW', lambda: (stop_backend(), root.destroy()))
    root.mainloop()


if __name__ == '__main__':
    main()
