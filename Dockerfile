# 使用官方Python运行时作为基础镜像
FROM python:3.11-slim

# 设置工作目录
WORKDIR /app

# 设置环境变量
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 复制requirements文件
COPY requirements.txt .

# 安装Python依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码和配置文件
COPY main.py gunicorn_config.py ./
COPY scripts/start_production.sh ./

# 创建必要的目录
RUN mkdir -p data logs

# 创建非root用户
RUN useradd --create-home --shell /bin/bash app \
    && chown -R app:app /app \
    && chmod +x start_production.sh
USER app

# 暴露端口
EXPOSE 5000

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:5000/v1/models || exit 1

# 设置环境变量
ENV ENVIRONMENT=production
ENV SERVER_HOST=0.0.0.0
ENV SERVER_PORT=5000

# 启动命令 - 使用 Gunicorn
CMD ["gunicorn", "--config", "gunicorn_config.py", "main:app"]