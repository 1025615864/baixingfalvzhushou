# 百姓助手 - 运维与部署文档

本文档提供百姓助手项目的完整运维与部署规范，涵盖从开发环境到生产环境的全流程指导。

---

## 1. 部署架构

### 1.1 系统架构拓扑

```
                                    ┌─────────────────┐
                                    │   用户终端      │
                                    │ (Web/Mobile)    │
                                    └────────┬────────┘
                                             │
                                    ┌────────▼────────┐
                                    │   Nginx        │
                                    │ (反向代理/负载均衡)│
                                    └────────┬────────┘
                                             │
                    ┌────────────────────────┼────────────────────────┐
                    │                        │                        │
           ┌────────▼────────┐      ┌────────▼────────┐      ┌────────▼────────┐
           │   前端服务      │      │   后端服务      │      │   静态资源      │
           │   (Next.js)    │      │   (FastAPI)     │      │   (图片/文件)   │
           └────────┬────────┘      └────────┬────────┘      └─────────────────┘
                    │                        │
                    │              ┌──────────┼──────────┐
                    │              │          │          │
           ┌────────▼────────┐ ┌──▼──┐ ┌────▼────┐ ┌───▼───┐
           │   PostgreSQL    │ │Redis│ │Aliyun  │ │Sentry │
           │   数据库        │ │缓存 │ │OSS存储 │ │监控   │
           └─────────────────┘ └─────┘ └─────────┘ └───────┘
```

### 1.2 基础设施要求

| 组件 | 最低配置 | 推荐配置 | 说明 |
|------|----------|----------|------|
| PostgreSQL | 2核2G | 4核8G | 主数据库，存储业务数据 |
| Redis | 1核512M | 2核1G | 缓存、会话、限流 |
| Backend | 2核1G | 4核2G | API服务，支持水平扩展 |
| Frontend | 1核512M | 2核1G | Web应用服务 |
| Nginx | 1核512M | 2核1G | 反向代理、SSL终端 |

### 1.3 服务组件规划

| 服务名称 | 容器名称 | 端口映射 | 依赖服务 |
|----------|----------|----------|----------|
| db | baixing_db_prod | 5432:5432 | - |
| redis | baixing_redis_prod | 6379:6379 | - |
| backend | baixing_backend_prod | 8000:8000 | db, redis |
| prometheus | baixing_prometheus | 9090:9090 | backend |
| grafana | baixing_grafana | 3001:3000 | prometheus |
| alertmanager | baixing_alertmanager | 9093:9093 | - |

---

## 2. Docker 部署

### 2.1 Docker Compose 配置说明

项目提供多个 Docker Compose 配置文件，适应不同环境：

| 文件 | 用途 | 说明 |
|------|------|------|
| [`docker-compose.yml`](../docker-compose.yml) | 开发环境 | 本地开发使用，包含所有基础服务 |
| [`docker-compose.prod.yml`](../docker-compose.prod.yml) | 生产环境 | 生产部署配置，含完整监控栈 |
| [`docker-compose.monitoring.yml`](../docker-compose.monitoring.yml) | 监控组件 | 仅部署监控组件（Prometheus/Grafana） |

### 2.2 环境变量配置

#### 生产环境必需环境变量

创建 `.env.prod` 文件，参考 [`.env.prod`](../.env.prod)：

```bash
# ==========================================
# 数据库配置 (PostgreSQL)
# ==========================================
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your-secure-password
POSTGRES_DB=baixing_law

# ==========================================
# 安全配置 (Security)
# ==========================================
SECRET_KEY=your-session-secret-key
JWT_SECRET_KEY=your-jwt-secret-key
PAYMENT_WEBHOOK_SECRET=your-payment-secret

# ==========================================
# 缓存与消息队列 (Redis)
# ==========================================
REDIS_PASSWORD=your-redis-password

# ==========================================
# 网络与跨域 (Network & CORS)
# ==========================================
CORS_ALLOW_ORIGINS=["https://yourdomain.com"]

# ==========================================
# AI 服务配置 (AI Services)
# ==========================================
OPENAI_API_KEY=your-openai-api-key
AI_MODEL=deepseek-chat

# ==========================================
# 监控配置
# ==========================================
SENTRY_DSN=your-sentry-dsn
PROMETHEUS_ENABLED=true

# ==========================================
# 新增功能配置 (阶段三)
# ==========================================
# 会员功能
MEMBERSHIP_ENABLED=true
MEMBERSHIP_PRICING_MONTHLY=29
MEMBERSHIP_PRICING_ANNUAL=299
MEMBERSHIP_PRICING_LIFETIME=999

# 视频咨询功能
VIDEO_CONSULTATION_ENABLED=true
VIDEO_CONSULTATION_BASE_FEE=99
TRTC_SDK_ID=your_trtc_sdk_id
TRTC_SDK_KEY=your_trtc_sdk_key

# 法律文书商城
LEGAL_DOCUMENT_ENABLED=true
LEGAL_DOCUMENT_INTEGRAL_RATIO=100

# 推荐系统
RECOMMENDATION_ENABLED=true
RECOMMENDATION_CACHE_TTL=3600
```

### 2.3 容器化部署步骤

#### 开发环境部署

```bash
# 1. 复制环境变量模板
cp .env.example .env

# 2. 修改环境变量
vim .env

# 3. 启动所有服务
docker-compose up -d

# 4. 查看服务状态
docker-compose ps

# 5. 查看日志
docker-compose logs -f backend
```

#### 生产环境部署

```bash
# 1. 复制生产环境配置
cp .env.prod .env

# 2. 修改生产环境变量（务必修改所有密钥）
vim .env.prod

# 3. 构建并启动生产环境
docker-compose -f docker-compose.prod.yml up -d --build

# 4. 检查容器健康状态
docker-compose -f docker-compose.prod.yml ps

# 5. 查看生产环境日志
docker-compose -f docker-compose.prod.yml logs -f backend
```

#### 监控组件单独部署

```bash
# 部署 Prometheus + Grafana + Alertmanager
docker-compose -f docker-compose.monitoring.yml up -d

# 访问地址
# Prometheus: http://localhost:9090
# Grafana: http://localhost:3001 (admin/admin123)
# Alertmanager: http://localhost:9093
```

---

## 3. Kubernetes 部署

### 3.1 Helm Chart 说明

项目提供 Helm Chart 部署配置，位于 [`helm/baixing-assistant/`](../helm/baixing-assistant/)：

```bash
# 添加 Helm 仓库（如果有私有仓库）
helm repo add baixing https://charts.yourcompany.com

# 安装 Chart
helm install baixing-app helm/baixing-assistant/ -f values.prod.yaml

# 升级 Chart
helm upgrade baixing-app helm/baixing-assistant/ -f values.prod.yaml

# 查看部署状态
helm status baixing-app
```

### 3.2 K8s 部署配置

#### values.yaml 主要配置项

参考 [`helm/baixing-assistant/values.yaml`](../helm/baixing-assistant/values.yaml)：

```yaml
replicaCount:
  backend: 2
  frontend: 2

image:
  backend:
    repository: baixing-backend
    tag: latest
  frontend:
    repository: baixing-frontend
    tag: latest

service:
  backend:
    type: ClusterIP
    port: 8000
  frontend:
    type: ClusterIP
    port: 3000

backend:
  config:
    DEBUG: "false"
    CORS_ALLOW_ORIGINS: "https://yourdomain.com"
    AI_MODEL: "deepseek-chat"
  
  secret:
    DATABASE_URL: ""
    JWT_SECRET_KEY: ""
    PAYMENT_WEBHOOK_SECRET: ""

ingress:
  enabled: true
  className: nginx
  host: yourdomain.com
  tls:
    enabled: true
    secretName: yourdomain-tls
```

#### 生产环境配置示例

参考 [`helm/baixing-assistant/values.prod.example.yaml`](../helm/baixing-assistant/values.prod.example.yaml)：

```yaml
replicaCount:
  backend: 4
  frontend: 3

backend:
  resources:
    requests:
      cpu: "2"
      memory: "2Gi"
    limits:
      cpu: "4"
      memory: "4Gi"

ingress:
  annotations:
    cert-manager.io/cluster-issuer: "letsencrypt-prod"
```

### 3.3 服务发现与负载均衡

#### Service 配置

```yaml
# backend-service.yaml
apiVersion: v1
kind: Service
metadata:
  name: backend
  labels:
    app: backend
spec:
  type: ClusterIP
  ports:
    - port: 8000
      targetPort: 8000
      protocol: TCP
  selector:
    app: backend
```

#### Ingress 配置

```yaml
# ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: baixing-ingress
  annotations:
    nginx.ingress.kubernetes.io/proxy-body-size: "20m"
    nginx.ingress.kubernetes.io/proxy-read-timeout: "300"
spec:
  ingressClassName: nginx
  rules:
    - host: yourdomain.com
      http:
        paths:
          - path: /api
            pathType: Prefix
            backend:
              service:
                name: backend
                port:
                  number: 8000
          - path: /
            pathType: Prefix
            backend:
              service:
                name: frontend
                port:
                  number: 3000
  tls:
    - hosts:
        - yourdomain.com
      secretName: yourdomain-tls
```

---

## 4. Nginx 配置

### 4.1 反向代理配置

参考 [`nginx/nginx.conf`](../nginx/nginx.conf)：

```nginx
# 上游服务器配置
upstream backend {
    server backend:8000;
    # 可添加多个后端实现负载均衡
    # server backend2:8000;
}

upstream frontend {
    server frontend:3000;
}

# HTTP 服务器 - 强制重定向到 HTTPS
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;

    # Let's Encrypt ACME 挑战
    location /.well-known/acme-challenge/ {
        root /var/www/certbot;
    }

    # 重定向到 HTTPS
    location / {
        return 301 https://$server_name$request_uri;
    }
}

# HTTPS 服务器
server {
    listen 443 ssl http2;
    server_name yourdomain.com;

    # SSL 证书配置
    ssl_certificate /etc/nginx/ssl/cert.pem;
    ssl_certificate_key /etc/nginx/ssl/key.pem;
    
    # SSL 安全配置
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;

    # 安全头
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains; preload" always;
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;

    # 客户端上传大小限制
    client_max_body_size 20M;

    # Gzip 压缩
    gzip on;
    gzip_types text/plain text/css application/json application/javascript;

    # 后端 API 代理
    location /api/ {
        proxy_pass http://backend;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # WebSocket 支持
    location /ws/ {
        proxy_pass http://backend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_read_timeout 86400;
    }

    # 前端静态文件
    location / {
        proxy_pass http://frontend;
    }
}
```

### 4.2 SSL/TLS 证书配置

#### 使用 Let's Encrypt 自动续期

```bash
# 安装 certbot
apt-get install certbot python3-certbot-nginx

# 获取证书
certbot --nginx -d yourdomain.com -d www.yourdomain.com

# 自动续期测试
certbot renew --dry-run
```

#### 手动证书配置

```bash
# 创建 SSL 目录
mkdir -p /etc/nginx/ssl

# 复制证书文件
cp cert.pem /etc/nginx/ssl/cert.pem
cp key.pem /etc/nginx/ssl/key.pem

# 重载 Nginx
nginx -s reload
```

### 4.3 静态资源缓存

```nginx
# 静态资源缓存配置
location ~* \.(jpg|jpeg|png|gif|ico|css|js|svg|woff|woff2|ttf|eot)$ {
    proxy_pass http://frontend;
    expires 30d;
    add_header Cache-Control "public, immutable";
}

# 上传文件不缓存
location /api/upload {
    proxy_pass http://backend;
    expires -1;
    add_header Cache-Control "no-store, no-cache, must-revalidate";
}
```

---

## 5. 监控配置

### 5.1 Prometheus 指标采集

参考 [`prometheus/prometheus.yml`](../prometheus/prometheus.yml)：

```yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s
  external_labels:
    cluster: 'baixing-legal-assistant'
    env: 'production'

alerting:
  alertmanagers:
    - static_configs:
        - targets:
            - alertmanager:9093

rule_files:
  - /etc/prometheus/ai-quality-alerts.yml
  - /etc/prometheus/backend-alerts.yml
  - /etc/prometheus/api_alerts.yml

scrape_configs:
  # 后端指标
  - job_name: 'backend'
    static_configs:
      - targets: ['backend:8000']
    metrics_path: '/metrics'

  # AI 质量指标
  - job_name: 'ai-quality'
    static_configs:
      - targets: ['backend:8000']
    metrics_path: '/api/system/ai-quality/prometheus'

  # Redis 指标
  - job_name: 'redis'
    static_configs:
      - targets: ['redis-exporter:9121']
```

### 5.2 Alertmanager 告警规则

参考 [`alertmanager/alertmanager.yml`](../alertmanager/alertmanager.yml)：

```yaml
global:
  resolve_timeout: 5m
  slack_api_url: '${SLACK_WEBHOOK_URL}'

route:
  group_by: ['alertname', 'cluster', 'service']
  group_wait: 30s
  group_interval: 5m
  repeat_interval: 4h
  receiver: 'default-receiver'

  routes:
    # 严重告警 - 立即通知
    - match:
        severity: critical
      receiver: 'critical-receiver'
      group_wait: 10s

    # 警告告警
    - match:
        severity: warning
      receiver: 'warning-receiver'

receivers:
  - name: 'default-receiver'
    slack_configs:
      - channel: '#alerts'
        send_resolved: true

  - name: 'critical-receiver'
    slack_configs:
      - channel: '#critical'
        send_resolved: true
        urgency: critical
```

### 5.3 Grafana 仪表盘

项目提供预配置的 Grafana 仪表盘：[`grafana/baixing_dashboard.json`](../grafana/baixing_dashboard.json)

#### 导入仪表盘

1. 访问 Grafana: http://localhost:3001
2. 进入 Dashboards -> Import
3. 上传 `grafana/baixing_dashboard.json`

### 5.4 关键告警指标

| 告警名称 | 表达式 | 阈值 | 说明 |
|----------|--------|------|------|
| BackendDown | up{job="backend"} == 0 | 0 | 后端服务不可用 |
| HighErrorRate | rate(http_requests_total{status=~"5.."}[5m]) | > 0.05 | 5xx错误率超过5% |
| HighLatency | histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m])) | > 2 | P95延迟超过2秒 |
| DatabaseDown | up{job="postgres"} == 0 | 0 | 数据库不可用 |
| RedisDown | up{job="redis"} == 0 | 0 | Redis不可用 |
| DiskSpaceLow | (node_filesystem_avail_bytes{mountpoint="/"} / node_filesystem_size_bytes) | < 0.1 | 磁盘空间不足10% |
| MemoryHigh | (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes) | < 0.2 | 可用内存不足20% |

---

## 6. 日志管理

### 6.1 日志收集策略

项目使用结构化 JSON 日志，参考 [`backend/app/utils/logging_config.py`](../backend/app/utils/logging_config.py)：

```python
log_format = "%(asctime)s | %(levelname)-8s | %(name)s:%(lineno)d | %(message)s"
```

#### Docker 日志驱动配置

```yaml
# docker-compose.yml
services:
  backend:
    logging:
      driver: "json-file"
      options:
        max-size: "100m"
        max-file: "5"
```

### 6.2 日志级别配置

| 环境 | 日志级别 | 说明 |
|------|----------|------|
| development | DEBUG | 详细调试信息 |
| production | INFO | 关键业务日志 |
| staging | INFO | 生产预发环境 |

```bash
# 通过环境变量配置
LOG_LEVEL=INFO
```

### 6.3 结构化日志格式

```json
{
  "timestamp": "2024-01-15T10:30:00.000Z",
  "level": "INFO",
  "logger": "app.routers.user",
  "message": "User logged in",
  "extra": {
    "user_id": 12345,
    "ip": "192.168.1.1",
    "user_agent": "Mozilla/5.0..."
  },
  "request_id": "abc-123-def"
}
```

---

## 7. 数据库运维

### 7.1 PostgreSQL 备份恢复

项目提供自动化备份脚本，位于 [`scripts/db_backup.py`](../scripts/db_backup.py) 和 [`scripts/db_restore.py`](../scripts/db_restore.py)：

#### 自动备份（推荐）

```bash
# 使用项目提供的自动备份脚本
# 详见 scripts/auto_backup.sh / auto_backup.ps1
```

#### 手动备份

```bash
# 备份数据库
docker exec baixing_db_prod pg_dump -U postgres baixing_law > backup_$(date +%Y%m%d_%H%M%S).sql

# 压缩备份
docker exec baixing_db_prod pg_dump -U postgres baixing_law | gzip > backup_$(date +%Y%m%d).sql.gz
```

#### 恢复数据库

```bash
# 停止应用服务
docker-compose stop backend

# 恢复数据库
docker exec -i baixing_db_prod psql -U postgres baixing_law < backup_20240115.sql

# 启动应用服务
docker-compose start backend
```

#### 备份策略

| 备份类型 | 频率 | 保留时间 | 说明 |
|----------|------|----------|------|
| 全量备份 | 每天 | 30天 | 每日凌晨2点执行 |
| 增量备份 | 每小时 | 7天 | 实时复制 |
| 归档备份 | 每周 | 90天 | 长期存档 |

### 7.2 Redis 缓存策略

参考 [`docker-compose.yml`](../docker-compose.yml) 中的 Redis 配置：

```yaml
redis:
  command: redis-server --requirepass ${REDIS_PASSWORD} --maxmemory 512mb --maxmemory-policy allkeys-lru
```

#### 缓存策略配置

| 场景 | TTL | 策略 |
|------|-----|------|
| 会话数据 | 7天 | LRU |
| API 缓存 | 1小时 | LRU |
| 限流计数 | 1分钟 | TTL |
| AI 质量日志 | 7天 | TTL |

#### Redis 备份

```bash
# 备份 Redis 数据
docker exec baixing_redis_prod redis-cli -a ${REDIS_PASSWORD} SAVE

# 复制备份文件
docker cp baixing_redis_prod:/data/dump.rdb ./redis_backup_$(date +%Y%m%d).rdb
```

### 7.3 Alembic 迁移管理

项目使用 Alembic 进行数据库迁移，参考 [`backend/alembic.ini`](../backend/alembic.ini)：

```bash
# 查看迁移状态
alembic current

# 生成新迁移
alembic revision --autogenerate -m "add new table"

# 执行迁移
alembic upgrade head

# 回滚迁移
alembic downgrade -1

# 查看迁移历史
alembic history --verbose
```

#### 生产环境迁移流程

```bash
# 1. 备份数据库（重要！）
docker exec baixing_db_prod pg_dump -U postgres baixing_law > pre_migration_backup.sql

# 2. 在测试环境验证迁移
# 3. 生产环境执行迁移
docker exec -it baixing_backend_prod alembic upgrade head

# 4. 验证迁移结果
docker exec -it baixing_backend_prod alembic current
```

---

## 8. 安全配置

### 8.1 API 安全策略

#### 身份认证

```python
# JWT 配置
# 算法: RS256 (生产环境)
# 访问令牌过期: 60分钟
# 刷新令牌过期: 7天
```

#### 请求限流

```python
# 限流配置
RATE_LIMIT_REQUESTS_PER_MINUTE = 60  # 每分钟60次请求
RATE_LIMIT_REQUESTS_PER_SECOND = 10  # 每秒10次请求
```

#### CORS 配置

```python
# 生产环境 CORS 配置
CORS_ALLOW_ORIGINS = ["https://yourdomain.com"]
```

### 8.2 支付安全配置

参考 [`backend/app/config/settings.py`](../backend/app/config/settings.py) 中的支付配置：

```bash
# 支付回调密钥（必填）
PAYMENT_WEBHOOK_SECRET=your-webhook-secret

# 支付宝配置
ALIPAY_APP_ID=your-app-id
ALIPAY_PRIVATE_KEY=your-private-key
ALIPAY_PUBLIC_KEY=alipay-public-key

# IkunPay 配置
IKUNPAY_PID=your-pid
IKUNPAY_KEY=your-key
```

#### 支付回调签名验证

项目内置签名验证机制，确保支付回调的合法性：

```python
# 参考 backend/app/utils/payment_security.py
def verify_payment_signature(payload: dict, signature: str) -> bool:
    # 使用 HMAC-SHA256 验证签名
    secret = settings.payment_webhook_secret
    expected = hmac.new(secret.encode(), json.dumps(payload).encode(), 'sha256').hexdigest()
    return hmac.compare_digest(expected, signature)
```

### 8.3 数据加密

#### 敏感数据加密

```python
# 使用 pydantic-settings 的敏感字段
from pydantic import Field

class Settings(BaseSettings):
    # 敏感字段自动从环境变量读取，不写入日志
    database_url: str = Field(..., sensitive=True)
    jwt_secret_key: str = Field(..., sensitive=True)
```

#### 数据库加密

- PostgreSQL 支持 TDE（透明数据加密）
- 推荐使用云数据库服务提供的加密功能

### 8.4 密钥管理

#### 生产环境密钥生成

```bash
# 生成强密码
openssl rand -hex 32

# 生成 JWT RSA 密钥对
openssl genrsa -out jwt_private.pem 2048
openssl rsa -in jwt_private.pem -pubout -out jwt_public.pem
```

#### 密钥轮换策略

| 密钥类型 | 轮换周期 | 备注 |
|----------|----------|------|
| 数据库密码 | 90天 | 配合蓝绿部署 |
| JWT 密钥 | 180天 | 支持密钥轮换 |
| 支付密钥 | 365天 | 按服务商要求 |
| API 密钥 | 按需 | 泄漏立即更换 |

---

## 9. 备份与恢复

### 9.1 数据库备份

#### 备份脚本使用

```bash
# 自动备份 (Linux/macOS)
./scripts/auto_backup.sh

# 自动备份 (Windows)
powershell -File scripts/auto_backup.ps1

# 手动备份
python scripts/db_backup.py --host localhost --port 5432 --database baixing_law
```

#### 备份验证

```bash
# 验证备份文件完整性
gunzip -t backup_20240115.sql.gz

# 测试恢复（不影响生产）
docker run --rm -v backups:/backup postgres:15 psql -h db -U postgres -d test < backup_20240115.sql
```

### 9.2 文件备份

需要备份的文件和目录：

| 路径 | 说明 | 备份频率 |
|------|------|----------|
| `/data/uploads` | 用户上传文件 | 实时同步 |
| `/data/knowledge_base` | 法律知识库 | 每周 |
| `/jwt_*.pem` | JWT 密钥文件 | 初始生成 |

```bash
# 备份上传文件
rsync -avz --progress data/uploads/ backup:/backups/uploads/

# 备份配置文件
tar -czf config_backup_$(date +%Y%m%d).tar.gz .env.prod jwt_*.pem
```

### 9.3 灾难恢复计划

#### RTO/RPO 目标

| 指标 | 目标值 | 说明 |
|------|--------|------|
| RTO | 4小时 | 恢复时间目标 |
| RPO | 1小时 | 恢复点目标 |

#### 恢复流程

```bash
# 1. 启动新环境
docker-compose -f docker-compose.prod.yml up -d db redis

# 2. 恢复数据库
docker exec -i baixing_db_prod psql -U postgres baixing_law < latest_backup.sql

# 3. 启动应用服务
docker-compose -f docker-compose.prod.yml up -d backend

# 4. 验证服务
curl -f http://localhost:8000/health

# 5. 切换流量
# 更新 DNS 或负载均衡配置
```

---

## 10. 故障排查

### 10.1 常见问题排查

#### 服务启动失败

```bash
# 1. 检查容器状态
docker-compose ps

# 2. 查看详细日志
docker-compose logs backend

# 3. 检查端口占用
netstat -tlnp | grep 8000

# 4. 检查环境变量
docker-compose config
```

#### 数据库连接问题

```bash
# 1. 检查数据库健康状态
docker exec baixing_db_prod pg_isready -U postgres

# 2. 测试数据库连接
docker exec -it baixing_db_prod psql -U postgres -d baixing_law

# 3. 检查连接数
docker exec baixing_db_prod psql -U postgres -c "SELECT count(*) FROM pg_stat_activity;"

# 4. 检查慢查询
docker exec baixing_db_prod psql -U postgres -c "SELECT * FROM pg_stat_statements ORDER BY total_time DESC LIMIT 10;"
```

#### Redis 连接问题

```bash
# 1. 检查 Redis 健康状态
docker exec baixing_redis_prod redis-cli -a ${REDIS_PASSWORD} ping

# 2. 查看 Redis 信息
docker exec baixing_redis_prod redis-cli -a ${REDIS_PASSWORD} info

# 3. 检查内存使用
docker exec baixing_redis_prod redis-cli -a ${REDIS_PASSWORD} memory stats
```

### 10.2 性能优化

#### 数据库优化

```sql
-- 分析慢查询
EXPLAIN ANALYZE SELECT * FROM users WHERE email = 'test@example.com';

-- 创建索引
CREATE INDEX idx_users_email ON users(email);

-- 查看索引使用情况
SELECT * FROM pg_stat_user_indexes WHERE idx_scan = 0;
```

#### Redis 优化

```bash
# 查看键空间统计
redis-cli -a ${REDIS_PASSWORD} INFO keyspace

# 清理过期键
redis-cli -a ${REDIS_PASSWORD} FLUSHDB

# 查看大键
redis-cli -a ${REDIS_PASSWORD} --bigkeys
```

#### Backend 性能优化

```bash
# 增加 Worker 数量
# docker-compose.yml
command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4

# 启用连接池
# backend/app/database/engine.py
engine = create_async_engine(
    DATABASE_URL,
    pool_size=20,
    max_overflow=10,
    pool_pre_ping=True,
)
```

### 10.3 紧急响应流程

#### 服务中断响应

```
1. 立即通知 (5分钟内)
   - 发送告警到 #incidents 频道
   - 通知 on-call 工程师

2. 快速评估 (10分钟内)
   - 确认影响范围
   - 确定服务等级

3. 止血措施 (30分钟内)
   - 启用备用服务
   - 回滚到上一个稳定版本

4. 根因分析 (2小时内)
   - 收集日志和监控数据
   - 确定故障原因

5. 修复验证 (4小时内)
   - 部署修复
   - 验证功能正常

6. 事后复盘 (24小时内)
   - 编写事件报告
   - 制定改进措施
```

#### 联系信息

| 角色 | 联系方式 | 响应时间 |
|------|----------|----------|
| 值班工程师 | on-call@company.com | 15分钟 |
| 技术负责人 | tech-lead@company.com | 30分钟 |
| 安全事件 | security@company.com | 立即 |

---

## 11. 新增功能部署说明 (阶段三)

### 11.1 新增功能概述

阶段三新增以下功能模块：

| 功能模块 | 说明 | 相关路由 |
|----------|------|----------|
| 会员功能 | 会员订阅、权益管理 | `/api/v1/membership/*` |
| 视频咨询 | 实时视频咨询服务 | `/api/v1/video-consultation/*` |
| 法律文书商城 | 法律文书模板下载与积分兑换 | `/api/v1/legal-documents/*` |
| 推荐系统 | 个性化内容推荐 | `/api/v1/recommendation/*` |

### 11.2 环境变量配置

#### 会员功能配置

```bash
# 会员功能开关
MEMBERSHIP_ENABLED=true

# 会员定价（单位：元）
MEMBERSHIP_PRICING_MONTHLY=29      # 月卡
MEMBERSHIP_PRICING_ANNUAL=299      # 年卡
MEMBERSHIP_PRICING_LIFETIME=999    # 终身会员
```

#### 视频咨询功能配置

```bash
# 视频咨询功能开关
VIDEO_CONSULTATION_ENABLED=true

# 基础咨询费用（单位：元/分钟）
VIDEO_CONSULTATION_BASE_FEE=99

# 腾讯云 TRTC SDK 配置
TRTC_SDK_ID=your_trtc_sdk_id
TRTC_SDK_KEY=your_trtc_sdk_key
```

> **注意**: TRTC SDK ID 和密钥需在 [腾讯云控制台](https://console.cloud.tencent.com/trtc) 申请。

#### 法律文书商城配置

```bash
# 法律文书商城开关
LEGAL_DOCUMENT_ENABLED=true

# 积分兑换比例（1 元 = 100 积分）
LEGAL_DOCUMENT_INTEGRAL_RATIO=100
```

#### 推荐系统配置

```bash
# 推荐系统开关
RECOMMENDATION_ENABLED=true

# 推荐缓存 TTL（单位：秒）
RECOMMENDATION_CACHE_TTL=3600
```

### 11.3 数据库迁移

确保以下迁移文件已执行：

```bash
# 查看当前迁移状态
docker exec -it baixing_backend_prod alembic current

# 执行所有迁移
docker exec -it baixing_backend_prod alembic upgrade head
```

#### 关键迁移文件

| 迁移文件 | 说明 |
|----------|------|
| `u3v4w5x6y7z8_add_user_onboarding_table.py` | 用户 Onboarding 表 |
| `u4w5x6y7z8_add_memberships_table.py` | 会员表 |
| `add_notification_read_at.py` | 通知已读字段 |
| `add_legal_document_tables.py` | 法律文书表 |

### 11.4 服务健康检查

```bash
# 检查后端服务
curl -f http://localhost:8000/health

# 检查会员功能
curl -f http://localhost:8000/api/v1/membership/plans

# 检查推荐功能
curl -f http://localhost:8000/api/v1/recommendation/home

# 检查法律文书商城
curl -f http://localhost:8000/api/v1/legal-documents/list
```

### 11.5 故障排查

#### 会员功能无法访问

```bash
# 检查环境变量
docker exec baixing_backend_prod env | grep MEMBERSHIP

# 查看服务日志
docker-compose logs -f backend | grep membership
```

#### 视频咨询连接失败

```bash
# 检查 TRTC 配置
docker exec baixing_backend_prod env | grep TRTC

# 检查网络连通性
docker exec baixing_backend_prod ping console.cloud.tencent.com
```

#### 推荐结果为空

```bash
# 清除推荐缓存
docker exec baixing_redis_prod redis-cli -a ${REDIS_PASSWORD} KEYS "recommendation:*"

# 检查推荐系统日志
docker-compose logs -f backend | grep recommendation
```

---

## 附录

### 常用命令速查

```bash
# 服务管理
docker-compose up -d              # 启动服务
docker-compose down                # 停止服务
docker-compose restart backend     # 重启后端

# 日志查看
docker-compose logs -f backend     # 实时日志
docker-compose logs --tail=100 backend  # 最近100行

# 数据库操作
docker exec -it baixing_db_prod psql -U postgres  # 连接数据库

# Redis 操作
docker exec -it baixing_redis_prod redis-cli -a ${REDIS_PASSWORD}  # 连接 Redis

# 迁移操作
docker exec -it baixing_backend_prod alembic upgrade head  # 执行迁移

# 健康检查
curl http://localhost:8000/health   # 后端健康检查
curl http://localhost:8000/metrics # Prometheus 指标
```

### 相关文档

- [开发文档](./DEVELOPMENT.md) - 开发环境配置
- [API 文档](./API_ADMIN_V1.md) - 后端 API 接口
- [Helm Chart 文档](../helm/baixing-assistant/README.md) - K8s 部署详情