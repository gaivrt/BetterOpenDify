# OpenDify 项目结构说明

## 项目组织原则

为了提高项目的可维护性和可读性，OpenDify 项目已按照功能分类重新组织文件结构。

## 目录结构

### 根目录文件
- `main.py` - 主应用程序入口
- `requirements.txt` - Python 依赖包列表
- `gunicorn_config.py` - Gunicorn 生产环境配置
- `Dockerfile` / `Dockerfile.dev` - Docker 镜像构建文件
- `docker-compose*.yml` - Docker Compose 配置文件
- `nginx.conf` - Nginx 反向代理配置
- `Makefile` - Make 构建和管理命令

### 📖 docs/ - 项目文档
存放所有项目相关文档，包括：
- `README.md` - 文档索引和快速导航
- `DEPLOYMENT.md` - 完整部署指南
- `API_DOCUMENTATION.md` - API 接口文档
- `CONFIGURATION_GUIDE.md` - 配置说明
- `STATE_MANAGEMENT.md` - 状态管理机制详解
- `TROUBLESHOOTING.md` - 故障排除指南
- `chat-id-integration-guide.md` - Chat ID 和 User ID 集成指南

### 🔧 scripts/ - 构建和部署脚本
存放所有自动化脚本，包括：
- `README.md` - 脚本使用说明
- `build.sh` - Docker 镜像构建脚本
- `export_image.sh` - Docker 镜像导出脚本
- `deploy.sh` - 生产环境部署管理脚本
- `run_docker.sh` - Docker 容器运行脚本
- `run_compose.sh` - Docker Compose 运行脚本
- `start_production.sh` - Gunicorn 生产环境启动脚本
- `start_development.sh` - 开发环境启动脚本

### 🧪 tests/ - 测试文件
存放所有测试相关文件，包括：
- `README.md` - 测试说明和使用指南
- `test_api.py` - OpenAI API 兼容性测试
- `manual_test.py` - 手动交互式测试
- `test_conversation_mapping.py` - 会话映射功能测试

### 💾 data/ - 数据存储
存放运行时数据文件：
- `conversation_mappings.json` - 会话映射持久化存储

## 文件组织优势

### 🎯 清晰分类
- **功能分离**: 文档、脚本、测试分别存放
- **易于查找**: 按功能快速定位所需文件
- **维护方便**: 相关文件集中管理

### 📚 文档完整
- **每个目录都有 README**: 说明该目录的用途和文件
- **交叉引用**: 文档间相互链接，形成完整体系
- **使用指南**: 详细的使用说明和示例

### 🔧 开发友好
- **脚本集中**: 所有构建部署脚本统一管理
- **测试独立**: 测试文件独立目录，不污染主代码
- **配置清晰**: 各种配置文件功能明确

### 🚀 部署简化
- **一键操作**: 通过脚本实现自动化部署
- **环境隔离**: 开发和生产环境脚本分离
- **文档同步**: 部署相关文档与脚本同步更新

## 使用指导

### 新用户入门
1. 阅读主 `README.md` 了解项目概况
2. 查看 `docs/` 目录获取详细文档
3. 使用 `scripts/` 中的脚本进行部署

### 开发者
1. 参考 `tests/` 目录了解测试方法
2. 使用 `scripts/start_development.sh` 启动开发环境
3. 查看 `docs/API_DOCUMENTATION.md` 了解 API 设计

### 运维人员
1. 使用 `scripts/deploy.sh` 进行生产部署
2. 参考 `docs/DEPLOYMENT.md` 了解部署细节
3. 查看 `docs/TROUBLESHOOTING.md` 解决问题

## 文件路径更新

项目重组后，所有文档和脚本中的文件路径引用已更新：
- ✅ `README.md` - 更新了脚本路径引用
- ✅ `DOCKER.md` - 更新了构建和部署脚本路径
- ✅ `Makefile` - 更新了所有脚本和测试文件路径
- ✅ 各目录 `README.md` - 提供了详细的使用说明

## 维护建议

### 添加新文件时
1. **文档**: 放入 `docs/` 目录并更新索引
2. **脚本**: 放入 `scripts/` 目录并更新说明
3. **测试**: 放入 `tests/` 目录并更新测试指南
4. **更新引用**: 确保所有相关文档中的路径正确

### 修改现有文件时
1. **保持结构**: 不要随意移动已组织好的文件
2. **更新文档**: 修改功能时同步更新相关文档
3. **测试验证**: 确保路径引用正确，功能正常

这种组织结构使 OpenDify 项目更加专业、易维护，为后续开发和部署提供了solid的基础。