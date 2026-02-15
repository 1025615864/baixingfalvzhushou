# JWT Token轮换机制

本文档介绍百姓法律助手应用的Token轮换安全机制。

## 概述

Token轮换机制增强了认证安全性，通过以下特性实现：

- **双Token策略**: access_token (短期15分钟) + refresh_token (长期7天)
- **Token刷新**: 使用refresh_token换取新的access_token
- **Token黑名单**: Redis存储已撤销的token
- **轮换次数限制**: 最多5次轮换，防止无限轮换攻击
- **Token家族**: 追踪同一登录会话的token族，防止重放攻击

## 架构设计

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   客户端     │────▶│  API网关    │────▶│ Token轮换   │
│             │     │  (versioning)│     │  服务       │
└─────────────┘     └─────────────┘     └──────┬──────┘
                                               │
                       ┌───────────────────────┼─────────────┐
                       │                       │             │
                       ▼                       ▼             ▼
                 ┌──────────┐          ┌──────────┐   ┌──────────┐
                 │ 数据库    │          │  Redis   │   │  JWT     │
                 │(refresh_ │          │(黑名单/ │   │ 签名验证  │
                 │ tokens)  │          │ 元数据)  │   │          │
                 └──────────┘          └──────────┘   └──────────┘
```

## 核心模块

### 1. TokenRotationService (`app/core/token_rotation.py`)

核心服务类，提供以下方法：

| 方法 | 说明 |
|------|------|
| `create_token_pair()` | 创建新的token对（登录时使用） |
| `rotate_tokens()` | 使用refresh_token换取新的token对 |
| `revoke_token()` | 撤销特定token（加入黑名单） |
| `revoke_family()` | 撤销整个token家族 |
| `verify_token()` | 验证token有效性 |
| `is_token_revoked()` | 检查token是否在黑名单中 |

### 2. 数据模型

#### RefreshTokenRecord (数据库表)

```sql
CREATE TABLE refresh_tokens (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    token_jti VARCHAR(64) UNIQUE NOT NULL,
    token_family VARCHAR(64) NOT NULL,
    issued_at TIMESTAMP WITH TIME ZONE NOT NULL,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    rotated_at TIMESTAMP WITH TIME ZONE,
    rotation_count INTEGER DEFAULT 0,
    is_revoked BOOLEAN DEFAULT FALSE,
    revoked_at TIMESTAMP WITH TIME ZONE,
    revoked_reason VARCHAR(50),
    device_info VARCHAR(255),
    ip_address VARCHAR(45)
);
```

索引:
- `ix_refresh_tokens_user_id` - 按用户查询
- `ix_refresh_tokens_token_jti` - 按JTI查询
- `ix_refresh_tokens_token_family` - 按家族查询
- `ix_refresh_tokens_expires_at` - 过期时间查询
- `ix_refresh_tokens_is_revoked` - 撤销状态查询

#### TokenMetadata (Redis)

```json
{
  "jti": "uuid-token-id",
  "sub": 123,
  "type": "refresh",
  "issued_at": 1706700000,
  "expires_at": 1707304800,
  "family": "fam_abc123",
  "rotation_count": 2
}
```

### 3. API端点

#### POST `/user/auth/refresh` - 刷新Token

**请求**:
```json
{
  "refresh_token": "optional-refresh-token-from-cookie-if-not-provided"
}
```

**响应**:
```json
{
  "access_token": "new-access-token",
  "refresh_token": "new-refresh-token-if-rotated",
  "token_type": "bearer",
  "expires_in": 900,
  "rotated": true,
  "message": "Token轮换成功"
}
```

**流程**:
1. 验证refresh_token有效性
2. 检查token是否在黑名单中
3. 检查轮换次数限制
4. 撤销旧的refresh_token
5. 生成新的token对
6. 更新数据库记录

#### POST `/user/auth/revoke` - 撤销Token

**请求**:
```json
{
  "token": "optional-specific-token"
}
```

**响应**:
```json
{
  "message": "Token已撤销 / 已撤销 X 个活跃会话",
  "success": true
}
```

#### GET `/user/auth/active-tokens` - 获取活跃Token列表

**响应**:
```json
{
  "tokens": [
    {
      "jti": "token-id",
      "family": "fam_abc123",
      "issued_at": "2026-01-31T10:00:00Z",
      "expires_at": "2026-02-07T10:00:00Z",
      "rotation_count": 2,
      "device_info": "Mozilla/5.0...",
      "ip_address": "192.168.1.1"
    }
  ],
  "total": 1
}
```

## 安全机制

### 1. 重放攻击防护

```
客户端                    服务器
  │                        │
  │── refresh_token #1 ───▶│  首次使用
  │                        │  1. 验证有效
  │◀── new token pair ─────│  2. 撤销 #1
  │                        │  3. 返回新token
  │                        │
  │── refresh_token #1 ───▶│  重放攻击!
  │                        │  1. 发现已在黑名单
  │◀── 401 Unauthorized ───│  2. 撤销整个家族
  │                        │  3. 要求重新登录
```

### 2. 轮换次数限制

每个token家族最多轮换5次，超过则：
- 撤销整个token家族
- 用户需要重新登录
- 记录安全日志

### 3. Token家族机制

同一登录会话的所有token属于同一家族（family）：
- 家族中的任一token被撤销 → 整个家族失效
- 用于检测异常登录行为
- 支持多设备管理

## 配置参数

```python
# app/core/token_rotation.py

ACCESS_TOKEN_EXPIRE_MINUTES = 15    # access_token有效期
REFRESH_TOKEN_EXPIRE_DAYS = 7       # refresh_token有效期
MAX_ROTATION_COUNT = 5              # 最大轮换次数
TOKEN_BLACKLIST_PREFIX = "token:revoked"    # Redis黑名单键前缀
TOKEN_FAMILY_PREFIX = "token:family"        # Token家族前缀
TOKEN_META_PREFIX = "token:meta"            # Token元数据前缀
```

## 使用示例

### 登录时创建Token对

```python
from app.core.token_rotation import TokenRotationService

# 用户登录
token_pair = await TokenRotationService.create_token_pair(
    user_id=user.id,
    user_email=user.email,
    user_role=user.role,
    device_info=request.headers.get("user-agent"),
    ip_address=request.client.host,
    db=db,
)

# 设置Cookie
response.set_cookie(key="access_token", value=token_pair.access_token, httponly=True)
response.set_cookie(key="refresh_token", value=token_pair.refresh_token, httponly=True)
```

### 前端Token刷新逻辑

```javascript
// 拦截器处理401错误
axios.interceptors.response.use(
  response => response,
  async error => {
    const originalRequest = error.config;
    
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;
      
      try {
        // 调用刷新接口
        const { data } = await axios.post('/user/auth/refresh', {}, {
          withCredentials: true  // 发送Cookie
        });
        
        // 保存新的access_token（如果有）
        if (data.access_token) {
          localStorage.setItem('access_token', data.access_token);
        }
        
        // 重试原请求
        return axios(originalRequest);
      } catch (refreshError) {
        // 刷新失败，跳转登录
        window.location.href = '/login';
        return Promise.reject(refreshError);
      }
    }
    
    return Promise.reject(error);
  }
);
```

## 数据库迁移

运行迁移创建refresh_tokens表：

```bash
cd backend
alembic upgrade head
```

## 清理任务

建议定期清理过期的token记录：

```python
# 定期任务
async def cleanup_expired_tokens():
    async with async_session() as db:
        count = await TokenRotationService.cleanup_expired_tokens(db)
        print(f"Cleaned up {count} expired tokens")
```

## 故障排查

| 问题 | 原因 | 解决方案 |
|------|------|----------|
| Token刷新失败 | refresh_token过期或已撤销 | 重新登录 |
| 轮换次数超限 | 同一token家族轮换超过5次 | 重新登录，检查账号安全 |
| 检测到重放攻击 | 同一token被多次使用 | 账号可能被攻击，建议修改密码 |
| Redis连接失败 | 黑名单检查降级 | 检查Redis服务状态 |

## 安全建议

1. **使用HTTPS**: 生产环境必须启用HTTPS
2. **Cookie安全属性**: 设置Secure和SameSite=Strict
3. **IP绑定**: 敏感操作可结合IP验证
4. **设备指纹识别**: 检测异常设备登录
5. **监控告警**: 监控token异常使用模式

## 相关文件

- `backend/app/core/token_rotation.py` - Token轮换核心实现
- `backend/app/routers/user.py` - API端点
- `backend/app/schemas/user.py` - 请求/响应模型
- `backend/alembic/versions/add_refresh_tokens_table.py` - 数据库迁移
- `backend/app/core/versioning.py` - API版本控制集成