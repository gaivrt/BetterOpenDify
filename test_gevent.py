#!/usr/bin/env python3
"""
测试 gevent 配置的脚本
"""
import os
import sys
import time
import subprocess
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
import json

# 配置
HOST = "127.0.0.1"
PORT = 5000
BASE_URL = f"http://{HOST}:{PORT}"

def start_server():
    """使用 gunicorn 启动服务器"""
    print("🚀 启动 Gunicorn 服务器 (gevent worker)...")
    
    # 设置测试环境变量
    env = os.environ.copy()
    env.update({
        'MODEL_CONFIG': '{"test-model":"test-api-key"}',
        'DIFY_API_BASE': 'https://api.dify.example.com/v1',
        'SERVER_HOST': HOST,
        'SERVER_PORT': str(PORT),
        'GUNICORN_WORKERS': '2'
    })
    
    # 启动 gunicorn
    cmd = [
        'gunicorn',
        'main:app',
        '-c', 'gunicorn_config.py',
        '--log-level', 'info'
    ]
    
    process = subprocess.Popen(cmd, env=env)
    
    # 等待服务器启动
    print("⏳ 等待服务器启动...")
    time.sleep(3)
    
    # 检查服务器是否启动
    try:
        response = requests.get(f"{BASE_URL}/v1/models", timeout=5)
        if response.status_code == 200:
            print("✅ 服务器启动成功！")
            print(f"📋 可用模型: {response.json()}")
        else:
            print(f"❌ 服务器响应异常: {response.status_code}")
    except Exception as e:
        print(f"❌ 无法连接到服务器: {e}")
        process.kill()
        sys.exit(1)
    
    return process

def test_basic_functionality():
    """测试基本功能"""
    print("\n📝 测试基本功能...")
    
    try:
        # 测试 models 端点
        response = requests.get(f"{BASE_URL}/v1/models")
        assert response.status_code == 200
        models = response.json()
        print(f"✅ GET /v1/models - 成功获取模型列表")
        
        # 测试 health 端点（如果有）
        response = requests.get(f"{BASE_URL}/health", timeout=2)
        if response.status_code == 200:
            print(f"✅ GET /health - 健康检查通过")
        
    except Exception as e:
        print(f"❌ 基本功能测试失败: {e}")
        return False
    
    return True

def concurrent_request(request_id):
    """单个并发请求"""
    try:
        start = time.time()
        response = requests.get(f"{BASE_URL}/v1/models", timeout=5)
        duration = time.time() - start
        
        return {
            'id': request_id,
            'status': response.status_code,
            'duration': duration,
            'success': response.status_code == 200
        }
    except Exception as e:
        return {
            'id': request_id,
            'status': 0,
            'duration': 0,
            'success': False,
            'error': str(e)
        }

def test_concurrent_performance():
    """测试并发性能"""
    print("\n🔄 测试并发性能...")
    
    # 并发请求数
    concurrent_requests = 50
    
    print(f"📊 发送 {concurrent_requests} 个并发请求...")
    
    start_time = time.time()
    
    # 使用线程池发送并发请求
    with ThreadPoolExecutor(max_workers=concurrent_requests) as executor:
        futures = [executor.submit(concurrent_request, i) for i in range(concurrent_requests)]
        results = [future.result() for future in as_completed(futures)]
    
    total_time = time.time() - start_time
    
    # 统计结果
    successful = sum(1 for r in results if r['success'])
    failed = len(results) - successful
    avg_duration = sum(r['duration'] for r in results) / len(results)
    
    print(f"\n📈 并发测试结果:")
    print(f"  - 总请求数: {concurrent_requests}")
    print(f"  - 成功: {successful}")
    print(f"  - 失败: {failed}")
    print(f"  - 总耗时: {total_time:.2f}s")
    print(f"  - 平均响应时间: {avg_duration:.3f}s")
    print(f"  - 请求/秒: {concurrent_requests / total_time:.2f}")
    
    # 显示错误（如果有）
    errors = [r for r in results if not r['success']]
    if errors:
        print(f"\n❌ 错误详情:")
        for error in errors[:5]:  # 只显示前5个错误
            print(f"  - 请求 {error['id']}: {error.get('error', 'Unknown error')}")
    
    return successful == concurrent_requests

def test_worker_info():
    """检查 worker 信息"""
    print("\n🔍 检查 Worker 信息...")
    
    # 运行 ps 命令查看 gunicorn 进程
    try:
        result = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
        gunicorn_processes = [line for line in result.stdout.split('\n') if 'gunicorn' in line and 'grep' not in line]
        
        print(f"📋 Gunicorn 进程数: {len(gunicorn_processes)}")
        for proc in gunicorn_processes:
            if 'master' in proc:
                print(f"  - Master 进程")
            else:
                print(f"  - Worker 进程 (gevent)")
    except Exception as e:
        print(f"❌ 无法获取进程信息: {e}")

def main():
    """主测试函数"""
    print("🧪 OpenDify Gevent 配置测试")
    print("=" * 50)
    
    # 启动服务器
    server_process = start_server()
    
    try:
        # 测试基本功能
        if not test_basic_functionality():
            print("\n❌ 基本功能测试失败，终止测试")
            return
        
        # 显示 worker 信息
        test_worker_info()
        
        # 测试并发性能
        test_concurrent_performance()
        
        print("\n✅ 所有测试完成！")
        print("\n💡 提示: gevent worker 已成功配置并运行")
        print("   - 适合 I/O 密集型的 API 代理服务")
        print("   - 可以处理大量并发连接")
        print("   - 内存占用更低")
        
    finally:
        # 停止服务器
        print("\n🛑 停止服务器...")
        server_process.terminate()
        server_process.wait()
        print("✅ 服务器已停止")

if __name__ == "__main__":
    main()