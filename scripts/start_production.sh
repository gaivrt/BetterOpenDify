#!/bin/bash

# OpenDify 生产环境启动脚本
# 使用 Gunicorn 作为 WSGI 服务器

set -e

# 切换到项目根目录
cd "$(dirname "$0")/.."

echo "🚀 启动 OpenDify 生产服务..."

# 检查环境变量
if [ -z "$DIFY_API_BASE" ]; then
    echo "❌ 错误: DIFY_API_BASE 环境变量未设置"
    echo "💡 请设置: export DIFY_API_BASE='https://api.dify.ai/v1'"
    exit 1
fi

if [ -z "$MODEL_CONFIG" ]; then
    echo "❌ 错误: MODEL_CONFIG 环境变量未设置"
    echo "💡 请设置: export MODEL_CONFIG='{\"model\":\"api-key\"}'"
    exit 1
fi

# 设置默认值
export SERVER_HOST=${SERVER_HOST:-"0.0.0.0"}
export SERVER_PORT=${SERVER_PORT:-"5000"}
export ENVIRONMENT=${ENVIRONMENT:-"production"}
export GUNICORN_WORKERS=${GUNICORN_WORKERS:-$(($(nproc) * 2 + 1))}
export LOG_LEVEL=${LOG_LEVEL:-"info"}

# 创建必要的目录
mkdir -p data logs

# 显示配置信息
echo "📋 启动配置:"
echo "  服务地址: $SERVER_HOST:$SERVER_PORT"
echo "  工作进程: $GUNICORN_WORKERS"
echo "  环境模式: $ENVIRONMENT"
echo "  日志级别: $LOG_LEVEL"
echo "  Dify API: $DIFY_API_BASE"

# 启动 Gunicorn
echo "🔥 启动 Gunicorn 服务器..."
exec gunicorn \
    --config gunicorn_config.py \
    --bind $SERVER_HOST:$SERVER_PORT \
    --workers $GUNICORN_WORKERS \
    --worker-class sync \
    --timeout 60 \
    --keepalive 2 \
    --max-requests 2000 \
    --max-requests-jitter 100 \
    --preload \
    --log-level $LOG_LEVEL \
    --access-logfile - \
    --error-logfile - \
    main:app