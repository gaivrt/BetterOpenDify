# OpenDify API 文档

## API 概述

OpenDify 提供与 OpenAI API 兼容的接口，允许现有的 OpenAI 客户端无缝切换到 Dify 后端。

## 基础信息

- **基础URL**: `http://localhost:5000/v1`
- **认证**: 使用任意 API Key（实际认证由 Dify 后端处理）
- **内容类型**: `application/json`

## 支持的端点

### 1. 聊天完成 (Chat Completions)

#### 请求
```http
POST /v1/chat/completions
Content-Type: application/json
Authorization: Bearer any-key

{
  "model": "claude-3-5-sonnet-v2",
  "messages": [
    {
      "role": "user",
      "content": "你好，请介绍一下你自己"
    }
  ],
  "stream": false
}
```

#### 参数说明

| 参数 | 类型 | 必需 | 说明 |
|------|------|------|------|
| `model` | string | 是 | 模型名称，必须在 MODEL_CONFIG 中配置 |
| `messages` | array | 是 | 对话消息数组 |
| `stream` | boolean | 否 | 是否启用流式响应，默认 false |
| `user` | string | 否 | 用户标识符，默认 "default_user" |

#### 消息格式
```json
{
  "role": "user|assistant|system",
  "content": "消息内容"
}
```

#### 响应格式

**非流式响应**:
```json
{
  "id": "msg_123456",
  "object": "chat.completion",
  "created": 1704603847,
  "model": "claude-3-5-sonnet-v2",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "你好！我是Claude，一个由Anthropic开发的AI助手..."
      },
      "finish_reason": "stop"
    }
  ]
}
```

**流式响应**:
```
data: {"id":"msg_123456","object":"chat.completion.chunk","created":1704603847,"model":"claude-3-5-sonnet-v2","choices":[{"index":0,"delta":{"content":"你好"},"finish_reason":null}]}

data: {"id":"msg_123456","object":"chat.completion.chunk","created":1704603847,"model":"claude-3-5-sonnet-v2","choices":[{"index":0,"delta":{"content":"！"},"finish_reason":null}]}

data: {"id":"msg_123456","object":"chat.completion.chunk","created":1704603847,"model":"claude-3-5-sonnet-v2","choices":[{"index":0,"delta":{},"finish_reason":"stop"}]}

data: [DONE]
```

### 2. 模型列表 (List Models)

#### 请求
```http
GET /v1/models
```

#### 响应
```json
{
  "object": "list",
  "data": [
    {
      "id": "claude-3-5-sonnet-v2",
      "object": "model",
      "created": 1704603847,
      "owned_by": "dify"
    },
    {
      "id": "gemini-2.0-flash",
      "object": "model",
      "created": 1704603847,
      "owned_by": "dify"
    }
  ]
}
```

### 3. 会话映射管理

#### 获取会话映射状态
```http
GET /v1/conversation/mappings
```

**响应**:
```json
{
  "mapping_count": 15,
  "oldest_mapping": 1704603847,
  "newest_mapping": 1704610000,
  "timestamp": 1704610123
}
```

#### 清理旧会话映射
```http
POST /v1/conversation/cleanup
Content-Type: application/json

{
  "max_age_days": 30
}
```

**响应**:
```json
{
  "removed_count": 5,
  "max_age_days": 30,
  "timestamp": 1704610123
}
```

## Open WebUI 集成

### Chat ID 映射

OpenDify 自动处理 Open WebUI 的会话映射：

1. **自动识别**: 从 HTTP 头部提取 `X-OpenWebUI-Chat-Id`
2. **映射管理**: 自动建立和维护 chat_id 到 conversation_id 的映射
3. **会话连续性**: 确保多轮对话的上下文连接

### 支持的头部
- `X-OpenWebUI-Chat-Id`
- `x-openwebui-chat-id`
- `X-Openwebui-Chat-Id`

## 错误处理

### 错误响应格式
```json
{
  "error": {
    "message": "错误描述",
    "type": "error_type",
    "code": "error_code"
  }
}
```

### 常见错误类型

| HTTP 状态码 | 错误类型 | 说明 |
|------------|----------|------|
| 400 | `invalid_request_error` | 请求格式错误 |
| 404 | `model_not_found` | 模型不存在或未配置 |
| 408 | `timeout_error` | 请求超时 |
| 500 | `internal_error` | 服务器内部错误 |
| 503 | `connection_error` | 连接 Dify API 失败 |

### 错误示例
```json
{
  "error": {
    "message": "Model claude-4 is not supported. Available models: claude-3-5-sonnet-v2, gemini-2.0-flash",
    "type": "invalid_request_error",
    "code": "model_not_found"
  }
}
```

## 客户端示例

### Python (OpenAI SDK)
```python
import openai

# 配置客户端
openai.api_base = "http://localhost:5000/v1"
openai.api_key = "any-key"

# 获取模型列表
models = openai.Model.list()
print(f"可用模型: {[m.id for m in models.data]}")

# 聊天对话
response = openai.ChatCompletion.create(
    model="claude-3-5-sonnet-v2",
    messages=[
        {"role": "user", "content": "你好"}
    ]
)
print(response.choices[0].message.content)

# 流式对话
response = openai.ChatCompletion.create(
    model="claude-3-5-sonnet-v2",
    messages=[
        {"role": "user", "content": "写一首关于AI的诗"}
    ],
    stream=True
)

for chunk in response:
    content = chunk.choices[0].delta.get('content')
    if content:
        print(content, end='')
```

### cURL
```bash
# 获取模型列表
curl -X GET "http://localhost:5000/v1/models" \
  -H "Authorization: Bearer any-key"

# 聊天请求
curl -X POST "http://localhost:5000/v1/chat/completions" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer any-key" \
  -d '{
    "model": "claude-3-5-sonnet-v2",
    "messages": [
      {"role": "user", "content": "你好"}
    ],
    "stream": false
  }'

# 流式聊天
curl -X POST "http://localhost:5000/v1/chat/completions" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer any-key" \
  -H "Accept: text/event-stream" \
  -d '{
    "model": "claude-3-5-sonnet-v2",
    "messages": [
      {"role": "user", "content": "你好"}
    ],
    "stream": true
  }'
```

### JavaScript (Node.js)
```javascript
const OpenAI = require('openai');

const openai = new OpenAI({
  baseURL: 'http://localhost:5000/v1',
  apiKey: 'any-key'
});

async function chat() {
  const response = await openai.chat.completions.create({
    model: 'claude-3-5-sonnet-v2',
    messages: [{ role: 'user', content: '你好' }],
  });
  
  console.log(response.choices[0].message.content);
}

async function streamChat() {
  const stream = await openai.chat.completions.create({
    model: 'claude-3-5-sonnet-v2',
    messages: [{ role: 'user', content: '写一首诗' }],
    stream: true,
  });
  
  for await (const chunk of stream) {
    const content = chunk.choices[0]?.delta?.content || '';
    process.stdout.write(content);
  }
}
```

## 性能优化

### 流式响应优化
- **智能缓冲**: 根据缓冲区大小动态调整输出速度
- **延迟计算**: 自动优化用户体验
- **连接复用**: HTTP 连接池减少延迟

### 缓冲策略
```
缓冲区大小 > 30 字符: 1ms 延迟
缓冲区大小 > 20 字符: 2ms 延迟  
缓冲区大小 > 10 字符: 10ms 延迟
缓冲区大小 <= 10 字符: 20ms 延迟
```

## 监控和调试

### 健康检查
```bash
curl http://localhost:5000/v1/models
```

### 日志级别
- `INFO`: 基础请求信息
- `DEBUG`: 详细调试信息
- `ERROR`: 错误和异常信息

### 调试头部
请求中包含所有头部信息的调试日志，便于排查 Open WebUI 集成问题。

## 最佳实践

### 模型配置
1. 在 Dify 平台预先配置好所有模型应用
2. 确保 API 密钥有效且有足够权限
3. 使用描述性的模型名称便于识别

### 错误处理
1. 始终检查响应状态码
2. 实现适当的重试机制
3. 记录详细的错误信息

### 性能优化
1. 使用连接池复用连接
2. 合理设置超时时间
3. 启用流式响应提升用户体验

### 安全考虑
1. 不在日志中记录敏感信息
2. 使用 HTTPS 加密传输
3. 定期清理过期的会话映射