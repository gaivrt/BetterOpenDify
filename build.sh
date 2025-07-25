#!/bin/bash

# OpenDify Docker构建脚本

set -e

# 配置
IMAGE_NAME="opendify"
TAG=${1:-latest}
FULL_IMAGE_NAME="${IMAGE_NAME}:${TAG}"

echo "🚀 开始构建OpenDify Docker镜像..."
echo "📦 镜像名称: ${FULL_IMAGE_NAME}"

# 构建镜像
echo "📋 构建Docker镜像..."
docker build -t ${FULL_IMAGE_NAME} .

# 显示镜像信息
echo "✅ 构建完成!"
docker images | grep ${IMAGE_NAME}

echo ""
echo "🎯 使用方法:"
echo "1. 复制.env.example为.env并配置你的参数"
echo "2. 运行: docker run -p 5000:5000 --env-file .env ${FULL_IMAGE_NAME}"
echo "3. 或使用docker-compose: docker-compose up"
echo ""
echo "🏥 健康检查: curl http://localhost:5000/health"
echo "📋 模型列表: curl http://localhost:5000/v1/models"