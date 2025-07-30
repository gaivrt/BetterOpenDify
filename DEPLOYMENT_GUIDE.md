# OpenDify 部署指南

本文档介绍两种部署 OpenDify 的方法：镜像传输部署和 Docker Compose 直接部署。

## 方法一：镜像传输部署（推荐）

适用于服务器网络环境较差或无法访问 Docker Hub 的情况。

### 本地操作

#### 1. 构建镜像
```bash
cd /path/to/OpenDify
docker build -t opendify .
```

#### 2. 导出镜像
```bash
# 运行导出脚本
./export_image.sh

# 或手动导出
docker save opendify | gzip > opendify.tar.gz
```

#### 3. 上传到服务器
```bash
# 使用 scp
scp opendify.tar.gz user@server:/home/user/

# 使用 rsync（支持断点续传）
rsync -avP opendify.tar.gz user@server:/home/user/
```

### 服务器操作

#### 1. 加载镜像
```bash
# 加载镜像
docker load < opendify.tar.gz

# 验证镜像
docker images | grep opendify
```

#### 2. 准备配置文件
创建 `.env` 文件：
```bash
# Dify API 配置
DIFY_API_BASE=http://dify.ai-role.cn/v1
DIFY_API_KEYS=app-your-api-key

# 模型配置
MODEL_CONFIG={"模型名称": "app-your-api-key"}

# 服务器配置
SERVER_HOST=0.0.0.0
SERVER_PORT=5000

# 其他配置
CONVERSATION_MEMORY_MODE=1
VALID_API_KEYS=sk-abc123
```

#### 3. 运行容器
```bash
# 使用运行脚本
./run_docker.sh

# 或手动运行
docker run -d \
    --name opendify \
    -p 5000:5000 \
    -e SERVER_HOST=0.0.0.0 \
    -e SERVER_PORT=5000 \
    --env-file .env \
    --restart unless-stopped \
    opendify
```

#### 4. 验证部署
```bash
# 检查容器状态
docker ps | grep opendify

# 查看日志
docker logs -f opendify

# 测试 API
curl http://localhost:5000/v1/models
python test_api.py
```

## 方法二：Docker Compose 部署

适用于网络环境良好的服务器。

### 1. 准备文件
确保服务器上有以下文件：
- `docker-compose.yml`
- `Dockerfile`
- `main.py`
- `requirements.txt`
- `.env`
- `nginx.conf`（可选）

### 2. 配置环境变量
编辑 `.env` 文件（同方法一）。

### 3. 使用 Docker Compose 部署

#### 基础部署
```bash
# 启动服务
docker-compose up -d

# 或使用运行脚本
./run_compose.sh
```

#### 带 Nginx 反向代理部署
```bash
# 启动服务和 Nginx
docker-compose --profile with-nginx up -d
```

### 4. 管理服务
```bash
# 查看状态
docker-compose ps

# 查看日志
docker-compose logs -f

# 停止服务
docker-compose down

# 重启服务
docker-compose restart

# 更新服务（修改代码后）
docker-compose build
docker-compose up -d
```

## 端口配置说明

### 默认端口
- API 服务：5000
- Nginx（可选）：80, 443

### 修改端口
如果 5000 端口被占用：

1. 修改 `.env`：
```bash
SERVER_PORT=5001
```

2. 修改 Docker 命令：
```bash
# 方法一：手动运行
docker run -p 5001:5001 -e SERVER_PORT=5001 ...

# 方法二：修改 docker-compose.yml
ports:
  - "5001:5001"
```

## 故障排除

### 1. 连接被拒绝
- 检查端口是否被占用：`lsof -i:5000`
- 确认 SERVER_HOST=0.0.0.0
- 检查防火墙设置

### 2. 镜像加载失败
- 检查磁盘空间：`df -h`
- 清理旧镜像：`docker image prune`

### 3. 服务启动失败
- 查看详细日志：`docker logs opendify`
- 检查 .env 配置
- 验证 Dify API 可访问性

### 4. Docker Compose 找不到命令
```bash
# 安装 Docker Compose（需要 sudo）
sudo yum install docker-compose-plugin

# 或下载到用户目录
mkdir -p ~/bin
curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o ~/bin/docker-compose
chmod +x ~/bin/docker-compose
export PATH="$HOME/bin:$PATH"
```

## 生产环境建议

1. **使用 Nginx 反向代理**
   - 提供 SSL 支持
   - 负载均衡
   - 静态文件缓存

2. **资源限制**
   - CPU：1 核心
   - 内存：512MB-1GB

3. **日志管理**
   ```bash
   # 限制日志大小
   docker run --log-opt max-size=10m --log-opt max-file=3 ...
   ```

4. **监控**
   - 使用 `docker stats` 监控资源
   - 配置健康检查

## 更新部署

### 方法一更新
1. 本地重新构建镜像
2. 导出并上传新镜像
3. 服务器执行：
   ```bash
   docker stop opendify
   docker rm opendify
   docker rmi opendify:latest
   docker load < opendify.tar.gz
   ./run_docker.sh
   ```

### 方法二更新
```bash
# 拉取最新代码
git pull

# 重新构建并启动
docker-compose build
docker-compose up -d
```

## 安全建议

1. 修改默认 API 密钥
2. 使用强密码
3. 限制端口访问（防火墙）
4. 定期更新镜像
5. 使用 HTTPS（通过 Nginx）