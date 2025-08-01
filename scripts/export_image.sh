#!/bin/bash

# 导出 Docker 镜像脚本

# 切换到项目根目录
cd "$(dirname "$0")/.."

# 检查镜像是否已存在
if docker image inspect opendify &> /dev/null; then
    echo "🔍 发现已存在的 opendify 镜像"
    echo -n "是否重新构建？[y/N]: "
    read -r REBUILD
    if [[ ! "$REBUILD" =~ ^[Yy]$ ]]; then
        echo "⏭️  跳过构建，使用现有镜像"
    else
        echo "🔨 重新构建 Docker 镜像..."
        docker build -t opendify . || {
            echo "❌ 构建失败"
            exit 1
        }
    fi
else
    echo "🔨 构建 Docker 镜像..."
    docker build -t opendify . || {
        echo "❌ 构建失败"
        exit 1
    }
fi

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