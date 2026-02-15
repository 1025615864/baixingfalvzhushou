# 管理后台 API V1 文档

> 统一的管理后台 API 入口，所有管理功能都挂载在 `/api/v1/admin/*` 路径下

## 基础信息

- **Base URL**: `http://localhost:8000/api/v1/admin`
- **认证方式**: JWT Token (Bearer)
- **权限要求**: 管理员权限

## 模块列表

| 模块 | 路径前缀 | 功能描述 |
|------|---------|---------|
| 律所管理 | `/law-firms` | 律所CRUD、批量审核、统计 |
| 提现管理 | `/withdrawals` | 提现申请审核、导出 |
| 帖子管理 | `/posts` | 帖子审核、置顶、精华 |
| 支付回调 | `/payment/callbacks` | 回调监控、重试、处理 |
| 结算统计 | `/payment/settlement` | 仪表盘、趋势、排行 |
| 系统通知 | `/notifications` | 广播、定向通知管理 |
| 文档模板 | `/document-templates` | 模板管理、版本控制 |
| 咨询模板 | `/consultation-templates` | 表单模板管理 |
| 系统设置 | `/settings` | 配置管理、监控、日志 |

---

## 1. 律所管理 API

### 1.1 获取律所列表
```http
GET /law-firms?page=1&page_size=20&city=&keyword=
```

**响应示例**:
```json
{
  "items": [
    {
      "id": 1,
      "name": "某某律师事务所",
      "city": "北京",
      "is_verified": true,
      "is_active": true,
      "lawyer_count": 10
    }
  ],
  "total": 100
}
```

### 1.2 批量审核律所
```http
POST /law-firms/batch/verify
```

**请求体**:
```json
{
  "firm_ids": [1, 2, 3],
  "is_verified": true,
  "reason": "审核通过"
}
```

### 1.3 更新律所状态
```http
PUT /law-firms/{firm_id}/status
```

**请求体**:
```json
{
  "is_active": false
}
```

### 1.4 律所统计概览
```http
GET /law-firms/statistics/overview
```

**响应示例**:
```json
{
  "total_count": 100,
  "verified_count": 80,
  "active_count": 95,
  "pending_count": 5,
  "city_stats": [
    {"city": "北京", "count": 30},
    {"city": "上海", "count": 25}
  ]
}
```

---

## 2. 提现管理 API

### 2.1 获取提现申请列表
```http
GET /withdrawals?page=1&page_size=20&status=&keyword=
```

### 2.2 批准提现
```http
POST /withdrawals/{withdrawal_id}/approve
```

### 2.3 拒绝提现
```http
POST /withdrawals/{withdrawal_id}/reject
```

**请求体**:
```json
{
  "reason": "信息不完整"
}
```

### 2.4 导出提现记录
```http
GET /withdrawals/export?status=&start_date=&end_date=
```

---

## 3. 帖子管理 API

### 3.1 审核帖子
```http
PUT /posts/{post_id}/review
```

**请求体**:
```json
{
  "status": "approved",
  "reason": "内容合规"
}
```

### 3.2 批量审核帖子
```http
POST /posts/batch/review
```

**请求体**:
```json
{
  "post_ids": [1, 2, 3],
  "status": "approved"
}
```

### 3.3 设置帖子置顶
```http
PUT /posts/{post_id}/sticky
```

**请求体**:
```json
{
  "is_sticky": true,
  "sticky_priority": 1
}
```

### 3.4 设置帖子精华
```http
PUT /posts/{post_id}/essence
```

**请求体**:
```json
{
  "is_essence": true
}
```

---

## 4. 支付回调管理 API

### 4.1 获取回调事件列表
```http
GET /payment/callbacks?page=1&page_size=20&provider=&status=
```

### 4.2 获取回调统计
```http
GET /payment/callbacks/stats
```

### 4.3 重试回调
```http
POST /payment/callbacks/{event_id}/retry
```

### 4.4 手动处理回调
```http
POST /payment/callbacks/{event_id}/process
```

**请求体**:
```json
{
  "success": true,
  "note": "手动标记成功"
}
```

---

## 5. 结算统计 API

### 5.1 仪表盘统计
```http
GET /payment/settlement/dashboard
```

**响应示例**:
```json
{
  "today_income": 1000.00,
  "today_withdrawal": 500.00,
  "today_order_count": 10,
  "total_income": 100000.00,
  "total_withdrawal": 50000.00,
  "total_lawyer_count": 50,
  "total_order_count": 1000,
  "pending_withdrawal_count": 5,
  "pending_withdrawal_amount": 2500.00,
  "pending_settlement_count": 10,
  "pending_settlement_amount": 5000.00,
  "total_wallet_balance": 80000.00,
  "total_frozen_amount": 20000.00
}
```

### 5.2 收入趋势
```http
GET /payment/settlement/trends?days=30
```

**响应示例**:
```json
{
  "dates": ["2024-01-01", "2024-01-02", ...],
  "income": [100, 200, ...],
  "withdrawal": [50, 100, ...],
  "orders": [5, 10, ...]
}
```

### 5.3 支付方式统计
```http
GET /payment/settlement/payment-methods?days=30
```

### 5.4 律师收入排行
```http
GET /payment/settlement/top-lawyers?limit=10&days=30
```

---

## 6. 系统通知 API

### 6.1 发布广播通知
```http
POST /notifications/admin/broadcast
```

**请求体**:
```json
{
  "title": "系统维护通知",
  "content": "系统将于今晚进行维护",
  "link": "/notice/1"
}
```

### 6.2 发送定向通知
```http
POST /notifications/admin/targeted
```

**请求体**:
```json
{
  "title": "定向通知",
  "content": "这是给特定用户的通知",
  "target_type": "users",
  "target_ids": [1, 2, 3]
}
```

**target_type 说明**:
- `users` - 指定用户（需传 target_ids）
- `role` - 指定角色（需传 target_role）
- `all` - 全部用户

### 6.3 获取系统通知列表
```http
GET /notifications/admin/system?page=1&page_size=20
```

### 6.4 编辑系统通知
```http
PUT /notifications/admin/{notification_id}
```

### 6.5 删除系统通知
```http
DELETE /notifications/admin/{notification_id}
```

---

## 7. 文档模板管理 API

### 7.1 获取模板列表
```http
GET /document-templates
```

### 7.2 创建模板
```http
POST /document-templates
```

**请求体**:
```json
{
  "key": "contract_template",
  "title": "合同模板",
  "description": "标准合同模板"
}
```

### 7.3 创建模板版本
```http
POST /document-templates/{template_id}/versions
```

**请求体**:
```json
{
  "content": "合同内容...",
  "publish": false,
  "variables": [
    {
      "name": "party_a",
      "type": "text",
      "label": "甲方名称",
      "required": true
    }
  ]
}
```

### 7.4 发布版本
```http
POST /document-templates/{template_id}/versions/{version_id}/publish
```

### 7.5 预览模板
```http
POST /document-templates/{template_id}/versions/{version_id}/preview
```

**请求体**:
```json
{
  "variables": {
    "party_a": "某某公司",
    "party_b": "某某律所"
  }
}
```

---

## 8. 咨询模板管理 API

### 8.1 获取模板列表
```http
GET /consultation-templates?page=1&page_size=20&category=&status=
```

### 8.2 创建模板
```http
POST /consultation-templates
```

**请求体**:
```json
{
  "key": "legal_consultation",
  "name": "法律咨询表单",
  "description": "标准法律咨询表单",
  "category": "legal",
  "questions": [
    {
      "id": "q1",
      "type": "text",
      "label": "您的姓名",
      "required": true
    },
    {
      "id": "q2",
      "type": "textarea",
      "label": "问题描述",
      "placeholder": "请详细描述您的问题",
      "required": true
    }
  ],
  "is_default": false
}
```

### 8.3 发布模板
```http
POST /consultation-templates/{template_id}/publish
```

### 8.4 预览模板
```http
POST /consultation-templates/{template_id}/preview
```

**请求体**:
```json
{
  "answers": {
    "q1": "张三",
    "q2": "我想咨询关于合同纠纷的问题"
  }
}
```

---

## 9. 系统设置 API

### 9.1 获取配置列表
```http
GET /settings?category=
```

### 9.2 更新配置
```http
PUT /settings/{key}
```

**请求体**:
```json
{
  "value": "new_value",
  "description": "配置说明"
}
```

### 9.3 批量更新配置
```http
POST /settings/batch
```

**请求体**:
```json
{
  "items": [
    {"key": "site_name", "value": "新站点名称"},
    {"key": "site_logo", "value": "https://example.com/logo.png"}
  ]
}
```

### 9.4 系统状态监控
```http
GET /settings/status
```

**响应示例**:
```json
{
  "version": "1.0.0",
  "environment": "production",
  "uptime": 3600,
  "database": {
    "connected": true,
    "latency": 5.2
  },
  "cache": {
    "connected": true,
    "latency": 2.1
  },
  "memory": {
    "total": 16777216000,
    "used": 8388608000,
    "percent": 50
  },
  "cpu": {
    "usage": 25.5,
    "cores": 8
  },
  "disk": {
    "total": 512000000000,
    "used": 256000000000,
    "percent": 50
  }
}
```

### 9.5 系统日志
```http
GET /settings/logs?page=1&page_size=50&level=&module=
```

### 9.6 备份列表
```http
GET /settings/backups?page=1&page_size=20
```

### 9.7 创建备份
```http
POST /settings/backups?backup_type=full
```

### 9.8 删除备份
```http
DELETE /settings/backups/{backup_id}
```

---

## 认证方式

所有管理 API 都需要在请求头中携带 JWT Token：

```http
Authorization: Bearer <your_jwt_token>
```

获取 Token 的方式：
```http
POST /api/v1/auth/login
```

**请求体**:
```json
{
  "username": "admin",
  "password": "your_password"
}
```

---

## 错误码说明

| 状态码 | 说明 |
|--------|------|
| 200 | 请求成功 |
| 400 | 请求参数错误 |
| 401 | 未认证 |
| 403 | 无权限 |
| 404 | 资源不存在 |
| 409 | 资源冲突 |
| 500 | 服务器内部错误 |

---

## 测试示例

### 使用 curl 测试

```bash
# 1. 登录获取 Token
TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"password"}' \
  | jq -r '.access_token')

# 2. 获取律所列表
curl -X GET http://localhost:8000/api/v1/admin/law-firms \
  -H "Authorization: Bearer $TOKEN"

# 3. 获取结算仪表盘
curl -X GET http://localhost:8000/api/v1/admin/payment/settlement/dashboard \
  -H "Authorization: Bearer $TOKEN"

# 4. 发布系统通知
curl -X POST http://localhost:8000/api/v1/admin/notifications/admin/broadcast \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"title":"测试通知","content":"这是一条测试通知"}'
```

---

**文档版本**: v1.0  
**最后更新**: 2024-01-01
