
# 前后端联调测试文档

本文档定义了前后端联调测试的范围、API 接口清单、响应格式验证和测试步骤。

## 目录

1. [联调测试范围](#1-联调测试范围)
2. [API 接口联调清单](#2-api-接口联调清单)
3. [响应格式验证](#3-响应格式验证)
4. [错误处理验证](#4-错误处理验证)
5. [前端组件验证](#5-前端组件验证)
6. [测试步骤](#6-测试步骤)
7. [测试环境配置](#7-测试环境配置)

---

## 1. 联调测试范围

### 1.1 需要联调测试的功能模块

| 模块 | 描述 | 前端路径 | 后端路由 |
|------|------|----------|----------|
| 会员中心 (membership) | 会员等级、价格、升级、订单管理 | `/vip` | `/api/membership` |
| 视频咨询 (video-consultation) | 预约、确认、开始、结束视频咨询 | `/video-consultation` | `/api/v1/video-consultations` |
| 法律文书商城 (legal-document-mall) | 文书浏览、分类、购买 | `/legal-documents` | `/api/legal-documents` |
| 认证模块 (auth) | 登录、注册、登出、用户信息 | `/login`, `/register` | `/api/user` |
| 支付模块 (payment) | 订单创建、支付、退款、余额 | `/payment`, `/orders` | `/api/payment` |
| 通知模块 (notification) | 通知列表、已读、批量操作 | `/notifications` | `/api/notifications` |

### 1.2 联调测试优先级

| 优先级 | 模块 | 原因 |
|--------|------|------|
| P0 (最高) | 认证模块 (auth) | 所有模块依赖用户认证 |
| P0 (最高) | 支付模块 (payment) | 核心业务流程 |
| P1 | 会员中心 (membership) | 付费功能依赖 |
| P1 | 视频咨询 (video-consultation) | 核心业务功能 |
| P2 | 法律文书商城 (legal-document-mall) | 业务功能 |
| P2 | 通知模块 (notification) | 辅助功能 |

---

## 2. API 接口联调清单

### 2.1 会员中心模块 (membership)

| 状态 | 方法 | 接口路径 | 描述 | 前端函数 |
|------|------|----------|------|----------|
| [ ] | GET | `/membership/pricing` | 获取会员价格配置 | `apiGetMembershipPricing()` |
| [ ] | GET | `/membership/me` | 获取当前用户会员信息 | `apiGetMembershipInfo()` |
| [ ] | GET | `/membership/benefits` | 获取所有会员等级配置 | `apiGetMembershipLevels()` |
| [ ] | GET | `/membership/benefits/{tier}` | 获取指定等级的会员权益 | `apiGetMembershipBenefits(tier)` |
| [ ] | POST | `/membership/upgrade` | 升级会员 | `apiUpgradeMembership(request)` |
| [ ] | POST | `/membership/orders` | 创建会员订单 | `apiCreateMembershipOrder(request)` |
| [ ] | GET | `/membership/orders` | 获取会员订单列表 | `apiGetMembershipOrders()` |
| [ ] | POST | `/membership/orders/{orderId}/cancel` | 取消会员订单 | `apiCancelMembershipOrder(request)` |
| [ ] | GET | `/membership/history` | 获取转化历史记录 | `apiGetConversionHistory(params)` |
| [ ] | GET | `/membership/stats/conversions` | 获取转化统计 | `apiGetConversionStats(days)` |
| [ ] | GET | `/membership/stats/revenue` | 获取收入统计 | `apiGetRevenueStats()` |

#### 请求参数示例

**POST /membership/upgrade**
```json
{
  "tier": "monthly",
  "duration": 1
}
```

**POST /membership/orders**
```json
{
  "tier": "annual",
  "duration": 12,
  "paymentMethod": "wechat"
}
```

#### 响应数据示例

**GET /membership/pricing**
```json
{
  "success": true,
  "message": "Success",
  "data": [
    {
      "tier": "monthly",
      "name": "月度会员",
      "monthly_price": 29,
      "annual_price": 290,
      "annual_discount": 0.86,
      "lifetime_price": 999,
      "savings_annual": 58
    }
  ]
}
```

**GET /membership/me**
```json
{
  "success": true,
  "message": "Success",
  "data": {
    "user_id": 123,
    "level": "monthly",
    "level_name": "月度会员",
    "start_date": "2024-01-01",
    "end_date": "2024-02-01",
    "auto_renew": true,
    "is_active": true,
    "is_vip": true,
    "benefits": {
      "ai_consultations": 50,
      "document_downloads": 100,
      "video_consultation_discount": 0.8
    }
  }
}
```

---

### 2.2 视频咨询模块 (video-consultation)

| 状态 | 方法 | 接口路径 | 描述 | 前端函数 |
|------|------|----------|------|----------|
| [ ] | POST | `/v1/video-consultations` | 创建视频咨询预约 | `createVideoConsultation(request)` |
| [ ] | GET | `/v1/video-consultations` | 获取视频咨询列表 | `getVideoConsultations(params)` |
| [ ] | GET | `/v1/video-consultations/{id}` | 获取视频咨询详情 | `getVideoConsultation(id)` |
| [ ] | POST | `/v1/video-consultations/{id}/confirm` | 确认视频咨询（律师端） | `confirmVideoConsultation(id)` |
| [ ] | POST | `/v1/video-consultations/{id}/start` | 开始视频咨询 | `startVideoConsultation(id)` |
| [ ] | POST | `/v1/video-consultations/{id}/end` | 结束视频咨询 | `endVideoConsultation(id)` |
| [ ] | POST | `/v1/video-consultations/{id}/cancel` | 取消视频咨询 | `cancelVideoConsultation(id)` |
| [ ] | GET | `/v1/video-consultations/lawyers/{id}/available-slots` | 获取律师可用时段 | `getLawyerVideoSlots(lawyerId, date)` |
| [ ] | GET | `/v1/video-consultations/lawyers/{id}/fee` | 获取律师视频咨询费用 | `getLawyerVideoFee(lawyerId)` |
| [ ] | GET | `/v1/video-consultations/member-discount` | 获取会员折扣 | `getMemberDiscount()` |
| [ ] | GET | `/v1/video-consultations/usage` | 获取使用情况 | `getMyUsage()` |

#### 请求参数示例

**POST /v1/video-consultations**
```json
{
  "lawyer_id": 456,
  "subject": "合同纠纷咨询",
  "description": "关于房屋租赁合同的问题",
  "category": "民事",
  "scheduled_time": "2024-02-20T14:00:00Z"
}
```

**GET /v1/video-consultations**
```
?page=1&page_size=20&status_filter=pending
```

#### 响应数据示例

**GET /v1/video-consultations**
```json
{
  "success": true,
  "message": "Success",
  "data": {
    "items": [
      {
        "id": 1,
        "user_id": 123,
        "lawyer_id": 456,
        "subject": "合同纠纷咨询",
        "scheduled_time": "2024-02-20T14:00:00Z",
        "duration_minutes": 30,
        "status": "confirmed",
        "payment_status": "paid",
        "payment_amount": 199,
        "is_free": false,
        "discount_rate": 0.8,
        "meeting_url": "https://meeting.example.com/room/abc123"
      }
    ],
    "total": 10,
    "page": 1,
    "page_size": 20
  }
}
```

**GET /v1/video-consultations/lawyers/{id}/available-slots**
```json
{
  "success": true,
  "message": "Success",
  "data": {
    "date": "2024-02-20",
    "slots": [
      {
        "start_time": "09:00",
        "end_time": "09:30",
        "available": true
      },
      {
        "start_time": "09:30",
        "end_time": "10:00",
        "available": false
      }
    ]
  }
}
```

---

### 2.3 法律文书商城模块 (legal-document-mall)

| 状态 | 方法 | 接口路径 | 描述 | 前端函数 |
|------|------|----------|------|----------|
| [ ] | GET | `/legal-documents/categories` | 获取文书分类列表 | `apiGetCategories()` |
| [ ] | GET | `/legal-documents` | 获取法律文书列表 | `apiGetDocuments(params)` |
| [ ] | GET | `/legal-documents/featured` | 获取推荐文书 | `apiGetFeaturedDocuments(limit)` |
| [ ] | GET | `/legal-documents/free` | 获取免费文书 | `apiGetFreeDocuments(limit)` |
| [ ] | GET | `/legal-documents/{id}` | 获取法律文书详情 | `apiGetDocument(documentId)` |
| [ ] | GET | `/legal-documents/{id}/content` | 获取文书内容（需已购买） | `apiGetDocumentContent(documentId)` |
| [ ] | GET | `/legal-documents/{id}/price` | 计算文书价格 | `apiCalculatePrice(documentId)` |
| [ ] | POST | `/legal-documents/{id}/purchase` | 购买法律文书 | `apiPurchaseDocument(documentId, request)` |
| [ ] | POST | `/legal-documents/{id}/favorite` | 添加收藏 | `apiAddFavorite(documentId)` |
| [ ] | DELETE | `/legal-documents/{id}/favorite` | 取消收藏 | `apiRemoveFavorite(documentId)` |
| [ ] | GET | `/legal-documents/user/favorites` | 获取收藏列表 | `apiGetFavorites()` |
| [ ] | GET | `/legal-documents/user/orders` | 获取购买记录 | `apiGetDocumentOrders(page, pageSize)` |

#### 请求参数示例

**GET /legal-documents**
```
?category=合同&keyword=租赁&page=1&page_size=20&is_featured=false&is_free=false
```

**POST /legal-documents/{id}/purchase**
```json
{
  "paymentMethod": "wechat",
  "usePoints": false
}
```

#### 响应数据示例

**GET /legal-documents/categories**
```json
{
  "success": true,
  "message": "Success",
  "data": [
    {
      "id": 1,
      "name": "合同范本",
      "description": "各类合同模板",
      "document_count": 50,
      "icon": "contract"
    }
  ]
}
```

**GET /legal-documents**
```json
{
  "success": true,
  "message": "Success",
  "data": {
    "items": [
      {
        "id": 1,
        "name": "房屋租赁合同",
        "category": "合同范本",
        "price": 29.9,
        "is_free": false,
        "is_featured": true,
        "description": "标准房屋租赁合同模板",
        "preview_url": "/preview/1"
      }
    ],
    "total": 100,
    "page": 1,
    "page_size": 20
  }
}
```

---

### 2.4 认证模块 (auth)

| 状态 | 方法 | 接口路径 | 描述 | 前端函数 |
|------|------|----------|------|----------|
| [ ] | POST | `/user/register` | 用户注册 | `register(data)` |
| [ ] | POST | `/user/login` | 用户登录 | `login(data)` |
| [ ] | POST | `/user/logout` | 用户登出 | `logout()` |
| [ ] | GET | `/user/me` | 获取当前用户信息 | `getCurrentUser()` |
| [ ] | PUT | `/user/me` | 更新用户信息 | `updateProfile(data)` |
| [ ] | PUT | `/user/me/password` | 修改密码 | - |
| [ ] | GET | `/user/me/csrf-token` | 获取 CSRF Token | - |
| [ ] | POST | `/user/auth/refresh` | 刷新 Token | - |

#### 请求参数示例

**POST /user/register**
```json
{
  "username": "testuser",
  "password": "Test@123456",
  "email": "test@example.com",
  "phone": "13800138000"
}
```

**POST /user/login**
```json
{
  "username": "testuser",
  "password": "Test@123456"
}
```

#### 响应数据示例

**POST /user/login**
```json
{
  "success": true,
  "message": "登录成功",
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIs...",
    "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
    "token_type": "bearer",
    "expires_in": 3600
  }
}
```

**GET /user/me**
```json
{
  "success": true,
  "message": "Success",
  "data": {
    "id": 123,
    "username": "testuser",
    "email": "test@example.com",
    "phone": "13800138000",
    "avatar": "https://example.com/avatar.jpg",
    "role": "user",
    "created_at": "2024-01-01T00:00:00Z"
  }
}
```

---

### 2.5 支付模块 (payment)

| 状态 | 方法 | 接口路径 | 描述 | 前端函数 |
|------|------|----------|------|----------|
| [ ] | GET | `/payment/orders` | 获取订单列表 | `getOrders(params)` |
| [ ] | GET | `/payment/orders/{orderNo}` | 获取订单详情 | `getOrderDetail(orderNo)` |
| [ ] | POST | `/payment/orders` | 创建订单 | `createOrder(data)` |
| [ ] | POST | `/payment/orders/{orderNo}/pay` | 支付订单 | `payOrder(orderNo, data)` |
| [ ] | POST | `/payment/orders/{orderNo}/cancel` | 取消订单 | `cancelOrder(orderNo)` |
| [ ] | GET | `/payment/balance` | 获取用户余额 | `getBalance()` |
| [ ] | GET | `/payment/balance/transactions` | 获取余额交易记录 | `getBalanceTransactions(page, pageSize)` |
| [ ] | GET | `/payment/pricing` | 获取价格表 | `getPricing()` |
| [ ] | POST | `/payment/refunds` | 申请退款 | `createRefund(data)` |
| [ ] | GET | `/payment/refunds/{refundNo}` | 获取退款详情 | `getRefundDetail(refundNo)` |
| [ ] | GET | `/payment/refunds` | 获取退款列表 | `getRefunds(params)` |

#### 请求参数示例

**POST /payment/orders**
```json
{
  "order_type": "membership",
  "product_id": "monthly",
  "amount": 29,
  "payment_method": "wechat"
}
```

**POST /payment/orders/{orderNo}/pay**
```json
{
  "payment_method": "wechat",
  "return_url": "https://example.com/payment/result"
}
```

#### 响应数据示例

**GET /payment/orders**
```json
{
  "success": true,
  "message": "Success",
  "data": {
    "items": [
      {
        "order_no": "ORD202402200001",
        "order_type": "membership",
        "amount": 29,
        "status": "paid",
        "payment_method": "wechat",
        "paid_at": "2024-02-20T10:00:00Z",
        "created_at": "2024-02-20T09:50:00Z"
      }
    ],
    "total": 50,
    "page": 1,
    "page_size": 20
  }
}
```

**POST /payment/orders/{orderNo}/pay**
```json
{
  "success": true,
  "message": "支付订单创建成功",
  "data": {
    "order_no": "ORD202402200001",
    "payment_url": "https://wx.tenpay.com/...",
    "qr_code": "weixin://wxpay/bizpayurl?...",
    "expire_at": "2024-02-20T10:30:00Z"
  }
}
```

---

### 2.6 通知模块 (notification)

| 状态 | 方法 | 接口路径 | 描述 | 前端函数 |
|------|------|----------|------|----------|
| [ ] | GET | `/notifications` | 获取通知列表 | `getNotifications(params)` |
| [ ] | GET | `/notifications/unread-count` | 获取未读通知数量 | `getUnreadCount()` |
| [ ] | PATCH | `/notifications/{id}/read` | 标记通知为已读 | `markAsRead(notificationId)` |
| [ ] | PATCH | `/notifications/read-all` | 标记所有通知为已读 | `markAllAsRead()` |
| [ ] | DELETE | `/notifications/{id}` | 删除通知 | `deleteNotification(notificationId)` |
| [ ] | POST | `/notifications/batch-read` | 批量标记通知为已读 | `batchMarkAsRead(data)` |
| [ ] | POST | `/notifications/batch-delete` | 批量删除通知 | `batchDeleteNotifications(data)` |
| [ ] | GET | `/notifications/types` | 获取通知类型统计 | `getNotificationTypesStats()` |

#### 请求参数示例

**GET /notifications**
```
?page=1&page_size=20&unread_only=false&notification_type=system
```

**POST /notifications/batch-read**
```json
{
  "ids": [1, 2, 3, 4, 5]
}
```

#### 响应数据示例

**GET /notifications**
```json
{
  "success": true,
  "message": "Success",
  "data": {
    "items": [
      {
        "id": 1,
        "type": "system",
        "title": "系统维护通知",
        "content": "系统将于今晚10点进行维护",
        "is_read": false,
        "created_at": "2024-02-20T08:00:00Z"
      }
    ],
    "total": 10,
    "page": 1,
    "page_size": 20
  }
}
```

**GET /notifications/unread-count**
```json
{
  "success": true,
  "message": "Success",
  "data": {
    "count": 5
  }
}
```

---

## 3. 响应格式验证

### 3.1 统一响应格式 (ApiResponse)

所有 API 接口应返回统一的响应格式：

```typescript
interface ApiResponse<T> {
  success: boolean;      // 请求是否成功
  message: string;       // 响应消息
  data: T | null;        // 响应数据（可选）
  error_code?: number | null;  // 错误码（失败时）
}
```

### 3.2 分页响应格式 (PaginatedResponse)

列表接口应返回分页响应格式：

```typescript
interface PaginatedResponse<T> {
  success: boolean;
  message: string;
  data: T[];
  pagination: {
    page: number;        // 当前页码
    page_size: number;   // 每页大小
    total: number;       // 总记录数
    total_pages: number; // 总页数
  };
}
```

### 3.3 验证检查项

| 检查项 | 描述 | 状态 |
|--------|------|------|
| [ ] 成功响应包含 `success: true` | 所有成功响应必须有 `success: true` | |
| [ ] 失败响应包含 `success: false` | 所有失败响应必须有 `success: false` | |
| [ ] 失败响应包含 `error_code` | 所有失败响应必须包含整数错误码 | |
| [ ] `message` 字段存在 | 所有响应都应包含用户友好的消息 | |
| [ ] `data` 字段正确 | 成功时 `data` 包含业务数据，失败时可为 `null` | |
| [ ] 分页响应包含 `pagination` | 列表接口应返回完整的分页信息 | |
| [ ] 字段命名使用 snake_case | 后端返回字段使用 snake_case 格式 | |

### 3.4 字段命名转换验证

前端 API 客户端会自动将后端 snake_case 转换为 camelCase：

| 后端字段 | 前端字段 | 验证状态 |
|----------|----------|----------|
| `user_id` | `userId` | [ ] |
| `order_no` | `orderNo` | [ ] |
| `created_at` | `createdAt` | [ ] |
| `updated_at` | `updatedAt` | [ ] |
| `page_size` | `pageSize` | [ ] |
| `is_active` | `isActive` | [ ] |

---

## 4. 错误处理验证

### 4.1 错误码规范

| 错误码范围 | 模块 | 示例 |
|------------|------|------|
| 1000-1999 | 通用错误 | 1004: 资源不存在 |
| 2000-2999 | 用户相关 | 2003: 用户名或密码错误 |
| 3000-3999 | 支付相关 | 3001: 支付失败 |
| 4000-4999 | AI相关 | 4001: AI服务不可用 |
| 5000-5999 | 业务相关 | 5002: 订单已过期 |
| 6000-6999 | 内容相关 | 6001: 内容不存在 |
| 7000-7999 | 论坛相关 | 7001: 帖子不存在 |
| 8000-8999 | 系统相关 | 8001: 系统维护中 |
| 9000-9999 | 限流相关 | 9001: 请求过于频繁 |

### 4.2 常见错误码验证清单

| 错误码 | 错误名称 | 描述 | 验证状态 |
|--------|----------|------|----------|
| 1001 | INVALID_PARAMS | 请求参数无效 | [ ] |
| 1002 | UNAUTHORIZED | 未授权，请登录 | [ ] |
| 1003 | FORBIDDEN | 权限不足 | [ ] |
| 1004 | NOT_FOUND | 资源不存在 | [ ] |
| 1005 | INTERNAL_ERROR | 系统内部错误 | [ ] |
| 2001 | USER_NOT_FOUND | 用户不存在 | [ ] |
| 2002 | USER_ALREADY_EXISTS | 用户已存在 | [ ] |
| 2003 | INVALID_CREDENTIALS | 用户名或密码错误 | [ ] |
| 2004 | TOKEN_EXPIRED | 登录已过期 | [ ] |
| 3001 | PAYMENT_FAILED | 支付失败 | [ ] |
| 3003 | PAYMENT_ORDER_NOT_FOUND | 订单不存在 | [ ] |
| 3004 | PAYMENT_ORDER_ALREADY_PAID | 订单已支付 | [ ] |
| 3011 | INSUFFICIENT_BALANCE | 余额不足 | [ ] |

### 4.3 错误响应示例

```json
{
  "success": false,
  "message": "用户名或密码错误",
  "data": null,
  "error_code": 2003
}
```

```json
{
  "success": false,
  "message": "支付失败：余额不足",
  "data": null,
  "error_code": 3011
}
```

### 4.4 前端错误处理验证

| 验证项 | 描述 | 状态 |
|--------|------|------|
| [ ] 401 自动刷新 Token | 前端应在收到 401 时尝试刷新 Token | |
| [ ] Token 刷新失败跳转登录 | 刷新失败应清除认证状态并跳转登录页 | |
| [ ] 错误消息用户友好 | 所有错误消息应用户友好，不暴露技术细节 | |
| [ ] 网络错误处理 | 网络异常时应显示友好的错误提示 | |
| [ ] 超时处理 | 请求超时应显示超时提示 | |

---

## 5. 前端组件验证

### 5.1 通用组件状态验证

每个功能模块的前端组件应正确处理以下状态：

| 状态 | 描述 | 验证项 | 状态 |
|------|------|--------|------|
| 加载中 | 数据请求进行中 | 显示 Loading/Skeleton 组件 | [ ] |
| 成功 | 数据请求成功 | 正确渲染数据 | [ ] |
| 错误 | 数据请求失败 | 显示错误信息，提供重试按钮 | [ ] |
| 空数据 | 数据为空 | 显示空状态提示 | [ ] |

### 5.2 各模块组件验证清单

#### 会员中心模块

| 组件 | 验证项 | 状态 |
|------|--------|------|
| `MembershipCard` | 正确显示会员等级和到期时间 | [ ] |
| `PricingCard` | 正确显示价格信息 | [ ] |
| `MembershipBenefits` | 正确显示会员权益列表 | [ ] |
| `PurchaseFlow` | 购买流程完整可用 | [ ] |
| `UpgradePrompt` | 升级提示正确显示 | [ ] |

#### 视频咨询模块

| 组件 | 验证项 | 状态 |
|------|--------|------|
| `VideoConsultationCard` | 正确显示咨询信息 | [ ] |
| `VideoConsultationList` | 正确显示列表和分页 | [ ] |
| `VideoConsultationBooking` | 预约流程完整可用 | [ ] |
| `LawyerSchedulePicker` | 正确显示律师可用时段 | [ ] |
| `VideoConsultationRoom` | 视频通话功能正常 | [ ] |

#### 法律文书商城模块

| 组件 | 验证项 | 状态 |
|------|--------|------|
| `DocumentCard` | 正确显示文书信息 | [ ] |
| `DocumentGrid` | 正确显示文书网格 | [ ] |
| `DocumentCategoryList` | 正确显示分类列表 | [ ] |
| `DocumentDetail` | 正确显示文书详情 | [ ] |
| `DocumentPurchaseFlow` | 购买流程完整可用 | [ ] |

#### 支付模块

| 组件 | 验证项 | 状态 |
|------|--------|------|
| `PaymentModal` | 支付弹窗正确显示 | [ ] |
| `PaymentMethodSelector` | 支付方式选择正确 | [ ] |
| `PaymentStatus` | 正确显示支付状态 | [ ] |
| `PaymentHistory` | 正确显示支付历史 | [ ] |
| `OrderCard` | 正确显示订单信息 | [ ] |

#### 通知模块

| 组件 | 验证项 | 状态 |
|------|--------|------|
| `NotificationBell` | 正确显示未读数量 | [ ] |
| `NotificationDropdown` | 下拉列表正确显示 | [ ] |
| `NotificationItem` | 正确显示通知内容 | [ ] |
| `NotificationEmpty` | 空状态正确显示 | [ ] |
| `ConnectionStatus` | WebSocket 连接状态正确 | [ ] |

---

## 6. 测试步骤

### 6.1 认证模块测试

#### 6.1.1 用户注册

1. 访问注册页面 `/register`
2. 输入用户名、密码、邮箱
3. 点击注册按钮
4. **验证**：
   - [ ] 注册成功后自动登录
   - [ ] 显示成功消息
   - [ ] 跳转到首页
   - [ ] 用户名重复时显示错误提示

#### 6.1.2 用户登录

1. 访问登录页面 `/login`
2. 输入用户名和密码
3. 点击登录按钮
4. **验证**：
   - [ ] 登录成功后跳转到首页或来源页面
   - [ ] Token 正确存储
   - [ ] 用户信息正确显示在导航栏
   - [ ] 错误密码显示正确的错误提示

#### 6.1.3 Token 刷新

1. 登录后等待 Token 过期（或手动修改过期时间）
2. 发起任意需要认证的请求
3. **验证**：
   - [ ] 自动刷新 Token
   - [ ] 原请求重试成功
   - [ ] 刷新失败时跳转登录页

### 6.2 会员中心测试

#### 6.2.1 查看会员信息

1. 登录后访问会员页面 `/vip`
2. **验证**：
   - [ ] 正确显示当前会员等级
   - [ ] 正确显示会员到期时间
   - [ ] 正确显示会员权益

#### 6.2.2 升级会员

1. 在会员页面选择升级套餐
2. 点击"立即开通"
3. 选择支付方式
4. **验证**：
   - [ ] 正确显示价格信息
   - [ ] 创建订单成功
   - [ ] 跳转支付页面
   - [ ] 支付成功后会员状态更新

### 6.3 视频咨询测试

#### 6.3.1 预约视频咨询

1. 访问视频咨询页面 `/video-consultation`
2. 选择律师
3. 选择咨询时间
4. 填写咨询主题和描述
5. **验证**：
   - [ ] 律师列表正确显示
   - [ ] 可用时段正确显示
   - [ ] 预约创建成功
   - [ ] 显示预约确认信息

#### 6.3.2 视频咨询列表

1. 访问视频咨询列表
2. **验证**：
   - [ ] 正确显示预约列表
   - [ ] 分页功能正常
   - [ ] 状态筛选功能正常
   - [ ] 点击可查看详情

### 6.4 法律文书商城测试

#### 6.4.1 浏览文书

1. 访问法律文书商城 `/legal-documents`
2. **验证**：
   - [ ] 分类列表正确显示
   - [ ] 文书列表正确显示
   - [ ] 搜索功能正常
   - [ ] 分页功能正常

#### 6.4.2 购买文书

1. 选择一个文书
2. 查看详情
3. 点击购买
4. **验证**：
   - [ ] 正确显示价格信息
   - [ ] 会员折扣正确应用
   - [ ] 购买流程完整
   - [ ] 购买后可查看内容

### 6.5 支付模块测试

#### 6.5.1 创建订单

1. 选择商品/服务
2. 点击购买
3. **验证**：
   - [ ] 订单创建成功
   - [ ] 订单信息正确

#### 6.5.2 支付订单

1. 选择支付方式（微信/支付宝）
2. 确认支付
3. **验证**：
   - [ ] 支付二维码正确显示
   - [ ] 支付状态轮询正常
   - [ ] 支付成功后状态更新
   - [ ] 支付超时正确处理

### 6.6 通知模块测试

#### 6.6.1 通知列表

1. 访问通知中心 `/notifications`
2. **验证**：
   - [ ] 通知列表正确显示
   - [ ] 分页功能正常
   - [ ] 未读/已读筛选正常

#### 6.6.2 通知操作

1. 点击单条通知
2. 点击全部已读
3. 批量删除通知
4. **验证**：
   - [ ] 标记已读成功
   - [ ] 全部已读成功
   - [ ] 删除成功
   - [ ] 未读数量正确更新

---

## 7. 测试环境配置

### 7.1 环境变量

```bash
# 前端环境变量 (.env)
VITE_API_BASE_URL=http://localhost:8000/api
VITE_WS_URL=ws://localhost:8000/ws
```

### 7.2 测试账号

| 角色 | 用户名 | 密码 | 用途 |
|------|--------|------|------|
| 普通用户 | testuser | Test@123456 | 普通功能测试 |
| VIP用户 | vipuser | Test@123456 | 会员功能测试 |
| 律师 | lawyer | Test@123456 | 律师端功能测试 |
| 管理员 | admin | Admin@123456 | 管理功能测试 |

### 7.3 测试数据准备

在执行联调测试前，确保数据库中存在以下测试数据：

- [ ] 至少 2 个用户账号（普通用户、VIP用户）
- [ ] 至少 1 个律师账号
- [ ] 至少 3 个法律文书分类
- [ ] 至少 10 个法律文书
- [ ] 至少 3 个会员等级配置
- [ ] 测试支付配置（沙箱环境）

### 7.4 浏览器兼容性

| 浏览器 | 版本 | 状态 |
|--------|------|------|
| Chrome | 最新版 | [ ] |
| Firefox | 最新版 | [ ] |
| Safari | 最新版 | [ ] |
| Edge | 最新版 | [ ] |

### 7.5 移动端适配

| 设备 | 分辨率 | 状态 |
|------|--------|------|
| iPhone 14 | 390x844 | [ ] |
| iPhone 14 Pro Max | 430x932 | [ ] |
| Samsung Galaxy S21 | 360x800 | [ ] |
| iPad Air | 820x1180 | [ ] |

---

## 附录

### A. API 文档参考

- [API 接口文档](./API.md)
- [架构设计文档](./ARCHITECTURE.md)
- [