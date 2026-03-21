# 百姓助手 API 文档

> 完整的 API 接口文档，包含所有用户端和管理端 API

## 目录

1. [API 基础说明](#api-基础说明)
2. [认证 API](#认证-api)
3. [会员相关 API](#会员相关-api)
4. [视频咨询 API](#视频咨询-api)
5. [法律文书商城 API](#法律文书商城-api)
6. [推荐系统 API](#推荐系统-api)
7. [通知 API](#通知-api)
8. [用户 API](#用户-api)
9. [AI 咨询 API](#ai-咨询-api)
10. [论坛 API](#论坛-api)
11. [知识库 API](#知识库-api)
12. [支付 API](#支付-api)
13. [积分 API](#积分-api)
14. [管理后台 API](#管理后台-api)
15. [错误码说明](#错误码说明)

---

## API 基础说明

### Base URL

- **生产环境**: `https://api.baixing.com`
- **开发环境**: `http://localhost:8000`

### API 版本控制

百姓助手 API 支持多版本控制，确保向后兼容性的同时允许 API 演进。

#### 支持的版本

| 版本 | 状态 | 说明 |
|------|------|------|
| v1 | 稳定 | 当前默认版本 |
| v2 | 稳定 | 新增功能版本 |
| v3 | 最新 | 最新版本，包含所有功能 |

#### 版本协商方式

客户端可以通过以下三种方式指定 API 版本（按优先级排序）：

1. **URL 路径版本控制**（推荐）

   在 URL 路径中指定版本：
   ```http
   GET /api/v2/users
   ```

2. **X-API-Version 请求头**

   通过自定义请求头指定版本：
   ```http
   GET /api/users
   X-API-Version: v2
   ```

3. **Accept-Version 请求头**

   通过 Accept-Version 请求头指定版本：
   ```http
   GET /api/users
   Accept-Version: v2
   ```

#### 版本响应头

每个 API 响应都会包含以下版本相关响应头：

| 响应头 | 说明 | 示例 |
|--------|------|------|
| `X-API-Version` | 当前请求使用的 API 版本 | `v2` |
| `X-API-Supported-Versions` | 服务器支持的所有版本 | `v1, v2, v3` |
| `X-API-Deprecated` | 标记版本是否已废弃 | `true` |
| `X-API-Sunset` | 废弃版本的停用日期 | `Sat, 01 Jan 2027 00:00:00 GMT` |
| `X-API-Latest-Version` | 最新可用版本 | `v3` |
| `Link` | RFC 8288 格式的接替版本链接 | `</api/v3/users>; rel="successor-version"` |
| `Warning` | 废弃警告信息 | `299 - "API v1 已废弃，请迁移到 v2"` |

#### 版本废弃策略

当一个 API 版本被废弃时：

1. **提前通知**：至少提前 6 个月通知废弃计划
2. **过渡期**：废弃版本在过渡期内仍可使用，但会返回 `X-API-Deprecated: true` 响应头
3. **Sunset 头**：返回 `X-API-Sunset` 响应头指明停用日期
4. **Warning 头**：返回 `Warning` 响应头提供迁移建议

#### 版本兼容性

- **向后兼容的更改**（不需要升级版本号）：
  - 添加新的可选字段
  - 添加新的端点
  - 添加新的枚举值
  
- **不兼容的更改**（需要升级版本号）：
  - 删除或重命名字段
  - 更改字段类型
  - 删除端点
  - 更改认证机制

#### 示例请求

**请求指定版本：**
```bash
# 使用 URL 路径
curl -X GET "https://api.baixing.com/api/v2/users" \
  -H "Authorization: Bearer <token>"

# 使用请求头
curl -X GET "https://api.baixing.com/api/users" \
  -H "Authorization: Bearer <token>" \
  -H "X-API-Version: v2"
```

**响应示例（稳定版本）：**
```http
HTTP/1.1 200 OK
X-API-Version: v2
X-API-Supported-Versions: v1, v2, v3
Content-Type: application/json

{
  "code": 200,
  "message": "success",
  "data": {...}
}
```

**响应示例（废弃版本）：**
```http
HTTP/1.1 200 OK
X-API-Version: v1
X-API-Supported-Versions: v1, v2, v3
X-API-Deprecated: true
X-API-Sunset: Sat, 01 Jul 2027 00:00:00 GMT
X-API-Latest-Version: v2
Link: </api/v2/users>; rel="successor-version"
Warning: 299 - "API v1 已废弃，请于 2027-07-01 前迁移到 v2"
Content-Type: application/json

{
  "code": 200,
  "message": "success",
  "data": {...}
}
```

### 认证方式

大部分 API 需要在请求头中携带 JWT Token：

```http
Authorization: Bearer <your_jwt_token>
```

### 请求格式

除文件上传外，所有请求体都使用 JSON 格式：

```http
Content-Type: application/json
```

### 响应格式

所有响应都使用统一的 JSON 格式：

```json
{
  "code": 200,
  "message": "success",
  "data": {}
}
```

### 分页格式

列表接口使用统一的分页格式：

**请求参数**:
- `page`: 页码，从 1 开始
- `page_size`: 每页数量，默认 20，最大 100

**响应格式**:
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "items": [],
    "total": 100,
    "page": 1,
    "page_size": 20,
    "total_pages": 5
  }
}
```

---

## 认证 API

### 用户登录

```http
POST /api/v1/auth/login
```

**请求体**:
```json
{
  "username": "user@example.com",
  "password": "password123"
}
```

**响应**:
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "bearer",
    "expires_in": 3600,
    "user": {
      "id": 1,
      "username": "user@example.com",
      "nickname": "用户昵称",
      "avatar": "https://..."
    }
  }
}
```

### 用户注册

```http
POST /api/v1/auth/register
```

**请求体**:
```json
{
  "username": "user@example.com",
  "password": "password123",
  "nickname": "用户昵称",
  "phone": "13800138000",
  "sms_code": "123456"
}
```

### 刷新 Token

```http
POST /api/v1/auth/refresh
```

**请求体**:
```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

### 退出登录

```http
POST /api/v1/auth/logout
```

---

## 会员相关 API

### 获取会员价格

```http
GET /api/v1/membership/pricing
```

**响应**:
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "plans": [
      {
        "id": "monthly",
        "name": "月度会员",
        "price": 29.90,
        "original_price": 59.80,
        "duration_days": 30,
        "features": [
          "每日 5 次免费咨询",
          "视频咨询 8 折",
          "法律文书 7 折",
          "专属客服"
        ]
      },
      {
        "id": "yearly",
        "name": "年度会员",
        "price": 299.00,
        "original_price": 717.60,
        "duration_days": 365,
        "features": [
          "每日 10 次免费咨询",
          "视频咨询 6 折",
          "法律文书 5 折",
          "专属客服",
          "优先服务"
        ]
      }
    ]
  }
}
```

### 获取当前用户会员信息

```http
GET /api/v1/membership/me
```

**响应**:
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "is_member": true,
    "level": "vip",
    "plan_id": "yearly",
    "plan_name": "年度会员",
    "started_at": "2024-01-01T00:00:00Z",
    "expires_at": "2025-01-01T00:00:00Z",
    "days_remaining": 180,
    "auto_renew": true,
    "benefits_used": {
      "free_consultations": 120,
      "free_consultations_limit": 3650,
      "video_discount": 0.6,
      "document_discount": 0.5
    }
  }
}
```

### 升级会员

```http
POST /api/v1/membership/upgrade
```

**请求体**:
```json
{
  "plan_id": "yearly",
  "auto_renew": true
}
```

**响应**:
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "order_id": "ORD202401010001",
    "amount": 299.00,
    "payment_url": "https://...",
    "qr_code": "data:image/png;base64,..."
  }
}
```

### 创建会员订单

```http
POST /api/v1/membership/orders
```

**请求体**:
```json
{
  "plan_id": "yearly",
  "coupon_code": "NEW2024"
}
```

**响应**:
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "order_id": "ORD202401010001",
    "amount": 269.10,
    "original_amount": 299.00,
    "discount_amount": 29.90,
    "payment_url": "https://...",
    "qr_code": "data:image/png;base64,...",
    "expires_at": "2024-01-01T01:00:00Z"
  }
}
```

---

## 视频咨询 API

### 创建视频咨询预约

```http
POST /api/v1/video-consultations
```

**请求体**:
```json
{
  "lawyer_id": 1,
  "scheduled_at": "2024-01-15T14:00:00Z",
  "duration_minutes": 30,
  "topic": "合同纠纷咨询",
  "description": "我想咨询关于劳动合同解除的问题",
  "client_name": "张三",
  "client_phone": "13800138000"
}
```

**响应**:
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "id": 1,
    "order_id": "ORD202401010002",
    "lawyer": {
      "id": 1,
      "name": "李律师",
      "avatar": "https://...",
      "title": "高级律师",
      "specialties": ["劳动法", "合同法"]
    },
    "scheduled_at": "2024-01-15T14:00:00Z",
    "duration_minutes": 30,
    "status": "pending_confirmation",
    "fee": 200.00,
    "member_discount": 0.8,
    "final_fee": 160.00,
    "payment_required": true,
    "payment_url": "https://..."
  }
}
```

### 获取视频咨询列表

```http
GET /api/v1/video-consultations?page=1&page_size=20&status=
```

**查询参数**:
- `status`: 筛选状态（pending_confirmation, confirmed, completed, cancelled）
- `lawyer_id`: 按律师 ID 筛选

**响应**:
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "items": [
      {
        "id": 1,
        "lawyer": {
          "id": 1,
          "name": "李律师",
          "avatar": "https://..."
        },
        "scheduled_at": "2024-01-15T14:00:00Z",
        "duration_minutes": 30,
        "status": "confirmed",
        "topic": "合同纠纷咨询",
        "fee": 200.00,
        "final_fee": 160.00
      }
    ],
    "total": 10,
    "page": 1,
    "page_size": 20
  }
}
```

### 获取视频咨询详情

```http
GET /api/v1/video-consultations/{id}
```

**响应**:
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "id": 1,
    "order_id": "ORD202401010002",
    "lawyer": {
      "id": 1,
      "name": "李律师",
      "avatar": "https://...",
      "title": "高级律师",
      "specialties": ["劳动法", "合同法"],
      "introduction": "从事法律工作 10 年，擅长处理劳动纠纷"
    },
    "client": {
      "name": "张三",
      "phone": "138****8000"
    },
    "scheduled_at": "2024-01-15T14:00:00Z",
    "duration_minutes": 30,
    "status": "confirmed",
    "topic": "合同纠纷咨询",
    "description": "我想咨询关于劳动合同解除的问题",
    "fee": 200.00,
    "member_discount": 0.8,
    "final_fee": 160.00,
    "payment_status": "paid",
    "room_url": "https://meet.baixing.com/room/xxx",
    "created_at": "2024-01-01T10:00:00Z",
    "confirmed_at": "2024-01-01T11:00:00Z"
  }
}
```

### 确认预约

```http
POST /api/v1/video-consultations/{id}/confirm
```

**响应**:
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "id": 1,
    "status": "confirmed",
    "room_url": "https://meet.baixing.com/room/xxx",
    "confirmed_at": "2024-01-01T11:00:00Z"
  }
}
```

### 开始咨询

```http
POST /api/v1/video-consultations/{id}/start
```

**响应**:
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "id": 1,
    "status": "in_progress",
    "started_at": "2024-01-15T14:00:00Z",
    "room_url": "https://meet.baixing.com/room/xxx"
  }
}
```

### 结束咨询

```http
POST /api/v1/video-consultations/{id}/end
```

**请求体**:
```json
{
  "summary": "已解答用户关于劳动合同解除的疑问，建议用户收集相关证据后申请劳动仲裁",
  "follow_up_suggestions": [
    "收集劳动合同、工资流水等证据",
    "向当地劳动仲裁委员会申请仲裁",
    "如有需要可再次咨询"
  ]
}
```

**响应**:
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "id": 1,
    "status": "completed",
    "ended_at": "2024-01-15T14:30:00Z",
    "duration_actual": 28,
    "summary": "已解答用户关于劳动合同解除的疑问...",
    "rating_required": true
  }
}
```

### 取消预约

```http
POST /api/v1/video-consultations/{id}/cancel
```

**请求体**:
```json
{
  "reason": "时间冲突，需要改期",
  "cancel_type": "client"
}
```

**响应**:
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "id": 1,
    "status": "cancelled",
    "refund_status": "processing",
    "refund_amount": 160.00
  }
}
```

### 获取律师可用时段

```http
GET /api/v1/video-consultations/lawyers/{id}/available-slots
```

**查询参数**:
- `date`: 日期，格式 YYYY-MM-DD
- `duration`: 期望时长（分钟），默认 30

**响应**:
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "lawyer_id": 1,
    "date": "2024-01-15",
    "available_slots": [
      {
        "start_time": "09:00",
        "end_time": "09:30"
      },
      {
        "start_time": "10:00",
        "end_time": "10:30"
      },
      {
        "start_time": "14:00",
        "end_time": "14:30"
      }
    ]
  }
}
```

### 获取律师咨询费用

```http
GET /api/v1/video-consultations/lawyers/{id}/fee
```

**响应**:
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "lawyer_id": 1,
    "base_fee": 200.00,
    "duration_minutes": 30,
    "member_fees": {
      "vip": 120.00,
      "premium": 160.00
    },
    "currency": "CNY"
  }
}
```

### 获取会员折扣

```http
GET /api/v1/video-consultations/member-discount
```

**响应**:
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "is_member": true,
    "level": "vip",
    "discount_rate": 0.6,
    "discount_description": "VIP 会员享受 6 折优惠"
  }
}
```

### 获取使用情况

```http
GET /api/v1/video-consultations/usage
```

**响应**:
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "total_consultations": 5,
    "completed_consultations": 3,
    "pending_consultations": 1,
    "cancelled_consultations": 1,
    "total_spent": 800.00,
    "member_savings": 320.00
  }
}
```

---

## 法律文书商城 API

### 获取分类列表

```http
GET /api/legal-documents/categories
```

**响应**:
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "categories": [
      {
        "id": 1,
        "name": "合同协议",
        "slug": "contracts",
        "icon": "file-text",
        "count": 50
      },
      {
        "id": 2,
        "name": "诉讼文书",
        "slug": "litigation",
        "icon": "gavel",
        "count": 30
      },
      {
        "id": 3,
        "name": "婚姻家庭",
        "slug": "marriage-family",
        "icon": "heart",
        "count": 20
      },
      {
        "id": 4,
        "name": "劳动人事",
        "slug": "labor",
        "icon": "users",
        "count": 25
      }
    ]
  }
}
```

### 获取文书列表

```http
GET /api/legal-documents?page=1&page_size=20&category=&keyword=&sort=
```

**查询参数**:
- `category`: 分类 slug
- `keyword`: 搜索关键词
- `sort`: 排序方式（popular, newest, price_asc, price_desc）

**响应**:
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "items": [
      {
        "id": 1,
        "title": "标准劳动合同模板",
        "category": {
          "id": 1,
          "name": "合同协议"
        },
        "description": "适用于企业与员工签订的标准劳动合同",
        "price": 29.90,
        "member_price": 14.95,
        "sales": 1200,
        "rating": 4.8,
        "review_count": 156,
        "thumbnail": "https://..."
      }
    ],
    "total": 125,
    "page": 1,
    "page_size": 20
  }
}
```

### 获取文书详情

```http
GET /api/legal-documents/{id}
```

**响应**:
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "id": 1,
    "title": "标准劳动合同模板",
    "category": {
      "id": 1,
      "name": "合同协议"
    },
    "description": "适用于企业与员工签订的标准劳动合同，包含必备条款",
    "content_preview": "甲方（用人单位）：____________\n乙方（劳动者）：____________\n...",
    "price": 29.90,
    "member_price": 14.95,
    "member_discount": 0.5,
    "sales": 1200,
    "rating": 4.8,
    "review_count": 156,
    "features": [
      "专业律师编写",
      "符合最新法律法规",
      "可直接使用",
      "含填写说明"
    ],
    "tags": ["劳动合同", "用工合同", "劳动合同模板"],
    "thumbnail": "https://...",
    "images": ["https://...", "https://..."],
    "created_at": "2024-01-01T00:00:00Z",
    "updated_at": "2024-01-10T00:00:00Z"
  }
}
```

### 获取价格（含会员折扣）

```http
GET /api/legal-documents/{id}/price
```

**响应**:
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "document_id": 1,
    "original_price": 29.90,
    "member_price": 14.95,
    "discount_rate": 0.5,
    "discount_description": "VIP 会员享受 5 折优惠",
    "currency": "CNY"
  }
}
```

### 购买文书

```http
POST /api/legal-documents/{id}/purchase
```

**响应**:
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "order_id": "ORD202401010003",
    "document_id": 1,
    "amount": 14.95,
    "payment_status": "pending",
    "payment_url": "https://...",
    "qr_code": "data:image/png;base64,..."
  }
}
```

### 收藏文书

```http
POST /api/legal-documents/{id}/favorite
```

**响应**:
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "favorited": true,
    "favorite_id": 1
  }
}
```

### 取消收藏

```http
DELETE /api/legal-documents/{id}/favorite
```

**响应**:
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "favorited": false
  }
}
```

### 获取购买记录

```http
GET /api/legal-documents/user/orders?page=1&page_size=20
```

**响应**:
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "items": [
      {
        "order_id": "ORD202401010003",
        "document": {
          "id": 1,
          "title": "标准劳动合同模板",
          "thumbnail": "https://..."
        },
        "amount": 14.95,
        "payment_status": "paid",
        "download_url": "https://...",
        "download_expires_at": "2024-12-31T23:59:59Z",
        "purchased_at": "2024-01-01T12:00:00Z"
      }
    ],
    "total": 5,
    "page": 1,
    "page_size": 20
  }
}
```

---

## 推荐系统 API

### 获取增强版个性化首页

```http
GET /api/v1/recommendation/enhanced/personalized-home
```

**查询参数**:
- `scene`: 场景（home, knowledge, lawyer）

**响应**:
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "banners": [
      {
        "id": 1,
        "title": "新用户专享",
        "image": "https://...",
        "link": "/vip"
      }
    ],
    "recommended_lawyers": [
      {
        "id": 1,
        "name": "李律师",
        "avatar": "https://...",
        "title": "高级律师",
        "specialties": ["劳动法", "合同法"],
        "rating": 4.9,
        "consultations": 500
      }
    ],
    "recommended_knowledge": [
      {
        "id": 1,
        "title": "劳动合同解除的 5 个注意事项",
        "category": "劳动法",
        "thumbnail": "https://...",
        "views": 10000
      }
    ],
    "recommended_services": [
      {
        "id": "video_consultation",
        "name": "视频咨询",
        "icon": "video",
        "description": "与律师面对面沟通"
      }
    ]
  }
}
```

### 基于咨询历史推荐律师

```http
GET /api/v1/recommendation/lawyers/by-consultation
```

**查询参数**:
- `limit`: 返回数量，默认 5

**响应**:
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "lawyers": [
      {
        "id": 1,
        "name": "李律师",
        "avatar": "https://...",
        "title": "高级律师",
        "specialties": ["劳动法", "合同法"],
        "rating": 4.9,
        "consultations": 500,
        "match_score": 0.95,
        "match_reason": "擅长处理您咨询过的劳动法问题"
      }
    ],
    "recommendation_type": "by_consultation_history"
  }
}
```

### 基于位置推荐律师

```http
GET /api/v1/recommendation/lawyers/by-location
```

**查询参数**:
- `city`: 城市名
- `limit`: 返回数量，默认 5

**响应**:
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "lawyers": [
      {
        "id": 1,
        "name": "李律师",
        "avatar": "https://...",
        "title": "高级律师",
        "city": "北京",
        "specialties": ["劳动法", "合同法"],
        "rating": 4.9,
        "consultations": 500,
        "distance": "5km"
      }
    ],
    "city": "北京",
    "recommendation_type": "by_location"
  }
}
```

### 基于兴趣推荐知识文章

```http
GET /api/v1/recommendation/knowledge/by-interests
```

**查询参数**:
- `limit`: 返回数量，默认 10

**响应**:
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "articles": [
      {
        "id": 1,
        "title": "劳动合同解除的 5 个注意事项",
        "category": "劳动法",
        "thumbnail": "https://...",
        "views": 10000,
        "match_score": 0.90,
        "match_reason": "根据您的浏览历史推荐"
      }
    ],
    "interests": ["劳动法", "合同法"],
    "recommendation_type": "by_interests"
  }
}
```

### 获取新闻推荐

```http
GET /api/v1/recommendation/news
```

**查询参数**:
- `limit`: 返回数量，默认 10
- `category`: 分类筛选

**响应**:
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "articles": [
      {
        "id": 1,
        "title": "2024年劳动法新规解读",
        "category": "劳动法",
        "thumbnail": "https://...",
        "views": 50000,
        "published_at": "2024-01-10T10:00:00Z"
      }
    ],
    "recommendation_type": "personalized"
  }
}
```

### 用户兴趣标签管理

```http
GET /api/v1/recommendation/interests
```

**响应**:
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "user_interests": ["劳动法", "合同法", "婚姻法"],
    "available_interests": [
      { "id": 1, "name": "劳动法", "category": "法律" },
      { "id": 2, "name": "合同法", "category": "法律" },
      { "id": 3, "name": "婚姻法", "category": "法律" },
      { "id": 4, "name": "房产纠纷", "category": "法律" },
      { "id": 5, "name": "刑事辩护", "category": "法律" }
    ]
  }
}
```

### 更新用户兴趣标签

```http
PUT /api/v1/recommendation/interests
```

**请求体**:
```json
{
  "interests": ["劳动法", "合同法", "婚姻法"]
}
```

**响应**:
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "user_interests": ["劳动法", "合同法", "婚姻法"],
    "updated_at": "2024-01-10T10:00:00Z"
  }
}
```

### 冷启动用户推荐

```http
GET /api/v1/recommendation/cold-start
```

**查询参数**:
- `role`: 用户角色（如 employee, employer, individual）
- `needs`: 用户需求标签数组

**请求示例**:
```http
GET /api/v1/recommendation/cold-start?role=employee&needs=labor_dispute,contract_review
```

**响应**:
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "recommended_lawyers": [
      {
        "id": 1,
        "name": "李律师",
        "specialties": ["劳动法"],
        "rating": 4.9
      }
    ],
    "recommended_knowledge": [
      {
        "id": 1,
        "title": "劳动者权益保护指南"
      }
    ],
    "recommended_services": [
      {
        "id": "ai_consultation",
        "name": "AI法律咨询"
      },
      {
        "id": "video_consultation",
        "name": "视频咨询律师"
      }
    ]
  }
}
```

### 获取首页推荐数据

```http
GET /api/v1/recommendation/home
```

**响应**:
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "hot_topics": [
      {
        "id": 1,
        "title": "2024 年劳动法新规解读",
        "views": 50000
      }
    ],
    "featured_lawyers": [
      {
        "id": 1,
        "name": "李律师",
        "avatar": "https://...",
        "rating": 4.9
      }
    ],
    "new_articles": [
      {
        "id": 1,
        "title": "劳动合同解除的 5 个注意事项",
        "category": "劳动法",
        "created_at": "2024-01-10T00:00:00Z"
      }
    ]
  }
}
```

---

## 通知 API

### 获取通知列表

```http
GET /api/v1/notifications?page=1&page_size=20&type=&is_read=
```

**查询参数**:
- `type`: 通知类型（system, order, consultation, message）
- `is_read`: 是否已读（true, false）

**响应**:
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "items": [
      {
        "id": 1,
        "type": "system",
        "title": "系统维护通知",
        "content": "系统将于今晚进行维护",
        "link": "/notice/1",
        "is_read": false,
        "created_at": "2024-01-10T10:00:00Z"
      }
    ],
    "total": 50,
    "unread_count": 5
  }
}
```

### 标记单条为已读

```http
PATCH /api/v1/notifications/{id}/read
```

**响应**:
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "id": 1,
    "is_read": true,
    "read_at": "2024-01-10T12:00:00Z"
  }
}
```

### 标记全部为已读

```http
PATCH /api/v1/notifications/read-all
```

**响应**:
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "marked_count": 5
  }
}
```

### 批量标记已读

```http
PATCH /api/v1/notifications/batch-read
```

**请求体**:
```json
{
  "notification_ids": [1, 2, 3]
}
```

**响应**:
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "marked_count": 3
  }
}
```

### 获取未读数量

```http
GET /api/v1/notifications/unread-count
```

**响应**:
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "total_unread": 5,
    "by_type": {
      "system": 2,
      "order": 1,
      "consultation": 2,
      "message": 0
    }
  }
}
```

### 标记通知为未读

```http
PATCH /api/v1/notifications/{id}/unread
```

**响应**:
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "id": 1,
    "is_read": false,
    "read_at": null
  }
}
```

### 获取通知设置

```http
GET /api/v1/notifications/settings
```

**响应**:
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "push_enabled": true,
    "email_enabled": false,
    "types": {
      "system": { "push": true, "email": false },
      "order": { "push": true, "email": true },
      "consultation": { "push": true, "email": true },
      "message": { "push": true, "email": false }
    },
    "quiet_hours": {
      "enabled": true,
      "start": "22:00",
      "end": "08:00"
    }
  }
}
```

### 更新通知设置

```http
PUT /api/v1/notifications/settings
```

**请求体**:
```json
{
  "push_enabled": true,
  "email_enabled": true,
  "types": {
    "system": { "push": true, "email": false },
    "order": { "push": true, "email": true },
    "consultation": { "push": true, "email": true },
    "message": { "push": true, "email": false }
  },
  "quiet_hours": {
    "enabled": true,
    "start": "22:00",
    "end": "08:00"
  }
}
```

### 删除通知

```http
DELETE /api/v1/notifications/{id}
```

**响应**:
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "deleted": true
  }
}
```

---

## 用户 API

### 获取用户信息

```http
GET /api/v1/user/profile
```

**响应**:
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "id": 1,
    "username": "user@example.com",
    "nickname": "用户昵称",
    "avatar": "https://...",
    "phone": "138****8000",
    "gender": "male",
    "birthday": "1990-01-01",
    "location": "北京市",
    "created_at": "2023-01-01T00:00:00Z"
  }
}
```

### 更新用户信息

```http
PUT /api/v1/user/profile
```

**请求体**:
```json
{
  "nickname": "新昵称",
  "avatar": "https://...",
  "gender": "male",
  "birthday": "1990-01-01",
  "location": "上海市"
}
```

### 修改密码

```http
POST /api/v1/user/change-password
```

**请求体**:
```json
{
  "old_password": "old_password123",
  "new_password": "new_password123"
}
```

### 绑定手机号

```http
POST /api/v1/user/bind-phone
```

**请求体**:
```json
{
  "phone": "13800138000",
  "sms_code": "123456"
}
```

### 获取设备列表

```http
GET /api/v1/user/devices
```

**响应**:
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "devices": [
      {
        "id": 1,
        "device_name": "iPhone 15",
        "device_type": "mobile",
        "os": "iOS 17.0",
        "last_login_at": "2024-01-10T10:00:00Z",
        "last_login_ip": "192.168.1.1",
        "is_current": true
      }
    ]
  }
}
```

### 删除设备

```http
DELETE /api/v1/user/devices/{id}
```

**响应**:
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "deleted": true
  }
}
```

### 登录审计日志

```http
GET /api/v1/user/login-history?page=1&page_size=20
```

**响应**:
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "items": [
      {
        "id": 1,
        "login_at": "2024-01-10T10:00:00Z",
        "ip": "192.168.1.1",
        "location": "北京市",
        "device": "iPhone 15",
        "status": "success"
      }
    ],
    "total": 50,
    "page": 1,
    "page_size": 20
  }
}
```

---

## AI 咨询 API

### 创建咨询会话

```http
POST /api/v1/ai/consultations
```

**请求体**:
```json
{
  "title": "劳动合同解除咨询",
  "category": "劳动法",
  "content": "我想咨询关于劳动合同解除的相关问题..."
}
```

**响应**:
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "id": 1,
    "session_id": "sess_xxx",
    "title": "劳动合同解除咨询",
    "category": "劳动法",
    "created_at": "2024-01-10T10:00:00Z"
  }
}
```

### 发送消息

```http
POST /api/v1/ai/consultations/{id}/messages
```

**请求体**:
```json
{
  "content": "公司可以单方面解除劳动合同吗？",
  "mode": "chat"
}
```

**响应**:
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "message_id": "msg_xxx",
    "content": "根据《劳动合同法》规定，公司在以下情况下可以单方面解除劳动合同：\n1. 劳动者严重违反用人单位规章制度...\n",
    "confidence": 0.95,
    "sources": [
      {
        "title": "劳动合同法第三十九条",
        "url": "https://..."
      }
    ],
    "created_at": "2024-01-10T10:00:00Z"
  }
}
```

### 获取咨询历史

```http
GET /api/v1/ai/consultations?page=1&page_size=20
```

**响应**:
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "items": [
      {
        "id": 1,
        "title": "劳动合同解除咨询",
        "category": "劳动法",
        "message_count": 5,
        "last_message_at": "2024-01-10T10:30:00Z",
        "created_at": "2024-01-10T10:00:00Z"
      }
    ],
    "total": 10,
    "page": 1,
    "page_size": 20
  }
}
```

### 获取会话详情

```http
GET /api/v1/ai/consultations/{id}
```

**响应**:
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "id": 1,
    "title": "劳动合同解除咨询",
    "category": "劳动法",
    "messages": [
      {
        "id": 1,
        "role": "user",
        "content": "公司可以单方面解除劳动合同吗？",
        "created_at": "2024-01-10T10:00:00Z"
      },
      {
        "id": 2,
        "role": "assistant",
        "content": "根据《劳动合同法》规定...",
        "confidence": 0.95,
        "created_at": "2024-01-10T10:00:01Z"
      }
    ],
    "created_at": "2024-01-10T10:00:00Z"
  }
}
```

### 删除咨询会话

```http
DELETE /api/v1/ai/consultations/{id}
```

**响应**:
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "deleted": true
  }
}
```

### 语音咨询

```http
POST /api/v1/ai/consultations/{id}/voice
```

**请求体**:
```json
{
  "audio_url": "https://...",
  "duration": 30
}
```

**响应**:
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "message_id": "msg_xxx",
    "transcription": "公司可以单方面解除劳动合同吗？",
    "content": "根据《劳动合同法》规定...",
    "audio_response_url": "https://..."
  }
}
```

---

## 论坛 API

### 获取帖子列表

```http
GET /api/v1/forum/posts?page=1&page_size=20&category=&sort=
```

**查询参数**:
- `category`: 分类 ID
- `sort`: 排序方式（latest, hot, essence）

**响应**:
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "items": [
      {
        "id": 1,
        "title": "劳动合同解除的 5 个注意事项",
        "category": {
          "id": 1,
          "name": "劳动法"
        },
        "author": {
          "id": 1,
          "nickname": "法律达人",
          "avatar": "https://..."
        },
        "views": 1000,
        "likes": 50,
        "comments_count": 20,
        "is_essence": true,
        "is_sticky": false,
        "created_at": "2024-01-10T10:00:00Z"
      }
    ],
    "total": 100,
    "page": 1,
    "page_size": 20
  }
}
```

### 获取帖子详情

```http
GET /api/v1/forum/posts/{id}
```

**响应**:
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "id": 1,
    "title": "劳动合同解除的 5 个注意事项",
    "content": "1. 提前通知...\n2. 经济补偿...\n...",
    "category": {
      "id": 1,
      "name": "劳动法"
    },
    "author": {
      "id": 1,
      "nickname": "法律达人",
      "avatar": "https://..."
    },
    "views": 1001,
    "likes": 50,
    "comments_count": 20,
    "is_essence": true,
    "is_sticky": false,
    "tags": ["劳动法", "劳动合同"],
    "created_at": "2024-01-10T10:00:00Z"
  }
}
```

### 创建帖子

```http
POST /api/v1/forum/posts
```

**请求体**:
```json
{
  "title": "劳动合同解除的 5 个注意事项",
  "content": "1. 提前通知...\n2. 经济补偿...\n...",
  "category_id": 1,
  "tags": ["劳动法", "劳动合同"]
}
```

**响应**:
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "id": 1,
    "title": "劳动合同解除的 5 个注意事项",
    "created_at": "2024-01-10T10:00:00Z"
  }
}
```

### 更新帖子

```http
PUT /api/v1/forum/posts/{id}
```

**请求体**:
```json
{
  "title": "更新后的标题",
  "content": "更新后的内容..."
}
```

### 删除帖子

```http
DELETE /api/v1/forum/posts/{id}
```

### 点赞帖子

```http
POST /api/v1/forum/posts/{id}/like
```

### 取消点赞

```http
DELETE /api/v1/forum/posts/{id}/like
```

### 获取评论列表

```http
GET /api/v1/forum/posts/{id}/comments?page=1&page_size=20
```

### 创建评论

```http
POST /api/v1/forum/posts/{id}/comments
```

**请求体**:
```json
{
  "content": "写得很好，学到了很多！",
  "parent_id": null
}
```

### 删除评论

```http
DELETE /api/v1/forum/comments/{id}
```

---

## 知识库 API

### 获取知识分类

```http
GET /api/v1/knowledge/categories
```

**响应**:
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "categories": [
      {
        "id": 1,
        "name": "劳动法",
        "slug": "labor-law",
        "article_count": 100
      },
      {
        "id": 2,
        "name": "合同法",
        "slug": "contract-law",
        "article_count": 80
      }
    ]
  }
}
```

### 获取知识文章列表

```http
GET /api/v1/knowledge/articles?page=1&page_size=20&category=&keyword=
```

**响应**:
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "items": [
      {
        "id": 1,
        "title": "劳动合同解除的 5 个注意事项",
        "category": {
          "id": 1,
          "name": "劳动法"
        },
        "summary": "本文介绍了劳动合同解除时需要注意的 5 个关键事项...",
        "thumbnail": "https://...",
        "views": 10000,
        "created_at": "2024-01-10T10:00:00Z"
      }
    ],
    "total": 100,
    "page": 1,
    "page_size": 20
  }
}
```

### 获取文章详情

```http
GET /api/v1/knowledge/articles/{id}
```

**响应**:
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "id": 1,
    "title": "劳动合同解除的 5 个注意事项",
    "content": "## 前言\n\n劳动合同解除是劳动者和用人单位都...",
    "category": {
      "id": 1,
      "name": "劳动法"
    },
    "author": {
      "id": 1,
      "nickname": "法律专家",
      "avatar": "https://..."
    },
    "views": 10001,
    "likes": 500,
    "related_articles": [
      {
        "id": 2,
        "title": "经济补偿金计算方法"
      }
    ],
    "created_at": "2024-01-10T10:00:00Z",
    "updated_at": "2024-01-10T12:00:00Z"
  }
}
```

### 点赞文章

```http
POST /api/v1/knowledge/articles/{id}/like
```

### 收藏文章

```http
POST /api/v1/knowledge/articles/{id}/favorite
```

### 取消收藏

```http
DELETE /api/v1/knowledge/articles/{id}/favorite
```

### 获取收藏列表

```http
GET /api/v1/knowledge/favorites?page=1&page_size=20
```

---

## 支付 API

### 创建订单

```http
POST /api/v1/payment/orders
```

**请求体**:
```json
{
  "product_type": "membership",
  "product_id": "yearly",
  "amount": 299.00
}
```

**响应**:
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "order_id": "ORD202401010001",
    "amount": 299.00,
    "payment_url": "https://...",
    "qr_code": "data:image/png;base64,...",
    "expires_at": "2024-01-01T01:00:00Z"
  }
}
```

### 获取订单详情

```http
GET /api/v1/payment/orders/{id}
```

**响应**:
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "order_id": "ORD202401010001",
    "product_type": "membership",
    "product_name": "年度会员",
    "amount": 299.00,
    "payment_status": "pending",
    "payment_method": null,
    "paid_at": null,
    "created_at": "2024-01-01T00:00:00Z",
    "expires_at": "2024-01-01T01:00:00Z"
  }
}
```

### 获取订单列表

```http
GET /api/v1/payment/orders?page=1&page_size=20&status=
```

**查询参数**:
- `status`: 订单状态（pending, paid, failed, refunded）

### 取消订单

```http
POST /api/v1/payment/orders/{id}/cancel
```

### 支付回调

```http
POST /api/v1/payment/callbacks/{provider}
```

### 申请退款

```http
POST /api/v1/payment/orders/{id}/refund
```

**请求体**:
```json
{
  "reason": "误操作购买",
  "amount": 299.00
}
```

---

## 积分 API

### 获取积分余额

```http
GET /api/v1/points/balance
```

**响应**:
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "balance": 1000,
    "frozen": 0,
    "available": 1000
  }
}
```

### 获取积分明细

```http
GET /api/v1/points/transactions?page=1&page_size=20&type=
```

**查询参数**:
- `type`: 类型（earn, spend）

**响应**:
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "items": [
      {
        "id": 1,
        "type": "earn",
        "amount": 100,
        "balance_after": 1000,
        "description": "每日签到",
        "created_at": "2024-01-10T10:00:00Z"
      }
    ],
    "total": 50,
    "page": 1,
    "page_size": 20
  }
}
```

### 每日签到

```http
POST /api/v1/points/checkin
```

**响应**:
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "points": 10,
    "streak_days": 5,
    "bonus_points": 20,
    "total_points": 30
  }
}
```

### 获取签到日历

```http
GET /api/v1/points/checkin/calendar?month=2024-01
```

### 积分兑换商品

```http
POST /api/v1/points/exchange
```

**请求体**:
```json
{
  "product_id": 1,
  "quantity": 1
}
```

### 获取兑换商品列表

```http
GET /api/v1/points/products?page=1&page_size=20
```

### 获取兑换记录

```http
GET /api/v1/points/exchanges?page=1&page_size=20
```

---

## 管理后台 API

管理后台 API 的详细文档请查看 [API_ADMIN_V1.md](../backend/API_ADMIN_V1.md)

### 基础信息

- **Base URL**: `http://localhost:8000/api/v1/admin`
- **认证方式**: JWT Token (Bearer)
- **权限要求**: 管理员权限

### 主要模块

| 模块 | 路径前缀 | 功能描述 |
|------|---------|---------|
| 律所管理 | `/law-firms` | 律所 CRUD、批量审核、统计 |
| 提现管理 | `/withdrawals` | 提现申请审核、导出 |
| 帖子管理 | `/posts` | 帖子审核、置顶、精华 |
| 支付回调 | `/payment/callbacks` | 回调监控、重试、处理 |
| 结算统计 | `/payment/settlement` | 仪表盘、趋势、排行 |
| 系统通知 | `/notifications` | 广播、定向通知管理 |
| 文档模板 | `/document-templates` | 模板管理、版本控制 |
| 咨询模板 | `/consultation-templates` | 表单模板管理 |
| 系统设置 | `/settings` | 配置管理、监控、日志 |

---

## 错误码说明

### HTTP 状态码

| 状态码 | 说明 |
|--------|------|
| 200 | 请求成功 |
| 201 | 创建成功 |
| 204 | 删除成功 |
| 400 | 请求参数错误 |
| 401 | 未认证/Token 过期 |
| 403 | 无权限 |
| 404 | 资源不存在 |
| 409 | 资源冲突 |
| 429 | 请求过于频繁 |
| 500 | 服务器内部错误 |

### 业务错误码

| 错误码 | 说明 |
|--------|------|
| 1001 | 用户不存在 |
| 1002 | 密码错误 |
| 1003 | Token 无效 |
| 1004 | Token 已过期 |
| 2001 | 订单不存在 |
| 2002 | 订单已支付 |
| 2003 | 订单已过期 |
| 2004 | 订单金额不匹配 |
| 3001 | 会员已过期 |
| 3002 | 会员权益不足 |
| 4001 | 咨询预约不存在 |
| 4002 | 预约时间不可用 |
| 4003 | 预约已确认 |
| 4004 | 预约已取消 |
| 5001 | 文书不存在 |
| 5002 | 文书未购买 |
| 6001 | 积分不足 |
| 6002 | 商品库存不足 |
| 7001 | 帖子不存在 |
| 7002 | 帖子已被删除 |
| 8001 | 文章不存在 |
| 9001 | 通知不存在 |

### 错误响应格式

```json
{
  "code": 1001,
  "message": "用户不存在",
  "data": null
}
```

---

## 版本历史

| 版本 | 日期 | 更新内容 |
|------|------|---------|
| v1.0.0 | 2024-01-01 | 初始版本 |
| v1.1.0 | 2024-01-15 | 新增会员系统 API |
| v1.2.0 | 2024-02-01 | 新增视频咨询 API |
| v1.3.0 | 2024-02-15 | 新增法律文书商城 API |
| v1.4.0 | 2024-03-01 | 新增推荐系统 API |
| v1.5.0 | 2024-03-15 | 通知 API 增强 |
| v2.0.0 | 2026-03-21 | 微服务架构拆分，11个独立服务 |

## 微服务架构

### 架构概览

```
┌─────────────────────────────────────────────────────────────────┐
│                         前端 (5173)                              │
│  vite.config.ts 配置了 11 个服务的代理                          │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                    API Gateway / Nginx                           │
│                      /api/v1/*                                   │
└─────────────────────────────────────────────────────────────────┘
    │           │           │           │           │
    ▼           ▼           ▼           ▼           ▼
┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐
│ Backend│ │ User   │ │Payment │ │Legal   │ │  AI    │
│ 8080   │ │Service │ │Channel │ │Service │ │Service │
│        │ │ 8001   │ │ 8002   │ │ 8004   │ │ 8005   │
└────────┘ └────────┘ └────────┘ └────────┘ └────────┘
                                │
              ┌─────────────────┼─────────────────┐
              ▼                 ▼                 ▼
        ┌────────┐       ┌────────┐         ┌────────┐
        │Accounting│       │ News   │         │Community│
        │ 8003   │       │Service │         │Service │
        └────────┘       │ 8006   │         │ 8007   │
                        └────────┘         └────────┘
                                │
        ┌───────────────────────┼───────────────────────┐
        ▼                       ▼                       ▼
    ┌────────┐           ┌────────┐              ┌────────┐
    │ Points │           │Notifi- │              │Search  │
    │Service │           │ cation │              │Service │
    │ 8008   │           │ 8009   │              │ 8011   │
    └────────┘           └────────┘              └────────┘
```

### 服务端口映射

| 服务 | 端口 | 前缀 | 说明 |
|------|------|------|------|
| Backend (Legacy) | 8080 | /api/v1 | 核心业务API |
| User Service | 8001 | /api/v1 | 用户、认证、会员 |
| Payment Channel | 8002 | /api/v1 | 支付通道 |
| Accounting | 8003 | /api/v1 | 账务结算 |
| Legal Service | 8004 | /api/v1 | 律师、法律知识 |
| AI Service | 8005 | /api/v1 | AI对话 |
| News Service | 8006 | /api/v1 | 新闻资讯 |
| Community | 8007 | /api/v1 | 社区论坛 |
| Points | 8008 | /api/v1 | 积分系统 |
| Notification | 8009 | /api/v1 | 通知推送 |
| Recommendation | 8010 | /api/v1 | 推荐系统 |
| Search | 8011 | /api/v1 | 搜索服务 |

### 前端代理配置

前端通过 vite.config.ts 配置代理:

```typescript
// 微服务代理
'/api/v1/auth': { target: 'http://127.0.0.1:8001' }
'/api/v1/users': { target: 'http://127.0.0.1:8001' }
'/api/v1/payment': { target: 'http://127.0.0.1:8002' }
'/api/v1/balance': { target: 'http://127.0.0.1:8003' }
'/api/v1/legal': { target: 'http://127.0.0.1:8004' }
'/api/v1/ai': { target: 'http://127.0.0.1:8005' }
'/api/v1/news': { target: 'http://127.0.0.1:8006' }
'/api/v1/community': { target: 'http://127.0.0.1:8007' }
'/api/v1/points': { target: 'http://127.0.0.1:8008' }
'/api/v1/notifications': { target: 'http://127.0.0.1:8009' }
'/api/v1/recommendations': { target: 'http://127.0.0.1:8010' }
'/api/v1/search': { target: 'http://127.0.0.1:8011' }
```

### 启动服务

```bash
# 启动后端
cd backend && uvicorn app.main:app --host 0.0.0.0 --port 8080

# 启动微服务
cd services/user-service && uvicorn app.main:app --port 8001
cd services/payment-channel-service && uvicorn app.main:app --port 8002
cd services/payment-accounting-service && uvicorn app.main:app --port 8003
cd services/legal-service && uvicorn app.main:app --port 8004
cd services/ai-service && uvicorn app.main:app --port 8005
cd services/news-service && uvicorn app.main:app --port 8006
cd services/community-service && uvicorn app.main:app --port 8007
cd services/points-service && uvicorn app.main:app --port 8008
cd services/notification-service && uvicorn app.main:app --port 8009
cd services/recommendation-service && uvicorn app.main:app --port 8010
cd services/search-service && uvicorn app.main:app --port 8011

# 运行联调测试
bash scripts/test-microservices.sh
```

---

## 联系方式

如有 API 相关问题，请联系：

- 邮箱：api@baixing.com
- 开发者文档：https://open.baixing.com