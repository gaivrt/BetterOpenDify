#!/usr/bin/env python3
"""
测试 ConversationMapper 和 chat_id 功能
"""
import requests
import json
import uuid

BASE_URL = "http://localhost:5000"

def test_conversation_mapping():
    """测试会话映射功能"""
    print("🧪 测试 ConversationMapper 功能...")
    
    # 生成测试 chat_id
    chat_id = f"test-chat-{uuid.uuid4()}"
    print(f"📝 使用 chat_id: {chat_id}")
    
    # 第一次请求 - 应该创建新的映射
    headers = {
        "Content-Type": "application/json",
        "X-OpenWebUI-Chat-Id": chat_id
    }
    
    data = {
        "model": "test-model",
        "messages": [{"role": "user", "content": "Hello"}],
        "stream": False
    }
    
    print("🔄 发送第一次请求...")
    try:
        response = requests.post(f"{BASE_URL}/v1/chat/completions", 
                               headers=headers, 
                               json=data)
        print(f"📋 响应状态: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"✅ 第一次请求成功")
    except Exception as e:
        print(f"❌ 请求失败: {e}")
        return
    
    # 检查映射状态
    print("\n🔍 检查映射状态...")
    try:
        response = requests.get(f"{BASE_URL}/v1/conversation/mappings")
        if response.status_code == 200:
            mappings = response.json()
            print(f"📊 映射统计:")
            print(f"   - 总映射数: {mappings['stats']['total_mappings']}")
            print(f"   - 内存使用: {mappings['stats']['memory_size_kb']} KB")
            
            # 检查我们的 chat_id 是否在映射中
            if chat_id in mappings['mappings']:
                print(f"✅ 找到 chat_id 映射:")
                print(f"   - conversation_id: {mappings['mappings'][chat_id]['conversation_id']}")
                print(f"   - user_id: {mappings['mappings'][chat_id]['user_id']}")
            else:
                print(f"❌ 未找到 chat_id 映射")
    except Exception as e:
        print(f"❌ 获取映射失败: {e}")
    
    # 第二次请求 - 应该使用相同的 conversation_id
    print("\n🔄 发送第二次请求（相同 chat_id）...")
    try:
        response = requests.post(f"{BASE_URL}/v1/chat/completions", 
                               headers=headers, 
                               json=data)
        print(f"📋 响应状态: {response.status_code}")
        if response.status_code == 200:
            print(f"✅ 第二次请求成功 - 应该使用相同的会话")
    except Exception as e:
        print(f"❌ 请求失败: {e}")

def test_models_endpoint():
    """测试模型列表端点"""
    print("\n🧪 测试模型列表端点...")
    try:
        response = requests.get(f"{BASE_URL}/v1/models")
        if response.status_code == 200:
            models = response.json()
            print(f"✅ 获取模型列表成功")
            print(f"📋 可用模型: {[m['id'] for m in models['data']]}")
        else:
            print(f"❌ 获取模型列表失败: {response.status_code}")
    except Exception as e:
        print(f"❌ 请求失败: {e}")

def main():
    print("🚀 OpenDify Chat ID 功能测试")
    print("=" * 50)
    
    # 测试模型端点
    test_models_endpoint()
    
    # 测试会话映射
    test_conversation_mapping()
    
    print("\n✅ 测试完成！")

if __name__ == "__main__":
    main()