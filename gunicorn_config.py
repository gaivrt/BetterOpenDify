#!/usr/bin/env python3
"""
Gunicorn 配置文件
用于生产环境部署 OpenDify
"""

import os
import multiprocessing

# 服务器配置
bind = f"{os.getenv('SERVER_HOST', '0.0.0.0')}:{os.getenv('SERVER_PORT', '5000')}"
backlog = 2048

# 工作进程配置
workers = int(os.getenv('GUNICORN_WORKERS', multiprocessing.cpu_count() * 2 + 1))
worker_class = "gevent"  # 使用 gevent 异步工作进程，适合 I/O 密集型应用
worker_connections = 1000
max_requests = 1000
max_requests_jitter = 50
timeout = 30
keepalive = 2

# 重启配置
preload_app = True
reload = os.getenv('GUNICORN_RELOAD', 'False').lower() == 'true'
reload_extra_files = ['main.py']

# 日志配置
accesslog = '-'  # 输出到 stdout
errorlog = '-'   # 输出到 stderr
loglevel = os.getenv('LOG_LEVEL', 'info')
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)sμs'

# 进程命名
proc_name = 'opendify'

# 用户和组（生产环境中设置）
# user = 'nobody'
# group = 'nogroup'

# 临时目录
tmp_upload_dir = None

# SSL 配置（如果需要）
# keyfile = '/path/to/keyfile'
# certfile = '/path/to/certfile'

# 钩子函数
def on_starting(server):
    """服务器启动时的钩子"""
    server.log.info("🚀 OpenDify 服务启动中...")

def on_reload(server):
    """重载时的钩子"""
    server.log.info("🔄 OpenDify 服务重载中...")

def worker_int(worker):
    """工作进程中断时的钩子"""
    worker.log.info(f"👷 工作进程 {worker.pid} 接收到中断信号")

def on_exit(server):
    """服务器退出时的钩子"""
    server.log.info("👋 OpenDify 服务已停止")

# 性能优化配置
preload_app = True
sendfile = True

# 环境特定配置
if os.getenv('ENVIRONMENT') == 'development':
    # 开发环境配置
    workers = 1
    reload = True
    loglevel = 'debug'
elif os.getenv('ENVIRONMENT') == 'production':
    # 生产环境配置
    workers = int(os.getenv('GUNICORN_WORKERS', multiprocessing.cpu_count() * 2 + 1))
    preload_app = True
    max_requests = 2000
    timeout = 60