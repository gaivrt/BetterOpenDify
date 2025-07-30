# OpenDify 脚本工具

本目录包含 OpenDify 项目的所有构建、部署和运行脚本。

## 脚本文件说明

### 构建相关脚本

#### `build.sh`
- **功能**: 构建 Docker 镜像
- **用途**: 自动化 Docker 镜像构建过程
- **运行**: `./scripts/build.sh`
- **输出**: 生成 `opendify:latest` Docker 镜像

#### `export_image.sh`
- **功能**: 导出 Docker 镜像
- **用途**: 将构建的镜像导出为 tar.gz 文件
- **运行**: `./scripts/export_image.sh`
- **输出**: 生成 `opendify.tar.gz` 镜像文件

### 部署相关脚本

#### `deploy.sh`
- **功能**: 生产环境部署管理
- **用途**: 提供完整的部署生命周期管理
- **特性**:
  - ✅ 交互式安全配置
  - ✅ 自动健康检查
  - ✅ 状态监控
  - ✅ 简化更新流程

**可用命令**:
```bash
./scripts/deploy.sh setup     # 创建配置文件
./scripts/deploy.sh deploy    # 部署服务
./scripts/deploy.sh update    # 更新部署
./scripts/deploy.sh status    # 查看状态
./scripts/deploy.sh logs      # 查看日志
./scripts/deploy.sh stop      # 停止服务
```

### 运行相关脚本

#### `run_docker.sh`
- **功能**: 直接运行 Docker 容器
- **用途**: 快速启动单个 Docker 容器
- **运行**: `./scripts/run_docker.sh`

#### `run_compose.sh`
- **功能**: 使用 Docker Compose 运行
- **用途**: 启动完整的服务栈（包括 Nginx）
- **运行**: `./scripts/run_compose.sh`

#### `start_production.sh`
- **功能**: 生产环境 Gunicorn 启动
- **用途**: 使用 Gunicorn 启动生产服务
- **运行**: `./scripts/start_production.sh`
- **特性**: 多进程、高性能、稳定运行

#### `start_development.sh`
- **功能**: 开发环境启动
- **用途**: 启动开发模式服务（支持热重载）
- **运行**: `./scripts/start_development.sh`
- **特性**: 单进程、热重载、详细日志

## 使用流程

### 本地开发
```bash
# 开发环境启动
./scripts/start_development.sh
```

### Docker 部署
```bash
# 1. 构建镜像
./scripts/build.sh

# 2. 直接运行
./scripts/run_docker.sh

# 或使用 Compose
./scripts/run_compose.sh
```

### 生产部署
```bash
# 1. 构建和导出
./scripts/build.sh
./scripts/export_image.sh

# 2. 部署到服务器
scp opendify.tar.gz scripts/deploy.sh user@server:/path/
ssh user@server
./deploy.sh setup
./deploy.sh deploy
```

### Gunicorn 生产模式
```bash
# 直接启动生产服务
./scripts/start_production.sh
```

## 脚本特性

### 安全性
- 交互式配置，避免硬编码敏感信息
- 环境变量验证
- 错误处理和回滚机制

### 便利性
- 一键部署和更新
- 自动健康检查
- 详细的状态反馈

### 可维护性
- 标准化的脚本结构
- 详细的日志输出
- 模块化设计

## 环境要求

- **Docker**: 构建和运行相关脚本需要 Docker
- **Python 3.9+**: Gunicorn 启动脚本需要 Python
- **Bash**: 所有脚本都使用 Bash 编写
- **网络访问**: 部署脚本需要访问 Dify API

## 添加新脚本

在添加新脚本时，请：
1. 使用 `#!/bin/bash` 作为首行
2. 添加详细的注释说明
3. 实现适当的错误处理
4. 更新本 README 文件
5. 确保脚本具有执行权限 (`chmod +x`)