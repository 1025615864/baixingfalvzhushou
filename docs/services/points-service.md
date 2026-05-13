# 积分服务

## 服务概览

| 属性 | 值 |
|------|-----|
| 服务名称 | points-service |
| 端口 | 8012 |
| 基础路径 | /api/v1/points |
| 技术栈 | FastAPI + SQLAlchemy 2.0 + PostgreSQL + Redis + Kafka |
| 数据库 | points_service |
| 健康检查 | GET /health |
| 就绪检查 | GET /health/ready |

## 服务描述

积分服务负责管理用户积分的获取、消费和历史记录。支持积分赚取与兑换、每日签到、积分商城等功能，并通过 Kafka 消费用户行为事件自动发放积分。

## API 端点

### 积分管理 (points.py)

| 方法 | 路径 | 说明 | 认证 |
|------|------|------|------|
| GET | /points/{user_id} | 获取用户积分余额 | 否 |
| GET | /points/{user_id}/history | 获取积分变动历史（分页） | 否 |
| POST | /points/earn | 增加积分 | 否 |
| POST | /points/redeem | 兑换积分（余额不足返回400） | 否 |

## 数据模型

### PointsUser

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer | 主键 |
| user_id | Integer | 用户ID（唯一索引） |
| balance | Integer | 当前余额 |
| total_earned | Integer | 累计获得 |
| total_spent | Integer | 累计消费 |

### PointsHistory

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer | 主键 |
| user_id | Integer | 用户ID（索引） |
| change | Integer | 变动值（正为获取，负为消费） |
| balance_after | Integer | 变动后余额 |
| source | String(50) | 来源标识 |
| reference_id | String(100) | 关联ID |
| description | String(200) | 描述 |
| created_at | DateTime | 创建时间（索引） |

### PointsMallItem

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer | 主键 |
| name | String(100) | 商品名称 |
| description | String(500) | 商品描述 |
| points_cost | Integer | 所需积分 |
| stock | Integer | 库存 |
| image_url | String(500) | 图片URL |
| status | String(20) | 状态（active/inactive） |

### PointsExchangeOrder

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer | 主键 |
| user_id | Integer | 用户ID（索引） |
| item_id | Integer | 商品ID |
| points_cost | Integer | 消耗积分 |
| status | String(20) | 订单状态（pending/completed） |

### DailyCheckIn

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer | 主键 |
| user_id | Integer | 用户ID（索引） |
| check_in_date | String(10) | 签到日期 |
| points_awarded | Integer | 获得积分 |

唯一索引：`ix_daily_check_in_user_date` (user_id, check_in_date)

## 关联服务

| 关联服务 | 通信方式 | 说明 |
|----------|----------|------|
| user-service | Kafka/HTTP | 消费用户注册、活跃事件发放积分 |
| order-service | Kafka | 消费订单完成事件发放积分 |
| backend-bff | HTTP | 通过 BFF 代理层对外提供 API |

## 配置项

| 环境变量 | 默认值 | 说明 |
|----------|--------|------|
| DATABASE_URL | postgresql+asyncpg://user:pass@localhost:5432/points | 数据库连接URL |
| DB_POOL_SIZE | 20 | 数据库连接池大小 |
| DB_MAX_OVERFLOW | 30 | 数据库连接池最大溢出 |
| REDIS_URL | redis://localhost:6379/0 | Redis连接URL |
| KAFKA_BOOTSTRAP_SERVERS | localhost:9092 | Kafka Broker地址 |
| OTEL_EXPORTER_OTLP_ENDPOINT | - | OpenTelemetry 链路追踪端点 |
| CONSUL_ENABLED | - | Consul 服务注册开关 |

## 部署信息

- Dockerfile: services/points-service/Dockerfile
- 健康检查: /health（含数据库就绪检查）
- 资源限制: CPU 0.5核 / 内存 512MB
