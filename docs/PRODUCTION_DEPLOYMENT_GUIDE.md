# 🚀 百姓法律助手 - 生产环境部署指南

**适用版本**: 生产环境部署  
**部署方式**: Docker Compose (推荐) / 裸机部署

---

## 一、环境要求

| 组件 | 版本 | 说明 |
|------|------|------|
| OS | Ubuntu 22.04+ / CentOS 8+ | 推荐 Ubuntu |
| Docker | 24.0+ | 含 Docker Compose v2 |
| CPU | 4 核+ | 最低 4 核，推荐 8 核 |
| RAM | 8GB+ | 最低 8GB，推荐 16GB |
| 磁盘 | 50GB+ | SSD 推荐 |
| 域名 | 1 个 | 用于 HTTPS 证书 |

---

## 二、部署前准备

### 2.1 安装依赖

```bash
# Ubuntu
sudo apt update
sudo apt install -y docker.io docker-compose-v2 certbot nginx

# CentOS
sudo dnf install -y docker docker-compose certbot nginx
sudo systemctl enable docker
sudo systemctl start docker
```

### 2.2 生成安全密钥

```bash
cd /opt/baixing-assistant

# 生成密钥
bash scripts/generate_secrets.sh

# 记录输出，后续配置 .env 文件
```

### 2.3 申请 SSL 证书

```bash
# Let's Encrypt 免费证书
sudo certbot certonly --standalone -d your-domain.com

# 证书路径
# /etc/letsencrypt/live/your-domain.com/fullchain.pem
# /etc/letsencrypt/live/your-domain.com/privkey.pem

# 复制到项目目录
sudo mkdir -p /opt/baixing-assistant/nginx/ssl
sudo cp /etc/letsencrypt/live/your-domain.com/fullchain.pem /opt/baixing-assistant/nginx/ssl/cert.pem
sudo cp /etc/letsencrypt/live/your-domain.com/privkey.pem /opt/baixing-assistant/nginx/ssl/privkey.pem
```

### 2.4 配置环境变量

```bash
# 复制模板
cp .env.example .env

# 编辑环境变量
vim .env
```

必须修改的配置：

| 变量 | 说明 | 示例值 |
|------|------|--------|
| `POSTGRES_PASSWORD` | 数据库密码 | 强密码 (16位+) |
| `SECRET_KEY` | Flask/FastAPI 密钥 | `openssl rand -hex 32` |
| `JWT_SECRET_KEY` | JWT 签名密钥 | `openssl rand -hex 32` |
| `REDIS_PASSWORD` | Redis 密码 | 强密码 (16位+) |
| `CORS_ALLOW_ORIGINS` | 允许跨域的域名 | `["https://your-domain.com"]` |
| `OPENAI_API_KEY` | AI 服务 API Key | `sk-xxx` |

---

## 三、Docker Compose 部署

### 3.1 基础部署（BFF + 数据库 + 缓存）

```bash
# 启动所有服务
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# 查看服务状态
docker compose ps

# 查看日志
docker compose logs -f
```

### 3.2 完整微服务部署

```bash
# 启动完整微服务集群
docker compose -f docker-compose.yml -f docker-compose.prod.yml -f docker-compose.microservices.yml up -d

# 验证服务健康状态
curl -f http://localhost:8000/health
curl -f http://localhost:8008/health
curl -f http://localhost:8007/health
```

### 3.3 数据库初始化

```bash
# 执行数据库初始化脚本
docker exec -i baixing_db_prod bash < scripts/init_db_prod.sh
```

### 3.4 运行数据库迁移

```bash
# BFF 层迁移
docker exec baixing_backend_prod alembic upgrade head

# 各微服务迁移（如有）
docker exec baixing_legal_service_prod alembic upgrade head
docker exec baixing_community_service_prod alembic upgrade head
```

---

## 四、Nginx 配置

### 4.1 配置 HTTPS

```bash
# 复制 SSL 配置
cp nginx/nginx-ssl-prod.conf /etc/nginx/conf.d/baixing.conf

# 替换域名
sed -i 's/YOUR_DOMAIN\.COM/your-domain.com/g' /etc/nginx/conf.d/baixing.conf

# 测试配置
sudo nginx -t

# 重载 Nginx
sudo systemctl reload nginx
```

### 4.2 配置自动续期

```bash
# 添加 Let's Encrypt 自动续期
sudo crontab -e

# 添加以下行（每天凌晨 2 点检查续期）
0 2 * * * certbot renew --quiet && systemctl reload nginx
```

---

## 五、配置备份

### 5.1 设置 Crontab

```bash
sudo crontab -e

# 添加备份任务
# 每天 2:00 备份数据库
0 2 * * * /opt/baixing-assistant/scripts/backup_db_prod.sh >> /var/log/baixing-backup.log 2>&1

# 每小时备份 Redis
0 * * * * /opt/baixing-assistant/scripts/backup_redis_prod.sh >> /var/log/baixing-backup.log 2>&1
```

### 5.2 备份验证

```bash
# 手动执行备份测试
bash scripts/backup_db_prod.sh
bash scripts/backup_redis_prod.sh

# 查看备份文件
ls -lh /opt/baixing-backups/db/
ls -lh /opt/baixing-backups/redis/
```

---

## 六、验证部署

### 6.1 健康检查

```bash
# 前端
curl -f https://your-domain.com/

# 后端 API
curl -f https://your-domain.com/api/health

# Swagger 文档
curl -f https://your-domain.com/api/docs

# 微服务（内部）
curl -f http://localhost:8008/health
curl -f http://localhost:8007/health
curl -f http://localhost:8006/health
```

### 6.2 注册测试

```bash
# 测试注册接口
curl -X POST https://your-domain.com/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"phone":"13800138000","password":"Test123456"}'
```

### 6.3 登录测试

```bash
# 测试登录接口
curl -X POST https://your-domain.com/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"phone":"13800138000","password":"Test123456"}'
```

---

## 七、监控与告警

### 7.1 访问 Prometheus

```
http://your-domain.com:9090
```

### 7.2 访问 Grafana

```
http://your-domain.com:3000
默认用户名/密码: admin/admin
```

### 7.3 查看告警规则

```bash
# 查看 Prometheus 告警规则
curl http://localhost:9090/api/v1/rules | jq '.data.groups[].rules[] | select(.type=="alerting")'
```

---

## 八、常见问题

### 8.1 容器启动失败

```bash
# 查看容器日志
docker compose logs <service-name>

# 重启容器
docker compose restart <service-name>

# 重新创建容器
docker compose up -d <service-name> --force-recreate
```

### 8.2 数据库连接失败

```bash
# 检查数据库是否运行
docker compose ps db

# 检查网络连接
docker compose exec backend ping db

# 查看数据库日志
docker compose logs db
```

### 8.3 SSL 证书问题

```bash
# 检查证书
openssl s_client -connect your-domain.com:443 -servername your-domain.com

# 手动续期证书
sudo certbot renew --force-renewal
```

### 8.4 磁盘空间不足

```bash
# 清理 Docker 镜像
docker system prune -a

# 清理旧备份
find /opt/baixing-backups -mtime +30 -delete

# 清理旧日志
find /var/log -name "*.log" -mtime +7 -delete
```

---

## 九、升级部署

```bash
# 拉取最新代码
cd /opt/baixing-assistant
git pull origin main

# 停止服务
docker compose -f docker-compose.yml -f docker-compose.prod.yml down

# 重新构建并启动
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build

# 运行迁移
docker compose exec backend alembic upgrade head
```

---

## 十、回滚方案

```bash
# 查看历史版本
git log --oneline -10

# 回滚到指定版本
git checkout <commit-hash>

# 重新部署
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build

# 数据库回滚（谨慎操作）
docker compose exec backend alembic downgrade -1
```

---

*部署指南 - 2026-05-07*
