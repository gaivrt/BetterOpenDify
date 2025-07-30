#!/usr/bin/env python3
"""
OpenDify API 简单测试脚本
"""

import requests
import json

def test_service():
    import sys
    base_url = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:5000/v1"
    
    print("🔍 测试模型列表...")
    try:
        response = requests.get(f"{base_url}/models")
        if response.status_code == 200:
            models = response.json().get("data", [])
            print(f"✅ 找到 {len(models)} 个模型")
            for model in models:
                print(f"   - {model['id']}")
        else:
            print(f"❌ 模型列表失败: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 连接失败: {e}")
        return False
    
    print("\n🔍 测试聊天...")
    try:
        payload = {
            "model": "Emohaa 0701 送测 【C】",
            "messages": [{"role": "user", "content": "你好"}],
            "stream": False
        }
        response = requests.post(f"{base_url}/chat/completions", json=payload)
        if response.status_code == 200:
            content = response.json()["choices"][0]["message"]["content"]
            print(f"✅ 聊天成功: {content[:50]}...")
        else:
            print(f"❌ 聊天失败: {response.status_code}")
            print(response.text)
            return False
    except Exception as e:
        print(f"❌ 聊天错误: {e}")
        return False
    
    print("\n🎉 服务运行正常！")
    return True

if __name__ == "__main__":
    test_service()