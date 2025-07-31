#!/bin/bash

# OpenDify 开发环境启动脚本
# 使用 Gunicorn 进行开发调试

set -e

# 切换到项目根目录
cd "$(dirname "$0")/.."

echo "🛠️ 启动 OpenDify 开发服务..."

# 设置开发环境变量
export ENVIRONMENT="development"
export SERVER_HOST=${SERVER_HOST:-"127.0.0.1"}
export SERVER_PORT=${SERVER_PORT:-"5000"}
export GUNICORN_WORKERS=${GUNICORN_WORKERS:-"1"}
export GUNICORN_RELOAD="true"
export LOG_LEVEL="debug"

# 设置默认的测试配置（如果未设置）
export DIFY_API_BASE=${DIFY_API_BASE:-"https://api.dify.ai/v1"}
export MODEL_CONFIG=${MODEL_CONFIG:-'{"test-model":"app-test-key"}'}

# 创建必要的目录
mkdir -p data logs

echo "📋 开发配置:"
echo "  服务地址: $SERVER_HOST:$SERVER_PORT"
echo "  工作进程: $GUNICORN_WORKERS (单进程调试模式)"
echo "  自动重载: 启用"
echo "  日志级别: $LOG_LEVEL"

# 启动 Gunicorn 开发服务器
echo "🔥 启动 Gunicorn 开发服务器..."
exec gunicorn \
    --config gunicorn_config.py \
    --bind $SERVER_HOST:$SERVER_PORT \
    --workers 1 \
    --worker-class sync \
    --timeout 30 \
    --reload \
    --log-level debug \
    --access-logfile - \
    --error-logfile - \
    main:app