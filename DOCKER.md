# OpenDify Docker 部署指南

## 🚀 快速开始

### 1. 准备配置文件
```bash
cp .env.example .env
# 编辑.env文件，配置你的DIFY_API_BASE和MODEL_CONFIG
```

### 2. 构建镜像
```bash
./build.sh
# 或者手动构建
docker build -t opendify:latest .
```

### 3. 运行容器

#### 方式1: 使用部署脚本（推荐）
```bash
# 交互式安全配置
./deploy.sh setup

# 一键部署
./deploy.sh deploy

# 查看状态
./deploy.sh status
```

#### 方式2: 直接运行
```bash
docker run -p 5000:5000 --env-file .env opendify:latest
```

#### 方式3: 使用docker-compose
```bash
docker-compose up -d
```

## 🔧 高级配置

### 环境变量
- `SERVER_HOST`: 服务器监听地址 (默认: 127.0.0.1，Docker中建议使用0.0.0.0)
- `SERVER_PORT`: 服务器端口 (默认: 5000)
- `DIFY_API_BASE`: Dify API基础URL
- `MODEL_CONFIG`: 模型配置JSON字符串

### Docker Compose配置

#### 基本运行
```bash
docker-compose up -d
```

#### 带Nginx反向代理
```bash
docker-compose --profile with-nginx up -d
```

### 生产环境部署建议

#### 使用部署脚本（最佳实践）

1. **安全配置**: 使用 `./deploy.sh setup` 交互式创建配置
2. **自动化部署**: 使用 `./deploy.sh deploy` 一键部署
3. **健康监控**: 使用 `./deploy.sh status` 监控服务状态
4. **简化更新**: 使用 `./deploy.sh update` 更新服务

#### 传统部署方式

1. **资源限制**: 根据实际需求调整CPU和内存限制
2. **日志管理**: 配置日志轮转
3. **监控**: 使用健康检查端点 `/v1/models`
4. **安全**: 使用HTTPS和适当的防火墙规则

#### 部署脚本优势

- ✅ **零配置泄露**: 敏感信息不出现在代码中
- ✅ **自动验证**: 自动检查服务健康状态
- ✅ **多环境支持**: 支持开发、测试、生产环境
- ✅ **简化运维**: 提供完整的服务管理命令

### 健康检查
```bash
# 检查服务状态（使用部署脚本）
./deploy.sh status

# 手动检查 API 可用性
curl http://localhost:5000/v1/models
```

### 查看日志
```bash
docker-compose logs -f opendify
```

## 🛠️ 故障排除

### 常见问题

1. **连接超时**: 检查DIFY_API_BASE配置
2. **端口占用**: 修改docker-compose.yml中的端口映射
3. **配置错误**: 检查.env文件格式

### 调试模式
```bash
# 进入容器查看
docker exec -it <container_id> /bin/bash

# 查看详细日志
docker-compose logs --follow opendify
```