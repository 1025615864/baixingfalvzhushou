# 社区服务 API 文档

## 基础信息

| 属性 | 值 |
|------|-----|
| 基础路径 | `/api/v1/community` |
| 认证方式 | `Authorization: Bearer <token>` |
| 数据格式 | `application/json` |

---

## 用户 API

### 创建帖子
```
POST /api/v1/community/posts
```

**请求体:**
```json
{
  "title": "离婚时房产如何分割？",
  "content": "详细描述...",
  "category": "婚姻家庭",
  "tags": ["离婚", "房产"]
}
```

**响应:**
```json
{
  "success": true,
  "data": {
    "id": 1,
    "title": "离婚时房产如何分割？",
    "content": "详细描述...",
    "user_id": 123,
    "author_name": "热心网友",
    "status": "published",
    "created_at": "2026-03-23T10:00:00Z"
  }
}
```

### 获取帖子列表
```
GET /api/v1/community/posts
```

**查询参数:**
| 参数 | 类型 | 说明 |
|------|------|------|
| page | int | 页码 (默认1) |
| page_size | int | 每页数量 (默认20) |
| category | string | 分类筛选 |
| topic | string | 话题筛选 |
| sort | string | 排序 (newest/hotest) |

### 获取帖子详情
```
GET /api/v1/community/posts/{id}
```

### 搜索帖子
```
GET /api/v1/community/posts/search
```

**查询参数:**
| 参数 | 类型 | 说明 |
|------|------|------|
| q | string | 搜索关键词 |
| page | int | 页码 |
| page_size | int | 每页数量 |

### 点赞帖子
```
POST /api/v1/community/posts/{id}/like
```

### 收藏帖子
```
POST /api/v1/community/posts/{id}/favorite
```

### 举报帖子
```
POST /api/v1/community/posts/{id}/report
```

**请求体:**
```json
{
  "reason": "垃圾广告",
  "description": "详细内容..."
}
```

### 获取热门帖子
```
GET /api/v1/community/hot/posts
```

### 获取热门话题
```
GET /api/v1/community/hot/topics
```

---

## 评论 API

### 创建评论
```
POST /api/v1/community/posts/{id}/comments
```

**请求体:**
```json
{
  "content": "评论内容...",
  "parent_id": null,
  "reply_to_user_id": null
}
```

### 获取评论列表
```
GET /api/v1/community/posts/{id}/comments
```

**查询参数:**
| 参数 | 类型 | 说明 |
|------|------|------|
| page | int | 页码 |
| page_size | int | 每页数量 |
| sort | string | 排序 (newest/oldest) |

### 删除评论
```
DELETE /api/v1/community/comments/{id}
```

---

## 话题 API

### 获取话题列表
```
GET /api/v1/community/topics
```

### 获取话题详情
```
GET /api/v1/community/topics/{slug}
```

### 话题内发帖
```
POST /api/v1/community/topics/{slug}/posts
```

### 标记最佳回答
```
POST /api/v1/community/topics/{slug}/best-answer
```

**请求体:**
```json
{
  "post_id": 1,
  "comment_id": 5
}
```

---

## 管理 API

### 获取审核队列
```
GET /api/v1/community/admin/moderation/queue
```

### 审核内容
```
POST /api/v1/community/admin/moderation/{id}/review
```

**请求体:**
```json
{
  "action": "approve",
  "reason": "审核通过",
  "modified_content": null
}
```

### 获取统计数据
```
GET /api/v1/community/admin/dashboard/stats
```

---

## 运营 API

> 所有运营 API 需要 `Authorization: Bearer <token>` 头，且用户具有相应运营角色。

### 运营认证

#### 角色列表
```
GET /api/v1/community/ops/roles
```
**权限:** community_director

#### 分配角色
```
POST /api/v1/community/ops/roles/assign
```
**权限:** community_director

**请求体:**
```json
{
  "user_id": 123,
  "role": "content_mod"
}
```

#### 撤销角色
```
DELETE /api/v1/community/ops/roles/{user_id}
```
**权限:** community_director

---

### 审计日志

#### 查询日志
```
GET /api/v1/community/ops/audit/logs
```
**权限:** community_director

**查询参数:**
| 参数 | 类型 | 说明 |
|------|------|------|
| operator_id | int | 操作者ID |
| action | string | 操作类型 |
| target_type | string | 目标类型 |
| period | int | 查询天数 (默认7) |
| page | int | 页码 |
| page_size | int | 每页数量 |

#### 日志统计
```
GET /api/v1/community/ops/audit/logs/summary
```
**权限:** community_director

---

### 内容审核

#### 审核队列
```
GET /api/v1/community/ops/content/queue
```
**权限:** content_mod

**查询参数:**
| 参数 | 类型 | 说明 |
|------|------|------|
| status | string | pending/reviewed |
| priority | string | high/normal/low |
| assigned_to | int | 分配给谁 |
| page | int | 页码 |
| page_size | int | 每页数量 |

#### 审核详情
```
GET /api/v1/community/ops/content/queue/{id}
```
**权限:** content_mod

#### 审核操作
```
POST /api/v1/community/ops/content/queue/{id}/review
```
**权限:** content_mod

**请求体:**
```json
{
  "action": "approve",
  "reason": "审核通过",
  "modified_content": null,
  "penalty": null
}
```

| action | 说明 |
|--------|------|
| approve | 通过 |
| reject | 拒绝 |
| modify | 修改后通过 |
| escalate | 升级处理 |

#### 批量审核
```
POST /api/v1/community/ops/content/queue/batch-review
```
**权限:** content_mod

**请求体:**
```json
{
  "ids": [1, 2, 3],
  "action": "approve",
  "reason": "批量通过"
}
```

#### 分配审核任务
```
POST /api/v1/community/ops/content/queue/{id}/assign
```
**权限:** content_mod

**请求体:**
```json
{
  "assignee_id": 456
}
```

#### 审核统计
```
GET /api/v1/community/ops/content/stats
```
**权限:** content_mod

---

### 用户运营

#### 搜索用户
```
GET /api/v1/community/ops/users/search
```
**权限:** user_ops

#### 用户画像
```
GET /api/v1/community/ops/users/{id}/profile
```
**权限:** user_ops

**响应:**
```json
{
  "success": true,
  "data": {
    "user_id": 123,
    "post_count": 50,
    "comment_count": 200,
    "violation_count": 2,
    "active_penalty": null
  }
}
```

#### 违规历史
```
GET /api/v1/community/ops/users/{id}/violations
```
**权限:** user_ops

#### 处罚用户
```
POST /api/v1/community/ops/users/{id}/penalty
```
**权限:** user_ops

**请求体:**
```json
{
  "type": "mute",
  "duration_hours": 24,
  "reason": "多次发布违规内容",
  "related_post_id": 123,
  "notify_user": true
}
```

| type | 说明 |
|------|------|
| warning | 警告 |
| mute | 禁言 |
| ban | 封禁 |

#### 解除处罚
```
DELETE /api/v1/community/ops/users/{id}/penalty
```
**权限:** user_ops

**查询参数:** `reason` - 解除原因

#### 申诉列表
```
GET /api/v1/community/ops/users/appeals
```
**权限:** user_ops

**查询参数:**
| 参数 | 类型 | 说明 |
|------|------|------|
| status | string | pending/accepted/rejected |
| page | int | 页码 |
| page_size | int | 每页数量 |

#### 处理申诉
```
POST /api/v1/community/ops/users/appeals/{id}/handle
```
**权限:** user_ops

**请求体:**
```json
{
  "action": "accept",
  "reason": "证据不足，予以通过"
}
```

| action | 说明 |
|--------|------|
| accept | 通过申诉，解除处罚 |
| reject | 驳回申诉，维持处罚 |

#### 发送通知
```
POST /api/v1/community/ops/users/{id}/notify
```
**权限:** user_ops

**请求体:**
```json
{
  "title": "重要提醒",
  "content": "您的发帖行为需要遵守社区规范...",
  "type": "warning"
}
```

| type | 说明 |
|------|------|
| info | 通知 |
| warning | 警告 |
| system | 系统消息 |

#### 广播
```
POST /api/v1/community/ops/users/broadcast
```
**权限:** user_ops

**请求体:**
```json
{
  "target": "all",
  "title": "系统公告",
  "content": "社区将于今晚进行维护..."
}
```

---

### 话题运营

#### 置顶帖子
```
POST /api/v1/community/ops/topics/posts/{id}/pin
```
**权限:** topic_ops

**请求体:**
```json
{
  "duration_hours": 72
}
```

#### 取消置顶
```
DELETE /api/v1/community/ops/topics/posts/{id}/pin
```
**权限:** topic_ops

#### 加精帖子
```
POST /api/v1/community/ops/topics/posts/{id}/feature
```
**权限:** topic_ops

#### 取消加精
```
DELETE /api/v1/community/ops/topics/posts/{id}/feature
```
**权限:** topic_ops

#### 推荐帖子
```
POST /api/v1/community/ops/topics/posts/{id}/recommend
```
**权限:** topic_ops

#### 取消推荐
```
DELETE /api/v1/community/ops/topics/posts/{id}/recommend
```
**权限:** topic_ops

#### 推荐位管理
```
GET /api/v1/community/ops/topics/recommendations
```
**权限:** topic_ops

```
PUT /api/v1/community/ops/topics/recommendations
```
**权限:** topic_ops

**请求体:**
```json
{
  "slots": [
    {"position": 1, "post_id": 123, "label": "精选", "duration_hours": 168},
    {"position": 2, "post_id": 456, "label": "热门"}
  ]
}
```

#### 话题公告
```
PUT /api/v1/community/ops/topics/{id}/announcement
```
**权限:** topic_ops

**请求体:**
```json
{
  "content": "本话题禁止发布广告内容..."
}
```

---

### 运营分析

#### 运营概览
```
GET /api/v1/community/ops/analytics/overview
```
**权限:** data_analyst

**查询参数:** `period` - 统计天数 (默认7)

**响应:**
```json
{
  "success": true,
  "data": {
    "active_users": 1000,
    "new_posts": 500,
    "new_comments": 2000,
    "total_interactions": 2500,
    "period_days": 7
  }
}
```

#### 趋势数据
```
GET /api/v1/community/ops/analytics/trends
```
**权限:** data_analyst

**查询参数:**
| 参数 | 类型 | 说明 |
|------|------|------|
| metric | string | posts/comments/users |
| period | int | 天数 (默认30) |
| granularity | string | day/hour |

#### 内容质量
```
GET /api/v1/community/ops/analytics/content-quality
```
**权限:** data_analyst

#### 审核效率
```
GET /api/v1/community/ops/analytics/moderation
```
**权限:** data_analyst

#### 导出报表
```
GET /api/v1/community/ops/analytics/export
```
**权限:** data_analyst

**查询参数:**
| 参数 | 类型 | 说明 |
|------|------|------|
| report_type | string | overview/posts/users/moderation |
| format | string | csv/xlsx |
| period | int | 天数 |

---

### 运营配置

#### 获取社区规则
```
GET /api/v1/community/ops/config/rules
```
**权限:** community_director

#### 更新社区规则
```
PUT /api/v1/community/ops/config/rules
```
**权限:** community_director

**请求体:**
```json
{
  "post_min_length": 20,
  "post_max_length": 50000,
  "comment_max_length": 2000,
  "posts_per_day_limit": 5
}
```

#### 敏感词列表
```
GET /api/v1/community/ops/config/sensitive-words
```
**权限:** content_mod

#### 添加敏感词
```
POST /api/v1/community/ops/config/sensitive-words
```
**权限:** content_mod

**请求体:**
```json
{
  "words": ["毒品", "赌博", "诈骗"],
  "category": "general"
}
```

#### 删除敏感词
```
DELETE /api/v1/community/ops/config/sensitive-words
```
**权限:** content_mod

**查询参数:** `words` - 要删除的词列表

#### 自动审核配置
```
GET /api/v1/community/ops/config/auto-moderation
```
**权限:** content_mod

#### 更新自动审核配置
```
PUT /api/v1/community/ops/config/auto-moderation
```
**权限:** content_mod

**请求体:**
```json
{
  "ai_review_enabled": true,
  "ai_confidence_threshold": 0.7,
  "auto_reject_threshold": 0.95
}
```

---

### 社区公告

#### 公告列表
```
GET /api/v1/community/ops/announcements
```
**权限:** topic_ops

#### 发布公告
```
POST /api/v1/community/ops/announcements
```
**权限:** topic_ops

**请求体:**
```json
{
  "scope": "global",
  "title": "重要通知",
  "content": "社区将于今晚进行维护...",
  "is_pinned": true,
  "starts_at": "2026-03-23T18:00:00Z",
  "expires_at": "2026-03-24T18:00:00Z"
}
```

| scope | 说明 |
|-------|------|
| global | 全站公告 |
| topic | 话题公告 |

#### 删除公告
```
DELETE /api/v1/community/ops/announcements/{id}
```
**权限:** community_director

---

## 系统 API

### 健康检查
```
GET /api/v1/community/health
```

### 就绪检查
```
GET /api/v1/community/health/ready
```

### 存活检查
```
GET /api/v1/community/health/live
```

### Prometheus 指标
```
GET /api/v1/community/metrics
```

---

## 错误码

| 错误码 | 说明 |
|--------|------|
| 1001 | 帖子不存在 |
| 1002 | 无权操作该帖子 |
| 1003 | 内容违反社区规则 |
| 1004 | 敏感词检测未通过 |
| 2001 | 用户不存在 |
| 2002 | 用户已被禁言 |
| 2003 | 用户已被封禁 |
| 3001 | 话题不存在 |
| 4001 | 审核项不存在 |
| 4002 | 无权进行审核操作 |
| 5001 | 运营角色不存在 |
| 5002 | 无权执行该操作 |
| 5003 | 配置不存在 |
| 9001 | 服务内部错误 |
| 9002 | 数据库错误 |
| 9003 | Kafka 错误 |

---

## 响应格式

### 成功响应
```json
{
  "success": true,
  "data": { ... }
}
```

### 分页响应
```json
{
  "success": true,
  "data": {
    "items": [ ... ],
    "total": 100,
    "page": 1,
    "page_size": 20
  }
}
```

### 错误响应
```json
{
  "success": false,
  "error": {
    "code": 1003,
    "message": "内容违反社区规则",
    "detail": "检测到敏感词"
  }
}
```
