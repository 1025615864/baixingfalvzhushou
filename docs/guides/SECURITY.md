# 安全实践指南

## 认证与授权

### JWT Token

```python
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

security = HTTPBearer()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> User:
    """验证 JWT Token"""
    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        user = await get_user(user_id)
        return user
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的认证凭据",
        )
```

### 权限检查

```python
from typing import List
from functools import wraps

def require_roles(roles: List[str]):
    """角色权限装饰器"""
    def decorator(func):
        @wraps(func)
        async def wrapper(current_user: User, *args, **kwargs):
            if current_user.role not in roles:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="权限不足",
                )
            return await func(current_user, *args, **kwargs)
        return wrapper
    return decorator

@router.get("/admin")
@require_roles(["admin"])
async def admin_only():
    return {"message": "仅管理员可访问"}
```

## 数据安全

### 敏感数据脱敏

```python
from app.core.security import mask_phone, mask_id_card

def user_response(user: User) -> dict:
    """返回用户信息时脱敏"""
    return {
        "id": user.id,
        "name": user.name,
        "phone": mask_phone(user.phone),  # 138****8888
        "id_card": mask_id_card(user.id_card),  # 110***********1234
    }
```

### SQL 注入防护

```python
# 使用 ORM 自动防护
from sqlalchemy import select

# ✅ 安全：使用参数化查询
await session.execute(
    select(User).where(User.username == username)
)

# ❌ 危险：禁止使用字符串拼接
# await session.execute(f"SELECT * FROM users WHERE username = '{username}'")
```

## API 安全

### 速率限制

```python
from app.middleware.rate_limit import RateLimitMiddleware

app.add_middleware(
    RateLimitMiddleware,
    requests_per_minute=60,  # 每分钟限制
    requests_per_second=10,  # 每秒限制
)
```

### CSRF 防护

```python
from app.middleware.csrf_middleware import csrf_middleware

app.middleware("http")(csrf_middleware)
```

### 输入验证

```python
from pydantic import BaseModel, Field, validator

class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=20)
    email: str = Field(..., regex=r"^[\w.-]+@[\w.-]+\.\w+$")
    password: str = Field(..., min_length=8)

    @validator("username")
    def username_not_admin(cls, v):
        if v.lower() in ["admin", "root"]:
            raise ValueError("用户名不允许")
        return v
```

## 日志安全

```python
import logging

logger = logging.getLogger(__name__)

# ❌ 禁止：记录敏感信息
# logger.info(f"User login: {password}")

# ✅ 正确：仅记录必要信息
logger.info(f"User login attempt: username={username}, ip={ip}")
```

## 依赖安全

```bash
# 检查依赖漏洞
cd backend
pip install safety
safety check -r requirements.txt

# 使用 Bandit 检查代码
py -m bandit -r app/
```

## SSRF 防护

### URL 白名单验证

```python
from urllib.parse import urlparse

def validate_redirect_uri(redirect_uri: str, allowed_hosts: list[str]) -> bool:
    """验证回调地址是否在白名单中"""
    parsed = urlparse(redirect_uri)
    
    # 禁止非 http/https 协议
    if parsed.scheme not in ("http", "https"):
        return False
    
    # 检查主机名
    host = parsed.hostname or ""
    for allowed in allowed_hosts:
        if host == allowed or host.endswith(f".{allowed}"):
            return True
    
    return False
```

## 路径遍历防护

### 文件名清理

```python
import re

def sanitize_filename(filename: str) -> str:
    """清理文件名，防止路径遍历攻击"""
    # 移除路径分隔符和危险字符
    sanitized = re.sub(r'[\\/<>"|?*\x00-\x1f]', '', filename)
    # 移除 .. 序列
    sanitized = sanitized.replace('..', '')
    # 移除首尾空格和点
    sanitized = sanitized.strip('. ')
    return sanitized


def validate_backup_path(backup_path: Path, backup_dir: Path) -> bool:
    """验证备份文件路径是否在允许的目录内"""
    try:
        backup_path = backup_path.resolve()
        backup_dir = backup_dir.resolve()
        return str(backup_path).startswith(str(backup_dir))
    except (OSError, ValueError):
        return False
```

## 并发安全

### 全局缓存锁保护

```python
import asyncio
from collections import OrderedDict

_memory_cache: OrderedDict[str, Any] = OrderedDict()
_memory_cache_lock: asyncio.Lock = asyncio.Lock()

async def cache_get(key: str):
    async with _memory_cache_lock:
        return _memory_cache.get(key)

async def cache_set(key: str, value: Any):
    async with _memory_cache_lock:
        _memory_cache[key] = value
```

## 命令注入防护

### 参数白名单验证

```python
import re

# 允许的HTTP方法白名单
ALLOWED_HTTP_METHODS = {"GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"}

# 允许的文件名字符白名单
ALLOWED_FILENAME_PATTERN = re.compile(r'^[a-zA-Z0-9_\-\.\/]+$')

def _validate_endpoint(endpoint: str) -> bool:
    """验证端点路径是否合法"""
    if not endpoint or not endpoint.startswith("/"):
        return False
    if ".." in endpoint:  # 禁止路径遍历
        return False
    pattern = r'^[\/a-zA-Z0-9_\-\.]+$'
    return bool(re.match(pattern, endpoint))

def _validate_http_method(method: str) -> bool:
    """验证HTTP方法是否合法"""
    return method.upper() in ALLOWED_HTTP_METHODS
```

### 安全的临时文件创建

```python
import tempfile
from pathlib import Path

def create_safe_temp_file(content: str, suffix: str = ".txt") -> Path:
    """创建安全的临时文件"""
    # 验证扩展名
    allowed_suffixes = {".txt", ".py", ".json"}
    if suffix not in allowed_suffixes:
        suffix = ".bin"
    
    # 使用系统临时目录
    temp_dir = tempfile.mkdtemp(prefix="app_")
    temp_file = Path(temp_dir) / f"temp{suffix}"
    
    with open(temp_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    return temp_file
```

## 安全审计清单

- [x] JWT Token 认证与 RS256 算法
- [x] CORS 跨域白名单配置
- [x] SQL 注入防护（使用 ORM）
- [x] XSS 防护（模板转义）
- [x] CSRF 令牌验证
- [x] 速率限制（基于 IP 和用户）
- [x] 敏感数据脱敏
- [x] 日志安全（禁止记录敏感信息）
- [x] SSRF 防护（URL 白名单）
- [x] 路径遍历防护（文件名清理）
- [x] 命令注入防护（参数白名单）
- [x] 并发安全（全局锁保护）
- [x] 支付回调 IP 白名单
- [x] 请求 ID 追踪
- [x] 异常信息隐藏（生产环境）
- [x] 文件扩展名白名单
