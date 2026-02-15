# 后端开发文档

## 项目结构

```
backend/
├── app/                    # 应用核心代码
│   ├── config/            # 配置模块
│   │   ├── __init__.py    # 配置导出
│   │   └── settings.py    # 应用设置
│   ├── core/              # 核心模块
│   │   ├── lifespan.py    # 应用生命周期管理
│   │   ├── middleware_config.py  # 中间件配置
│   │   ├── monitoring/    # 监控模块
│   │   │   ├── db_pool.py       # 连接池监控
│   │   │   └── query_monitor.py # SQL查询监控
│   │   └── middleware/    # 中间件
│   │       ├── slow_query.py     # 慢查询中间件
│   │       ├── rate_limit.py     # 限流中间件
│   │       └── auth_context.py   # 认证上下文
│   ├── routers/           # API 路由模块
│   │   ├── ai/           # AI 对话相关
│   │   ├── user/         # 用户相关
│   │   ├── forum/        # 论坛相关
│   │   ├── news/         # 新闻相关
│   │   ├── payment/      # 支付相关
│   │   ├── lawfirm/      # 律所相关
│   │   └── admin_monitor.py  # 监控管理API
│   ├── services/         # 业务逻辑层
│   │   ├── ai/           # AI 服务
│   │   ├── payment/      # 支付服务
│   │   ├── points/       # 积分服务
│   │   └── slow_query_analyzer.py  # 慢查询分析
│   ├── models/           # 数据模型
│   │   ├── consultation.py  # 咨询模型（SQLAlchemy 2.0）
│   │   ├── user.py       # 用户模型
│   │   └── payment.py    # 支付模型
│   └── utils/            # 工具函数
├── tests/                 # 测试文件
│   ├── e2e/              # E2E测试
│   │   ├── specs/        # 测试用例
│   │   │   ├── payment.spec.ts      # 支付流程
│   │   │   ├── consultation.spec.ts # 咨询流程
│   │   │   └── api-health.spec.ts   # API健康
│   │   └── helpers/      # 测试辅助
│   └── *.py              # 单元测试
├── alembic/              # 数据库迁移
└── docs/                 # 本文档目录
```

## 快速开始

### 环境配置

```bash
# 创建虚拟环境
py -m venv .venv
.venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt
pip install -r requirements-dev.txt

# 配置环境变量
copy .env.example .env
# 编辑 .env 文件配置数据库、Redis、支付等
```

### 数据库

```bash
# 生成迁移脚本
py -m alembic revision --autogenerate -m "描述"

# 执行迁移
py -m alembic upgrade head

# 回滚迁移
py -m alembic downgrade -1
```

### 运行服务

```bash
# 开发模式
py -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 生产模式
py -m gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker
```

## 核心功能

### 1. SQL查询性能监控

系统已集成自动SQL查询监控，通过 SQLAlchemy 事件监听实现：

```python
# 监控自动在应用启动时启用（lifespan.py）
from app.core.monitoring.query_monitor import get_query_stats

# 获取查询统计
stats = get_query_stats()
# {
#     "total_queries": 1000,
#     "slow_queries": 10,
#     "avg_time_ms": 5.2,
#     "slow_ratio": 0.01
# }
```

### 2. 管理API端点（需管理员权限）

| 端点 | 方法 | 描述 |
|------|------|------|
| `/admin/monitor/query-stats` | GET | 获取查询统计和优化建议 |
| `/admin/monitor/query-stats/reset` | POST | 重置查询统计 |
| `/admin/monitor/slow-queries` | GET | 获取慢查询列表 |
| `/admin/monitor/optimization-suggestions` | GET | 获取优化建议 |

### 3. 配置管理

配置已从单文件重构为模块化结构：

```python
# 使用方式（向后兼容）
from app.config import get_settings

settings = get_settings()
database_url = settings.database_url
```

支持的配置类别：
- **基础配置**：应用名称、调试模式、数据库URL
- **安全配置**：JWT（RS256/HS256）、密钥管理
- **支付配置**：支付宝、微信支付、IkunPay
- **AI配置**：OpenAI、语音转录、模型选择
- **监控配置**：Sentry、Prometheus、日志脱敏

## API 开发

### 创建新路由

```python
# app/routers/example/__init__.py
from fastapi import APIRouter

router = APIRouter()

@router.get("/items")
async def list_items():
    return {"items": []}
```

```python
# app/main.py
from app.routers import example

app.include_router(example.router, prefix="/api")
```

### 数据库模型（SQLAlchemy 2.0风格）

```python
from sqlalchemy import Integer, String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

class Consultation(Base):
    __tablename__ = "consultations"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=True, index=True
    )
    title: Mapped[str] = mapped_column(String(200))
    
    # 关系定义
    messages: Mapped[list["ChatMessage"]] = relationship(
        "ChatMessage", back_populates="consultation", lazy="selectin"
    )
```

### 添加复合索引

```python
# 在模型定义中添加
from sqlalchemy import Index

class PaymentOrder(Base):
    __tablename__ = "payment_orders"
    
    # 字段定义...
    
    # 复合索引示例
    __table_args__ = (
        Index('ix_payment_orders_user_status', 'user_id', 'status'),
        Index('ix_payment_orders_created', 'created_at'),
    )
```

## 测试

### 单元测试

```bash
# 运行所有测试
py -m pytest tests/ -v

# 运行指定测试
py -m pytest tests/test_user.py -v

# 生成覆盖率报告
py -m pytest --cov=app --cov-report=term-missing

# 带安全扫描的测试
py -m pytest --bandit
```

### E2E测试

```bash
# 安装E2E依赖
cd tests/e2e
npm install

# 运行E2E测试
npx playwright test

# 运行特定浏览器
npx playwright test --project=chromium

# 调试模式
npx playwright test --headed
```

E2E测试覆盖：
- **支付流程**：订单创建、支付回调、历史查询
- **法律咨询**：咨询提交、律师选择、实时聊天
- **合同审核**：文件上传、审核报告
- **API健康**：端点可用性、错误处理

## 性能优化

### 慢查询监控配置

```python
# 调整慢查询阈值（毫秒）
from app.core.monitoring.query_monitor import QueryMonitor

monitor = QueryMonitor(slow_threshold_ms=50.0)  # 默认100ms
```

### 数据库连接池监控

```python
# 连接池指标自动收集
from app.core.monitoring.db_pool import get_db_pool_stats

stats = get_db_pool_stats()
# {
#     "size": 10,
#     "checked_in": 8,
#     "checked_out": 2,
#     "overflow": 0
# }
```

## 代码规范

- 使用类型注解（Python 3.10+ 语法）
- 中文注释关键逻辑
- 遵循 PEP 8
- 函数不超过 100 行
- 复杂逻辑需要单元测试
- 数据库模型使用 SQLAlchemy 2.0 风格
- 配置使用 Pydantic Settings 管理

## 部署检查清单

- [ ] 环境变量配置完整（生产环境必须）
- [ ] Redis 服务可用
- [ ] 数据迁移已执行
- [ ] JWT 密钥已生成（RS256推荐）
- [ ] 支付配置已验证
- [ ] Sentry DSN 已配置（可选）
- [ ] 日志级别设置为 INFO 或更高
