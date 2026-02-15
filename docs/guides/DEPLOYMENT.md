# 部署指南

## Docker 部署

### 1. 构建镜像

```bash
# 构建后端镜像
cd backend
docker build -t baixing-backend:latest .

# 构建前端镜像
cd frontend
docker build -t baixing-frontend:latest .
```

### 2. 运行容器

```bash
# 使用 docker-compose
docker-compose up -d

# 或手动运行
docker run -d \
  --name baixing-backend \
  -p 8000:8000 \
  -e DATABASE_URL=postgresql://user:pass@db:5432/baixing \
  -e REDIS_URL=redis://cache:6379 \
  baixing-backend:latest
```

### 3. 检查状态

```bash
docker-compose ps
docker-compose logs -f
```

## Kubernetes 部署

### 1. 安装 Helm

```bash
# 添加 Helm 仓库
helm repo add baixing https://charts.baixing-law.com

# 安装
helm install baixing-assistant baixing/baixing-assistant \
  --namespace production \
  --values values.yaml
```

### 2. 配置说明

参考 `helm/baixing-assistant/values.yaml`

```yaml
replicaCount: 2

image:
  repository: baixing/backend
  tag: latest

resources:
  requests:
    memory: "512Mi"
    cpu: "500m"
  limits:
    memory: "1Gi"
    cpu: "1000m"

autoscaling:
  minReplicas: 2
  maxReplicas: 10
  targetCPUUtilizationPercentage: 80
```

## 环境配置

### 生产环境变量

```bash
# .env.prod
DATABASE_URL=postgresql://user:pass@prod-db:5432/baixing
REDIS_URL=redis://prod-redis:6379
JWT_SECRET=your-production-secret
OPENAI_API_KEY=sk-xxx
SENTRY_DSN=https://xxx@sentry.io/xxx
PROMETHEUS_ENABLED=true
ENVIRONMENT=production
DEBUG=false
```

### Nginx 配置

```nginx
server {
    listen 80;
    server_name api.baixing-law.com;

    location / {
        proxy_pass http://backend:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location /ws {
        proxy_pass http://backend:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

## 监控配置

### Prometheus

```yaml
# prometheus.yaml
scrape_configs:
  - job_name: 'baixing-backend'
    static_configs:
      - targets: ['backend:8000']
    metrics_path: /metrics
```

### Grafana

导入 `docs/grafana/ai-quality-dashboard.json`

## 故障排查

| 问题 | 解决方案 |
|------|----------|
| 容器启动失败 | `docker-compose logs backend` |
| 数据库连接失败 | 检查 `DATABASE_URL` 配置 |
| 内存不足 | 增加容器内存限制 |
| 502 错误 | 检查后端服务健康状态 |
