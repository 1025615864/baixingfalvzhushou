# Docker 部署指南

本文档说明如何使用 Docker Compose 部署百姓法律助手项目。

## 目录

- [快速开始](#快速开始)
- [环境要求](#环境要求)
- [配置文件说明](#配置文件说明)
- [部署模式](#部署模式)
- [服务端口映射](#服务端口映射)
- [常见问题](#常见问题)

## 快速开始

### 1. 克隆项目

```bash
git clone <repository-url>
cd baixingfalvzhushou
```

### 2. 配置环境变量

```bash
# 复制环境变量模板
cp .env.example .env

# 生成安全密钥
bash scripts/generate_secrets.sh

# 编辑 .env 文件配置必要参数
vim .env  # Windows: notepad .env
```

### 3. 启动项目

```bash
# 方式一：使用启动脚本（推荐）
bash scripts/start.sh --dev   # 开发环境（核心服务）
bash scripts/start.sh --full  # 完整微服务集群

# 方式二：直接使用 Docker Compose
docker compose -f docker-compose.dev.yml up -d  # 开发环境
docker compose up -d                            # 完整集群
```

### 4. 验证服务

```bash
# 使用健康检查脚本
bash scripts/health-check.sh

# 或手动检查
curl http://localhost:8000/health
curl http://localhost:3000
```

## 环境要求

- **Docker**: 20.10+
- **Docker Compose**: v2.0+
- **内存**: 
  - 开发环境：最低 4GB
  - 完整集群：最低 16GB
- **磁盘空间**: 至少 10GB

## 配置文件说明

### docker-compose.yml

完整微服务集群配置，包含：
- PostgreSQL 数据库
- Redis 缓存
- 后端 API 服务
- 前端 React 应用
- 11 个微服务
- Prometheus + Grafana + Alertmanager 监控系统

### docker-compose.dev.yml

轻量开发环境，仅包含核心服务：
- PostgreSQL 数据库
- Redis 缓存
- 后端 API 服务（带热重载）
- 前端 React 应用

### .env.example

环境变量模板，包含：
- 数据库配置
- 安全密钥
- AI 服务配置
- 监控配置

## 部署模式

### 开发环境

适合日常开发和功能测试：

```bash
bash scripts/start.sh --dev
```

**特点**:
- 启动快速，资源占用少
- 后端支持代码热重载
- 仅包含核心功能

### 完整微服务集群

适合集成测试和生产环境模拟：

```bash
bash scripts/start.sh --full
```

**特点**:
- 包含所有 11 个微服务
- 完整的监控系统
- 模拟真实生产环境

### 仅启动数据库和Redis

如果只需要数据库和缓存：

```bash
docker compose up -d db redis
```

## 服务端口映射

### 核心服务

| 服务 | 容器名 | 端口 | 说明 |
|------|--------|------|------|
| PostgreSQL | baixing_db | 5433 | 主数据库 |
| Redis | baixing_redis | 16379 | 缓存 |
| Backend API | baixing_backend | 8000 | 主后端 |
| Frontend | baixing_frontend | 3000 | 前端 |

### 微服务

| 服务 | 端口 | 说明 |
|------|------|------|
| 用户服务 | 8001 | 用户管理、认证 |
| 订单服务 | 8004 | 订单处理 |
| 通知服务 | 8005 | 消息通知 |
| 新闻服务 | 8006 | 法律资讯 |
| 社区服务 | 8007 | 社区互动 |
| 法律服务 | 8008 | 法律咨询 |
| 搜索服务 | 8009 | 全文搜索 |
| 推荐服务 | 8010 | 智能推荐 |
| 积分服务 | 8012 | 积分系统 |
| 归档服务 | 8013 | 数据归档 |
| 知识库服务 | 8081 | 法律知识库 |

### 监控系统

| 服务 | 端口 | 说明 |
|------|------|------|
| Prometheus | 19090 | 指标收集 |
| Grafana | 3001 | 监控面板 (admin/admin123) |
| Alertmanager | 9200 | 告警管理 |

## 常用命令

### 查看服务状态

```bash
docker compose ps
```

### 查看日志

```bash
# 查看所有服务日志
docker compose logs -f

# 查看特定服务日志
docker compose logs -f backend
docker compose logs -f legal-service
```

### 停止服务

```bash
# 停止并保留数据
docker compose down

# 停止并删除数据卷
docker compose down -v
```

### 重启服务

```bash
docker compose restart backend
```

### 进入容器

```bash
docker compose exec backend bash
docker compose exec db psql -U postgres
docker compose exec redis redis-cli -a $REDIS_PASSWORD
```

### 重新构建

```bash
# 重新构建所有服务
docker compose up -d --build

# 重新构建单个服务
docker compose up -d --build backend
```

## 数据库初始化

首次启动时，数据库会自动创建。如需手动初始化：

```bash
# 进入数据库容器
docker compose exec db psql -U postgres -d baixing_law

# 查看数据库列表
\l

# 查看表
\dt
```

## 健康检查

所有服务都配置了健康检查，可以通过以下方式查看：

```bash
# 查看服务健康状态
docker compose ps

# 使用健康检查脚本
bash scripts/health-check.sh
```

## 常见问题

### 1. 端口冲突

如果端口被占用，可以修改 `.env` 文件或 `docker-compose.yml` 中的端口映射。

### 2. 容器启动失败

查看日志定位问题：

```bash
docker compose logs <service-name>
```

### 3. 数据库连接失败

确保 PostgreSQL 已启动并且端口正确：

```bash
docker compose ps db
docker compose logs db
```

### 4. 内存不足

完整集群需要较多内存，可以通过以下方式减少资源占用：

- 使用 `docker-compose.dev.yml` 仅启动核心服务
- 在 `.env` 中调整资源限制
- 注释掉不需要的微服务

### 5. 权限问题

如果遇到权限问题，确保以正确方式运行 Docker：

```bash
# Linux 用户加入 docker 组
sudo usermod -aG docker $USER
```

### 6. 数据持久化

数据卷默认持久化在 Docker 管理目录中：

```bash
# 查看数据卷
docker volume ls | grep baixing

# 备份数据卷
docker run --rm -v baixing_postgres_data:/data -v $(pwd):/backup alpine tar czf /backup/postgres-backup.tar.gz -C /data .
```

## 生产部署注意事项

生产环境部署时，请：

1. 修改所有默认密码
2. 配置 HTTPS 证书
3. 启用防火墙规则
4. 配置日志轮转
5. 设置自动备份
6. 配置监控告警
7. 使用外部负载均衡

## 性能优化

### 资源限制

在 `docker-compose.yml` 中可以调整资源限制：

```yaml
deploy:
  resources:
    limits:
      cpus: '1'
      memory: 1G
    reservations:
      cpus: '0.5'
      memory: 512M
```

### 日志管理

配置日志轮转避免磁盘占满：

```yaml
logging:
  driver: "json-file"
  options:
    max-size: "50m"
    max-file: "3"
```

## 故障排查

### 1. 服务无法启动

```bash
# 查看详细日志
docker compose logs --tail=100 <service-name>

# 检查端口占用
netstat -tulpn | grep <port>

# 检查容器状态
docker compose ps
```

### 2. 服务间通信失败

```bash
# 检查网络连接
docker network ls
docker network inspect baixing_backend-network

# 测试服务连通性
docker compose exec backend ping db
docker compose exec backend ping redis
```

### 3. 数据库迁移

```bash
# 进入后端容器执行迁移
docker compose exec backend python -m alembic upgrade head
```

## 安全建议

1. **永远不要**将 `.env` 文件提交到版本控制
2. **定期更新**所有密码和密钥
3. **使用 HTTPS** 加密外部访问
4. **限制端口** 暴露范围
5. **启用防火墙** 规则
6. **定期备份** 数据卷
7. **监控异常** 访问行为
