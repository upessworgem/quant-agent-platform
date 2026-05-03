# 多阶段构建 Dockerfile

# 阶段1: 构建前端
FROM node:16-alpine AS frontend-builder

WORKDIR /app/web-admin

# 复制前端依赖文件
COPY web-admin/package*.json ./

# 安装前端依赖
RUN npm ci

# 复制前端源码
COPY web-admin/ ./

# 构建生产版本
RUN npm run build

# 阶段2: 构建后端
FROM python:3.11-slim

# 设置环境变量
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    FLASK_ENV=production \
    FLASK_DEBUG=false

# 安装系统依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# 创建工作目录
WORKDIR /app

# 复制后端依赖文件
COPY requirements.txt .

# 安装 Python 依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制后端源码
COPY . .

# 复制前端构建结果
COPY --from=frontend-builder /app/web-admin/dist ./web-admin/dist

# 创建数据目录
RUN mkdir -p /app/data

# 暴露端口
EXPOSE 5000

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5000/api/health || exit 1

# 启动命令
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "4", "--threads", "2", "app:app"]
