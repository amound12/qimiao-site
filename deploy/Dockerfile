# 奇妙小站 · 生产镜像
# 原则：非 root 运行、无缓存安装、只带必需文件（.dockerignore 负责瘦身）
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_INDEX_URL=https://pypi.tuna.tsinghua.edu.cn/simple
# 国内服务器构建提速：pip 走清华镜像源，海外也能正常访问

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
# --proxy-headers：Nginx 反代后正确解析 X-Forwarded-For（容器只监听宿主机回环，信任来源安全）
# --no-server-header：不暴露服务器软件版本
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers", "--forwarded-allow-ips=*", "--no-server-header"]
