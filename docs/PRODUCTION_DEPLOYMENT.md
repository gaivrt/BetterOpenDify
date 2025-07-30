# OpenDify 生产环境部署指南

## 概述

OpenDify 现在使用 **Gunicorn** 作为 WSGI 服务器进行生产部署，提供更好的性能、稳定性和扩展性。

## 部署方式对比

| 部署方式 | 适用场景 | 性能 | 稳定性 | 推荐度 |
|----------|----------|------|--------|--------|
| `python main.py` | 开发调试 | 低 | 低 | ❌ 不推荐生产使用 |
| **Gunicorn** | 生产环境 | 高 | 高 | ✅ **推荐** |
| Docker + Gunicorn | 容器化部署 | 高 | 高 | ✅ **强烈推荐** |

## 快速开始

### 方式1: 直接使用 Gunicorn

#### 安装依赖
```bash
pip install -r requirements.txt
```

#### 生产环境启动
```bash
# 设置环境变量
export DIFY_API_BASE="https://api.dify.ai/v1"
export MODEL_CONFIG='{"claude-3-5-sonnet":"app-your-key"}'

# 启动生产服务
./start_production.sh
```

#### 开发环境启动
```bash
# 开发环境（自动重载）
./start_development.sh
```

### 方式2: Docker Compose（推荐）

#### 生产环境部署
```bash
# 1. 配置环境变量
cp .env.example .env
# 编辑 .env 文件

# 2. 启动服务
docker-compose up -d

# 3. 查看日志
docker-compose logs -f opendify
```

#### 开发环境部署
```bash
# 启动开发环境（代码热重载）
docker-compose -f docker-compose.dev.yml up -d
```

## 详细配置

### Gunicorn 配置文件

配置文件：`gunicorn_config.py`

**核心配置**：
```python
# 服务器绑定
bind = "0.0.0.0:5000"

# 工作进程数（推荐：CPU核心数 * 2 + 1）
workers = multiprocessing.cpu_count() * 2 + 1

# 工作进程类型
worker_class = "sync"  # Flask 使用同步工作进程

# 超时设置
timeout = 30
keepalive = 2

# 性能优化
max_requests = 1000
max_requests_jitter = 50
preload_app = True
```

**环境特定配置**：
- **开发环境**: 单进程、热重载、调试日志
- **生产环境**: 多进程、性能优化、信息日志

### 环境变量配置

#### 服务器配置
```bash
SERVER_HOST=0.0.0.0              # 监听地址
SERVER_PORT=5000                 # 监听端口
ENVIRONMENT=production           # 环境模式
```

#### Gunicorn 配置
```bash
GUNICORN_WORKERS=4              # 工作进程数
GUNICORN_RELOAD=false           # 是否热重载
LOG_LEVEL=info                  # 日志级别
```

#### 应用配置
```bash
DIFY_API_BASE="https://api.dify.ai/v1"
MODEL_CONFIG='{"model":"api-key"}'
```

### 启动脚本详解

#### 生产启动脚本 (`start_production.sh`)
```bash
#!/bin/bash
# 检查必需环境变量
# 设置默认值
# 启动 Gunicorn 生产服务器

exec gunicorn \
    --config gunicorn_config.py \
    --bind $SERVER_HOST:$SERVER_PORT \
    --workers $GUNICORN_WORKERS \
    --worker-class sync \
    --timeout 60 \
    --keepalive 2 \
    --max-requests 2000 \
    --preload \
    main:app
```

**特性**：
- ✅ 多进程并发处理
- ✅ 请求超时控制
- ✅ 自动进程重启
- ✅ 预加载应用
- ✅ 生产级别日志

#### 开发启动脚本 (`start_development.sh`)
```bash
#!/bin/bash
# 开发环境配置
export ENVIRONMENT="development"
export GUNICORN_RELOAD="true"
export LOG_LEVEL="debug"

exec gunicorn \
    --config gunicorn_config.py \
    --workers 1 \
    --reload \
    --log-level debug \
    main:app
```

**特性**：
- ✅ 代码热重载
- ✅ 单进程调试
- ✅ 详细日志输出
- ✅ 快速启动

## Docker 部署

### 生产环境 Dockerfile
```dockerfile
FROM python:3.11-slim

# 复制应用代码和配置
COPY main.py gunicorn_config.py start_production.sh ./

# 设置环境变量
ENV ENVIRONMENT=production
ENV SERVER_HOST=0.0.0.0
ENV SERVER_PORT=5000

# 启动命令
CMD ["gunicorn", "--config", "gunicorn_config.py", "main:app"]
```

### Docker Compose 配置

#### 生产环境 (`docker-compose.yml`)
```yaml
services:
  opendify:
    build: .
    ports:
      - "5000:5000"
    environment:
      - ENVIRONMENT=production
      - GUNICORN_WORKERS=4
      - LOG_LEVEL=info
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 1G
```

#### 开发环境 (`docker-compose.dev.yml`)
```yaml
services:
  opendify-dev:
    build:
      dockerfile: Dockerfile.dev
    environment:
      - ENVIRONMENT=development
      - GUNICORN_WORKERS=1
      - GUNICORN_RELOAD=true
    volumes:
      - .:/app  # 挂载源码实现热重载
```

## 性能优化

### 工作进程数配置

**推荐公式**：
```
workers = (CPU核心数 × 2) + 1
```

**示例**：
- 4核CPU：`GUNICORN_WORKERS=9`
- 8核CPU：`GUNICORN_WORKERS=17`

### 内存优化

**配置建议**：
```python
# gunicorn_config.py
max_requests = 2000          # 每个进程处理请求数后重启
max_requests_jitter = 100    # 随机抖动避免同时重启
preload_app = True           # 预加载减少内存占用
```

### 连接优化

**应用层优化**：
```python
# main.py 中的 HTTP 客户端配置
HTTP_CLIENT_CONFIG = {
    "timeout": 30.0,
    "limits": httpx.Limits(
        max_keepalive_connections=20,
        max_connections=100
    )
}
```

## 监控和日志

### 日志配置

**Gunicorn 日志**：
```python
# 访问日志格式
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)sμs'

# 日志输出
accesslog = '-'  # stdout
errorlog = '-'   # stderr
```

**应用日志**：
```python
# main.py 中的日志配置
logging.basicConfig(
    level=logging.INFO,  # 生产环境使用 INFO 级别
    format='%(asctime)s - %(levelname)s - %(message)s'
)
```

### 健康检查

**Docker 健康检查**：
```dockerfile
HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
    CMD curl -f http://localhost:5000/v1/models || exit 1
```

**监控端点**：
```bash
# 检查服务状态
curl http://localhost:5000/v1/models

# 查看会话映射统计
curl http://localhost:5000/v1/conversation/mappings
```

### 系统监控

**推荐监控指标**：
- CPU 使用率
- 内存使用率
- 请求响应时间
- 错误率
- 并发连接数

**监控命令**：
```bash
# 查看进程状态
ps aux | grep gunicorn

# 查看端口监听
netstat -tlnp | grep 5000

# 查看资源使用
docker stats opendify
```

## 扩展部署

### 负载均衡

**Nginx 反向代理**：
```nginx
upstream opendify_backend {
    server 127.0.0.1:5000;
    server 127.0.0.1:5001;
    server 127.0.0.1:5002;
}

server {
    listen 80;
    location / {
        proxy_pass http://opendify_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

**多实例部署**：
```bash
# 启动多个实例
GUNICORN_WORKERS=4 SERVER_PORT=5000 ./start_production.sh &
GUNICORN_WORKERS=4 SERVER_PORT=5001 ./start_production.sh &
GUNICORN_WORKERS=4 SERVER_PORT=5002 ./start_production.sh &
```

### 容器编排

**Docker Swarm**：
```yaml
version: '3.8'
services:
  opendify:
    image: opendify:latest
    deploy:
      replicas: 3
      resources:
        limits:
          cpus: '0.5'
          memory: 512M
    networks:
      - opendify-network
```

**Kubernetes**：
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: opendify
spec:
  replicas: 3
  selector:
    matchLabels:
      app: opendify
  template:
    spec:
      containers:
      - name: opendify
        image: opendify:latest
        ports:
        - containerPort: 5000
        resources:
          limits:
            cpu: 500m
            memory: 512Mi
```

## 故障排除

### 常见问题

#### 1. Gunicorn 启动失败
```bash
# 检查配置文件语法
python -c "exec(open('gunicorn_config.py').read())"

# 检查端口占用
netstat -tlnp | grep 5000
```

#### 2. 进程内存泄漏
```bash
# 设置进程自动重启
max_requests = 1000  # 在 gunicorn_config.py 中设置
```

#### 3. 性能问题
```bash
# 调整工作进程数
GUNICORN_WORKERS=8 ./start_production.sh

# 监控资源使用
htop
iotop
```

### 调试模式

**启用详细日志**：
```bash
export LOG_LEVEL=debug
./start_production.sh
```

**单进程调试**：
```bash
gunicorn --workers 1 --reload --log-level debug main:app
```

## 最佳实践

### 部署检查清单

- [ ] 配置环境变量
- [ ] 设置合适的工作进程数
- [ ] 配置日志轮转
- [ ] 设置健康检查
- [ ] 配置资源限制
- [ ] 设置监控告警
- [ ] 备份会话映射数据
- [ ] 测试故障恢复

### 安全建议

1. **使用非 root 用户**运行服务
2. **设置防火墙规则**限制访问
3. **使用 HTTPS**加密传输
4. **定期更新依赖**修复安全漏洞
5. **限制资源使用**防止 DoS 攻击

### 运维建议

1. **定期备份**会话映射数据
2. **监控资源使用**及时调整配置
3. **设置日志轮转**防止磁盘满
4. **建立告警机制**快速响应问题
5. **制定恢复流程**确保服务可用性

## 命令参考

### 基本命令
```bash
# 生产环境启动
./start_production.sh

# 开发环境启动
./start_development.sh

# Docker 生产部署
docker-compose up -d

# Docker 开发部署
docker-compose -f docker-compose.dev.yml up -d
```

### 管理命令
```bash
# 查看运行状态
ps aux | grep gunicorn

# 重启服务
killall gunicorn
./start_production.sh

# 查看日志
tail -f logs/gunicorn.log

# 测试配置
gunicorn --check-config gunicorn_config.py
```

通过使用 Gunicorn，OpenDify 现在具备了生产级别的性能和稳定性，能够处理高并发请求并提供可靠的服务。