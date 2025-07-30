# OpenDify 项目文档

## 项目概述

OpenDify 是一个将 Dify API 转换为 OpenAI API 格式的代理服务器，允许使用标准的 OpenAI API 客户端直接与 Dify 服务进行交互。该项目完全由 AI 辅助编程工具（Cursor + Claude-3.5）自动生成。

## 核心功能

### API 转换
- **OpenAI to Dify**: 将 OpenAI Chat Completions API 格式转换为 Dify API 格式
- **Dify to OpenAI**: 将 Dify 响应转换回 OpenAI 标准格式
- **模型映射**: 支持多个模型配置，每个模型对应一个 Dify 应用

### 流式响应优化
- **智能缓冲**: 动态调整输出速度，提供流畅的用户体验
- **延迟控制**: 根据缓冲区大小自动计算最优延迟
- **实时处理**: 支持 Server-Sent Events (SSE) 流式输出

### 会话管理
- **对话映射**: 自动管理 Open WebUI chat_id 与 Dify conversation_id 的映射关系
- **用户识别**: 智能提取和管理用户标识，支持多种用户ID来源
- **持久化存储**: 映射关系保存在 `data/conversation_mappings.json`
- **会话清理**: 支持自动清理过期的会话映射

## 技术架构

### 核心组件

#### 1. Flask Web 服务器 (`main.py`)
- **端点**:
  - `POST /v1/chat/completions` - 聊天完成API
  - `GET /v1/models` - 获取可用模型列表
  - `GET /v1/conversation/mappings` - 查看会话映射状态（调试用）
  - `POST /v1/conversation/cleanup` - 清理旧会话映射

#### 2. ConversationMapper 类
- **功能**: 管理 Open WebUI 与 Dify 之间的会话映射
- **存储**: JSON 文件持久化
- **线程安全**: 使用锁机制保证并发安全
- **方法**:
  - `get_dify_conversation_id()` - 获取 Dify 会话ID
  - `set_mapping()` - 设置映射关系
  - `cleanup_old_mappings()` - 清理过期映射

#### 3. 用户标识管理
- **多源提取**: 支持从 HTTP 头部、请求体、元数据提取用户ID
- **优先级机制**: OpenAI user 字段 > Open WebUI 头部 > 默认值
- **智能识别**: 自动识别 Open WebUI 用户标识格式
- **函数**:
  - `extract_webui_user_id()` - 提取 Open WebUI 用户ID
  - `extract_webui_chat_id()` - 提取 Open WebUI 会话ID

#### 4. HTTP 客户端管理
- **连接池**: 使用 httpx 客户端复用连接
- **超时控制**: 30秒请求超时
- **错误处理**: 完整的异常捕获和处理

### 数据流程

```
OpenAI Client → OpenDify → Dify API
     ↑                         ↓
     ←─── Response Transform ←───
```

1. **请求接收**: 客户端发送 OpenAI 格式请求
2. **身份识别**: 提取用户ID和会话ID（支持多种来源）
3. **请求转换**: 转换为 Dify API 格式，包含正确的用户标识
4. **会话映射**: 处理 Open WebUI chat_id 到 Dify conversation_id 映射
5. **API 调用**: 调用 Dify API
6. **响应转换**: 将 Dify 响应转换为 OpenAI 格式
7. **流式输出**: 优化的流式响应处理

## 配置系统

### 环境变量
- `MODEL_CONFIG`: JSON 格式的模型配置 `{"model_name": "api_key"}`
- `DIFY_API_BASE`: Dify API 基础URL
- `SERVER_HOST`: 服务器监听地址（默认 127.0.0.1）
- `SERVER_PORT`: 服务器端口（默认 5000）

### 模型配置示例
```json
{
  "claude-3-5-sonnet-v2": "app-xxxxxx",
  "gemini-2.0-flash": "app-yyyyyy"
}
```

## 部署方案

### 1. 直接运行
```bash
pip install -r requirements.txt
python main.py
```

### 2. Docker 容器
```bash
docker build -t opendify .
docker run -p 5000:5000 --env-file .env opendify
```

### 3. Docker Compose
```bash
# 基础服务
docker-compose up -d

# 带 Nginx 反向代理
docker-compose --profile with-nginx up -d
```

## 安全特性

### 容器安全
- 非 root 用户运行
- 最小化基础镜像
- 健康检查机制

### 网络安全
- Nginx 反向代理支持
- 请求限流配置
- HTTPS 支持（通过 Nginx）

### 数据安全
- API 密钥环境变量保护
- 会话数据本地存储
- 无敏感信息日志

## 监控和维护

### 健康检查
- Docker 容器健康检查
- 模型可用性检测
- API 响应时间监控

### 日志系统
- 详细的请求/响应日志
- 错误追踪和调试信息
- 结构化日志格式

### 性能优化
- HTTP 连接池复用
- 智能缓冲区管理
- 动态延迟调整

## 扩展性

### 模型支持
- 动态模型配置
- 多 Dify 应用支持
- 自定义模型名称

### 协议兼容
- 完整 OpenAI API 兼容
- 流式响应支持
- 错误码标准化

### 部署灵活性
- 多种部署方式
- 环境配置分离
- 容器化支持

## 开发指南

### 项目结构
```
OpenDify/
├── main.py                 # 主应用程序
├── requirements.txt        # Python 依赖
├── Dockerfile             # Docker 镜像构建
├── docker-compose.yml     # Docker Compose 配置
├── nginx.conf             # Nginx 配置
├── build.sh              # 构建脚本
├── test_api.py           # API 测试脚本
└── docs/                 # 项目文档
```

### 测试
```bash
# 运行 API 测试
python test_api.py

# 测试指定服务器
python test_api.py http://localhost:5000/v1
```

### 调试
- 开启 Flask 调试模式 (`debug=True`)
- 设置日志级别为 DEBUG
- 使用 httpx 详细日志

## 故障排除

### 常见问题
1. **配置验证失败**: 检查 MODEL_CONFIG 格式和 DIFY_API_BASE
2. **连接超时**: 验证 Dify API 可访问性
3. **会话映射失败**: 检查 data 目录权限
4. **流式响应中断**: 检查网络稳定性和超时配置

### 调试命令
```bash
# 查看容器日志
docker-compose logs -f opendify

# 进入容器调试
docker exec -it <container_id> /bin/bash

# 测试 API 连通性
curl http://localhost:5000/v1/models
```

## 贡献指南

### 代码规范
- Python PEP 8 规范
- 完整的错误处理
- 详细的日志记录
- 类型提示支持

### 测试要求
- API 功能测试
- 错误场景覆盖
- 性能基准测试

### 文档要求
- 功能变更文档
- API 接口文档
- 部署指南更新

## 许可证

MIT License - 详见 LICENSE 文件