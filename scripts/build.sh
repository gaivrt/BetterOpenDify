#!/bin/bash

# OpenDify Docker构建脚本
# 支持生产和开发环境镜像构建

set -e

# 帮助信息
show_help() {
    echo "OpenDify Docker 构建脚本"
    echo ""
    echo "用法:"
    echo "  $0 [环境] [标签]"
    echo ""
    echo "环境:"
    echo "  prod    - 构建生产环境镜像 (默认)"
    echo "  dev     - 构建开发环境镜像"
    echo ""
    echo "示例:"
    echo "  $0              # 构建生产环境 latest 镜像"
    echo "  $0 prod v1.0    # 构建生产环境 v1.0 镜像"
    echo "  $0 dev          # 构建开发环境镜像"
    echo ""
}

# 解析参数
ENV=${1:-prod}
TAG=${2:-latest}

if [ "$ENV" = "help" ] || [ "$ENV" = "--help" ] || [ "$ENV" = "-h" ]; then
    show_help
    exit 0
fi

# 配置
IMAGE_NAME="opendify"
if [ "$ENV" = "dev" ]; then
    DOCKERFILE="Dockerfile.dev"
    FULL_IMAGE_NAME="${IMAGE_NAME}-dev:${TAG}"
    echo "🛠️ 构建开发环境镜像..."
else
    DOCKERFILE="Dockerfile"
    FULL_IMAGE_NAME="${IMAGE_NAME}:${TAG}"
    echo "🚀 构建生产环境镜像..."
fi

echo "📦 镜像名称: ${FULL_IMAGE_NAME}"
echo "📋 使用文件: ${DOCKERFILE}"

# 检查 Dockerfile 是否存在
if [ ! -f "$DOCKERFILE" ]; then
    echo "❌ 错误: $DOCKERFILE 文件不存在"
    exit 1
fi

# 构建镜像
echo "🔨 开始构建Docker镜像..."
docker build -f ${DOCKERFILE} -t ${FULL_IMAGE_NAME} .

# 显示镜像信息
echo "✅ 构建完成!"
docker images | grep ${IMAGE_NAME} | head -5

echo ""
echo "🎯 使用方法:"
if [ "$ENV" = "dev" ]; then
    echo "开发环境:"
    echo "  make docker-dev                    # 使用 docker-compose 启动"
    echo "  docker-compose -f docker-compose.dev.yml up -d"
    echo "  docker run -p 5000:5000 --env-file .env -v \$(pwd):/app ${FULL_IMAGE_NAME}"
else
    echo "生产环境:"
    echo "  make docker-prod                   # 使用 docker-compose 启动"
    echo "  docker-compose up -d               # 标准启动"
    echo "  docker run -p 5000:5000 --env-file .env ${FULL_IMAGE_NAME}"
fi

echo ""
echo "⚙️ 配置说明:"
echo "1. 复制并配置环境变量:"
echo "   cp .env.example .env"
echo "   # 编辑 .env 文件设置 DIFY_API_BASE 和 MODEL_CONFIG"
echo ""
echo "🔍 健康检查:"
echo "  curl http://localhost:5000/v1/models"
echo ""
echo "📋 更多命令:"
echo "  make help                          # 查看所有可用命令"