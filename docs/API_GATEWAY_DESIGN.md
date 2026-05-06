# API Gateway 架构设计 (APISIX)

## 1. 概述

本文档描述百姓助手项目 API Gateway 架构改进方案，采用 **APISIX** 作为统一 API 网关。

## 2. 为什么选择 APISIX

| 特性 | APISIX | Kong | 传统 Nginx |
|------|--------|------|------------|
| 性能 | ⭐⭐⭐⭐⭐ (异步) | ⭐⭐⭐⭐ | ⭐⭐⭐ |
| 插件扩展 | ⭐⭐⭐⭐⭐ (热加载) | ⭐⭐⭐⭐ | ⭐ |
| 学习曲线 | ⭐⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐⭐ |
| K8s 集成 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐ |
| 国产支持 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ |

## 3. 目标架构

```
                    ┌─────────────────────────────────────────────────────────────┐
                    │                         APISIX Gateway                        │
                    │  ┌─────────────┐ ┌─────────────┐ ┌─────────────────────────┐│
                    │  │  路由管理    │ │  认证授权    │ │    限流熔断             ││
                    │  │  /api/v1/* │ │  JWT验证    │ │   滑动窗口限流          ││
                    │  └─────────────┘ └─────────────┘ └─────────────────────────┘│
                    │  ┌─────────────┐ ┌─────────────┐ ┌─────────────────────────┐│
                    │  │  日志审计    │ │  安全头     │ │    监控指标             ││
                    │  │  请求日志    │ │  CORS/WAF  │ │   Prometheus          ││
                    │  └─────────────┘ └─────────────┘ └─────────────────────────┘│
                    └────────────────────────────┬────────────────────────────────┘
                                                  │
        ┌─────────────────┬─────────────────┬─────┴──────┬─────────────────┬──────────────┐
        │                 │                 │            │                 │              │
        ▼                 ▼                 ▼            ▼                 ▼              ▼
┌───────────────┐ ┌───────────────┐ ┌───────────────┐ ┌───────────────┐ ┌───────────────┐
│ User Service  │ │Payment Service│ │Legal Service  │ │ AI Service   │ │ News Service  │
│    :8001      │ │    :8002     │ │    :8004     │ │    :8005     │ │    :8006      │
└───────────────┘ └───────────────┘ └───────────────┘ └───────────────┘ └───────────────┘
```

## 4. APISIX 配置设计

### 4.1 目录结构

```
apisix/
├── config.yaml                 # APISIX 主配置
├── config虾/
│   ├── apisix.yml             # 路由配置
│   ├── upstream-*.yml          # 上游服务配置
│   └── plugin-*.yml            # 插件配置
├── apisix-admin/              # Admin API 配置
│   └── apisix-admin.yaml
├── Dashboard/                 # APISIX Dashboard
│   └── docker-compose.yml
└── ssl/                       # SSL 证书
    ├── server.crt
    └── server.key
```

### 4.2 APISIX 配置文件 (config.yaml)

```yaml
apisix:
  node_listen: 8080            # APISIX 监听端口
  enable_admin: true           # 开启 Admin API
  admin_key:
    - name: "admin"
      key: your-admin-key-here
      role: admin
    - name: "viewer"
      key: your-viewer-key-here
      role: viewer

  ssl:
    enable: true
    ssl_protocols: [TLSv1.2, TLSv1.3]

etcd:
  host: "http://etcd:2379"
  prefix: /apisix
  timeout: 30

plugins:
  - proxy-rewrite
  - cors
  - jwt-auth
  - limit-req
  - limit-count
  - limit-conn
  - rate-limit
  - rate-limit-by-key
  - grpc-transcode
  - prometheus
  - skywalking
  - opentelemetry
  - key-auth
  - wolf-rbac
  - hmac-auth
  - api-breaker
  - circuit-breaker
  - request-id
  - log-rotate
  - gzip

plugin_attr:
  prometheus:
    export_uri: /apisix/prometheus
    enable_export_server: true
```

### 4.3 路由配置示例 (apisix.yml)

```yaml
routes:
  # 用户服务路由
  - id: user-service
    uri: /api/v1/auth/*
    upstream:
      type: roundrobin
      nodes:
        - host: user-service
          port: 8001
          weight: 100
    plugins:
      jwt-auth:
        key: user-key
        secret: your-jwt-secret
      limit-req:
        rate: 100
        burst: 50
      cors:
        allow_origins: "*"
        allow_methods: GET,POST,PUT,DELETE,OPTIONS
        allow_headers: "*"

  # 支付服务路由
  - id: payment-service
    uri: /api/v1/payment/*
    upstream:
      type: roundrobin
      nodes:
        - host: payment-channel-service
          port: 8002
          weight: 100
    plugins:
      jwt-auth:
        key: user-key
      limit-req:
        rate: 50
        burst: 25
      api-breaker:
        break_response_code: 503
        unhealthy:
          http_status: 500
          failures: 3
        healthy:
          http_status: 200
          successes: 1

  # AI 服务路由 (支持 WebSocket)
  - id: ai-service
    uri: /api/v1/ai/*
    upstream:
      type: roundrobin
      nodes:
        - host: ai-service
          port: 8005
          weight: 100
    plugins:
      jwt-auth:
        key: user-key
      proxy-rewrite:
        headers:
          X-Request-ID: $request_id

  # 后端服务路由 (Legacy)
  - id: backend-service
    uri: /api/v1/*  # 匹配其他所有路由
    upstream:
      type: roundrobin
      nodes:
        - host: backend
          port: 8080
          weight: 100
    plugins:
      jwt-auth:
        key: user-key
      limit-req:
        rate: 200
        burst: 100
```

## 5. 插件配置

### 5.1 JWT 认证插件 (jwt-auth.yaml)

```yaml
consumers:
  - username: user-consumer
    plugins:
      jwt-auth:
        key: user-key
        secret: user-jwt-secret-key-min-32-chars
        algorithm: RS256

  - username: admin-consumer
    plugins:
      jwt-auth:
        key: admin-key
        secret: admin-jwt-secret-key-min-32-chars
        algorithm: RS256
```

### 5.2 限流插件 (rate-limit.yaml)

```yaml
# 全局限流策略
global:
  limit-req:
    rate: 1000
    burst: 500

# 服务级别限流
services:
  - name: payment-service
    limit-req:
      rate: 50
      burst: 25
    limit-count:
      count: 100
      time_window: 60

  - name: ai-service
    limit-req:
      rate: 100
      burst: 50
```

## 6. Docker Compose 部署

### 6.1 apisix/docker-compose.yml

```yaml
version: '3.8'

services:
  apisix:
    image: apache/apisix:3.9-debian
    container_name: apisix
    volumes:
      - ./config.yaml:/usr/local/apisix/conf/config.yaml:ro
      - ./ssl:/usr/local/apisix/conf/ssl:ro
    ports:
      - "8080:8080"      # APISIX 监听
      - "8443:8443"      # HTTPS
      - "9090:9090"      # Admin API
    environment:
      - APISIX_DEFER_INIT=true
    depends_on:
      - etcd
    networks:
      - baixing-network

  apisix-dashboard:
    image: apache/apisix-dashboard:3.0
    container_name: apisix-dashboard
    volumes:
      - ./dashboard/conf.yaml:/usr/local/apisix-dashboard/conf/conf.yaml:ro
    ports:
      - "9000:9000"
    depends_on:
      - etcd
    networks:
      - baixing-network

  etcd:
    image: bitnami/etcd:3.5
    container_name: etcd
    environment:
      - ALLOW_NONE_AUTHENTICATION=yes
      - ETCD_ADVERTISE_CLIENT_URLS=http://etcd:2379
    volumes:
      - etcd-data:/bitnami/etcd
    networks:
      - baixing-network

volumes:
  etcd-data:
    driver: local

networks:
  baixing-network:
    external: true
```

### 6.2 Dashboard 配置 (dashboard/conf.yaml)

```yaml
conf:
  etcd:
    endpoints:
      - "etcd:2379"
    username: ""
    password: ""

  db_database: apisix
  db_host: "127.0.0.1"
  db_port: 5432
  db_user: postgres
  db_password: ""
  db_sqlite_path: /usr/local/apisix-dateway/conf/apisix.db

server:
  listen:
    host: 0.0.0.0
    port: 9000
  allow_list:
    - 0.0.0.0/0
```

## 7. Kubernetes 部署

### 7.1 Helm Values (apisix/values.yaml)

```yaml
apisix:
  replicaCount: 2

  image:
    repository: apache/apisix
    tag: 3.9-debian

  service:
    type: ClusterIP
    ports:
      - name: http
        port: 80
        targetPort: 9080
      - name: https
        port: 443
        targetPort: 9443
      - name: admin
        port: 9090
        targetPort: 9090

  config:
    apisix:
      node_listen: 9080
      enable_admin: true
      ssl:
        enable: true
        protocols:
          - TLSv1.2
          - TLSv1.3

  plugins:
    - proxy-rewrite
    - cors
    - jwt-auth
    - limit-req
    - limit-count
    - prometheus
    - api-breaker
    - circuit-breaker
    - request-id
    - log-rotate

etcd:
  enabled: true
  replicaCount: 3

  image:
    repository: bitnami/etcd
    tag: 3.5

  auth:
    rbac:
      create: true
      user: root
      password: etcd-password

  persistence:
    enabled: true
    size: 10Gi

dashboard:
  enabled: true
  replicaCount: 1

  image:
    repository: apache/apisix-dashboard
    tag: 3.0

  service:
    type: ClusterIP
    port: 9000

ingress:
  enabled: true
  className: nginx
  annotations:
    kubernetes.io/ingress.class: nginx
  hosts:
    - host: api.baixing.local
      paths:
        - path: /
          pathType: Prefix
```

## 8. 迁移计划

### 8.1 Phase 1: 本地开发环境 (Week 1)
1. 启动 APISIX + etcd + Dashboard
2. 配置基本路由 (只做透传)
3. 验证路由正确性

### 8.2 Phase 2: 添加认证授权 (Week 2)
1. 配置 JWT 认证插件
2. 迁移现有 Token 验证逻辑到 APISIX
3. 测试认证流程

### 8.3 Phase 3: 添加限流熔断 (Week 3)
1. 配置限流策略
2. 配置熔断规则
3. 压力测试验证

### 8.4 Phase 4: 生产环境部署 (Week 4)
1. K8s 部署 APISIX
2. 配置 SSL/TLS
3. 配置监控告警
4. 切换生产流量 (蓝绿部署)

## 9. 监控配置

### 9.1 Prometheus Metrics

```yaml
# prometheus 抓取配置
scrape_configs:
  - job_name: 'apisix'
    static_configs:
      - targets: ['apisix:9090']
    metrics_path: /apisix/prometheus
```

### 9.2 Grafana Dashboard

APISIX 官方提供 Grafana Dashboard，导入 ID: `13013`

## 10. 回滚策略

1. **蓝绿部署**: 保留旧版本 APISIX，新版本验证通过后切换
2. **Nginx 回退**: 配置 Nginx 直接路由到后端服务，绕过 APISIX
3. **DNS 回退**: 切换回原有域名解析

## 11. 预期效果

| 指标 | 改进前 | 改进后 |
|------|--------|--------|
| 统一鉴权 | 各服务独立实现 | APISIX 统一处理 |
| 限流粒度 | 粗粒度 | 精细到服务/用户 |
| 熔断保护 | 无 | 自动熔断 |
| 请求追踪 | 有限 | 完整链路追踪 |
| 监控能力 | 基础 | 全面指标覆盖 |
