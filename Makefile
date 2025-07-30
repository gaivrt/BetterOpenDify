# OpenDify Makefile
# 简化部署和开发操作

.PHONY: help install dev prod docker-dev docker-prod clean test

# 默认目标
help:
	@echo "OpenDify 部署命令:"
	@echo ""
	@echo "开发环境:"
	@echo "  make install    - 安装依赖"
	@echo "  make dev        - 启动开发服务 (Gunicorn + 热重载)"
	@echo "  make docker-dev - 启动Docker开发环境"
	@echo ""
	@echo "生产环境:"
	@echo "  make prod       - 启动生产服务 (Gunicorn)"
	@echo "  make docker-prod- 启动Docker生产环境"
	@echo ""
	@echo "构建命令:"
	@echo "  make build      - 构建生产环境镜像"
	@echo "  make build-dev  - 构建开发环境镜像"
	@echo "  make build-all  - 构建所有镜像"
	@echo ""
	@echo "工具命令:"
	@echo "  make test       - 运行API测试"
	@echo "  make clean      - 清理临时文件"
	@echo "  make logs       - 查看Docker日志"
	@echo "  make check      - 检查配置"

# 安装依赖
install:
	@echo "📦 安装Python依赖..."
	pip install -r requirements.txt
	@echo "✅ 依赖安装完成"

# 开发环境
dev: install
	@echo "🛠️ 启动开发环境..."
	chmod +x start_development.sh
	./start_development.sh

# 生产环境
prod: install
	@echo "🚀 启动生产环境..."
	chmod +x start_production.sh
	./start_production.sh

# Docker 开发环境
docker-dev:
	@echo "🐳 启动Docker开发环境..."
	docker-compose -f docker-compose.dev.yml up -d
	@echo "✅ 开发环境已启动，访问 http://localhost:5000"

# Docker 生产环境
docker-prod:
	@echo "🐳 启动Docker生产环境..."
	docker-compose up -d
	@echo "✅ 生产环境已启动，访问 http://localhost:5000"

# 查看Docker日志
logs:
	@echo "📋 查看服务日志..."
	docker-compose logs -f

# 停止Docker服务
docker-stop:
	@echo "⏹️ 停止Docker服务..."
	docker-compose down
	docker-compose -f docker-compose.dev.yml down

# 运行测试
test:
	@echo "🧪 运行API测试..."
	python test_api.py

# 清理临时文件
clean:
	@echo "🧹 清理临时文件..."
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type f -name "*.log" -delete
	@echo "✅ 清理完成"

# 构建Docker镜像
build:
	@echo "🔨 构建生产环境Docker镜像..."
	./build.sh prod latest

# 构建开发环境镜像
build-dev:
	@echo "🔨 构建开发环境Docker镜像..."
	./build.sh dev latest

# 构建所有镜像
build-all: build build-dev
	@echo "✅ 所有镜像构建完成"

# 检查配置
check:
	@echo "🔍 检查配置..."
	@if [ -z "$$DIFY_API_BASE" ]; then \
		echo "❌ DIFY_API_BASE 未设置"; \
		exit 1; \
	fi
	@if [ -z "$$MODEL_CONFIG" ]; then \
		echo "❌ MODEL_CONFIG 未设置"; \
		exit 1; \
	fi
	@echo "✅ 配置检查通过"

# 生产环境预检查
prod-check: check
	@echo "🔍 生产环境预检查..."
	python -c "exec(open('gunicorn_config.py').read())"
	@echo "✅ Gunicorn配置正确"