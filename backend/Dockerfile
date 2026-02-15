# ============================================
# 百姓助手后端服务 - 安全加固版 Dockerfile
# ============================================

FROM python:3.11-slim

# 镜像标签信息
LABEL maintainer="百姓助手团队" \
      description="百姓助手后端服务" \
      version="1.0" \
      security.scan="trivy" \
      security.compliance="enabled"

WORKDIR /app

# 创建非 root 用户和组
RUN groupadd --gid 10000 appgroup \
    && useradd --uid 10000 --gid appgroup \
        --shell /bin/false \
        --no-create-home \
        --home-dir /app \
        appuser

# 配置镜像源并安装运行时依赖
RUN set -eux \
    && if [ -f /etc/apt/sources.list ]; then \
        sed -i \
            -e 's|http://deb.debian.org/debian|https://mirrors.tuna.tsinghua.edu.cn/debian|g' \
            -e 's|http://deb.debian.org/debian-security|https://mirrors.tuna.tsinghua.edu.cn/debian-security|g' \
            /etc/apt/sources.list; \
    fi \
    && if [ -f /etc/apt/sources.list.d/debian.sources ]; then \
        sed -i \
            -e 's|http://deb.debian.org/debian|https://mirrors.tuna.tsinghua.edu.cn/debian|g' \
            -e 's|http://deb.debian.org/debian-security|https://mirrors.tuna.tsinghua.edu.cn/debian-security|g' \
            /etc/apt/sources.list.d/debian.sources; \
    fi \
    && apt-get update -o Acquire::Retries=5 \
        -o Acquire::http::Timeout=30 \
        -o Acquire::https::Timeout=30 \
    && apt-get install -y --no-install-recommends \
        gcc \
        g++ \
        libpq-dev \
        libpq5 \
        ffmpeg \
        libsndfile1 \
    && rm -rf /var/lib/apt/lists/* /var/cache/apt/* /var/log/apt/* \
    && apt-get clean \
    && apt-get autoremove -y

# 复制依赖文件
COPY requirements.txt .

# 安装 Python 依赖
RUN pip install --no-cache-dir --retries 5 --timeout 60 \
    -i https://pypi.tuna.tsinghua.edu.cn/simple \
    -r requirements.txt

# 设置 Python 环境变量
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONFAULTHANDLER=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# 创建应用目录并设置权限
RUN mkdir -p /app/data/sherpa_models /app/logs \
    && chown -R appuser:appgroup /app

# 复制应用代码（使用非 root 用户权限）
COPY --chown=appuser:appgroup . .

# 移除不必要的文件
RUN rm -rf \
        tests/ \
        docs/ \
        scripts/*.py \
        .bandit \
        .coveragerc \
        pytest.ini \
        pyrightconfig.json \
        requirements-dev.txt \
    2>/dev/null || true

# 设置文件权限
RUN chmod -R 555 /app/app /app/alembic 2>/dev/null || true \
    && chmod -R 750 /app/data /app/logs \
    && chmod 644 /app/requirements.txt 2>/dev/null || true

# 切换到非 root 用户
USER appuser

# 健康检查
HEALTHCHECK --interval=30s \
            --timeout=10s \
            --start-period=30s \
            --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health', timeout=5)" || exit 1

# 暴露端口
EXPOSE 8000

# 启动命令
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
