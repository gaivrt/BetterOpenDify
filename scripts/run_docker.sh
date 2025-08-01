#!/bin/bash

# OpenDify Docker 运行脚本（无需构建）

# 切换到项目根目录
cd "$(dirname "$0")/.."

echo "🚀 启动 OpenDify 服务..."

# 检查是否有 .env 文件
if [ ! -f .env ]; then
    echo "❌ 错误: 找不到 .env 文件"
    echo "请先创建 .env 文件并配置你的API密钥"
    exit 1
fi

# 检查镜像是否存在
if ! docker images | grep -q "opendify"; then
    echo "❌ 错误: 找不到 opendify 镜像"
    echo "请先加载镜像: docker load < opendify.tar.gz"
    exit 1
fi

# 停止并删除旧容器
echo "🛑 清理旧容器..."
docker stop opendify 2>/dev/null
docker rm opendify 2>/dev/null

# 启动新容器
echo "🚀 启动容器..."
docker run -d \
    --name opendify \
    -p 5000:5000 \
    --env-file .env \
    --restart unless-stopped \
    opendify

# 等待服务启动
echo "⏳ 等待服务启动..."
sleep 5

# 检查容器状态
if docker ps | grep -q "opendify"; then
    # 检查服务是否响应
    if curl -s http://localhost:5000/v1/models > /dev/null 2>&1; then
        echo "✅ 服务启动成功！"
        echo ""
        echo "📋 服务信息:"
        echo "   - API地址: http://localhost:5000/v1"
        echo "   - 容器名称: opendify"
        echo "   - 查看日志: docker logs -f opendify"
        echo "   - 停止服务: docker stop opendify"
        echo "   - 重启服务: docker restart opendify"
        echo ""
        echo "🧪 测试API: python tests/test_api.py"
    else
        echo "⚠️  容器已启动但服务未响应"
        echo "查看日志: docker logs opendify"
    fi
else
    echo "❌ 容器启动失败"
    echo "查看日志: docker logs opendify"
    exit 1
fi