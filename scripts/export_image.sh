#!/bin/bash

# 导出 Docker 镜像脚本

# 切换到项目根目录
cd "$(dirname "$0")/.."

echo "🔨 构建 Docker 镜像..."
docker build -t opendify . || {
    echo "❌ 构建失败"
    exit 1
}

echo "📦 导出镜像为压缩文件..."
docker save opendify | gzip > opendify.tar.gz

# 获取文件大小
SIZE=$(ls -lh opendify.tar.gz | awk '{print $5}')

echo "✅ 镜像导出成功！"
echo "📋 文件信息："
echo "   - 文件名: opendify.tar.gz"
echo "   - 大小: $SIZE"
echo ""
echo "📤 上传命令示例："
echo "   scp opendify.tar.gz user@server:/path/to/destination/"
echo ""
echo "💡 在服务器上加载："
echo "   docker load < opendify.tar.gz"