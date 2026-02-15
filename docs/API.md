# 百姓法律助手 API 接口完整文档

> 本文档整理自后端代码路由定义，完整API列表请以 `/docs` Swagger UI 为准。

## 基础信息

- **Base URL**: `http://localhost:8000/api`
- **认证**: Bearer Token (Cookie: `access_token`)
- **Content-Type**: application/json

---

## 目录

1. [用户认证 (User)](#用户认证-user)
2. [AI法律助手 (AI)](#ai法律助手-ai)
3. [论坛 (Forum)](#forum)
4. [新闻推荐 (News)](#新闻推荐-news)
5. [文书生成 (Documents)](#文书生成-documents)
6. [咨询预约 (Consultations)](#咨询预约-consultations)
7. [支付 (Payment)](#支付-payment)
8. [首页 (Home)](#首页-home)
9. [管理后台 (Admin)](#管理后台-admin)
10. [监控 (Monitor)](#监控-monitor)
11. [其他 (Others)](#其他-others)

---

## 用户认证 (User)

| 方法 | 路径 | 说明 | 认证 |
|------|------|------|------|
| POST | `/user/register` | 用户注册 | ❌ |
| POST | `/user/login` | 用户登录 | ❌ |
| POST | `/user/logout` | 用户登出 | ✅ |
| GET | `/user/me` | 获取当前用户信息 | ✅ |
| GET | `/user/me/quotas` | 获取当前用户配额 | ✅ |
| GET | `/user/me/quota-usage` | 获取配额消耗记录 | ✅ |
| PUT | `/user/me` | 更新当前用户信息 | ✅ |
| PUT | `/user/me/password` | 修改密码 | ✅ |
| GET | `/user/me/stats` | 获取用户统计数据 | ✅ |
| GET | `/user/{user_id}` | 获取指定用户信息 | ❌ |

---

## AI法律助手 (AI)

| 方法 | 路径 | 说明 | 认证 |
|------|------|------|------|
| POST | `/ai/chat` | AI对话（普通） | ✅/❌ |
| POST | `/ai/chat/stream` | AI对话（流式） | ✅/❌ |
| GET | `/ai/history` | 获取对话历史 | ✅ |
| DELETE | `/ai/history/{id}` | 删除对话 | ✅ |
| POST | `/ai/analysis` | AI法律分析 | ✅ |
| POST | `/ai/share` | 分享对话 | ✅ |
| POST | `/ai/transcription` | 转录服务 | ✅ |
| GET | `/ai/quality` | AI质量监控 | ✅ |

---

## Forum

### 帖子 (Posts)

| 方法 | 路径 | 说明 | 认证 |
|------|------|------|------|
| GET | `/forum/posts` | 获取帖子列表 | ❌ |
| POST | `/forum/posts` | 发布帖子 | ✅ |
| GET | `/forum/posts/{id}` | 获取帖子详情 | ❌ |
| PUT | `/forum/posts/{id}` | 编辑帖子 | ✅ |
| DELETE | `/forum/posts/{id}` | 删除帖子 | ✅ |
| POST | `/forum/posts/{id}/restore` | 恢复帖子 | ✅ |
| POST | `/forum/posts/{id}/purge` | 永久删除 | ✅ |
| POST | `/forum/posts/{id}/like` | 点赞/取消点赞 | ✅ |
| POST | `/forum/posts/batch/delete` | 批量删除 | ✅ |
| POST | `/forum/posts/batch/restore` | 批量恢复 | ✅ |
| POST | `/forum/posts/batch/purge` | 批量永久删除 | ✅ |
| GET | `/forum/posts/hot` | 获取热门帖子 | ❌ |
| GET | `/forum/posts/user/{user_id}` | 获取用户帖子 | ❌ |
| GET | `/forum/posts/user/{user_id}/deleted` | 获取用户已删除帖子 | ✅ |

### 评论 (Comments)

| 方法 | 路径 | 说明 | 认证 |
|------|------|------|------|
| POST | `/forum/posts/{post_id}/comments` | 发表评论 | ✅ |
| GET | `/forum/posts/{post_id}/comments` | 获取评论列表 | ❌ |
| DELETE | `/forum/comments/{id}` | 删除评论 | ✅ |

### 收藏 (Favorites)

| 方法 | 路径 | 说明 | 认证 |
|------|------|------|------|
| POST | `/forum/favorites` | 收藏帖子 | ✅ |
| GET | `/forum/favorites` | 获取收藏列表 | ✅ |
| DELETE | `/forum/favorites/{id}` | 取消收藏 | ✅ |

### 反应 (Reactions)

| 方法 | 路径 | 说明 | 认证 |
|------|------|------|------|
| POST | `/forum/posts/{post_id}/reactions` | 添加反应 | ✅ |
| DELETE | `/forum/posts/{post_id}/reactions/{reaction_type}` | 移除反应 | ✅ |

### 审核 (Moderation)

| 方法 | 路径 | 说明 | 认证 |
|------|------|------|------|
| POST | `/forum/moderation/report` | 举报帖子 | ✅ |
| GET | `/forum/moderation/pending` | 获取待审核帖子 | ✅ |
| POST | `/forum/moderation/{post_id}/approve` | 审核通过 | ✅ |
| POST | `/forum/moderation/{post_id}/reject` | 审核拒绝 | ✅ |

---

## 新闻推荐 (News)

| 方法 | 路径 | 说明 | 认证 |
|------|------|------|------|
| GET | `/news/recommendations` | 获取个性化推荐 | ❌ |
| GET | `/news/recommendations/similar/{news_id}` | 获取相似新闻 | ❌ |
| GET | `/news/recommendations/trending` | 获取热门新闻 | ❌ |
| GET | `/news/recommendations/quality/{news_id}` | 新闻质量评估 | ❌ |
| POST | `/news/recommendations/behavior` | 追踪用户行为 | ❌ |
| GET | `/news/recommendations/interests` | 获取用户兴趣画像 | ✅ |
| GET | `/news` | 获取新闻列表 | ❌ |
| GET | `/news/{id}` | 获取新闻详情 | ❌ |
| GET | `/news/topics` | 获取话题列表 | ❌ |

---

## 文书生成 (Documents)

| 方法 | 路径 | 说明 | 认证 |
|------|------|------|------|
| POST | `/documents/generate` | 生成法律文书 | ✅/❌ |
| POST | `/documents/export/pdf` | 导出PDF | ✅/❌ |
| GET | `/documents` | 获取文书列表 | ✅ |
| GET | `/documents/{id}` | 获取文书详情 | ✅ |
| PUT | `/documents/{id}` | 更新文书 | ✅ |
| DELETE | `/documents/{id}` | 删除文书 | ✅ |
| GET | `/documents/templates` | 获取文书模板 | ❌ |
| GET | `/documents/templates/{id}` | 获取模板详情 | ❌ |

---

## 咨询预约 (Consultations)

| 方法 | 路径 | 说明 | 认证 |
|------|------|------|------|
| POST | `/consultations` | 预约咨询 | ✅ |
| GET | `/consultations` | 获取我的咨询列表 | ✅ |
| GET | `/consultations/{id}` | 获取咨询详情 | ✅ |
| PUT | `/consultations/{id}` | 更新咨询 | ✅ |
| DELETE | `/consultations/{id}` | 取消咨询 | ✅ |
| GET | `/consultations/{id}/messages` | 获取咨询消息列表 | ✅ |
| POST | `/consultations/{id}/messages` | 发送消息 | ✅ |

### 律所 (Lawfirms)

| 方法 | 路径 | 说明 | 认证 |
|------|------|------|------|
| GET | `/lawfirms` | 获取律所列表 | ❌ |
| GET | `/lawfirms/{id}` | 获取律所详情 | ❌ |
| GET | `/lawyers` | 获取律师列表 | ❌ |
| GET | `/lawyers/{id}` | 获取律师详情 | ❌ |
| GET | `/lawyers/{id}/reviews` | 获取律师评价 | ❌ |
| POST | `/lawyers/{id}/reviews` | 评价律师 | ✅ |
| GET | `/lawyers/{id}/schedule` | 获取律师可预约时间 | ❌ |

---

## 支付 (Payment)

### 订单 (Orders)

| 方法 | 路径 | 说明 | 认证 |
|------|------|------|------|
| POST | `/payment/orders` | 创建订单 | ✅ |
| GET | `/payment/orders/{id}` | 获取订单详情 | ✅ |
| GET | `/payment/orders` | 获取我的订单 | ✅ |
| POST | `/payment/orders/{id}/cancel` | 取消订单 | ✅ |

### 回调 (Callbacks)

| 方法 | 路径 | 说明 | 认证 |
|------|------|------|------|
| POST | `/payment/alipay/notify` | 支付宝异步通知 | ❌ |
| POST | `/payment/wechat/notify` | 微信回调 | ❌ |
| POST | `/payment/ikunpay/notify` | Ikunpay回调 | ❌ |
| POST | `/payment/webhook` | 内部Webhook | ❌ |

### 微信支付 (WeChat Pay)

| 方法 | 路径 | 说明 | 认证 |
|------|------|------|------|
| POST | `/payment/wechat/pay/unified-order` | 统一下单 | ✅ |
| GET | `/payment/wechat/pay/config` | 获取JSAPI配置 | ✅ |
| POST | `/payment/wechat/pay/query` | 查询订单 | ✅ |
| POST | `/payment/wechat/pay/close` | 关闭订单 | ✅ |

### VIP

| 方法 | 路径 | 说明 | 认证 |
|------|------|------|------|
| GET | `/vip/plans` | 获取套餐列表 | ❌ |
| POST | `/vip/subscribe` | 订阅会员 | ✅ |
| GET | `/vip/status` | 获取会员状态 | ✅ |
| GET | `/vip/history` | 获取会员记录 | ✅ |

---

## 首页 (Home)

| 方法 | 路径 | 说明 | 认证 |
|------|------|------|------|
| GET | `/home/data` | 获取首页数据 | ❌ |
| GET | `/home/banners` | 获取首页横幅 | ❌ |
| GET | `/home/quick-actions` | 获取快捷入口 | ❌ |
| GET | `/home/recommendations` | 获取推荐内容 | ❌ |
| GET | `/home/features` | 获取功能卡片 | ❌ |
| GET | `/home/stats` | 获取统计数据 | ❌ |

---

## 管理后台 (Admin)

| 方法 | 路径 | 说明 | 认证 |
|------|------|------|------|
| GET | `/admin/stats` | 获取系统统计 | ✅ |
| GET | `/admin/export/users` | 导出用户CSV | ✅ |
| GET | `/admin/export/posts` | 导出帖子CSV | ✅ |
| GET | `/admin/export/news` | 导出新闻CSV | ✅ |
| GET | `/admin/export/lawyers` | 导出律师CSV | ✅ |
| GET | `/admin/export/consultations` | 导出咨询CSV | ✅ |

---

## 监控 (Monitor)

| 方法 | 路径 | 说明 | 认证 |
|------|------|------|------|
| GET | `/monitor/health` | 健康检查 | ❌ |
| GET | `/monitor/health/detailed` | 详细健康检查 | ❌ |
| GET | `/monitor/metrics` | 获取指标 | ❌ |
| GET | `/monitor/alerts` | 获取告警列表 | ✅ |
| GET | `/monitor/alert-rules` | 获取告警规则 | ✅ |
| POST | `/monitor/alert-rules/{rule_name}/enable` | 启用告警规则 | ✅ |
| POST | `/monitor/alert-rules/{rule_name}/disable` | 禁用告警规则 | ✅ |

---

## 其他 (Others)

### 知识库 (Knowledge)

| 方法 | 路径 | 说明 | 认证 |
|------|------|------|------|
| GET | `/knowledge` | 获取知识库列表 | ❌ |
| GET | `/knowledge/{id}` | 获取知识库详情 | ❌ |
| POST | `/knowledge` | 创建知识库 | ✅ |
| PUT | `/knowledge/{id}` | 更新知识库 | ✅ |
| DELETE | `/knowledge/{id}` | 删除知识库 | ✅ |

### 合同 (Contracts)

| 方法 | 路径 | 说明 | 认证 |
|------|------|------|------|
| POST | `/contracts/generate` | 生成合同 | ✅ |
| POST | `/contracts/analyze` | 分析合同 | ✅ |
| GET | `/contracts/templates` | 获取合同模板 | ❌ |

### 反馈 (Feedback)

| 方法 | 路径 | 说明 | 认证 |
|------|------|------|------|
| POST | `/feedback` | 提交反馈 | ✅ |
| GET | `/feedback` | 获取反馈列表 | ✅ |

### 常見問題 (FAQ)

| 方法 | 路径 | 说明 | 认证 |
|------|------|------|------|
| GET | `/faq` | 获取FAQ列表 | ❌ |
| GET | `/faq/{id}` | 获取FAQ详情 | ❌ |

### 日历 (Calendar)

| 方法 | 路径 | 说明 | 认证 |
|------|------|------|------|
| GET | `/calendar/events` | 获取日历事件 | ✅ |
| POST | `/calendar/events` | 创建日历事件 | ✅ |
| PUT | `/calendar/events/{id}` | 更新日历事件 | ✅ |
| DELETE | `/calendar/events/{id}` | 删除日历事件 | ✅ |

### 分析 (Analytics)

| 方法 | 路径 | 说明 | 认证 |
|------|------|------|------|
| GET | `/analytics/overview` | 数据概览 | ✅ |
| GET | `/analytics/funnel` | 漏斗分析 | ✅ |
| GET | `/analytics/retention` | 留存分析 | ✅ |

### WebSocket

| 方法 | 路径 | 说明 | 认证 |
|------|------|------|------|
| GET | `/ws/connect` | WebSocket连接 | ✅ |
| GET | `/ws/status` | WebSocket状态 | ✅ |
| GET | `/ws/config` | WebSocket配置 | ✅ |

### 垂直频道 (Vertical Channel)

| 方法 | 路径 | 说明 | 认证 |
|------|------|------|------|
| GET | `/vertical/channels` | 获取频道列表 | ❌ |
| GET | `/vertical/channels/{key}/news` | 获取频道新闻 | ❌ |
| GET | `/vertical/channels/{key}/consultation/types` | 获取频道咨询类型 | ❌ |
| GET | `/vertical/channels/{key}/document/types` | 获取频道文书类型 | ❌ |
| GET | `/vertical/channels/{key}/stats` | 获取频道统计 | ❌ |

---

## 错误码

| 状态码 | 说明 |
|--------|------|
| 200 | 成功 |
| 400 | 请求参数错误 |
| 401 | 未认证 |
| 403 | 权限不足 |
| 404 | 资源不存在 |
| 422 | 数据验证失败 |
| 429 | 请求过于频繁 |
| 500 | 服务器错误 |
| 503 | 服务不可用 |

---

## 完整文档

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

> ⚠️ 本文档由代码自动生成，如有遗漏请以Swagger UI为准。
