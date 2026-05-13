# Backend BFF（后端聚合层）

## 服务概览

| 属性 | 值 |
|------|-----|
| 服务名称 | backend-bff |
| 端口 | 8000 |
| 基础路径 | /api/v1 |
| 技术栈 | FastAPI + SQLAlchemy 2.0 + PostgreSQL + Redis + OpenTelemetry |
| 数据库 | baixing_law |
| 健康检查 | GET /health |
| 就绪检查 | GET /health/detailed |

## 服务描述

Backend BFF（Backend for Frontend）是面向前端的应用聚合层，统一管理用户认证、AI 对话、搜索、支付、文件上传等核心功能，并通过微服务代理层将请求路由到后端各专业微服务。内置熔断器保护，确保下游服务故障时系统整体可用性。

## API 端点

### 认证模块 (auth.py)

| 方法 | 路径 | 说明 | 认证 |
|------|------|------|------|
| POST | /api/auth/login | 用户登录 | 否 |
| POST | /api/auth/register | 用户注册 | 否 |
| POST | /api/auth/wechat/login | 微信扫码登录 | 否 |
| POST | /api/auth/logout | 用户登出 | 否 |
| POST | /api/auth/refresh | 刷新 Token | 否 |

### 用户模块 (user_profile.py)

| 方法 | 路径 | 说明 | 认证 |
|------|------|------|------|
| POST | /api/user/register | 用户注册（含协议确认） | 否 |
| POST | /api/user/login | 用户登录 | 否 |
| GET | /api/user/me | 获取当前用户信息 | 是 |
| PATCH | /api/user/me | 更新当前用户信息 | 是 |
| PUT | /api/user/me | 更新当前用户信息（PUT） | 是 |
| PUT | /api/user/me/password | 修改密码 | 是 |
| GET | /api/user/me/csrf-token | 获取 CSRF Token | 是 |
| GET | /api/user/me/settings | 获取用户设置 | 是 |
| PUT | /api/user/me/settings | 更新用户设置 | 是 |
| GET | /api/user/me/stats | 获取用户统计 | 是 |
| GET | /api/user/me/quotas | 获取用户配额 | 是 |
| GET | /api/user/me/usage | 获取用户使用记录 | 是 |
| GET | /api/user/me/preferences | 获取用户偏好 | 是 |
| PUT | /api/user/me/preferences | 更新用户偏好 | 是 |
| GET | /api/user/me/2fa/status | 获取2FA状态 | 是 |
| POST | /api/user/me/2fa/setup | 设置2FA | 是 |
| POST | /api/user/me/2fa/disable | 禁用2FA | 是 |
| GET | /api/user/me/sessions | 获取会话列表 | 是 |
| DELETE | /api/user/me/sessions/{session_id} | 删除会话 | 是 |
| DELETE | /api/user/me | 删除账号 | 是 |
| GET | /api/user/{user_id} | 获取用户公开信息 | 否 |
| POST | /api/user/password-reset/request | 请求密码重置 | 否 |
| POST | /api/user/password-reset/confirm | 确认密码重置 | 否 |
| POST | /api/user/email-verification/request | 请求邮箱验证 | 是 |
| GET | /api/user/email-verification/verify | 验证邮箱 | 否 |
| POST | /api/user/sms/send | 发送短信验证码 | 是 |
| POST | /api/user/sms/verify | 验证短信验证码 | 是 |
| GET | /api/user/me/quota-usage | 获取配额消耗记录 | 是 |
| GET | /api/user/admin/list | 管理员获取用户列表 | 是 |
| PUT | /api/user/admin/{user_id}/toggle-active | 管理员切换用户状态 | 是 |
| PUT | /api/user/admin/{user_id}/role | 管理员修改用户角色 | 是 |

### AI 对话模块 (ai/chat.py)

| 方法 | 路径 | 说明 | 认证 |
|------|------|------|------|
| POST | /api/ai/chat | AI 法律对话（同步） | 否 |
| POST | /api/ai/chat/stream | AI 法律对话（流式SSE） | 否 |
| POST | /api/ai/quick-replies | 获取快捷回复建议 | 否 |
| GET | /api/ai/consultations | 获取咨询列表 | 否 |
| GET | /api/ai/consultations/{session_id} | 获取咨询详情 | 否 |
| DELETE | /api/ai/consultations/{session_id} | 删除咨询会话 | 否 |

### 搜索模块 (search.py)

| 方法 | 路径 | 说明 | 认证 |
|------|------|------|------|
| GET | /api/search | 全局搜索 | 否 |
| GET | /api/search/suggestions | 搜索建议 | 否 |
| GET | /api/search/hot | 热门关键词 | 否 |
| GET | /api/search/history | 搜索历史 | 是 |
| DELETE | /api/search/history | 清除搜索历史 | 是 |

### 文件上传模块 (upload.py)

| 方法 | 路径 | 说明 | 认证 |
|------|------|------|------|
| POST | /api/upload/avatar | 上传头像（2MB限制） | 是 |
| GET | /api/upload/avatars/{filename} | 获取头像 | 是 |
| POST | /api/upload/file | 上传附件（10MB限制） | 是 |
| GET | /api/upload/files/{filename} | 获取附件 | 是 |
| POST | /api/upload/image | 上传图片（2MB限制，含内容审核） | 是 |
| GET | /api/upload/images/{filename} | 获取图片 | 是 |

### 微信模块 (wechat.py)

| 方法 | 路径 | 说明 | 认证 |
|------|------|------|------|
| GET | /api/wechat/qrcode | 获取微信扫码登录二维码 | 否 |
| GET | /api/wechat/qrcode/status/{qrcode_id} | 轮询二维码扫码状态 | 否 |
| POST | /api/wechat/qrcode/confirm/{qrcode_id} | 确认扫码登录 | 否 |
| POST | /api/wechat/callback | 微信 OAuth 回调 | 否 |

### WebSocket 模块 (websocket.py)

| 方法 | 路径 | 说明 | 认证 |
|------|------|------|------|
| WS | /ws | WebSocket 连接端点 | Token |
| GET | /ws/status | 获取 WebSocket 连接状态 | 否 |
| GET | /ws/config | 获取 WebSocket 配置信息 | 否 |

### 管理后台 (admin.py)

| 方法 | 路径 | 说明 | 认证 |
|------|------|------|------|
| GET | /api/admin/stats | 获取系统统计数据 | 是 |
| GET | /api/admin/export/users | 导出用户数据（CSV） | 是 |
| GET | /api/admin/export/posts | 导出帖子数据（CSV） | 是 |
| GET | /api/admin/export/news | 导出新闻数据（CSV） | 是 |
| GET | /api/admin/export/lawfirms | 导出律所数据（CSV） | 是 |
| GET | /api/admin/export/knowledge | 导出知识库数据（CSV） | 是 |
| GET | /api/admin/export/consultations | 导出咨询记录（CSV） | 是 |

### 管理后台 V1 (admin_v1.py)

| 方法 | 路径 | 说明 | 认证 |
|------|------|------|------|
| * | /api/v1/admin/law-firms/* | 律所管理 | 是 |
| * | /api/v1/admin/withdrawals/* | 提现管理 | 是 |
| * | /api/v1/admin/posts/* | 帖子管理 | 是 |
| * | /api/v1/admin/payment/callbacks/* | 支付回调管理 | 是 |
| * | /api/v1/admin/payment/settlement/* | 结算管理 | 是 |
| * | /api/v1/admin/notifications/* | 系统通知管理 | 是 |
| * | /api/v1/admin/document-templates/* | 文档模板管理 | 是 |
| * | /api/v1/admin/consultation-templates/* | 咨询模板管理 | 是 |
| * | /api/v1/admin/settings/* | 系统设置 | 是 |

### 首页模块 (home.py)

| 方法 | 路径 | 说明 | 认证 |
|------|------|------|------|
| GET | /api/home/data | 获取首页完整数据聚合 | 否 |
| GET | /api/home/banners | 获取首页横幅 | 否 |
| GET | /api/home/quick-actions | 获取快捷入口 | 否 |
| GET | /api/home/recommendations | 获取推荐内容 | 否 |
| GET | /api/home/stats | 获取首页统计数据 | 否 |
| POST | /api/home/track-click | 追踪点击行为 | 否 |
| PUT | /api/home/interests | 更新用户兴趣 | 否 |

### 微服务代理 (microservice_proxy.py)

| 方法 | 路径 | 说明 | 认证 |
|------|------|------|------|
| * | /api/v1/order/* | 代理到 order-service | 是 |
| * | /api/v1/notification/* | 代理到 notification-service | 是 |
| * | /api/v1/news/* | 代理到 news-service | 是 |
| * | /api/v1/community/* | 代理到 community-service | 是 |
| * | /api/v1/legal/* | 代理到 legal-service | 是 |
| * | /api/v1/search/* | 代理到 search-service | 是 |
| * | /api/v1/recommendation/* | 代理到 recommendation-service | 是 |
| * | /api/v1/points/* | 代理到 points-service | 是 |
| * | /api/v1/archive/* | 代理到 archive-service | 是 |
| * | /api/v1/knowledge/* | 代理到 knowledge-service | 是 |
| GET | /proxy/circuit-status | 获取所有微服务熔断器状态 | 否 |

### 论坛模块 (forum/)

| 方法 | 路径 | 说明 | 认证 |
|------|------|------|------|
| * | /api/forum/comments/* | 评论管理 | 是 |
| * | /api/forum/favorites/* | 收藏管理 | 是 |
| * | /api/forum/reactions/* | 点赞/表情管理 | 是 |

### 新闻模块 (news/)

| 方法 | 路径 | 说明 | 认证 |
|------|------|------|------|
| * | /api/news/* | 新闻资讯管理 | 否 |

### 支付模块 (payment/)

| 方法 | 路径 | 说明 | 认证 |
|------|------|------|------|
| * | /api/payment/* | 订单创建、支付、回调 | 是 |

### 系统端点

| 方法 | 路径 | 说明 | 认证 |
|------|------|------|------|
| GET | / | 根路由（服务信息） | 否 |
| GET | /health | 健康检查 | 否 |
| GET | /health/detailed | 详细健康检查 | 否 |
| GET | /api/health | 健康检查（API别名） | 否 |
| GET | /metrics | Prometheus 指标 | Token |
| GET | /robots.txt | 搜索引擎爬虫配置 | 否 |
| GET | /sitemap.xml | 站点地图 | 否 |

## 关联服务

| 关联服务 | 通信方式 | 说明 |
|----------|----------|------|
| order-service | HTTP（代理） | 订单服务，端口 8004 |
| notification-service | HTTP（代理） | 通知服务，端口 8011 |
| news-service | HTTP（代理） | 新闻服务，端口 8006 |
| community-service | HTTP（代理） | 社区服务，端口 8007 |
| legal-service | HTTP（代理） | 法律服务，端口 8008 |
| search-service | HTTP（代理） | 搜索服务，端口 8009 |
| recommendation-service | HTTP（代理） | 推荐服务，端口 8010 |
| points-service | HTTP（代理） | 积分服务，端口 8012 |
| archive-service | HTTP（代理） | 档案库服务，端口 8013 |
| knowledge-service | HTTP（代理） | 知识库服务，端口 8081 |
| Redis | TCP | 缓存、会话、限流 |
| PostgreSQL | TCP | 主数据库 |
| OpenAI API | HTTP | AI 对话模型调用 |

## 配置项

| 环境变量 | 默认值 | 说明 |
|----------|--------|------|
| DATABASE_URL | sqlite+aiosqlite:///./data/app.db | 数据库连接URL |
| SECRET_KEY | - | JWT 签名密钥 |
| JWT_ALGORITHM | RS256 | JWT 算法（开发环境回退HS256） |
| JWT_RSA_PRIVATE_KEY | - | RSA 私钥 |
| JWT_RSA_PUBLIC_KEY | - | RSA 公钥 |
| ACCESS_TOKEN_EXPIRE_MINUTES | 60 | Access Token 过期时间（分钟） |
| REFRESH_TOKEN_EXPIRE_DAYS | 7 | Refresh Token 过期时间（天） |
| REDIS_URL | - | Redis 连接URL |
| CORS_ALLOW_ORIGINS | [] | CORS 允许来源 |
| OPENAI_API_KEY | - | OpenAI API 密钥 |
| OPENAI_BASE_URL | https://api.openai.com/v1 | OpenAI API 基础URL |
| AI_MODEL | deepseek-chat | AI 对话模型名称 |
| FRONTEND_BASE_URL | http://localhost:5173 | 前端基础URL |
| ENVIRONMENT | development | 运行环境 |
| CSRF_SECRET_KEY | - | CSRF 密钥 |
| CSRF_ENABLED | true | CSRF 保护开关 |
| RATE_LIMIT_PER_MINUTE | 60 | 速率限制（每分钟） |
| ORDER_SERVICE_URL | http://order-service:8004 | 订单服务地址 |
| NOTIFICATION_SERVICE_URL | http://notification-service:8011 | 通知服务地址 |
| NEWS_SERVICE_URL | http://news-service:8006 | 新闻服务地址 |
| COMMUNITY_SERVICE_URL | http://community-service:8007 | 社区服务地址 |
| LEGAL_SERVICE_URL | http://legal-service:8008 | 法律服务地址 |
| SEARCH_SERVICE_URL | http://search-service:8009 | 搜索服务地址 |
| RECOMMENDATION_SERVICE_URL | http://recommendation-service:8010 | 推荐服务地址 |
| POINTS_SERVICE_URL | http://points-service:8012 | 积分服务地址 |
| ARCHIVE_SERVICE_URL | http://archive-service:8013 | 档案库服务地址 |
| KNOWLEDGE_SERVICE_URL | http://knowledge-service:8081 | 知识库服务地址 |
| SENTRY_DSN | - | Sentry 错误追踪DSN |
| STORAGE_PROVIDER | local | 存储提供商（local/s3） |
| ALIPAY_APP_ID | - | 支付宝应用ID |
| WECHATPAY_MCH_ID | - | 微信支付商户ID |
| IKUNPAY_PID | - | IkunPay 商户ID |

## 部署信息

- Dockerfile: backend/Dockerfile
- 健康检查: /health
- 资源限制: CPU 1核 / 内存 1GB
- 熔断器: 每个微服务独立熔断（失败5次触发，30秒恢复）
