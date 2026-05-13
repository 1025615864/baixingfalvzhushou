# 社区服务 (Community Service)

## 服务概览

| 属性 | 值 |
|------|-----|
| 服务名称 | community-service |
| 端口 | 8007 |
| 基础路径 | /api/v1/community |
| 技术栈 | FastAPI + SQLAlchemy 2.0 + PostgreSQL + Redis |
| 数据库 | community_service |
| 健康检查 | GET /health |
| 就绪检查 | GET /health/ready |
| 存活检查 | GET /health/live |

## 服务描述

社区服务是法律知识分享与讨论的核心平台，提供帖子发布、评论互动、话题管理、内容审核、运营管理等功能。包含完整的运营后台体系，支持内容审核队列、用户处罚、话题运营、数据分析等运营能力。

## API 端点

### 帖子路由 (post_router)

| 方法 | 路径 | 说明 | 认证 |
|------|------|------|------|
| GET | / | 获取帖子列表（分页） | 否 |
| GET | /search/ | 搜索帖子 | 否 |
| GET | /cursor/ | 游标分页获取帖子 | 否 |
| GET | /{post_id} | 获取帖子详情 | 否 |
| POST | / | 创建帖子 | 是 |
| PATCH | /{post_id} | 更新帖子 | 是 |
| DELETE | /{post_id} | 删除帖子 | 是 |
| POST | /{post_id}/like | 点赞帖子 | 是 |
| POST | /{post_id}/favorite | 收藏帖子 | 是 |
| GET | /user/{user_id} | 获取用户帖子 | 否 |
| GET | /categories/ | 获取分类列表 | 否 |

### 评论路由 (comment_router)

| 方法 | 路径 | 说明 | 认证 |
|------|------|------|------|
| GET | /{post_id}/comments | 获取评论列表 | 否 |
| POST | /{post_id}/comments | 创建评论 | 是 |
| DELETE | /{comment_id} | 删除评论 | 是 |
| POST | /{comment_id}/like | 点赞评论 | 是 |

### 话题路由 (topic_router)

| 方法 | 路径 | 说明 | 认证 |
|------|------|------|------|
| GET | / | 获取话题列表 | 否 |
| GET | /{topic_name} | 获取话题详情 | 否 |
| GET | /{topic_name}/posts | 获取话题内帖子 | 否 |
| POST | / | 创建话题 | 是 |
| PUT | /{topic_id} | 更新话题 | 是 |
| DELETE | /{topic_id} | 删除话题 | 是 |
| POST | /posts/{post_id}/best-answer | 标记最佳回答 | 是 |
| GET | /posts/{post_id}/best-answer | 获取最佳回答 | 否 |
| DELETE | /posts/{post_id}/best-answer | 取消最佳回答 | 是 |

### 热门路由 (hot_router)

| 方法 | 路径 | 说明 | 认证 |
|------|------|------|------|
| GET | /posts | 获取热门帖子 | 否 |
| POST | /recalculate | 重新计算热度 | 是 |

### 收藏路由 (favorite_router)

| 方法 | 路径 | 说明 | 认证 |
|------|------|------|------|
| GET | / | 获取收藏列表 | 是 |
| GET | /{post_id}/status | 获取收藏状态 | 是 |

### 举报路由 (report_router)

| 方法 | 路径 | 说明 | 认证 |
|------|------|------|------|
| POST | / | 提交举报 | 是 |
| GET | /my | 获取我的举报 | 是 |

### 仪表盘路由 (dashboard_router)

| 方法 | 路径 | 说明 | 认证 |
|------|------|------|------|
| GET | /overview | 运营概览 | 是 |
| GET | /trending-topics | 热门话题 | 否 |
| GET | /user-activity | 用户活跃度 | 是 |
| GET | /top-posts | 热门帖子 | 否 |
| GET | /category-distribution | 分类分布 | 是 |

### 审核路由 (moderation_router)

| 方法 | 路径 | 说明 | 认证 |
|------|------|------|------|
| GET | /queue | 获取审核队列 | 是 |
| GET | /queue/{item_id} | 获取审核项详情 | 是 |
| POST | /queue/{item_id} | 审核操作 | 是 |
| GET | /stats | 审核统计 | 是 |

### 管理路由 (admin_router)

| 方法 | 路径 | 说明 | 认证 |
|------|------|------|------|
| GET | /posts/pending | 获取待审核帖子 | 是 |
| POST | /posts/{post_id}/review | 审核帖子 | 是 |
| GET | /reports | 获取举报列表 | 是 |
| POST | /reports/{report_id}/handle | 处理举报 | 是 |
| POST | /users/{user_id}/ban | 封禁用户 | 是 |
| GET | /statistics | 获取统计数据 | 是 |

### 指标路由 (metrics_router)

| 方法 | 路径 | 说明 | 认证 |
|------|------|------|------|
| GET | / | 获取指标 | 否 |
| POST | /reset | 重置指标 | 是 |

### 运营路由 (ops)

| 方法 | 路径 | 说明 | 认证 |
|------|------|------|------|
| POST | /auth/login | 运营登录 | 否 |
| GET | /roles | 获取角色列表 | 是 |
| POST | /roles/assign | 分配角色 | 是 |
| DELETE | /roles/{user_id} | 撤销角色 | 是 |
| GET | /roles/permissions | 获取权限列表 | 是 |
| GET | /content/queue | 内容审核队列 | 是 |
| GET | /content/queue/{queue_id} | 审核详情 | 是 |
| POST | /content/queue/{queue_id}/review | 审核操作 | 是 |
| POST | /content/queue/batch-review | 批量审核 | 是 |
| POST | /content/queue/{queue_id}/assign | 分配审核 | 是 |
| GET | /content/stats | 审核统计 | 是 |
| GET | /users/search | 搜索用户 | 是 |
| GET | /users/{user_id}/profile | 用户画像 | 是 |
| GET | /users/{user_id}/violations | 违规历史 | 是 |
| POST | /users/{user_id}/penalty | 处罚用户 | 是 |
| DELETE | /users/{user_id}/penalty | 解除处罚 | 是 |
| GET | /users/appeals | 申诉列表 | 是 |
| POST | /users/appeals/{appeal_id}/handle | 处理申诉 | 是 |
| POST | /users/{user_id}/notify | 发送通知 | 是 |
| POST | /users/broadcast | 广播消息 | 是 |
| POST | /topics/posts/{post_id}/pin | 置顶帖子 | 是 |
| DELETE | /topics/posts/{post_id}/pin | 取消置顶 | 是 |
| POST | /topics/posts/{post_id}/feature | 加精帖子 | 是 |
| DELETE | /topics/posts/{post_id}/feature | 取消加精 | 是 |
| POST | /topics/posts/{post_id}/recommend | 推荐帖子 | 是 |
| DELETE | /topics/posts/{post_id}/recommend | 取消推荐 | 是 |
| GET | /topics/recommendations | 推荐位列表 | 是 |
| PUT | /topics/recommendations | 更新推荐位 | 是 |
| PUT | /topics/{topic_id}/announcement | 话题公告 | 是 |
| GET | /analytics/overview | 运营概览 | 是 |
| GET | /analytics/trends | 趋势数据 | 是 |
| GET | /analytics/content-quality | 内容质量 | 是 |
| GET | /analytics/moderation | 审核效率 | 是 |
| GET | /analytics/export | 导出报表 | 是 |
| GET | /config/rules | 社区规则 | 是 |
| PUT | /config/rules | 更新规则 | 是 |
| GET | /config/sensitive-words | 敏感词列表 | 是 |
| POST | /config/sensitive-words | 添加敏感词 | 是 |
| DELETE | /config/sensitive-words | 删除敏感词 | 是 |
| GET | /config/auto-moderation | 自动审核配置 | 是 |
| PUT | /config/auto-moderation | 更新自动审核 | 是 |
| GET | /announcements | 公告列表 | 是 |
| POST | /announcements | 发布公告 | 是 |
| GET | /announcements/{announcement_id} | 公告详情 | 是 |
| DELETE | /announcements/{announcement_id} | 删除公告 | 是 |
| GET | /audit/logs | 审计日志 | 是 |
| GET | /audit/logs/summary | 日志统计 | 是 |

## 数据模型

| 模型 | 说明 |
|------|------|
| Post | 帖子（标题、内容、分类、状态、点赞/收藏数） |
| Comment | 评论（内容、帖子ID、父评论ID） |
| Topic | 话题（名称、描述、帖子数） |
| Report | 举报（原因、状态、处理结果） |
| ModerationQueue | 审核队列（内容、状态、审核人） |
| Draft | 草稿（内容、状态） |
| OpsModels | 运营模型（角色、处罚、公告等） |

## 关联服务

| 关联服务 | 通信方式 | 说明 |
|----------|----------|------|
| user-service | HTTP | 获取用户信息、验证身份 |
| ai-service | HTTP | AI 内容审核辅助 |
| points-service | Kafka | 发帖/评论积分事件 |
| notification-service | Kafka | 社区互动通知事件 |
| search-service | HTTP | 社区内容搜索聚合 |
| backend-bff | HTTP | BFF 聚合社区接口 |

## 配置项

| 环境变量 | 默认值 | 说明 |
|----------|--------|------|
| SERVICE_PORT | 8007 | 服务端口 |
| DATABASE_URL | - | PostgreSQL 连接串 |
| REDIS_URL | - | Redis 连接串 |
| KAFKA_BOOTSTRAP_SERVERS | kafka:9092 | Kafka 地址 |

## 部署信息

- Dockerfile: services/community-service/Dockerfile
- 健康检查: /health
- 资源限制: CPU 0.5核 / 内存 512MB
- 详细 API 文档: [services/community-service/API.md](../../services/community-service/API.md)
