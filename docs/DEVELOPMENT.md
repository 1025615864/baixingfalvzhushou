# 百姓助手开发规范

本文档定义了百姓助手项目的开发规范，旨在确保团队协作的一致性和代码质量。

---

## 1. 开发环境配置

### 1.1 后端环境要求

| 组件 | 版本要求 | 说明 |
|------|----------|------|
| Python | 3.11+ | 推荐使用 3.11 或 3.12 |
| Redis | 7.0+ | 用于缓存和会话存储 |
| PostgreSQL | 14+ | 主数据库 |
| Docker | 24.0+ | 容器化部署 |

#### 后端依赖安装

```bash
# 进入后端目录
cd backend

# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
# Windows
venv\Scripts\activate
# Linux/macOS
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 安装开发依赖
pip install -r requirements-dev.txt
```

#### 环境变量配置

后端配置文件位于 [`backend/.env.example`](backend/.env.example)，复制并配置以下变量：

```bash
# 数据库配置
DATABASE_URL=postgresql://user:password@localhost:5432/baixing
REDIS_URL=redis://localhost:6379/0

# 应用配置
APP_ENV=development
APP_DEBUG=true
APP_SECRET_KEY=your-secret-key-here

# JWT 配置
JWT_SECRET_KEY=your-jwt-secret-key
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7

# 第三方服务（根据需要配置）
OPENAI_API_KEY=sk-xxx
WECHAT_APP_ID=xxx
WECHAT_APP_SECRET=xxx
ALIPAY_APP_ID=xxx
```

### 1.2 前端环境要求

| 组件 | 版本要求 | 说明 |
|------|----------|------|
| Node.js | 18+ | 推荐使用 18 LTS 或 20 LTS |
| npm | 9.0+ | 包管理器 |

#### 前端依赖安装

```bash
# 进入前端目录
cd frontend-v2

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

### 1.3 开发工具推荐

- **IDE**: VS Code 或 PyCharm
- **API 测试**: Postman / Bruno
- **数据库客户端**: DBeaver / DataGrip
- **Redis 客户端**: Redis Desktop Manager

---

## 2. 代码规范

### 2.1 后端 (Python)

#### 2.1.1 编码风格

- 遵循 [PEP 8](https://peps.python.org/pep-0008/)
- 最大行长度：88 字符（Black 默认值）
- 使用 4 空格缩进

#### 2.1.2 代码格式化

项目使用以下工具进行代码格式化：

| 工具 | 用途 | 配置文件 |
|------|------|----------|
| Black | 代码格式化 | [`pyproject.toml`](backend/pyproject.toml) |
| isort | 导入排序 | [`pyproject.toml`](backend/pyproject.toml) |
| pyupgrade | 自动升级语法 | [`pyproject.toml`](backend/pyproject.toml) |

#### 格式化命令

```bash
# 格式化所有 Python 文件
black .
isort .
pyupgrade --py311-plus .

# 或使用 Makefile
make format
```

#### 2.1.3 类型提示

所有函数必须包含类型提示：

```python
# ✅ 正确示例
def get_user_by_id(user_id: int) -> User | None:
    """根据 ID 获取用户"""
    pass

def calculate_total(items: list[OrderItem], tax_rate: float = 0.1) -> Decimal:
    """计算订单总金额"""
    pass

# ❌ 错误示例
def get_user_by_id(user_id):
    pass
```

#### 2.1.4 Pydantic 模型定义规范

所有 API 请求/响应模型必须使用 Pydantic v2：

```python
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime


class UserCreate(BaseModel):
    """用户创建请求模型"""
    username: str = Field(..., min_length=3, max_length=50)
    email: str = Field(..., pattern=r'^[\w\.-]+@[\w\.-]+\.\w+$')
    password: str = Field(..., min_length=8)
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "username": "john_doe",
                "email": "john@example.com",
                "password": "secure_password123"
            }
        }
    )


class UserResponse(BaseModel):
    """用户响应模型"""
    id: int
    username: str
    email: str
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)
```

#### 2.1.5 导入排序规则

导入顺序必须遵循 isort 的 `requirements-style` 配置：

1. 标准库
2. 第三方库
3. 本地应用（相对于项目根目录）

```python
# 标准库
import json
from datetime import datetime
from typing import Optional

# 第三方库
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

# 本地应用
from app.models.user import User
from app.schemas.user import UserCreate, UserResponse
from app.services.user_service import UserService
```

### 2.2 前端 (TypeScript/React)

#### 2.2.1 ESLint + Prettier 配置

项目使用 ESLint 和 Prettier 进行代码检查和格式化：

| 工具 | 用途 | 配置文件 |
|------|------|----------|
| ESLint | 代码检查 | `.eslintrc.js` |
| Prettier | 代码格式化 | `.prettierrc` |

#### 2.2.2 组件命名规范

- **组件文件**: 使用 PascalCase，如 `UserProfile.tsx`
- **组件名称**: 使用 PascalCase，如 `UserProfile`
- **Hook 函数**: 使用 camelCase，以 `use` 开头，如 `useUserProfile`
- **工具函数**: 使用 camelCase，如 `formatDate`

```typescript
// ✅ 正确示例
// 文件名: UserProfile.tsx
import { UserProfile } from './components/UserProfile';

// 文件名: useUserProfile.ts
export function useUserProfile(userId: string) {
  // ...
}

// 文件名: formatDate.ts
export function formatDate(date: Date): string {
  // ...
}

// ❌ 错误示例
import user_profile from './user_profile';
function getUserData() { }
```

#### 2.2.3 目录结构规范（Features 模块化）

前端采用 Features 模块化架构：

```
frontend-v2/src/
├── features/                 # 功能模块（核心目录结构）
│   ├── home/                # 首页功能
│   │   ├── api/             # API 接口
│   │   ├── components/      # 页面组件
│   │   ├── hooks/           # 自定义 Hooks
│   │   ├── pages/           # 页面组件
│   │   ├── types/           # 类型定义
│   │   └── index.ts         # 导出入口
│   ├── chat/                # 咨询功能
│   ├── forum/               # 论坛功能
│   ├── lawyer/              # 律师功能
│   ├── contracts/           # 合同功能
│   ├── points/              # 积分功能
│   └── admin_monitor/       # 管理监控功能
├── components/              # 共享组件
├── hooks/                   # 共享 Hooks
├── services/                # 全局服务
├── utils/                   # 工具函数
├── stores/                  # 状态管理
└── types/                   # 全局类型定义
```

#### 2.2.4 状态管理规范

项目使用 **Zustand** 进行全局状态管理，使用 **React Query** 进行服务端状态管理：

```typescript
// Zustand Store 示例
import { create } from 'zustand';
import { persist } from 'zustand/middleware';

interface UserStore {
  user: User | null;
  setUser: (user: User | null) => void;
  logout: () => void;
}

export const useUserStore = create<UserStore>()(
  persist(
    (set) => ({
      user: null,
      setUser: (user) => set({ user }),
      logout: () => set({ user: null }),
    }),
    {
      name: 'user-storage',
    }
  )
);

// React Query 使用示例
import { useQuery, useMutation } from '@tanstack/react-query';
import { userApi } from '../features/home/api';

function useUserProfile(userId: string) {
  return useQuery({
    queryKey: ['user', userId],
    queryFn: () => userApi.getProfile(userId),
    staleTime: 5 * 60 * 1000, // 5 分钟
  });
}
```

#### 2.2.5 API 调用规范

每个 Feature 模块的 API 应该统一导出：

```typescript
// features/home/api/index.ts
import axios from 'axios';
import type { HomeData, Feature } from '../types';

export const homeApi = {
  getHomeData: () => axios.get<HomeData>('/api/home'),
  getFeatures: () => axios.get<Feature[]>('/api/features'),
};
```

---

## 3. Git 工作流

### 3.1 分支策略

采用 Git Flow 分支模型：

| 分支 | 用途 | 命名规范 |
|------|------|----------|
| `main` | 生产环境代码 | - |
| `develop` | 开发主分支 | - |
| `feature/*` | 新功能开发 | `feature/功能描述` |
| `fix/*` | Bug 修复 | `fix/问题描述` |
| `hotfix/*` | 紧急修复 | `hotfix/问题描述` |
| `release/*` | 发布准备 | `release/版本号` |

#### 分支命名示例

```bash
# 创建新功能分支
git checkout -b feature/user-profile-edit

# 创建 Bug 修复分支
git checkout -b fix/login-validation-error

# 创建热修复分支
git checkout -b hotfix/payment-timeout
```

### 3.2 提交信息规范

使用 [Conventional Commits](https://www.conventionalcommits.org/) 格式：

```
<type>(<scope>): <subject>

[optional body]

[optional footer]
```

#### Type 类型说明

| Type | 说明 | 示例 |
|------|------|------|
| `feat` | 新功能 | `feat(user): 添加用户头像上传功能` |
| `fix` | Bug 修复 | `fix(auth): 修复登录超时问题` |
| `docs` | 文档更新 | `docs: 更新 API 文档` |
| `style` | 代码格式 | `style: 格式化代码` |
| `refactor` | 代码重构 | `refactor(payment): 重构支付流程` |
| `perf` | 性能优化 | `perf(query): 优化数据库查询` |
| `test` | 测试相关 | `test: 添加用户测试用例` |
| `chore` | 构建/工具 | `chore: 更新依赖版本` |

#### 提交示例

```bash
# 正确示例
git commit -m "feat(user): 添加用户头像上传功能"
git commit -m "fix(auth): 修复登录超时导致的 token 失效问题"
git commit -m "docs: 更新 API 接口文档"

# 错误示例
git commit -m "fix bug"
git commit -m "update"
git commit -m "WIP"
```

### 3.3 PR 流程

1. **创建分支**: 从 `develop` 创建功能分支
2. **开发功能**: 在分支上进行开发
3. **提交代码**: 遵循 Conventional Commits 规范
4. **推送分支**: `git push -u origin feature/xxx`
5. **创建 PR**: 指向 `develop` 分支
6. **代码审查**: 至少一名开发者审查通过
7. **合并代码**: 审查通过后合并到 `develop`

#### PR 描述模板

```markdown
## 描述
[简要描述这个 PR 解决的问题]

## 变更内容
- [ ] 功能1
- [ ] 功能2

## 测试
- [ ] 单元测试通过
- [ ] 手动测试通过

## 截图（如果涉及 UI）
[添加截图]
```

### 3.4 代码审查要求

- 所有 PR 必须通过 CI/CD 检查
- 至少一名开发者审批
- 必须解决所有评论
- 涉及支付、安全相关代码需要额外审批

---

## 4. API 设计规范

### 4.1 RESTful 风格

| HTTP 方法 | 用途 | 示例 |
|-----------|------|------|
| `GET` | 获取资源 | `GET /api/v1/users` |
| `POST` | 创建资源 | `POST /api/v1/users` |
| `PUT` | 完整更新 | `PUT /api/v1/users/1` |
| `PATCH` | 部分更新 | `PATCH /api/v1/users/1` |
| `DELETE` | 删除资源 | `DELETE /api/v1/users/1` |

#### URL 设计原则

- 使用名词而非动词：`/users` 而非 `/getUsers`
- 使用复数形式：`/users` 而非 `/user`
- 使用小写字母：`/api/v1/users`
- 使用连字符分隔单词：`/user-profile`（避免）
- 层级关系使用路径：`/users/1/posts`

### 4.2 响应格式统一

所有 API 响应必须使用统一的响应格式：

#### 成功响应

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "id": 1,
    "username": "john_doe",
    "email": "john@example.com"
  },
  "timestamp": "2024-01-15T10:30:00Z"
}
```

#### 分页响应

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "items": [...],
    "total": 100,
    "page": 1,
    "page_size": 20,
    "total_pages": 5
  },
  "timestamp": "2024-01-15T10:30:00Z"
}
```

#### 错误响应

```json
{
  "code": 1001,
  "message": "用户名或密码错误",
  "details": null,
  "timestamp": "2024-01-15T10:30:00Z"
}
```

### 4.3 错误码定义

错误码定义在 [`app/core/error_codes.py`](app/core/error_codes.py)：

| 错误码范围 | 说明 |
|------------|------|
| 1000-1999 | 通用错误 |
| 2000-2999 | 认证/授权错误 |
| 3000-3999 | 用户相关错误 |
| 4000-4999 | 业务逻辑错误 |
| 5000-5999 | 第三方服务错误 |
| 9000-9999 | 系统错误 |

### 4.4 版本控制策略

- URL 路径版本：`/api/v1/users`
- 版本号格式：`v{major}.{minor}`
- 主版本号变更：不兼容的 API 变更
- 次版本号变更：向后兼容的新功能

---

## 5. 测试规范

### 5.1 单元测试要求

#### 后端测试

使用 **pytest** 和 **pytest-asyncio** 进行单元测试：

```python
# tests/test_user_service.py
import pytest
from app.services.user_service import UserService


class TestUserService:
    """用户服务测试"""
    
    @pytest.fixture
    def user_service(self):
        return UserService()
    
    @pytest.mark.asyncio
    async def test_create_user(self, user_service):
        """测试创建用户"""
        # Arrange
        user_data = UserCreate(
            username="test_user",
            email="test@example.com",
            password="password123"
        )
        
        # Act
        result = await user_service.create_user(user_data)
        
        # Assert
        assert result.username == "test_user"
        assert result.email == "test@example.com"
```

#### 运行测试

```bash
# 运行所有测试
pytest

# 运行指定文件
pytest tests/test_user_service.py

# 运行并生成覆盖率报告
pytest --cov=app --cov-report=html

# 使用 Makefile
make test
```

#### 测试覆盖率要求

| 类型 | 覆盖率要求 |
|------|------------|
| 核心业务逻辑 | ≥ 80% |
| 新功能 | ≥ 70% |
| 整体 | ≥ 60% |

### 5.2 E2E 测试要求

使用 **Playwright** 进行端到端测试：

```typescript
// tests/e2e/specs/user.spec.ts
import { test, expect } from '@playwright/test';

test.describe('用户功能', () => {
  test('用户登录', async ({ page }) => {
    await page.goto('/login');
    await page.fill('[data-testid="username"]', 'testuser');
    await page.fill('[data-testid="password"]', 'password123');
    await page.click('[data-testid="login-button"]');
    
    await expect(page).toHaveURL('/dashboard');
  });
});
```

#### 运行 E2E 测试

```bash
# 进入 E2E 测试目录
cd tests/e2e

# 安装依赖
npm install

# 运行测试
npx playwright test

# 生成测试报告
npx playwright show-report
```

### 5.3 Mock 数据规范

使用项目提供的 Mock 工具：

```python
# 使用 mock_utils
from tests.helpers.mock_utils import MockUser, MockOrder

@pytest.fixture
def mock_user():
    return MockUser(
        id=1,
        username="test_user",
        email="test@example.com"
    )
```

---

## 6. 数据库规范

### 6.1 Alembic 迁移规范

#### 创建迁移

```bash
# 创建新迁移
alembic revision --autogenerate -m "add_user_avatar_column"

# 运行迁移
alembic upgrade head

# 回滚迁移
alembic downgrade -1
```

#### 迁移文件命名规范

使用有意义的描述性名称：

```
✅ 正确示例
add_user_avatar_column.py
create_user_follows_table.py
add_index_to_user_email.py

❌ 错误示例
migration1.py
update.py
fix.py
```

#### 迁移编写规范

```python
"""add_user_avatar_column

Revision ID: abc123
Revises: prev123
Create Date: 2024-01-15 10:00:00

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers
revision = 'abc123'
down_revision = 'prev123'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """添加用户头像列"""
    op.add_column(
        'users',
        sa.Column('avatar_url', sa.String(255), nullable=True)
    )
    
    # 创建索引
    op.create_index(
        'ix_users_avatar_url',
        'users',
        ['avatar_url'],
        unique=False
    )


def downgrade() -> None:
    """回滚：删除用户头像列"""
    op.drop_index('ix_users_avatar_url', 'users')
    op.drop_column('users', 'avatar_url')
```

### 6.2 模型定义规范

使用 SQLAlchemy 进行模型定义：

```python
# app/models/user.py
from sqlalchemy import Column, Integer, String, DateTime, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database.base import Base


class User(Base):
    """用户模型"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # 关系
    profile = relationship("UserProfile", back_populates="user", uselist=False)
    posts = relationship("Post", back_populates="author")
    
    def __repr__(self):
        return f"<User(id={self.id}, username={self.username})>"
```

### 6.3 索引和查询优化

#### 创建索引

```python
# 单一列索引（通常在 Column 定义中）
email = Column(String(255), unique=True, index=True)

# 多列索引
__table_args__ = (
    Index('ix_user_email_active', 'email', 'is_active'),
)
```

#### 查询优化建议

1. **避免 SELECT ***：明确指定需要的列
2. **使用 Pagination**：大结果集必须分页
3. **使用 eager loading**：避免 N+1 查询
4. **添加合适的索引**：高频查询字段应建立索引

```python
# ✅ 正确示例
users = await session.execute(
    select(User.id, User.username, User.email)
    .where(User.is_active == True)
    .limit(20)
)

# ❌ 错误示例
users = await session.execute(select(User))  # 获取所有用户
```

---

## 7. 安全规范

### 7.1 敏感信息处理

#### 禁止提交敏感信息

- 绝对不要提交 `.env` 文件到版本控制
- 使用 `.env.example` 作为环境变量模板
- 敏感信息使用密钥管理服务

#### 密码处理

```python
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证密码"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """获取密码哈希"""
    return pwd_context.hash(password)
```

### 7.2 支付安全

#### 支付幂等性

所有支付接口必须实现幂等性：

```python
# 使用幂等键
class PaymentService:
    async def create_payment(
        self,
        order_id: int,
        amount: Decimal,
        idempotency_key: str
    ) -> Payment:
        # 检查幂等键是否已存在
        existing = await self.get_payment_by_idempotency_key(idempotency_key)
        if existing:
            return existing
        
        # 创建新支付
        payment = await self._create_payment(order_id, amount)
        await self._store_idempotency_key(idempotency_key, payment.id)
        return payment
```

#### 支付签名验证

```python
from app.utils.signature import verify_payment_signature


async def handle_payment_callback(callback_data: dict):
    """处理支付回调"""
    signature = callback_data.pop('signature')
    
    if not verify_payment_signature(callback_data, signature):
        raise HTTPException(status_code=400, detail="签名验证失败")
    
    # 处理业务逻辑
    await process_payment(callback_data)
```

### 7.3 用户数据保护

#### PII 数据处理

```python
from app.utils.pii import mask_pii_data, PII_TYPES


def sanitize_user_data(user: User) -> dict:
    """脱敏用户数据"""
    return {
        'id': user.id,
        'username': user.username,
        'email': mask_pii_data(user.email, PII_TYPES.EMAIL),
        'phone': mask_pii_data(user.phone, PII_TYPES.PHONE),
        'id_card': mask_pii_data(user.id_card, PII_TYPES.ID_CARD),
    }
```

### 7.4 API 鉴权

#### JWT 认证

```python
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.services.token_service import TokenService

security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    token_service: TokenService = Depends(get_token_service)
) -> User:
    """获取当前用户"""
    token = credentials.credentials
    
    try:
        payload = await token_service.verify_access_token(token)
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="无效的认证凭证"
            )
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的认证凭证"
        )
    
    user = await user_service.get_user_by_id(int(user_id))
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户不存在"
        )
    
    return user
```

---

## 8. 文档规范

### 8.1 代码注释要求

#### 公共 API 必须添加文档字符串

```python
def calculate_tax(amount: Decimal, tax_rate: float = 0.1) -> Decimal:
    """计算税费
    
    Args:
        amount: 金额
        tax_rate: 税率，默认为 10%
    
    Returns:
        税费金额
    
    Raises:
        ValueError: 当金额为负数时
    
    Example:
        >>> calculate_tax(Decimal('100'), 0.1)
        Decimal('10')
    """
    if amount < 0:
        raise ValueError("金额不能为负数")
    return amount * Decimal(str(tax_rate))
```

#### 复杂逻辑添加行内注释

```python
# 使用金融精度计算，避免浮点数精度问题
total = Decimal(str(amount)) * Decimal(str(tax_rate))
```

### 8.2 API 文档更新

- 所有 API 端点必须包含 OpenAPI 文档
- 使用 Pydantic 的 `Field` 描述字段
- 提供请求/响应示例

```python
from fastapi import APIRouter
from app.schemas.user import UserCreate, UserResponse

router = APIRouter()


@router.post(
    "/users",
    response_model=UserResponse,
    summary="创建用户",
    description="创建一个新的用户账号"
)
async def create_user(user: UserCreate):
    """创建用户"""
    return await user_service.create_user(user)
```

### 8.3 README 维护

每个主要目录应包含 README.md：

- **backend/README.md**: 后端项目说明
- **frontend-v2/README.md**: 前端项目说明
- **tests/README.md**: 测试说明

#### README 内容模板

```markdown
# 项目名称

## 简介
简要描述项目

## 快速开始

### 前置要求
- Python 3.11+
- Node.js 18+

### 安装
```bash
# 安装命令
```

### 运行
```bash
# 运行命令
```

## 相关文档
- [API 文档](./docs/API.md)
- [部署文档](./docs/DEPLOYMENT.md)
```

---

## 附录

### 常用命令

#### 后端

```bash
# 格式化代码
make format

# 运行测试
make test

# 运行开发服务器
make dev

# 运行 linting
make lint
```

#### 前端

```bash
# 安装依赖
npm install

# 开发模式
npm run dev

# 构建生产版本
npm run build

# 运行 lint
npm run lint
```

### 相关配置文件

- [`backend/pyproject.toml`](backend/pyproject.toml) - Python 项目配置
- [`backend/Makefile`](backend/Makefile) - 后端任务脚本
- [`.pre-commit-config.yaml`](.pre-commit-config.yaml) - Git 钩子配置
- [`backend/pytest.ini`](backend/pytest.ini) - 测试配置

### 参考资源

- [PEP 8 Style Guide](https://peps.python.org/pep-0008/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [React TypeScript Guide](https://react.dev/learn/typescript)
- [Conventional Commits](https://www.conventionalcommits.org/)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)