# OpenDify 配置指南

## 配置概述

OpenDify 使用环境变量进行配置，支持多种部署方式的灵活配置。本指南详细说明了所有配置选项和最佳实践。

## 环境变量配置

### 必需配置

#### DIFY_API_BASE
Dify API 的基础URL地址。

```bash
DIFY_API_BASE="https://api.dify.ai/v1"
# 或者私有部署的地址
DIFY_API_BASE="https://your-dify-instance.com/v1"
```

**注意事项**:
- 必须是完整的 URL，包含协议 (http/https)
- 路径必须以 `/v1` 结尾
- 不支持带端口号的 IP 地址格式

#### MODEL_CONFIG
模型配置，定义可用的模型和对应的 Dify API 密钥。

```bash
MODEL_CONFIG='{"claude-3-5-sonnet-v2":"app-xxxxxx","gemini-2.0-flash":"app-yyyyyy"}'
```

**格式要求**:
- 必须是有效的 JSON 字符串
- 必须在单行内（python-dotenv 限制）
- 键是模型名称，值是对应的 Dify 应用 API 密钥
- API 密钥格式通常为 `app-` 开头的字符串

### 可选配置

#### SERVER_HOST
服务器监听地址。

```bash
SERVER_HOST="127.0.0.1"  # 默认，仅本地访问
SERVER_HOST="0.0.0.0"    # 允许外部访问，适用于容器部署
```

#### SERVER_PORT
服务器监听端口。

```bash
SERVER_PORT=5000  # 默认端口
SERVER_PORT=8080  # 自定义端口
```

## 配置文件示例

### .env 文件模板
```bash
# Dify API 配置
DIFY_API_BASE="https://api.dify.ai/v1"

# 模型配置 - 必须是单行JSON格式
MODEL_CONFIG='{"claude-3-5-sonnet-20241022":"app-abcd1234","gpt-4":"app-efgh5678","gemini-pro":"app-ijkl9012"}'

# 服务器配置
SERVER_HOST="127.0.0.1"
SERVER_PORT=5000
```

### 生产环境配置
```bash
# 生产环境 .env 示例
DIFY_API_BASE="https://your-production-dify.com/v1"
MODEL_CONFIG='{"production-claude":"app-prod-1234","production-gpt":"app-prod-5678"}'
SERVER_HOST="0.0.0.0"
SERVER_PORT=5000
```

## 模型配置详解

### 获取 Dify API 密钥

1. **登录 Dify 平台**
   - 访问 [Dify 官网](https://dify.ai) 或你的私有部署地址
   - 使用账号登录

2. **创建应用**
   - 进入工作室 (Studio)
   - 点击"创建应用"
   - 选择应用类型（通常选择"聊天助手"）

3. **配置模型**
   - 在应用设置中选择要使用的模型（如 Claude、GPT-4、Gemini 等）
   - 配置提示词和参数
   - 保存配置

4. **发布应用**
   - 点击"发布"按钮
   - 确认发布设置

5. **获取 API 密钥**
   - 进入"访问 API"页面
   - 生成或查看 API 密钥
   - 密钥格式通常为 `app-xxxxxxxxxx`

### 模型配置策略

#### 单模型配置
```bash
MODEL_CONFIG='{"claude-3-5-sonnet":"app-your-api-key"}'
```

#### 多模型配置
```bash
MODEL_CONFIG='{"claude-3-5-sonnet":"app-key1","gpt-4":"app-key2","gemini-pro":"app-key3"}'
```

#### 专用模型配置
```bash
MODEL_CONFIG='{"translator":"app-translate-key","coder":"app-code-key","analyst":"app-analysis-key"}'
```

### 模型命名建议

1. **使用标准名称**: 使用通用的模型标识符
   ```json
   {
     "claude-3-5-sonnet-20241022": "app-xxx",
     "gpt-4-turbo": "app-yyy",
     "gemini-1.5-pro": "app-zzz"
   }
   ```

2. **使用功能名称**: 根据应用用途命名
   ```json
   {
     "translator": "app-xxx",
     "code-reviewer": "app-yyy", 
     "data-analyst": "app-zzz"
   }
   ```

3. **使用环境标识**: 区分不同环境
   ```json
   {
     "prod-claude": "app-xxx",
     "dev-claude": "app-yyy",
     "test-claude": "app-zzz"
   }
   ```

## 配置验证

### 启动时验证
OpenDify 在启动时会自动验证配置：

```
✅ Configuration validation passed
✅ Loaded 3 model(s): claude-3-5-sonnet, gpt-4, gemini-pro  
✅ Dify API base: https://api.dify.ai/v1
```

### 常见验证错误

#### 1. DIFY_API_BASE 错误
```
❌ DIFY_API_BASE is not set or empty
❌ DIFY_API_BASE must be a valid URL, got: invalid-url
```

**解决方案**:
- 确保设置了正确的 URL
- 包含协议前缀 (http:// 或 https://)

#### 2. MODEL_CONFIG 错误
```
❌ No valid models configured in MODEL_CONFIG
❌ Failed to parse MODEL_CONFIG as JSON
❌ Empty API key for model: claude-3-5-sonnet
```

**解决方案**:
- 检查 JSON 格式是否正确
- 确保所有模型都有对应的 API 密钥
- 使用在线 JSON 验证工具检查格式

### 手动验证
```bash
# 检查配置文件
cat .env

# 验证 JSON 格式
echo $MODEL_CONFIG | python -m json.tool

# 测试服务器连通性
curl http://localhost:5000/v1/models
```

## Docker 配置

### Docker Run
```bash
docker run -p 5000:5000 \
  -e DIFY_API_BASE="https://api.dify.ai/v1" \
  -e MODEL_CONFIG='{"claude":"app-xxx"}' \
  -e SERVER_HOST="0.0.0.0" \
  opendify:latest
```

### Docker Compose
```yaml
version: '3.8'
services:
  opendify:
    build: .
    ports:
      - "5000:5000"
    environment:
      - DIFY_API_BASE=${DIFY_API_BASE}
      - MODEL_CONFIG=${MODEL_CONFIG}
      - SERVER_HOST=0.0.0.0
      - SERVER_PORT=5000
    env_file:
      - .env
```

### 环境变量文件
```bash
# .env 文件
DIFY_API_BASE=https://api.dify.ai/v1
MODEL_CONFIG={"claude":"app-xxx","gpt":"app-yyy"}
```

## 高级配置

### HTTP 客户端配置
在 `main.py` 中可以调整 HTTP 客户端参数：

```python
HTTP_CLIENT_CONFIG = {
    "timeout": 30.0,                    # 请求超时时间
    "limits": httpx.Limits(
        max_keepalive_connections=20,   # 最大保持连接数
        max_connections=100             # 最大连接数
    ),
    "follow_redirects": True           # 跟随重定向
}
```

### 日志配置
```python
logging.basicConfig(
    level=logging.DEBUG,               # 日志级别
    format='%(asctime)s - %(levelname)s - %(message)s'
)
```

### 会话管理配置
```python
# 会话映射存储文件
storage_file = "data/conversation_mappings.json"

# 自动清理配置
max_age_days = 30  # 会话映射保留天数
```

## 安全配置

### API 密钥保护
1. **使用环境变量**: 不要在代码中硬编码 API 密钥
2. **文件权限**: 确保 `.env` 文件权限正确 (600)
3. **版本控制**: 将 `.env` 添加到 `.gitignore`

```bash
# 设置文件权限
chmod 600 .env

# 添加到 .gitignore
echo ".env" >> .gitignore
```

### 网络安全
```bash
# 仅本地访问
SERVER_HOST="127.0.0.1"

# 使用反向代理
# 配置 nginx 或其他代理服务器处理外部访问
```

## 故障排除

### 配置问题诊断

#### 1. 检查环境变量
```bash
# 检查是否正确加载
env | grep DIFY
env | grep MODEL_CONFIG
env | grep SERVER
```

#### 2. 验证 JSON 格式
```bash
# 使用 Python 验证
python -c "import json; print(json.loads('$MODEL_CONFIG'))"

# 使用 jq 验证
echo $MODEL_CONFIG | jq .
```

#### 3. 测试 API 连接
```bash
# 测试 Dify API 连接
curl -H "Authorization: Bearer app-your-key" \
     $DIFY_API_BASE/chat-messages

# 测试 OpenDify 服务
curl http://localhost:5000/v1/models
```

### 常见问题解决

#### 问题 1: 模型列表为空
```bash
# 检查
curl http://localhost:5000/v1/models

# 可能原因
- MODEL_CONFIG 格式错误
- API 密钥无效
- DIFY_API_BASE 错误
```

#### 问题 2: 连接超时
```bash
# 可能原因
- DIFY_API_BASE 不可访问
- 网络连接问题
- 防火墙阻止
```

#### 问题 3: 认证失败
```bash
# 可能原因
- API 密钥已过期
- 密钥权限不足
- 应用未发布
```

## 配置最佳实践

### 1. 环境分离
```bash
# 开发环境
cp .env.example .env.dev

# 生产环境  
cp .env.example .env.prod

# 测试环境
cp .env.example .env.test
```

### 2. 配置管理
```bash
# 使用配置管理工具
- Docker secrets
- Kubernetes ConfigMaps
- HashiCorp Vault
- AWS Parameter Store
```

### 3. 监控配置
```bash
# 添加健康检查
- 定期检查 API 密钥有效性
- 监控 Dify API 连接状态
- 记录配置变更日志
```

### 4. 备份策略
```bash
# 备份重要配置
- 定期备份 .env 文件
- 版本控制配置变更
- 文档化配置决策
```