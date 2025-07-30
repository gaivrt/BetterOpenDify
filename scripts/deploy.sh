#!/bin/bash

# OpenDify 部署脚本
# 用于管理环境变量和部署流程

set -e

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# 默认值
ENV_FILE=".env.production"
IMAGE_NAME="opendify:latest"
CONTAINER_NAME="opendify"
PORT="5000"

# 显示帮助
show_help() {
    echo "OpenDify Docker 部署脚本"
    echo ""
    echo "用法: $0 [命令] [选项]"
    echo ""
    echo "命令:"
    echo "  setup     - 创建环境配置文件"
    echo "  deploy    - 部署容器"
    echo "  update    - 更新部署"
    echo "  status    - 查看状态"
    echo "  logs      - 查看日志"
    echo "  stop      - 停止服务"
    echo ""
    echo "选项:"
    echo "  --env-file FILE   - 指定环境文件 (默认: .env.production)"
    echo "  --port PORT       - 指定端口 (默认: 5000)"
    echo ""
}

# 创建环境配置
setup_env() {
    echo -e "${GREEN}🔧 创建环境配置文件${NC}"
    
    if [ -f "$ENV_FILE" ]; then
        echo -e "${YELLOW}⚠️  文件 $ENV_FILE 已存在${NC}"
        read -p "是否覆盖? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            echo "已取消"
            return
        fi
    fi
    
    # 交互式输入配置
    echo "请输入配置信息:"
    read -p "DIFY API 地址 (例: https://api.dify.ai/v1): " DIFY_API_BASE
    
    echo "配置模型 (输入 'done' 完成):"
    MODEL_CONFIG="{"
    FIRST=true
    while true; do
        read -p "模型名称 (或 'done'): " MODEL_NAME
        if [ "$MODEL_NAME" = "done" ]; then
            break
        fi
        read -p "API Key (app-xxxxx): " API_KEY
        
        if [ "$FIRST" = true ]; then
            MODEL_CONFIG="${MODEL_CONFIG}\"${MODEL_NAME}\":\"${API_KEY}\""
            FIRST=false
        else
            MODEL_CONFIG="${MODEL_CONFIG},\"${MODEL_NAME}\":\"${API_KEY}\""
        fi
    done
    MODEL_CONFIG="${MODEL_CONFIG}}"
    
    # 写入配置文件
    cat > "$ENV_FILE" << EOF
# OpenDify 生产环境配置
# 生成时间: $(date)

# Dify API 配置
DIFY_API_BASE="${DIFY_API_BASE}"

# 模型配置 (JSON格式，必须单行)
MODEL_CONFIG='${MODEL_CONFIG}'

# 服务器配置
SERVER_HOST="0.0.0.0"
SERVER_PORT=5000

# 其他配置
# LOG_LEVEL=INFO
EOF
    
    echo -e "${GREEN}✅ 配置文件已创建: $ENV_FILE${NC}"
    echo ""
    echo "配置内容:"
    cat "$ENV_FILE" | grep -v "^#" | grep -v "^$"
}

# 部署容器
deploy() {
    echo -e "${GREEN}🚀 部署 OpenDify${NC}"
    
    # 检查环境文件
    if [ ! -f "$ENV_FILE" ]; then
        echo -e "${RED}❌ 环境文件不存在: $ENV_FILE${NC}"
        echo "请先运行: $0 setup"
        exit 1
    fi
    
    # 检查镜像
    if ! docker images | grep -q "${IMAGE_NAME%:*}"; then
        echo -e "${RED}❌ Docker 镜像不存在: $IMAGE_NAME${NC}"
        echo "请先加载镜像: docker load < opendify.tar.gz"
        exit 1
    fi
    
    # 停止旧容器
    if docker ps -a | grep -q "$CONTAINER_NAME"; then
        echo "停止并删除旧容器..."
        docker stop "$CONTAINER_NAME" 2>/dev/null || true
        docker rm "$CONTAINER_NAME" 2>/dev/null || true
    fi
    
    # 启动新容器
    echo "启动容器..."
    docker run -d \
        --name "$CONTAINER_NAME" \
        -p "${PORT}:5000" \
        --env-file "$ENV_FILE" \
        --restart unless-stopped \
        --health-cmd "curl -f http://localhost:5000/v1/models || exit 1" \
        --health-interval 30s \
        --health-timeout 10s \
        --health-retries 3 \
        "$IMAGE_NAME"
    
    echo -e "${GREEN}✅ 部署完成!${NC}"
    echo ""
    
    # 等待健康检查
    echo "等待服务启动..."
    sleep 5
    
    # 检查状态
    check_status
}

# 更新部署
update() {
    echo -e "${GREEN}🔄 更新 OpenDify${NC}"
    
    # 加载新镜像
    if [ -f "opendify.tar.gz" ]; then
        echo "加载新镜像..."
        docker load < opendify.tar.gz
    fi
    
    # 重新部署
    deploy
}

# 检查状态
check_status() {
    echo -e "${GREEN}📊 检查服务状态${NC}"
    
    # 容器状态
    if docker ps | grep -q "$CONTAINER_NAME"; then
        echo -e "容器状态: ${GREEN}运行中${NC}"
        
        # 健康检查
        HEALTH=$(docker inspect --format='{{.State.Health.Status}}' "$CONTAINER_NAME" 2>/dev/null || echo "unknown")
        if [ "$HEALTH" = "healthy" ]; then
            echo -e "健康状态: ${GREEN}健康${NC}"
        else
            echo -e "健康状态: ${YELLOW}$HEALTH${NC}"
        fi
        
        # API 测试
        echo ""
        echo "测试 API..."
        if curl -s "http://localhost:${PORT}/v1/models" | grep -q "data"; then
            echo -e "API 状态: ${GREEN}正常${NC}"
            echo ""
            echo "可用模型:"
            curl -s "http://localhost:${PORT}/v1/models" | python -m json.tool | grep '"id"' | cut -d'"' -f4 | sed 's/^/  - /'
        else
            echo -e "API 状态: ${RED}异常${NC}"
        fi
    else
        echo -e "容器状态: ${RED}未运行${NC}"
    fi
}

# 查看日志
view_logs() {
    echo -e "${GREEN}📋 查看日志${NC}"
    docker logs -f "$CONTAINER_NAME"
}

# 停止服务
stop_service() {
    echo -e "${YELLOW}⏹️  停止服务${NC}"
    docker stop "$CONTAINER_NAME"
    echo -e "${GREEN}✅ 服务已停止${NC}"
}

# 解析参数
COMMAND=$1
shift

while [[ $# -gt 0 ]]; do
    case $1 in
        --env-file)
            ENV_FILE="$2"
            shift 2
            ;;
        --port)
            PORT="$2"
            shift 2
            ;;
        *)
            echo -e "${RED}未知选项: $1${NC}"
            show_help
            exit 1
            ;;
    esac
done

# 执行命令
case $COMMAND in
    setup)
        setup_env
        ;;
    deploy)
        deploy
        ;;
    update)
        update
        ;;
    status)
        check_status
        ;;
    logs)
        view_logs
        ;;
    stop)
        stop_service
        ;;
    help|--help|-h|"")
        show_help
        ;;
    *)
        echo -e "${RED}未知命令: $COMMAND${NC}"
        show_help
        exit 1
        ;;
esac