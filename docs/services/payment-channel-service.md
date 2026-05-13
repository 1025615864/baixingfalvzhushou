# 支付通道服务 (Payment Channel Service)

## 服务概览

| 属性 | 值 |
|------|-----|
| 服务名称 | payment-channel-service |
| 端口 | 8002 |
| 基础路径 | /api/v1/payment |
| 技术栈 | FastAPI + SQLAlchemy 2.0 + PostgreSQL + Redis |
| 数据库 | payment_channel_service |
| 健康检查 | GET /health |
| 就绪检查 | GET /health/ready |

## 服务描述

支付通道服务负责统一管理多渠道支付，支持支付宝和微信支付两种通道适配。提供支付订单创建、支付发起、回调处理（含幂等校验）、退款管理等功能。支付完成后通过 Kafka 发布事件通知下游服务。

## API 端点

### 支付订单 (order.py)

| 方法 | 路径 | 说明 | 认证 |
|------|------|------|------|
| POST | /api/v1/payment/orders | 创建支付订单（30分钟过期） | 否 |
| GET | /api/v1/payment/orders | 查询用户订单列表（分页，支持状态筛选） | 否 |
| GET | /api/v1/payment/orders/{order_no} | 根据订单号查询订单详情 | 否 |
| POST | /api/v1/payment/orders/{order_no}/pay | 发起支付，返回支付URL/二维码 | 否 |
| GET | /api/v1/payment/orders/{order_no}/status | 查询支付状态（含通道侧状态） | 否 |

### 支付回调 (callback.py)

| 方法 | 路径 | 说明 | 认证 |
|------|------|------|------|
| POST | /api/v1/payment/callbacks/alipay | 支付宝异步回调通知 | 否 |
| POST | /api/v1/payment/callbacks/wechat | 微信支付异步回调通知 | 否 |

### 退款管理 (refund.py)

| 方法 | 路径 | 说明 | 认证 |
|------|------|------|------|
| POST | /api/v1/payment/orders/{order_no}/refund | 发起退款（全额或部分） | 否 |
| POST | /api/v1/payment/refund/{provider} | 退款回调通知（alipay/wechat） | 否 |

## 数据模型

| 模型 | 表名 | 说明 |
|------|------|------|
| PaymentOrder | payment_orders | 支付订单，含订单号/金额/状态/通道/交易号 |
| PaymentCallback | payment_callbacks | 支付回调记录，含原始载荷 |
| PaymentRefund | payment_refunds | 退款记录，含退款号/金额/状态/通道退款号 |

## 关联服务

| 关联服务 | 通信方式 | 说明 |
|----------|----------|------|
| order-service | Kafka | 支付完成后发布 PaymentCompletedEvent |
| user-service | HTTP | 查询用户信息、会员升级 |
| 支付宝 | HTTP | 支付宝支付通道API |
| 微信支付 | HTTP | 微信支付通道API |

## 配置项

| 环境变量 | 默认值 | 说明 |
|----------|--------|------|
| DATABASE_URL | postgresql+asyncpg://user:pass@localhost:5432/payment_channel_service | 数据库连接 |
| REDIS_URL | redis://localhost:6379/0 | Redis连接 |
| ALIPAY_APP_ID | (空) | 支付宝应用ID |
| ALIPAY_PRIVATE_KEY | (空) | 支付宝应用私钥 |
| ALIPAY_PUBLIC_KEY | (空) | 支付宝公钥 |
| ALIPAY_GATEWAY_URL | https://openapi.alipay.com/gateway.do | 支付宝网关地址 |
| ALIPAY_NOTIFY_URL | (空) | 支付宝回调通知URL |
| WECHATPAY_MCH_ID | (空) | 微信支付商户号 |
| WECHATPAY_PRIVATE_KEY | (空) | 微信支付商户私钥 |
| WECHATPAY_API_V3_KEY | (空) | 微信支付APIv3密钥 |
| WECHATPAY_APP_ID | (空) | 微信支付应用ID |
| WECHATPAY_CERT_PATH | (空) | 微信支付证书路径 |
| WECHATPAY_NOTIFY_URL | (空) | 微信支付回调通知URL |
| KAFKA_BOOTSTRAP_SERVERS | localhost:9092 | Kafka地址 |
| CONSUL_ENABLED | false | 是否启用Consul服务注册 |

## 部署信息

- Dockerfile: services/payment-channel-service/Dockerfile
- 健康检查: /health
- 资源限制: CPU 0.5核 / 内存 512MB
