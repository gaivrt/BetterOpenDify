#!/usr/bin/env python3
"""
手动测试脚本 - 验证 conversation_id 映射功能
"""
import requests
import json
import time

# 测试配置
BASE_URL = "http://127.0.0.1:5000"
TEST_MODEL = "Emohaa 0701 送测 【C】"  # 确保在 .env 中配置了这个模型

def test_conversation_continuity():
    """测试会话连续性"""
    print("🧪 测试会话连续性...")
    
    # 模拟 Open WebUI 发送的 chat_id
    test_chat_id = f"test-chat-{int(time.time())}"
    
    headers = {
        "Content-Type": "application/json",
        "X-OpenWebUI-Chat-Id": test_chat_id
    }
    
    # 第一轮对话：透露信息
    print(f"📤 第一轮对话 (chat_id: {test_chat_id[:8]}...)")
    first_request = {
        "model": TEST_MODEL,
        "messages": [
            {"role": "user", "content": "请记住：我的名字是张三，我来自北京"}
        ],
        "stream": False
    }
    
    try:
        response1 = requests.post(f"{BASE_URL}/v1/chat/completions", 
                                json=first_request, headers=headers)
        print(f"✅ 第一轮响应状态: {response1.status_code}")
        if response1.status_code == 200:
            data1 = response1.json()
            print(f"📝 第一轮回复: {data1['choices'][0]['message']['content'][:100]}...")
        else:
            print(f"❌ 第一轮失败: {response1.text}")
            return False
    except Exception as e:
        print(f"❌ 第一轮请求异常: {e}")
        return False
    
    # 等待一下
    time.sleep(1)
    
    # 第二轮对话：测试记忆
    print(f"📤 第二轮对话 (相同 chat_id)")
    second_request = {
        "model": TEST_MODEL,
        "messages": [
            {"role": "user", "content": "请记住：我的名字是张三，我来自北京"},
            {"role": "assistant", "content": data1['choices'][0]['message']['content']},
            {"role": "user", "content": "请告诉我，我的名字是什么，我来自哪里？"}
        ],
        "stream": False
    }
    
    try:
        response2 = requests.post(f"{BASE_URL}/v1/chat/completions", 
                                json=second_request, headers=headers)
        print(f"✅ 第二轮响应状态: {response2.status_code}")
        if response2.status_code == 200:
            data2 = response2.json()
            reply2 = data2['choices'][0]['message']['content']
            print(f"📝 第二轮回复: {reply2}")
            
            # 检查是否记住了信息
            if "张三" in reply2 and "北京" in reply2:
                print("🎉 测试成功！AI 记住了之前的对话内容")
                return True
            else:
                print("⚠️  测试失败：AI 没有记住之前的对话内容")
                return False
        else:
            print(f"❌ 第二轮失败: {response2.text}")
            return False
    except Exception as e:
        print(f"❌ 第二轮请求异常: {e}")
        return False

def test_different_chats():
    """测试不同聊天的隔离性"""
    print("\n🧪 测试不同聊天的隔离性...")
    
    chat_id_1 = f"test-chat-1-{int(time.time())}"
    chat_id_2 = f"test-chat-2-{int(time.time())}"
    
    # 聊天1：设置信息
    headers1 = {
        "Content-Type": "application/json",
        "X-OpenWebUI-Chat-Id": chat_id_1
    }
    
    request1 = {
        "model": TEST_MODEL,
        "messages": [
            {"role": "user", "content": "请记住：我喜欢苹果"}
        ],
        "stream": False
    }
    
    try:
        response1 = requests.post(f"{BASE_URL}/v1/chat/completions", 
                                json=request1, headers=headers1)
        print(f"✅ 聊天1响应状态: {response1.status_code}")
    except Exception as e:
        print(f"❌ 聊天1异常: {e}")
        return False
    
    # 聊天2：测试隔离
    headers2 = {
        "Content-Type": "application/json",
        "X-OpenWebUI-Chat-Id": chat_id_2
    }
    
    request2 = {
        "model": TEST_MODEL,
        "messages": [
            {"role": "user", "content": "我喜欢什么水果？"}
        ],
        "stream": False
    }
    
    try:
        response2 = requests.post(f"{BASE_URL}/v1/chat/completions", 
                                json=request2, headers=headers2)
        print(f"✅ 聊天2响应状态: {response2.status_code}")
        if response2.status_code == 200:
            data2 = response2.json()
            reply2 = data2['choices'][0]['message']['content']
            print(f"📝 聊天2回复: {reply2[:100]}...")
            
            # 检查是否正确隔离
            if "苹果" not in reply2:
                print("🎉 测试成功！不同聊天正确隔离")
                return True
            else:
                print("⚠️  测试失败：聊天间出现了信息泄露")
                return False
    except Exception as e:
        print(f"❌ 聊天2异常: {e}")
        return False

def test_mapping_status():
    """测试映射状态"""
    print("\n🧪 测试映射状态...")
    
    try:
        response = requests.get(f"{BASE_URL}/v1/conversation/mappings")
        print(f"✅ 映射状态响应: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"📊 当前映射数量: {data['mapping_count']}")
            return True
        else:
            print(f"❌ 获取映射状态失败: {response.text}")
            return False
    except Exception as e:
        print(f"❌ 映射状态请求异常: {e}")
        return False

def main():
    """主测试函数"""
    print("🚀 开始手动测试 OpenDify conversation_id 映射功能")
    print("=" * 60)
    
    # 检查服务是否运行
    try:
        response = requests.get(f"{BASE_URL}/v1/models")
        if response.status_code != 200:
            print(f"❌ OpenDify 服务未运行或配置错误: {response.status_code}")
            return
        print("✅ OpenDify 服务正常运行")
    except Exception as e:
        print(f"❌ 无法连接到 OpenDify 服务: {e}")
        print("请确保已启动 OpenDify 服务：python main.py")
        return
    
    # 运行测试
    tests = [
        test_mapping_status,
        test_conversation_continuity,
        test_different_chats,
        test_mapping_status,  # 再次检查映射数量
    ]
    
    passed = 0
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"❌ 测试异常: {e}")
    
    print("\n" + "=" * 60)
    print(f"🏁 测试完成: {passed}/{len(tests)} 项测试通过")
    
    if passed == len(tests):
        print("🎉 所有测试通过！conversation_id 映射功能工作正常")
    else:
        print("⚠️  部分测试失败，请检查配置和实现")

if __name__ == "__main__":
    main()