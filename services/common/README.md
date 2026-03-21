# 服务通信模块

提供微服务间通信的统一接口。

## 目录结构

```
common/
├── proto/          # Protocol Buffer 定义（未来可扩展）
├── events/          # Kafka 事件定义
├── client/          # HTTP 客户端
│   ├── http_client.py      # HTTP 调用客户端
│   └── service_router.py   # 服务路由
└── config/          # 通用配置
```

## 服务列表

| 服务 | 端口 | 描述 |
|-----|------|------|
| user-service | 8001 | 用户服务 |
| payment-channel-service | 8002 | 支付通道服务 |
| payment-accounting-service | 8003 | 账务服务 |
| legal-service | 8004 | 法律服务 |
| ai-service | 8005 | AI服务 |
| news-service | 8006 | 新闻服务 |
| community-service | 8007 | 社区服务 |
| points-service | 8008 | 积分服务 |
| notification-service | 8009 | 通知服务 |
| recommendation-service | 8010 | 推荐服务 |
| search-service | 8011 | 搜索服务 |
