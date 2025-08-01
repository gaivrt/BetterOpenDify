#!/bin/bash

# 运行Docker Compose的脚本

# 切换到项目根目录
cd "$(dirname "$0")/.."

echo "🚀 启动 OpenDify 服务..."

# 检查是否有.env文件
if [ ! -f .env ]; then
    echo "❌ 错误: 找不到 .env 文件"
    echo "请先复制 .env.example 并配置你的API密钥"
    exit 1
fi

# 检查Docker是否运行
if ! docker info > /dev/null 2>&1; then
    echo "❌ 错误: Docker 未运行"
    echo "请先启动 Docker"
    exit 1
fi

# 停止旧容器
echo "🛑 停止旧容器..."
docker-compose down

# 构建并启动
echo "🔨 构建镜像..."
docker-compose build

echo "🚀 启动容器..."
docker-compose up -d

# 等待服务启动
echo "⏳ 等待服务启动..."
sleep 5

# 检查服务状态
echo "🔍 检查服务状态..."
if curl -s http://localhost:5000/v1/models > /dev/null; then
    echo "✅ 服务启动成功！"
    echo ""
    echo "📋 服务信息:"
    echo "   - API地址: http://localhost:5000/v1"
    echo "   - 查看日志: docker-compose logs -f"
    echo "   - 停止服务: docker-compose down"
    echo ""
    
    # 检查数据库状态
    echo "🗄️  检查数据库状态..."
    DB_INFO=$(curl -s http://localhost:5000/v1/conversation/database/info 2>/dev/null)
    if [ $? -eq 0 ] && [ ! -z "$DB_INFO" ]; then
        echo "   - 数据库: SQLite (多进程安全)"
        # 尝试提取映射数量
        MAPPING_COUNT=$(echo "$DB_INFO" | grep -o '"mapping_count":[0-9]*' | cut -d':' -f2 2>/dev/null || echo "0")
        echo "   - 会话映射: $MAPPING_COUNT 条记录"
    else
        echo "   - 数据库: 状态检查失败"
    fi
    
    echo ""
    echo "📊 监控端点:"
    echo "   - 会话统计: curl http://localhost:5000/v1/conversation/mappings"
    echo "   - 数据库信息: curl http://localhost:5000/v1/conversation/database/info"
    echo "   - 最近会话: curl http://localhost:5000/v1/conversation/recent"
    echo ""
    echo "🧪 运行测试: python tests/test_api.py"
    echo "🔧 并发测试: python tests/test_multiprocess.py"
else
    echo "❌ 服务启动失败"
    echo "查看日志: docker-compose logs"
    exit 1
fi