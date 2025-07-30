# OpenDify 测试文件

本目录包含 OpenDify 项目的所有测试文件。

## 测试文件说明

### `test_api.py`
- **功能**: OpenAI API 兼容性测试
- **用途**: 测试 `/v1/models` 和 `/v1/chat/completions` 端点
- **运行**: `python tests/test_api.py [服务器URL]`
- **默认服务器**: `http://localhost:5000/v1`

### `manual_test.py`
- **功能**: 手动交互式测试
- **用途**: 人工测试和调试特定功能
- **运行**: `python tests/manual_test.py`

### `test_conversation_mapping.py`
- **功能**: 会话映射功能测试
- **用途**: 测试 WebUI chat_id 到 Dify conversation_id 的映射
- **运行**: `python tests/test_conversation_mapping.py`

## 运行测试

### 运行所有测试
```bash
# 确保服务已启动
python main.py &

# 运行 API 测试
python tests/test_api.py

# 运行会话映射测试
python tests/test_conversation_mapping.py
```

### 运行特定测试
```bash
# 测试特定服务器
python tests/test_api.py http://your-server:5000/v1

# 手动测试模式
python tests/manual_test.py
```

## 测试环境要求

1. **服务运行**: 确保 OpenDify 服务正在运行
2. **环境配置**: 配置正确的 `.env` 文件
3. **网络连接**: 确保能访问 Dify API
4. **依赖安装**: `pip install -r requirements.txt`

## 测试覆盖范围

- ✅ OpenAI API 兼容性
- ✅ 流式响应处理
- ✅ 错误处理机制
- ✅ 会话映射功能
- ✅ 用户ID识别
- ✅ 模型列表获取

## 添加新测试

在添加新测试时，请：
1. 遵循现有的命名约定
2. 添加详细的文档说明
3. 更新本 README 文件
4. 确保测试可以独立运行