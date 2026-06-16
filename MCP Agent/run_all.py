"""一键运行脚本（跨平台）
- 在项目根创建/使用 `.venv` 虚拟环境
- 安装 `requirements.txt`
- 启动 `api_server.py` 后端（后台进程）
- 启动 `desktop_chat.py` 前端（阻塞，关闭后会清理后端）

用法：
    python run_all.py
"""
import os
import sys
import subprocess
import time
import urllib.request
import json
import signal

ROOT = os.path.dirname(__file__)
VENV_DIR = os.path.join(ROOT, '.venv')
REQUIREMENTS = os.path.join(ROOT, 'requirements.txt')
API_URL = 'http://127.0.0.1:5001/chat'


def venv_python():
    if sys.platform == 'win32':
        return os.path.join(VENV_DIR, 'Scripts', 'python.exe')
    else:
        return os.path.join(VENV_DIR, 'bin', 'python')


def ensure_venv():
    if not os.path.exists(VENV_DIR):
        print('创建虚拟环境...')
        subprocess.check_call([sys.executable, '-m', 'venv', VENV_DIR])

    py = venv_python()
    if not os.path.exists(py):
        raise RuntimeError(f'无法找到虚拟环境的 python：{py}')
    return py


def install_requirements(py):
    if os.path.exists(REQUIREMENTS):
        print('安装依赖...')
        subprocess.check_call([py, '-m', 'pip', 'install', '--upgrade', 'pip'])
        subprocess.check_call([py, '-m', 'pip', 'install', '-r', REQUIREMENTS])
    else:
        print('未找到 requirements.txt，跳过安装。')


def wait_backend_ready(timeout=10):
    start = time.time()
    data = json.dumps({'text': 'ping'}).encode('utf-8')
    headers = {'Content-Type': 'application/json; charset=utf-8'}
    while time.time() - start < timeout:
        try:
            req = urllib.request.Request(API_URL, data=data, headers=headers, method='POST')
            with urllib.request.urlopen(req, timeout=2) as resp:
                _ = resp.read()
                return True
        except Exception:
            time.sleep(0.3)
    return False


def main():
    py = ensure_venv()
    install_requirements(py)

    # 启动后端
    print('启动后端 api_server.py ...')
    backend = subprocess.Popen([py, os.path.join(ROOT, 'api_server.py')], cwd=ROOT)

    try:
        ok = wait_backend_ready(10)
        if not ok:
            print('后端未在超时时间内响应，请检查日志。')
        else:
            print('后端已启动。')

        # 启动桌面前端（阻塞）
        print('启动桌面前端 desktop_chat.py ...')
        subprocess.call([py, os.path.join(ROOT, 'desktop_chat.py')], cwd=ROOT)

    finally:
        print('正在关闭后端...')
        try:
            if backend.poll() is None:
                if sys.platform == 'win32':
                    backend.terminate()
                else:
                    os.kill(backend.pid, signal.SIGTERM)
                backend.wait(timeout=5)
        except Exception:
            pass
        print('已退出。')


if __name__ == '__main__':
    main()
