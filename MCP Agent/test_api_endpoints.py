"""
测试API端点是否正常工作
"""
import requests
import json

def test_api_endpoints():
    base_url = "http://127.0.0.1:5001"
    
    print("=" * 70)
    print("[测试] API端点检查")
    print("=" * 70)
    print()
    
    # 测试1：检查在线模式API
    print("[1] 测试 /api/online-mode (GET)...")
    try:
        response = requests.get(f"{base_url}/api/online-mode", timeout=5)
        print(f"    状态码: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"    当前状态: {'启用' if data['enabled'] else '禁用'}")
            print("    [OK] 在线模式API正常")
        print()
    except Exception as e:
        print(f"    错误: {e}")
        print()
    
    # 测试2：切换在线模式
    print("[2] 测试 /api/online-mode (POST)...")
    try:
        response = requests.post(
            f"{base_url}/api/online-mode",
            json={"enabled": False},
            timeout=5
        )
        print(f"    状态码: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"    已切换到: {'启用' if data['enabled'] else '禁用'}")
            print("    [OK] 切换功能正常")
        print()
    except Exception as e:
        print(f"    错误: {e}")
        print()
    
    # 测试3：切换回来
    print("[3] 测试重新启用在线模式...")
    try:
        response = requests.post(
            f"{base_url}/api/online-mode",
            json={"enabled": True},
            timeout=5
        )
        if response.status_code == 200:
            data = response.json()
            print(f"    已切换到: {'启用' if data['enabled'] else '禁用'}")
            print("    [OK] 切换功能正常")
        print()
    except Exception as e:
        print(f"    错误: {e}")
        print()
    
    # 测试4：获取模型
    print("[4] 测试 /api/models (GET)...")
    try:
        response = requests.get(f"{base_url}/api/models", timeout=5)
        print(f"    状态码: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"    模型数量: {len(data.get('providers', []))}")
            print("    [OK] 模型API正常")
        print()
    except Exception as e:
        print(f"    错误: {e}")
        print()
    
    print("=" * 70)
    print("[完成] API端点测试")
    print("=" * 70)

if __name__ == "__main__":
    test_api_endpoints()
