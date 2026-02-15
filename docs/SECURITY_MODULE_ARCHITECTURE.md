# Security 模块架构设计文档

## 方案C：扩展双功能

后端同时支持数据安全（原有）+ 用户安全中心（新增），前端保持现有用户安全中心实现。

---

## 一、功能范围划分

### 1.1 数据安全平台（原有功能）
- **目标用户**：管理员
- **核心功能**：
  - 数据分级（Data Classification）
  - 敏感数据脱敏（Data Masking）
  - 审计日志（Audit Logging）
- **API前缀**：`/api/v1/security/`
- **权限**：管理员专用

### 1.2 用户安全中心（新增功能）
- **目标用户**：普通用户
- **核心功能**：
  - 双因素认证（2FA/TOTP）
  - 设备管理（登录设备列表、踢出设备）
  - 登录审计（查看自己的登录记录）
  - 密码安全（修改密码、密码强度检查）
  - 安全等级评估
- **API前缀**：`/api/v1/user/security/`
- **权限**：登录用户

---

## 二、后端 API 设计

### 2.1 2FA 管理端点

```python
# 前缀: /api/v1/user/security/2fa

GET    /status              # 获取2FA状态（是否启用）
POST   /setup/init          # 初始化2FA设置（返回二维码/密钥）
POST   /setup/verify        # 验证并启用2FA（需验证码）
POST   /disable             # 禁用2FA（需验证码或密码）
POST   /verify              # 验证2FA码（登录时用）
```

### 2.2 设备管理端点

```python
# 前缀: /api/v1/user/security/devices

GET    /                    # 获取当前登录设备列表
DELETE /{device_id}         # 踢出指定设备（撤销其token）
DELETE /others              # 踢出除当前设备外的所有设备
GET    /current             # 获取当前设备信息
```

### 2.3 登录审计端点

```python
# 前缀: /api/v1/user/security/audit

GET    /logins              # 获取登录历史
       查询参数: page, page_size, start_date, end_date
       返回: 登录时间、IP、设备、地点、结果
```

### 2.4 密码安全端点

```python
# 前缀: /api/v1/user/security/password

POST   /change              # 修改密码（需旧密码）
POST   /check-strength      # 检查密码强度
GET    /last-changed        # 获取密码最后修改时间
```

### 2.5 安全等级评估端点

```python
# 前缀: /api/v1/user/security/level

GET    /                    # 获取安全等级评分
       评分维度: 2FA、密码强度、设备安全、登录异常
```

---

## 三、数据库模型设计

### 3.1 UserSecuritySettings（用户安全设置）

```python
class UserSecuritySettings(Base):
    """用户安全中心设置表"""
    __tablename__ = "user_security_settings"
    
    id: int                    # 主键
    user_id: int               # 用户ID（外键）
    
    # 2FA设置
    totp_secret: str | None    # TOTP密钥（加密存储）
    is_2fa_enabled: bool       # 是否启用2FA
    backup_codes: list[str]    # 备用验证码（哈希存储）
    
    # 密码安全
    password_changed_at: datetime  # 密码最后修改时间
    
    # 安全通知
    login_alert_enabled: bool  # 新设备登录提醒
    unusual_activity_alert: bool  # 异常活动提醒
    
    created_at: datetime
    updated_at: datetime
```

### 3.2 UserDevice（用户设备）

```python
class UserDevice(Base):
    """用户登录设备表"""
    __tablename__ = "user_devices"
    
    id: int                    # 主键
    user_id: int               # 用户ID
    
    # 设备信息
    device_id: str             # 设备唯一标识
    device_name: str           # 设备名称（用户可自定义）
    device_type: str           # 类型: web/mobile/app
    user_agent: str            # UA信息
    
    # 登录信息
    ip_address: str            # IP地址
    location: str | None       # 登录地点
    first_login_at: datetime   # 首次登录时间
    last_login_at: datetime    # 最后活跃时间
    
    # 安全状态
    is_current: bool           # 是否为当前设备
    is_revoked: bool           # 是否已撤销
    revoked_at: datetime | None
    
    # Token指纹（用于识别token）
    token_fingerprint: str
```

### 3.3 LoginAudit（登录审计）

```python
class LoginAudit(Base):
    """用户登录审计表"""
    __tablename__ = "user_login_audits"
    
    id: int                    # 主键
    user_id: int               # 用户ID
    
    # 登录信息
    action: str                # 动作: login/logout/2fa_verify/failed
    ip_address: str            # IP地址
    user_agent: str            # UA
    device_id: str | None      # 设备ID
    
    # 结果
    success: bool              # 是否成功
    failure_reason: str | None # 失败原因
    
    # 元数据
    location: str | None       # 地理位置
    created_at: datetime       # 时间戳
    
    # 索引: user_id + created_at（用于查询用户登录历史）
```

---

## 四、服务层设计

### 4.1 新增服务文件

```
backend/app/services/
├── user_security_service.py    # 用户安全中心主服务
├── totp_service.py             # TOTP/2FA服务
├── device_manager.py           # 设备管理服务
└── login_audit_service.py      # 登录审计服务
```

### 4.2 关键服务方法

#### UserSecurityService
```python
class UserSecurityService:
    async def get_2fa_status(self, user_id: int) -> TwoFAStatus
    async def setup_2fa(self, user_id: int) -> TwoFASetupInfo  # 返回QR码
    async def verify_and_enable_2fa(self, user_id: int, code: str) -> bool
    async def disable_2fa(self, user_id: int, code: str) -> bool
    async def verify_2fa_code(self, user_id: int, code: str) -> bool
    
    async def get_security_level(self, user_id: int) -> SecurityLevel
```

#### DeviceManager
```python
class DeviceManager:
    async def list_devices(self, user_id: int) -> list[DeviceInfo]
    async def register_device(self, user_id: int, device_info: DeviceInfo) -> str  # 返回device_id
    async def revoke_device(self, user_id: int, device_id: str) -> bool
    async def revoke_other_devices(self, user_id: int, current_device_id: str) -> int  # 返回撤销数量
    async def get_current_device(self, user_id: int, token_fingerprint: str) -> DeviceInfo
```

#### LoginAuditService
```python
class LoginAuditService:
    async def log_login(self, user_id: int, success: bool, **kwargs)
    async def log_logout(self, user_id: int, device_id: str)
    async def log_2fa_verify(self, user_id: int, success: bool)
    async def get_login_history(self, user_id: int, pagination: Pagination) -> list[LoginRecord]
```

---

## 五、前端对接方案

### 5.1 保持现有结构

前端 `features/security/` 目录结构保持不变，API 层需要对接新的后端端点。

### 5.2 需要修改的文件

| 文件 | 修改内容 |
|------|----------|
| `api/index.ts` | 更新 API 调用为新的端点路径 |
| `types/index.ts` | 添加新接口的 TypeScript 类型 |
| `hooks/useSecurity.ts` | 更新 hooks 使用新的 API |

### 5.3 API 路径映射

```typescript
// 当前前端期望的 API -> 需要改为 -> 后端提供的新 API

// 2FA
'/security/2fa/status'      -> GET  /api/v1/user/security/2fa/status
'/security/2fa/setup'       -> POST /api/v1/user/security/2fa/setup/init
'/security/2fa/verify'      -> POST /api/v1/user/security/2fa/setup/verify
'/security/2fa/disable'     -> POST /api/v1/user/security/2fa/disable

// 设备管理
'/security/devices'         -> GET  /api/v1/user/security/devices
'/security/devices/{id}'    -> DELETE /api/v1/user/security/devices/{id}

// 登录审计
'/security/audit/logins'    -> GET  /api/v1/user/security/audit/logins

// 密码
'/security/password/change' -> POST /api/v1/user/security/password/change
```

---

## 六、实现计划

### 阶段一：数据库和模型（1天）
1. 创建 Alembic 迁移脚本
2. 新增数据模型文件
3. 更新 models/__init__.py

### 阶段二：后端服务层（2天）
1. 实现 totp_service.py
2. 实现 device_manager.py
3. 实现 login_audit_service.py
4. 实现 user_security_service.py（整合）

### 阶段三：后端 API 层（1天）
1. 新增 user/security 路由（或在现有 user 路由下扩展）
2. 实现所有端点
3. 添加权限检查

### 阶段四：前端对接（1天）
1. 更新 api/index.ts
2. 更新类型定义
3. 测试验证

---

## 七、接口文档

### 7.1 统一响应格式

```json
{
  "code": 200,
  "message": "success",
  "data": { ... }
}
```

### 7.2 错误码定义

| 错误码 | 说明 |
|--------|------|
| 4001 | 2FA验证码错误 |
| 4002 | 2FA已启用 |
| 4003 | 2FA未启用 |
| 4004 | 设备不存在 |
| 4005 | 密码强度不足 |
| 4006 | 旧密码错误 |

---

## 八、安全注意事项

1. **TOTP密钥加密**：使用 AES-256 加密存储
2. **备用码哈希**：使用 bcrypt 哈希存储
3. **设备指纹**：使用 HMAC-SHA256 生成
4. **审计日志**：不可删除，保留至少90天
5. **敏感操作**：修改密码、禁用2FA等需要二次验证

---

## 九、后续扩展

1. **WebAuthn**：支持硬件安全密钥
2. **OAuth绑定**：第三方登录绑定管理
3. **会话管理**：查看和管理活跃会话
4. **安全通知**：邮件/短信安全提醒

---

**创建日期**: 2026-02-05  
**版本**: v1.0  
**状态**: 待实现