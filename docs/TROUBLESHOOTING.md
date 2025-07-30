# OpenDify 故障排除指南

## 常见问题诊断

### 快速诊断清单

在深入调试之前，请先检查以下基础项目：

- [ ] 服务是否正常启动（检查启动日志）
- [ ] 配置文件是否正确（`.env` 文件）
- [ ] 网络连接是否正常（能否访问 Dify API）
- [ ] API 密钥是否有效（Dify 平台检查）
- [ ] 端口是否被占用（`netstat -tulpn | grep 5000`）

## 启动问题

### 问题 1: 配置验证失败

**错误信息**:
```
❌ Configuration validation failed:
  - DIFY_API_BASE is not set or empty
  - No valid models configured in MODEL_CONFIG
❌ Startup aborted due to configuration errors
```

**解决步骤**:

1. **检查环境变量文件**:
   ```bash
   # 确保 .env 文件存在
   ls -la .env
   
   # 检查文件内容
   cat .env
   ```

2. **验证配置格式**:
   ```bash
   # 检查 DIFY_API_BASE
   echo $DIFY_API_BASE
   
   # 验证 MODEL_CONFIG JSON 格式
   echo $MODEL_CONFIG | python -m json.tool
   ```

3. **修复配置**:
   ```bash
   # 示例正确配置
   echo 'DIFY_API_BASE="https://api.dify.ai/v1"' >> .env
   echo 'MODEL_CONFIG='"'"'{"claude":"app-your-key"}'"'"'' >> .env
   ```

### 问题 2: 端口占用

**错误信息**:
```
OSError: [Errno 98] Address already in use
```

**解决步骤**:

1. **查找占用端口的进程**:
   ```bash
   netstat -tulpn | grep 5000
   # 或者
   lsof -i :5000
   ```

2. **终止占用进程**:
   ```bash
   kill -9 <PID>
   ```

3. **更改端口**:
   ```bash
   echo 'SERVER_PORT=5001' >> .env
   ```

### 问题 3: 依赖安装失败

**错误信息**:
```
ModuleNotFoundError: No module named 'flask'
```

**解决步骤**:
```bash
# 重新安装依赖
pip install -r requirements.txt

# 或者使用虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或 venv\Scripts\activate  # Windows
pip install -r requirements.txt
```

## API 连接问题

### 问题 4: Dify API 连接超时

**错误信息**:
```
❌ Stream connection timeout: timeout
❌ Request timeout: 30.0 seconds
```

**诊断步骤**:

1. **测试 Dify API 连通性**:
   ```bash
   # 测试基础连接
   curl -I $DIFY_API_BASE
   
   # 测试具体端点
   curl -H "Authorization: Bearer app-your-key" \
        $DIFY_API_BASE/chat-messages \
        -d '{"query":"test"}' \
        -H "Content-Type: application/json"
   ```

2. **检查网络配置**:
   ```bash
   # 检查 DNS 解析
   nslookup api.dify.ai
   
   # 检查路由
   traceroute api.dify.ai
   
   # 检查防火墙
   telnet api.dify.ai 443
   ```

3. **调整超时设置**:
   ```python
   # 在 main.py 中调整超时
   HTTP_CLIENT_CONFIG = {
       "timeout": 60.0,  # 增加到60秒
       # ... 其他配置
   }
   ```

### 问题 5: API 密钥认证失败

**错误信息**:
```
❌ Dify API error: {"error": "Invalid API key"}
❌ Request failed: 401 Unauthorized
```

**解决步骤**:

1. **验证 API 密钥格式**:
   ```bash
   # API 密钥应该以 app- 开头
   echo $MODEL_CONFIG | grep "app-"
   ```

2. **在 Dify 平台检查密钥**:
   - 登录 Dify 平台
   - 进入对应应用的"访问 API"页面
   - 确认密钥是否有效
   - 检查应用是否已发布

3. **测试密钥有效性**:
   ```bash
   curl -H "Authorization: Bearer app-your-actual-key" \
        https://api.dify.ai/v1/chat-messages \
        -d '{"query":"test","response_mode":"blocking","user":"test"}' \
        -H "Content-Type: application/json"
   ```

## 运行时问题

### 问题 6: 模型列表为空

**现象**:
```bash
curl http://localhost:5000/v1/models
# 返回: {"object": "list", "data": []}
```

**解决步骤**:

1. **检查模型配置**:
   ```bash
   # 确保 MODEL_CONFIG 不为空
   echo $MODEL_CONFIG
   
   # 验证 JSON 格式
   python -c "import json; print(json.loads('$MODEL_CONFIG'))"
   ```

2. **检查 API 密钥**:
   ```bash
   # 确保每个模型都有对应的密钥
   python -c "
   import json, os
   config = json.loads(os.getenv('MODEL_CONFIG'))
   for model, key in config.items():
       if not key or not key.strip():
           print(f'Empty key for model: {model}')
   "
   ```

3. **查看启动日志**:
   ```bash
   # 查找配置加载信息
   python main.py 2>&1 | grep "Loaded.*model"
   ```

### 问题 7: 流式响应中断

**现象**:
- 流式响应突然停止
- 收到不完整的回复
- 连接意外断开

**诊断步骤**:

1. **检查网络稳定性**:
   ```bash
   # 持续 ping 测试
   ping -c 100 api.dify.ai
   
   # 检查网络延迟
   mtr api.dify.ai
   ```

2. **查看详细日志**:
   ```python
   # 启用详细日志
   logging.getLogger("httpx").setLevel(logging.DEBUG)
   ```

3. **调整缓冲策略**:
   ```python
   # 减少缓冲延迟
   def calculate_delay(buffer_size):
       return 0.001  # 固定最小延迟
   ```

### 问题 8: 会话映射失败

**现象**:
- 多轮对话无法保持上下文
- 每次请求都创建新会话

**解决步骤**:

1. **检查会话映射文件**:
   ```bash
   # 检查映射文件是否存在
   ls -la data/conversation_mappings.json
   
   # 查看映射内容
   cat data/conversation_mappings.json | jq .
   ```

2. **检查权限**:
   ```bash
   # 确保目录可写
   mkdir -p data
   chmod 755 data
   touch data/conversation_mappings.json
   chmod 644 data/conversation_mappings.json
   ```

3. **查看映射日志**:
   ```bash
   # 查找会话相关日志
   python main.py 2>&1 | grep -i "conversation\|mapping\|chat_id"
   ```

## Docker 相关问题

### 问题 9: Docker 容器无法启动

**错误信息**:
```
docker: Error response from daemon: Container command not found
```

**解决步骤**:

1. **检查 Dockerfile**:
   ```bash
   # 验证 Dockerfile 语法
   docker build --no-cache -t opendify .
   ```

2. **检查基础镜像**:
   ```bash
   # 拉取基础镜像
   docker pull python:3.11-slim
   ```

3. **查看构建日志**:
   ```bash
   docker build -t opendify . --progress=plain
   ```

### 问题 10: 容器内网络连接问题

**现象**:
- 容器内无法访问外部 API
- DNS 解析失败

**解决步骤**:

1. **检查 Docker 网络**:
   ```bash
   # 查看网络配置
   docker network ls
   docker network inspect bridge
   ```

2. **测试容器内网络**:
   ```bash
   # 进入容器
   docker exec -it <container_id> /bin/bash
   
   # 测试网络连接
   ping 8.8.8.8
   nslookup api.dify.ai
   curl -I https://api.dify.ai
   ```

3. **配置 DNS**:
   ```yaml
   # docker-compose.yml
   services:
     opendify:
       dns:
         - 8.8.8.8
         - 8.8.4.4
   ```

## 性能问题

### 问题 11: 响应速度慢

**现象**:
- API 响应时间超过 30 秒
- 流式输出卡顿

**优化步骤**:

1. **启用连接池**:
   ```python
   # 已在代码中实现，检查配置
   HTTP_CLIENT_CONFIG = {
       "limits": httpx.Limits(
           max_keepalive_connections=20,
           max_connections=100
       )
   }
   ```

2. **调整缓冲策略**:
   ```python
   # 优化延迟计算
   def calculate_delay(buffer_size):
       if buffer_size > 50:
           return 0.001
       elif buffer_size > 20:
           return 0.005
       else:
           return 0.01
   ```

3. **监控系统资源**:
   ```bash
   # CPU 使用率
   htop
   
   # 内存使用
   free -h
   
   # 网络连接
   ss -tuln
   ```

### 问题 12: 内存泄漏

**现象**:
- 内存使用持续增长
- 容器重启

**解决步骤**:

1. **监控内存使用**:
   ```bash
   # 容器内存使用
   docker stats
   
   # 进程内存使用
   ps aux | grep python
   ```

2. **检查连接泄漏**:
   ```bash
   # 检查网络连接数
   netstat -an | grep :5000 | wc -l
   ```

3. **启用资源限制**:
   ```yaml
   # docker-compose.yml
   deploy:
     resources:
       limits:
         memory: 512M
   ```

## 调试工具

### 日志分析

1. **启用详细日志**:
   ```python
   logging.basicConfig(level=logging.DEBUG)
   ```

2. **结构化日志查看**:
   ```bash
   # 查看特定类型日志
   python main.py 2>&1 | grep "ERROR"
   python main.py 2>&1 | grep "conversation"
   python main.py 2>&1 | grep "stream"
   ```

### 网络调试

1. **抓包分析**:
   ```bash
   # 使用 tcpdump
   tcpdump -i any -w opendify.pcap port 5000
   
   # 使用 wireshark 分析
   wireshark opendify.pcap
   ```

2. **HTTP 请求调试**:
   ```bash
   # 使用 curl 详细模式
   curl -v -X POST http://localhost:5000/v1/chat/completions \
        -H "Content-Type: application/json" \
        -d '{"model":"claude","messages":[{"role":"user","content":"test"}]}'
   ```

### API 测试

1. **自动化测试**:
   ```bash
   # 运行内置测试
   python test_api.py
   
   # 自定义服务器测试
   python test_api.py http://localhost:5000/v1
   ```

2. **压力测试**:
   ```bash
   # 使用 ab 进行压力测试
   ab -n 100 -c 10 -H "Content-Type: application/json" \
      -p test_payload.json \
      http://localhost:5000/v1/chat/completions
   ```

## 获取帮助

### 收集调试信息

在寻求帮助时，请提供以下信息：

1. **系统信息**:
   ```bash
   uname -a
   python --version
   docker --version
   ```

2. **配置信息** (脱敏):
   ```bash
   env | grep -E "(DIFY|MODEL|SERVER)" | sed 's/app-[^"]*/"app-***"/g'
   ```

3. **错误日志**:
   ```bash
   python main.py 2>&1 | tail -50
   ```

4. **网络测试结果**:
   ```bash
   curl -I $DIFY_API_BASE
   ```

### 日志模板

```
**问题描述**: 简要描述遇到的问题

**环境信息**:
- OS: Ubuntu 20.04
- Python: 3.11.0
- Docker: 20.10.0

**配置信息**:
- DIFY_API_BASE: https://api.dify.ai/v1
- 模型数量: 2

**错误日志**:
```
[粘贴相关错误日志]
```

**重现步骤**:
1. 启动服务
2. 发送请求
3. 观察错误

**期望结果**: 描述期望的正常行为
**实际结果**: 描述实际发生的问题
```

### 社区资源

- **GitHub Issues**: 提交 bug 报告和功能请求
- **文档**: 查看最新的使用文档
- **示例代码**: 参考测试脚本和配置示例

记住：大多数问题都可以通过仔细检查配置和日志来解决。保持耐心，逐步排查问题。