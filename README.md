# OpenDify

OpenDify 是一个将 Dify API 转换为 OpenAI API 格式的代理服务器。它允许使用 OpenAI API 客户端直接与 Dify 服务进行交互。

> 🌟 本项目完全由 Cursor + Claude-3.5 自动生成，未手动编写任何代码（包括此Readme），向 AI 辅助编程的未来致敬！

## 功能特点

- 完整支持 OpenAI API 格式转换为 Dify API
- 支持流式输出（Streaming）
- 智能动态延迟控制，提供流畅的输出体验
- 支持多个模型配置
- 完整的错误处理和日志记录
- 兼容标准的 OpenAI API 客户端
- 灵活的模型配置支持

## 支持的模型

支持任意 Dify 模型，只需在配置文件中添加对应的 API Key 即可。

## 快速开始

### 环境要求

- Python 3.9+
- pip

### 安装依赖

```bash
pip install -r requirements.txt
```

### 配置

1. 复制 `.env.example` 文件并重命名为 `.env`：
```bash
cp .env.example .env
```

2. 在 Dify 平台配置应用：
   - 登录 Dify 平台，进入工作室
   - 点击"创建应用"，配置好需要的模型（如 Claude、Gemini 等）
   - 配置应用的提示语和其他参数
   - 发布应用
   - 进入"访问 API"页面，生成 API 密钥

   > **重要说明**：Dify 不支持在请求时动态传入提示词、切换模型及其他参数。所有这些配置都需要在创建应用时设置好。Dify 会根据 API 密钥来确定使用哪个应用及其对应的配置。

3. 在 `.env` 文件中配置你的 Dify 模型和 API Keys：
```env
# Dify Model Configurations
# 注意：必须是单行的 JSON 字符串格式
MODEL_CONFIG={"claude-3-5-sonnet-v2":"your-claude-api-key","custom-model":"your-custom-api-key"}

# Dify API Base URL
DIFY_API_BASE="https://your-dify-api-base-url/v1"

# Server Configuration
SERVER_HOST="127.0.0.1"
SERVER_PORT=5000
```

你可以根据需要添加或删除模型配置，但必须保持 JSON 格式在单行内。这是因为 python-dotenv 的限制。

每个模型配置的格式为：`"模型名称": "Dify应用的API密钥"`。其中：
- 模型名称：可以自定义，用于在 API 调用时识别不同的应用
- API 密钥：从 Dify 平台获取的应用 API 密钥

例如，如果你在 Dify 上创建了一个使用 Claude 的翻译应用和一个使用 Gemini 的代码助手应用，可以这样配置：
```env
MODEL_CONFIG={"translator":"app-xxxxxx","code-assistant":"app-yyyyyy"}
```

### 运行服务

#### 方式1: 生产环境部署（推荐）

使用 Gunicorn 启动生产服务：

```bash
# 安装依赖
make install

# 启动生产服务
make prod
```

#### 方式2: 开发环境

启动开发服务（支持热重载）：

```bash
# 启动开发服务
make dev
```

#### 方式3: Docker 部署（强烈推荐）

##### 快速部署（使用自动化脚本）

```bash
# 1. 构建和导出镜像
./scripts/build.sh
./scripts/export_image.sh

# 2. 上传到服务器
scp opendify.tar.gz scripts/deploy.sh user@server:/path/

# 3. 服务器上部署
ssh user@server
cd /path/
docker load < opendify.tar.gz

# 4. 交互式安全配置（不写死敏感信息）
./deploy.sh setup

# 5. 一键部署
./deploy.sh deploy

# 6. 检查状态
./deploy.sh status
```

##### 使用 Make 命令

```bash
# 生产环境
make docker-prod

# 开发环境
make docker-dev
```

#### 部署脚本功能

部署脚本 `scripts/deploy.sh` 提供完整的生产部署管理：

- ✅ **安全配置**：交互式创建配置，避免敏感信息泄露
- ✅ **健康检查**：自动验证服务启动状态
- ✅ **状态监控**：实时查看服务和API状态
- ✅ **简化更新**：一键更新部署流程
- ✅ **多环境支持**：支持测试、生产等不同环境

```bash
# 部署脚本命令
./scripts/deploy.sh setup     # 创建配置文件
./scripts/deploy.sh deploy    # 部署服务
./scripts/deploy.sh update    # 更新部署
./scripts/deploy.sh status    # 查看状态
./scripts/deploy.sh logs      # 查看日志
./scripts/deploy.sh stop      # 停止服务
```

#### 方式4: 传统方式（不推荐生产使用）

```bash
python main.py
```

服务将在 `http://127.0.0.1:5000` 启动

> 💡 **建议**: 生产环境请使用 Gunicorn 或 Docker 部署，`python main.py` 仅适用于开发调试。

## API 使用

### List Models

获取所有可用模型列表：

```python
import openai

openai.api_base = "http://127.0.0.1:5000/v1"
openai.api_key = "any"  # 可以使用任意值

# 获取可用模型列表
models = openai.Model.list()
print(models)

# 输出示例：
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
            "id": "gemini-2.0-flash-thinking-exp-1219",
            "object": "model",
            "created": 1704603847,
            "owned_by": "dify"
        },
        // ... 其他在 MODEL_CONFIG 中配置的模型
    ]
}
```

只有在 `.env` 文件的 `MODEL_CONFIG` 中配置了 API Key 的模型才会出现在列表中。

### Chat Completions

```python
import openai

openai.api_base = "http://127.0.0.1:5000/v1"
openai.api_key = "any"  # 可以使用任意值

response = openai.ChatCompletion.create(
    model="claude-3-5-sonnet-v2",  # 使用在 MODEL_CONFIG 中配置的模型名称
    messages=[
        {"role": "user", "content": "你好"}
    ],
    stream=True
)

for chunk in response:
    print(chunk.choices[0].delta.content or "", end="")
```

## 特性说明

### 流式输出优化

- 智能缓冲区管理
- 动态延迟计算
- 平滑的输出体验

### 错误处理

- 完整的错误捕获和处理
- 详细的日志记录
- 友好的错误提示

### 配置灵活性

- 支持动态添加新模型
- 支持 JSON 格式配置
- 支持自定义模型名称

## 📚 详细文档

- **[完整文档](docs/)** - 所有文档索引
- **[部署指南](docs/DEPLOYMENT.md)** - 生产环境部署
- **[API 文档](docs/API_DOCUMENTATION.md)** - 接口使用说明
- **[配置指南](docs/CONFIGURATION_GUIDE.md)** - 环境配置详解
- **[故障排除](docs/TROUBLESHOOTING.md)** - 问题诊断和解决

## 📁 项目结构

```
OpenDify/
├── main.py                    # 主应用程序
├── requirements.txt           # Python 依赖
├── gunicorn_config.py        # Gunicorn 生产配置
├── Dockerfile                # Docker 镜像构建
├── docker-compose.yml        # Docker Compose 配置
├── nginx.conf               # Nginx 反向代理配置
├── Makefile                 # Make 构建命令
├── docs/                    # 📖 项目文档
│   ├── README.md           # 文档索引
│   ├── DEPLOYMENT.md       # 部署指南
│   ├── API_DOCUMENTATION.md # API 文档
│   ├── CONFIGURATION_GUIDE.md # 配置指南
│   ├── STATE_MANAGEMENT.md  # 状态管理
│   ├── TROUBLESHOOTING.md   # 故障排除
│   └── chat-id-integration-guide.md # Chat ID 集成
├── scripts/                 # 🔧 构建和部署脚本
│   ├── README.md           # 脚本说明文档
│   ├── build.sh            # Docker 镜像构建
│   ├── export_image.sh     # 镜像导出
│   ├── deploy.sh           # 生产部署管理
│   ├── run_docker.sh       # Docker 容器运行
│   ├── run_compose.sh      # Docker Compose 运行
│   ├── start_production.sh # Gunicorn 生产启动
│   └── start_development.sh # 开发环境启动
├── tests/                   # 🧪 测试文件
│   ├── README.md           # 测试说明文档
│   ├── test_api.py         # API 兼容性测试
│   ├── manual_test.py      # 手动交互测试
│   └── test_conversation_mapping.py # 会话映射测试
└── data/                    # 💾 数据存储
    └── conversation_mappings.json # 会话映射持久化
```

## 🧪 测试

### 运行测试
```bash
# API 兼容性测试
python tests/test_api.py

# 会话映射测试
python tests/test_conversation_mapping.py

# 手动交互测试
python tests/manual_test.py
```

详细测试说明请参考 [tests/README.md](tests/README.md)。

## 🔧 开发工具

### 构建脚本
- `scripts/build.sh` - Docker 镜像构建
- `scripts/export_image.sh` - 镜像导出

### 部署脚本
- `scripts/deploy.sh` - 生产部署管理
- `scripts/start_production.sh` - Gunicorn 生产启动
- `scripts/start_development.sh` - 开发环境启动

详细脚本说明请参考 [scripts/README.md](scripts/README.md)。

## 贡献指南

欢迎提交 Issue 和 Pull Request 来帮助改进项目。

## 许可证

[MIT License](LICENSE) 