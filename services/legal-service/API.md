# 律师服务 API 文档

## 基础信息

| 属性 | 值 |
|------|-----|
| 基础路径 | `/api/v1/legal` |
| HTTP 端口 | 8004 |
| gRPC 端口 | 50052 |
| 认证方式 | `Authorization: Bearer <token>` |
| 数据格式 | `application/json` |

---

## 认证说明

### 请求头

| 头 | 说明 |
|----|------|
| Authorization | Bearer Token 认证 |
| X-User-ID | 用户 ID |
| X-User-Role | 用户角色 (user/lawyer/admin) |
| Idempotency-Key | 幂等键 (POST/PUT/PATCH 请求) |

### 角色权限

| 角色 | 说明 |
|------|------|
| user | 普通用户 |
| lawyer | 律师 |
| admin | 管理员 |

---

## 咨询 API

### 创建咨询
```
POST /api/v1/legal/consultations/
```

**请求体:**
```json
{
  "category": "婚姻继承",
  "title": "离婚财产分割",
  "description": "婚后财产如何分割...",
  "ai_assisted": true
}
```

**响应:**
```json
{
  "id": 1,
  "user_id": 123,
  "category": "婚姻继承",
  "title": "离婚财产分割",
  "description": "婚后财产如何分割...",
  "status": "pending",
  "ai_assisted": true,
  "created_at": "2026-03-23T10:00:00Z"
}
```

### 获取咨询列表
```
GET /api/v1/legal/consultations/
```

**查询参数:**
| 参数 | 类型 | 说明 |
|------|------|------|
| page | int | 页码 (默认1) |
| page_size | int | 每页数量 (默认20) |
| status | string | 状态筛选 |

### 获取咨询详情
```
GET /api/v1/legal/consultations/{id}
```

### 获取咨询统计
```
GET /api/v1/legal/consultations/stats
```

**响应:**
```json
{
  "total": 100,
  "pending": 20,
  "processing": 30,
  "answered": 50
}
```

### 获取待匹配咨询
```
GET /api/v1/legal/consultations/pending
```

**查询参数:**
| 参数 | 类型 | 说明 |
|------|------|------|
| category | string | 分类筛选 |
| page | int | 页码 |
| page_size | int | 每页数量 |

### 分配律师
```
POST /api/v1/legal/consultations/{id}/assign
```

**请求体:**
```json
{
  "lawyer_id": 1
}
```

### 完成咨询
```
POST /api/v1/legal/consultations/{id}/complete
```

### 取消咨询
```
POST /api/v1/legal/consultations/{id}/cancel
```

### 添加消息
```
POST /api/v1/legal/consultations/{id}/messages
```

**请求体:**
```json
{
  "role": "user",
  "content": "我想咨询一下..."
}
```

### 获取消息列表
```
GET /api/v1/legal/consultations/{id}/messages
```

---

## 律师 API

### 获取律师列表
```
GET /api/v1/legal/lawyers/
```

**查询参数:**
| 参数 | 类型 | 说明 |
|------|------|------|
| page | int | 页码 |
| page_size | int | 每页数量 |
| city | string | 城市筛选 |
| specialty | string | 专业筛选 |
| status | string | 状态筛选 (verified/pending) |

**响应:**
```json
{
  "items": [
    {
      "id": 1,
      "name": "张律师",
      "title": "高级合伙人",
      "specialties": ["刑事辩护", "民事诉讼"],
      "rating": 4.8,
      "consultation_count": 156,
      "city": "北京",
      "status": "verified"
    }
  ],
  "total": 100,
  "page": 1,
  "page_size": 20,
  "total_pages": 5
}
```

### 获取律师详情
```
GET /api/v1/legal/lawyers/{id}
```

### 搜索律师
```
GET /api/v1/legal/lawyers/search
```

**查询参数:**
| 参数 | 类型 | 说明 |
|------|------|------|
| q | string | 搜索关键词 |
| city | string | 城市 |
| specialty | string | 专业 |
| page | int | 页码 |
| page_size | int | 每页数量 |

### 获取律师评价
```
GET /api/v1/legal/lawyers/{id}/reviews
```

### 获取律师日程
```
GET /api/v1/legal/lawyers/{id}/schedule
```

**查询参数:**
| 参数 | 类型 | 说明 |
|------|------|------|
| date | string | 日期 (YYYY-MM-DD) |
| year | int | 年份 |
| month | int | 月份 |

### 创建律师档案
```
POST /api/v1/legal/lawyers/
```

**请求体:**
```json
{
  "user_id": 123,
  "name": "张律师",
  "title": "高级合伙人",
  "specialties": ["刑事辩护", "民事诉讼"],
  "bio": "从业20年...",
  "city": "北京"
}
```

### 更新律师档案
```
PATCH /api/v1/legal/lawyers/{id}
```

**请求体:**
```json
{
  "title": "合伙人",
  "specialties": ["刑事辩护"],
  "bio": "从业20年..."
}
```

### 获取律师统计
```
GET /api/v1/legal/lawyers/{id}/stats
```

---

## 律所 API

### 申请入驻律所
```
POST /api/v1/legal/firms/
```

**请求体:**
```json
{
  "name": "XX律师事务所",
  "license_no": "12345678",
  "province": "北京",
  "city": "北京",
  "address": "XX路XX号"
}
```

### 获取律所列表
```
GET /api/v1/legal/firms/
```

**查询参数:**
| 参数 | 类型 | 说明 |
|------|------|------|
| page | int | 页码 |
| page_size | int | 每页数量 |
| city | string | 城市筛选 |
| province | string | 省份筛选 |

### 获取律所详情
```
GET /api/v1/legal/firms/{id}
```

### 更新律所信息
```
PATCH /api/v1/legal/firms/{id}
```

**请求体:**
```json
{
  "name": "XX律师事务所",
  "province": "北京",
  "city": "北京",
  "address": "XX路XX号"
}
```

### 提交资质审核
```
POST /api/v1/legal/firms/{id}/verification
```

### 获取审核状态
```
GET /api/v1/legal/firms/{id}/verification
```

### 获取律所律师列表
```
GET /api/v1/legal/firms/{id}/lawyers
```

### 邀请律师加入
```
POST /api/v1/legal/firms/{id}/invitations
```

**请求体:**
```json
{
  "lawyer_id": 1,
  "role": "partner"
}
```

### 获取邀请列表
```
GET /api/v1/legal/firms/{id}/invitations
```

### 移除律师
```
DELETE /api/v1/legal/firms/{id}/lawyers/{lawyer_id}
```

---

## 邀请响应 API

### 接受邀请
```
POST /api/v1/legal/invitations/{id}/accept
```

### 拒绝邀请
```
POST /api/v1/legal/invitations/{id}/reject
```

### 我的邀请列表
```
GET /api/v1/legal/invitations/me
```

---

## 预约 API

### 创建预约
```
POST /api/v1/legal/appointments/
```

**请求体:**
```json
{
  "consultation_id": 1,
  "lawyer_id": 1,
  "appointment_type": "video",
  "scheduled_at": "2024-01-15T10:00:00Z",
  "price": 500.00
}
```

### 获取预约列表
```
GET /api/v1/legal/appointments/
```

**查询参数:**
| 参数 | 类型 | 说明 |
|------|------|------|
| page | int | 页码 |
| page_size | int | 每页数量 |
| lawyer_id | int | 律师ID |
| status | string | 状态筛选 |

### 获取预约详情
```
GET /api/v1/legal/appointments/{id}
```

### 取消预约
```
POST /api/v1/legal/appointments/{id}/cancel
```

---

## 评价 API

### 创建评价
```
POST /api/v1/legal/reviews/
```

**请求体:**
```json
{
  "consultation_id": 1,
  "lawyer_id": 1,
  "rating": 5,
  "content": "律师很专业...",
  "is_anonymous": false
}
```

### 获取评价列表
```
GET /api/v1/legal/reviews/
```

**查询参数:**
| 参数 | 类型 | 说明 |
|------|------|------|
| lawyer_id | int | 律师ID |
| page | int | 页码 |
| page_size | int | 每页数量 |

---

## 排班 API

### 创建排班
```
POST /api/v1/legal/schedules/
```

**请求体:**
```json
{
  "lawyer_id": 1,
  "date": "2024-01-15",
  "start_time": "09:00",
  "end_time": "10:00"
}
```

### 批量创建排班
```
POST /api/v1/legal/schedules/bulk
```

**请求体:**
```json
{
  "lawyer_id": 1,
  "schedules": [
    {"date": "2024-01-15", "start_time": "09:00", "end_time": "10:00"},
    {"date": "2024-01-15", "start_time": "10:00", "end_time": "11:00"}
  ]
}
```

### 获取排班列表
```
GET /api/v1/legal/schedules/
```

**查询参数:**
| 参数 | 类型 | 说明 |
|------|------|------|
| lawyer_id | int | 律师ID |
| date | string | 日期 |
| year | int | 年份 |
| month | int | 月份 |

### 更新排班可用性
```
PATCH /api/v1/legal/schedules/{id}
```

**请求体:**
```json
{
  "is_available": false
}
```

---

## 文书 API

### 创建文书
```
POST /api/v1/legal/documents/
```

**请求体:**
```json
{
  "consultation_id": 1,
  "document_type": "合同",
  "title": "离婚协议",
  "content": "...",
  "generated_by_ai": false
}
```

### 获取文书详情
```
GET /api/v1/legal/documents/{id}
```

### 获取咨询的所有文书
```
GET /api/v1/legal/documents/consultation/{consultation_id}
```

### 更新文书
```
PATCH /api/v1/legal/documents/{id}
```

**请求体:**
```json
{
  "content": "...",
  "status": "completed"
}
```

### 删除文书
```
DELETE /api/v1/legal/documents/{id}
```

### 获取文书模板
```
GET /api/v1/legal/documents/templates/
```

**查询参数:**
| 参数 | 类型 | 说明 |
|------|------|------|
| category | string | 分类筛选 |

---

## 管理 API

### 获取统计数据
```
GET /api/v1/legal/admin/stats
```

**响应:**
```json
{
  "total_lawyers": 100,
  "verified_lawyers": 80,
  "pending_lawyers": 20,
  "total_consultations": 500,
  "active_consultations": 50
}
```

### 获取所有律所列表
```
GET /api/v1/legal/admin/firms
```

### 获取待审核律所列表
```
GET /api/v1/legal/admin/firms/pending
```

### 获取审核中律所列表
```
GET /api/v1/legal/admin/firms/reviewing
```

### 审核通过
```
POST /api/v1/legal/admin/firms/{id}/approve
```

### 审核拒绝
```
POST /api/v1/legal/admin/firms/{id}/reject
```

**请求体:**
```json
{
  "reason": "资质不符合要求"
}
```

### 获取律所统计
```
GET /api/v1/legal/admin/firms/{id}/stats
```

### 获取律师统计
```
GET /api/v1/legal/admin/firms/{id}/lawyer-stats
```

### 清除缓存
```
POST /api/v1/legal/cache/clear
```

**查询参数:**
| 参数 | 类型 | 说明 |
|------|------|------|
| type | string | 缓存类型 (lawyer/firm/all) |

---

## 监控 API

### Prometheus 指标
```
GET /api/v1/legal/metrics
```

---

## 系统 API

### 健康检查
```
GET /health
```

### 就绪检查
```
GET /health/ready
```

### 存活检查
```
GET /health/live
```

---

## 统一 API 响应格式

所有 API 响应均遵循以下统一格式：

```json
{
  "code": 0,
  "message": "success",
  "data": { ... }
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| code | int | 状态码，0 表示成功，非 0 表示错误 |
| message | string | 状态信息，成功时为 "success" |
| data | object | 响应数据，失败时为 null |

**示例 - 成功响应：**
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "id": 1,
    "name": "张律师"
  }
}
```

**示例 - 错误响应：**
```json
{
  "code": 10001,
  "message": "咨询不存在",
  "data": null
}
```

---

## 错误码

| 错误码 | 说明 |
|--------|------|
| L14041 | 咨询不存在 |
| L14091 | 咨询已关闭 |
| L14291 | 咨询次数超限 |
| L14092 | 咨询状态无效 |
| L24041 | 律师不存在 |
| L24091 | 律师当前不可用 |
| L24092 | 律师已认证 |
| L24093 | 律师未认证 |
| L24094 | 不能分配给自己 |
| L34041 | 预约不存在 |
| L34091 | 预约时间冲突 |
| L34092 | 该时段不可预约 |
| L34093 | 预约状态无效 |
| L44091 | 已提交过评价 |
| L44031 | 无权评价此咨询 |
| L54041 | 律所不存在 |
| L54091 | 律所未认证 |
| L40001 | 参数错误 |
| L40101 | Token无效 |
| L40102 | Token已过期 |
| L50301 | 服务暂时不可用 |
| L50001 | 内部错误 |

---

## gRPC API

### GetLawyer

获取律师信息

```protobuf
message GetLawyerRequest {
  string lawyer_id = 1;
}

message Lawyer {
  string lawyer_id = 1;
  string name = 2;
  string firm_id = 3;
  string title = 4;
  repeated string expertise = 5;
  int32 rating = 6;
  int32 consultation_count = 7;
  int64 price_per_hour = 8;
}
```

### GetLawyerSchedule

获取律师排班

```protobuf
message GetLawyerScheduleRequest {
  string lawyer_id = 1;
  string date = 2;
}

message LawyerSchedule {
  string lawyer_id = 1;
  repeated TimeSlot available_slots = 2;
}

message TimeSlot {
  string slot_id = 1;
  Timestamp start_time = 2;
  Timestamp end_time = 3;
  bool is_available = 4;
}
```
