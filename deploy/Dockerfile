# 奇妙小站 · 生产镜像
# 原则：非 root 运行、无缓存安装、只带必需文件（.dockerignore 负责瘦身）
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# 先只装依赖：代码变动时不重装，构建更快
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# 非 root 用户运行 + 数据目录授权
RUN useradd -m qimiao \
    && mkdir -p /app/data \
    && chown -R qimiao:qimiao /app
USER qimiao

EXPOSE 8000

# 单进程足够自用小站；以后需要多 worker 再调 --workers
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
