import urllib.request
import json

def test_api():
    url = 'http://127.0.0.1:5001/chat'
    
    print("测试天气查询...")
    data = json.dumps({'text': '天气 北京'}).encode('utf-8')
    req = urllib.request.Request(url, data=data)
    req.add_header('Content-Type', 'application/json')
    
    with urllib.request.urlopen(req, timeout=5) as resp:
        result = json.loads(resp.read().decode('utf-8'))
        print(f"天气查询结果: {result}")
    
    print("\n测试RAG查询...")
    data = json.dumps({'text': '什么是RAG'}).encode('utf-8')
    req = urllib.request.Request(url, data=data)
    req.add_header('Content-Type', 'application/json')
    
    with urllib.request.urlopen(req, timeout=5) as resp:
        result = json.loads(resp.read().decode('utf-8'))
        print(f"RAG查询结果: {result}")
    
    print("\nAPI测试完成！")

if __name__ == "__main__":
    test_api()
