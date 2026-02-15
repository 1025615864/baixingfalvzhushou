# 认证与授权指南

## JWT 认证

### Token 结构

```python
# payload 结构
{
    "sub": "user_id",
    "username": "用户名",
    "role": "user/vip/admin",
    "exp": 1234567890,  # 过期时间
    "iat": 1234567890   # 签发时间
}
```

### 生成 Token

```python
from datetime import datetime, timedelta
from jose import jwt

def create_access_token(user: User, expires_delta: timedelta = None):
    expire = datetime.utcnow() + (expires_delta or timedelta(hours=24))
    payload = {
        "sub": str(user.id),
        "username": user.username,
        "role": user.role,
        "exp": expire,
        "iat": datetime.utcnow(),
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
```

### 验证 Token

```python
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

security = HTTPBearer()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> User:
    try:
        payload = jwt.decode(
            credentials.credentials,
            SECRET_KEY,
            algorithms=[ALGORITHM]
        )
        user_id = payload.get("sub")
        user = await user_service.get_by_id(int(user_id))
        return user
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的认证凭据",
        )
```

## 权限控制

### 角色装饰器

```python
from functools import wraps
from fastapi import HTTPException, status

def require_role(roles: list[str]):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            current_user = kwargs.get('current_user')
            if current_user.role not in roles:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="权限不足"
                )
            return await func(*args, **kwargs)
        return wrapper
    return decorator

@router.get("/admin")
@require_role(["admin"])
async def admin_only(current_user: User = Depends(get_current_user)):
    return {"message": "仅管理员可访问"}
```

### 资源权限

```python
async def check_post_owner(user: User, post_id: int) -> bool:
    post = await post_service.get(post_id)
    return post.user_id == user.id

@router.delete("/posts/{post_id}")
async def delete_post(
    post_id: int,
    current_user: User = Depends(get_current_user)
):
    if not await check_post_owner(current_user, post_id):
        raise HTTPException(status_code=403, detail="无权删除此帖子")
    await post_service.delete(post_id)
    return {"message": "删除成功"}
```

## 前端认证

### Token 存储

```typescript
// 使用 localStorage（注意 XSS 风险）
const token = localStorage.getItem('token');

// 或使用 HttpOnly Cookie（更安全）
// 需要后端设置 Set-Cookie
```

### 请求拦截

```typescript
// src/api/client.ts
client.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});
```

### 认证状态

```typescript
// src/stores/auth.ts
import { create } from 'zustand';

interface AuthState {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  login: (user: User, token: string) => void;
  logout: () => void;
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  token: null,
  isAuthenticated: false,
  login: (user, token) => {
    localStorage.setItem('token', token);
    set({ user, token, isAuthenticated: true });
  },
  logout: () => {
    localStorage.removeItem('token');
    set({ user: null, token: null, isAuthenticated: false });
  },
}));
```
