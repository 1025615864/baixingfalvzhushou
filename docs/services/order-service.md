# 订单服务 (Order Service)

## 服务概览

| 属性 | 值 |
|------|-----|
| 服务名称 | order-service |
| 端口 | 8004 |
| 基础路径 | /api/v1/orders |
| 技术栈 | FastAPI + SQLAlchemy 2.0 + PostgreSQL |
| 数据库 | order_service |
| 健康检查 | GET /health |
| 就绪检查 | GET /health/ready |

## 服务描述

订单服务负责订单全生命周期管理，包括订单创建、状态流转、取消和查询。集成 SAGA 分布式事务编排，与支付通道服务协作完成支付-订单的最终一致性。支持法律咨询、文档服务、会员等多种订单类型。

## API 端点

### 订单管理 (orders.py)

| 方法 | 路径 | 说明 | 认证 |
|------|------|------|------|
| GET | /orders | 查询用户订单列表（分页，支持状态筛选） | 否 |
| GET | /orders/{order_id} | 根据订单ID或订单号查询订单详情 | 否 |
| POST | /orders | 创建订单（自动生成订单号，计算实付金额） | 否 |
| PUT | /orders/{order_id}/status | 更新订单状态 | 否 |
| DELETE | /orders/{order_id}/cancel | 取消订单 | 否 |

## 数据模型

| 模型 | 表名 | 说明 |
|------|------|------|
| Order | orders | 订单主表，含订单号/类型/金额/状态/Saga事务ID/业务关联 |
| OrderItem | order_items | 订单明细，含商品名称/数量/单价/总价 |

### 订单状态枚举

| 状态 | 值 | 说明 |
|------|-----|------|
| PENDING | pending | 待支付 |
| PAID | paid | 已支付 |
| SHIPPED | shipped | 已发货 |
| COMPLETED | completed | 已完成 |
| CANCELLED | cancelled | 已取消 |
| REFUNDED | refunded | 已退款 |
| FAILED | failed | 失败 |

### 订单类型枚举

| 类型 | 值 | 说明 |
|------|-----|------|
| LEGAL_CONSULTATION | legal_consultation | 法律咨询 |
| DOCUMENT_SERVICE | document_service | 文档服务 |
| MEMBERSHIP | membership | 会员购买 |
| OTHER | other | 其他 |

### 支付方式枚举

| 方式 | 值 | 说明 |
|------|-----|------|
| ALIPAY | alipay | 支付宝 |
| WECHATPAY | wechatpay | 微信支付 |
| IKUNPAY | ikunpay | 自有支付 |
| BALANCE | balance | 余额支付 |

## 关联服务

| 关联服务 | 通信方式 | 说明 |
|----------|----------|------|
| payment-channel-service | HTTP/Saga | SAGA分布式事务编排，支付-订单最终一致性 |
| user-service | HTTP | 查询用户信息、会员状态 |

## 配置项

| 环境变量 | 默认值 | 说明 |
|----------|--------|------|
| DATABASE_URL | (未在settings中定义，需通过环境变量配置) | 数据库连接 |
| ENABLE_SAGA_PERSISTENCE | false | 是否启用Saga持久化 |
| SERVICE_PORT | 8014 | 服务端口 |
| CONSUL_ENABLED | false | 是否启用Consul服务注册 |
| OTEL_EXPORTER_OTLP_ENDPOINT | (空) | OpenTelemetry导出端点 |

## 部署信息

- Dockerfile: services/order-service/Dockerfile
- 健康检查: /health
- 资源限制: CPU 0.5核 / 内存 512MB
