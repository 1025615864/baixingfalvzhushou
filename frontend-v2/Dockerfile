# ============================================
# 百姓助手前端 Dockerfile
# 多阶段构建 - 生产环境优化
# ============================================

# 阶段1: 构建阶段
FROM node:20-alpine AS builder

# 设置工作目录
WORKDIR /app

# 配置 npm 使用淘宝镜像
RUN npm config set registry https://registry.npmmirror.com

# 安装依赖（利用 Docker 缓存层）
COPY package.json package-lock.json ./
RUN npm ci --legacy-peer-deps

# 复制源代码
COPY . .

# 构建参数 - 环境变量注入
ARG VITE_API_BASE_URL=/api
ARG VITE_WS_URL=ws://localhost:8000/ws

# 设置环境变量
ENV VITE_API_BASE_URL=$VITE_API_BASE_URL
ENV VITE_WS_URL=$VITE_WS_URL
ENV NODE_ENV=production

# 执行构建
RUN npm run build

# 阶段2: 生产阶段 - 使用 Nginx 服务静态文件
FROM nginx:alpine AS production

# 安装 curl 用于健康检查
RUN apk add --no-cache curl

# 复制自定义 Nginx 配置
COPY <<'EOF' /etc/nginx/conf.d/default.conf
server {
    listen 3000;
    server_name localhost;
    root /usr/share/nginx/html;
    index index.html;

    # Gzip 压缩
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_proxied any;
    gzip_types text/plain text/css text/xml text/javascript application/javascript application/json application/xml;
    gzip_comp_level 6;

    # 安全头
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;

    # 静态资源缓存
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    # API 代理
    location /api {
        proxy_pass http://backend:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # WebSocket 代理
    location /ws {
        proxy_pass http://backend:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_read_timeout 86400;
    }

    # SPA 路由支持 - 所有路由返回 index.html
    location / {
        try_files $uri $uri/ /index.html;
    }

    # 健康检查端点
    location /health {
        access_log off;
        return 200 "OK";
        add_header Content-Type text/plain;
    }
}
EOF

# 复制构建产物
COPY --from=builder /app/dist /usr/share/nginx/html

# 暴露端口
EXPOSE 3000

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:3000/health || exit 1

# 启动 Nginx
CMD ["nginx", "-g", "daemon off;"]
