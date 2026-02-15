# 用户认证（AUTH）

本模块负责用户的注册、登录、找回密码、邮箱验证等身份管理功能。

## 1. 业务流程

### 1.1 注册
- 输入邮箱、密码、确认密码。
- 调用 `POST /api/user/register`。
- 发送激活邮件。
- 用户通过邮件链接激活账号 (`GET /api/user/email-verification/verify`)。

### 1.2 登录
- 支持邮箱密码登录 (`POST /api/user/login`)。
- 支持微信扫描登录 (对接微信开发平台)。
- 支持验证码登录 (待扩展)。
- 返回 JWT Token，前端存储在 `localStorage` 或 `HttpOnly Cookie`。

### 1.3 密码管理
- 忘记密码：输入邮箱，发送重置链接 (`POST /api/user/email-verification/request`)。
- 重置密码：通过邮件 Token 设置新密码。

## 2. API 参考

- `POST /api/user/register`: 注册新用户
- `POST /api/user/login`: 账户登录
- `GET /api/user/me`: 获取当前用户信息
- `PUT /api/user/me/password`: 修改密码
- `GET /api/user/me/quotas`: 获取用户配额
- `POST /api/user/email-verification/request`: 请求验证邮件
- `GET /api/user/email-verification/verify`: 验证邮箱 Token
- `POST /api/user/sms/send`: 发送短信验证码
- `POST /api/user/sms/verify`: 校验验证码并绑定手机号

## 3. 前端实现

### 3.1 核心组件 (`frontend/src/features/auth/pages/`)
- `LoginPage`: 登录表单
- `RegisterPage`: 注册表单
- `ForgotPasswordPage`: 忘记密码
- `ResetPasswordPage`: 重置密码
- `VerifyEmailPage`: 邮箱激活

### 3.2 状态管理
- 使用 `AuthContext` 管理全局登录状态 (`user`, `isAuthenticated`, `isLoading`)。
- 封装 `useAuth` Hook 供业务组件调用。

## 4. 安全约束
- 密码强度校验：最小长度、大小写字母、数字符号组合。
- 登录防爆破：连续失败 5 次锁定 30 分钟。
- Token 安全：支持 Token 刷新机制，过期时间可配置。

## 5. 常见问题
- **验证邮件未收到**：检查后台邮件队列及 IP 评分，建议配置生产级 SMTP 服务。
- **Token 过期频繁**：调整 `AUTHENTICATION_TOKEN_EXPIRE` 配置。
