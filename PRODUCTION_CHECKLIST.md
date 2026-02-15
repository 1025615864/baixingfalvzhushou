# 生产环境部署检查清单

## 部署前必须完成

### 1. 环境配置

- [ ] 复制 `.env.example` 到 `.env.production`
- [ ] 设置 `DEBUG=False`
- [ ] 配置 `DATABASE_URL` (使用PostgreSQL，非SQLite)
- [ ] 配置 `REDIS_URL`

### 2. 安全密钥

- [ ] 生成CSRF密钥: `openssl rand -hex 32`
  ```bash
  # 设置到环境变量
  CSRF_SECRET_KEY=<生成的密钥>
  ```

- [ ] 生成Prometheus认证令牌: `openssl rand -hex 32`
  ```bash
  METRICS_AUTH_TOKEN=<生成的令牌>
  ```

- [ ] 生成JWT RSA密钥对:
  ```bash
  openssl genrsa -out private_key.pem 2048
  openssl rsa -in private_key.pem -pubout -out public_key.pem
  ```
  将内容设置到:
  - `JWT_RSA_PRIVATE_KEY` (私钥内容，包含BEGIN/END行)
  - `JWT_RSA_PUBLIC_KEY` (公钥内容)

- [ ] 设置支付回调密钥 (至少16字符):
  ```bash
  PAYMENT_WEBHOOK_SECRET=<你的密钥>
  ```

### 3. CORS配置

- [ ] 配置允许的前端域名:
  ```bash
  CORS_ALLOW_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
  ```

### 4. 前端配置

- [ ] 设置 `VITE_DEV_MODE=false`
- [ ] 配置正确的API地址

### 5. 第三方服务

- [ ] 配置支付宝密钥 (如使用)
- [ ] 配置微信支付密钥 (如使用)
- [ ] 配置Sentry DSN (错误追踪)
- [ ] 配置短信服务提供商

### 6. 数据库

- [ ] 运行数据库迁移:
  ```bash
  cd backend
  alembic upgrade head
  ```

- [ ] 验证迁移成功

### 7. 监控

- [ ] 验证Prometheus可访问 (/metrics端点需要认证)
- [ ] 验证健康检查端点:
  - `/health`
  - `/api/health`
  - `/health/detailed`
- [ ] 配置Alertmanager告警规则

### 8. 测试

- [ ] 运行完整测试套件:
  ```bash
  cd backend
  pytest --cov=app --cov-fail-under=62
  ```

- [ ] 手动测试关键流程:
  - 用户注册/登录
  - 支付流程
  - AI咨询
  - 文件上传

## 部署后验证

### 1. 安全验证

- [ ] 确认 `/docs` 和 `/redoc` 不可访问 (返回404)
- [ ] 确认 `/metrics` 需要认证
- [ ] 确认DEBUG模式已关闭

### 2. 功能验证

- [ ] 健康检查返回正常
- [ ] 用户可正常登录
- [ ] 数据库连接正常
- [ ] Redis连接正常
- [ ] AI服务可用

### 3. 性能验证

- [ ] 响应时间符合预期
- [ ] 无明显性能瓶颈

## 常用命令

```bash
# 生成32字节随机密钥
openssl rand -hex 32

# 生成RSA密钥对
openssl genrsa -out private_key.pem 2048
openssl rsa -in private_key.pem -pubout -out public_key.pem

# 查看密钥内容 (用于复制到环境变量)
cat private_key.pem
cat public_key.pem

# 运行数据库迁移
alembic upgrade head

# 运行测试
pytest --cov=app

# 检查应用健康
curl http://localhost:8000/health
curl http://localhost:8000/health/detailed
```

## 紧急回滚

如发现问题需要回滚:

1. 切换到上一个稳定版本
2. 重启服务
3. 检查日志确认回滚成功
4. 通知相关团队
