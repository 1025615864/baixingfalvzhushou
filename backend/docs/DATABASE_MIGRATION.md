# 数据库迁移指南

## Alembic 使用

### 创建迁移

```bash
# 自动生成迁移脚本
cd backend
py -m alembic revision --autogenerate -m "描述变更"

# 手动创建迁移脚本
py -m alembic revision -m "描述变更"
```

### 执行迁移

```bash
# 升级到最新版本
py -m alembic upgrade head

# 升级指定版本
py -m alembic upgrade abc123

# 回滚一个版本
py -m alembic downgrade -1

# 回滚到指定版本
py -m alembic downgrade abc123

# 重置所有迁移（危险！）
py -m alembic downgrade base
```

### 查看迁移状态

```bash
# 查看当前版本
py -m alembic current

# 查看所有迁移历史
py -m alembic history

# 查看迁移脚本
py -m alembic show abc123
```

## 迁移脚本结构

```python
# alembic/versions/xxx_create_users.py
"""create users table

Revision ID: abc123
Revises: 
Create Date: 2026-01-31 10:00:00
"""

from alembic import op
import sqlalchemy as sa

def upgrade():
    # 创建表
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('username', sa.String(50), nullable=False),
        sa.Column('email', sa.String(100), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )

def downgrade():
    # 删除表
    op.drop_table('users')
```

## 常见操作

### 添加列

```python
def upgrade():
    op.add_column('users', sa.Column('phone', sa.String(20), nullable=True))

def downgrade():
    op.drop_column('users', 'phone')
```

### 重命名列

```python
def upgrade():
    op.alter_column('users', 'old_name', new_column_name='new_name')

def downgrade():
    op.alter_column('users', 'new_name', new_column_name='old_name')
```

### 创建索引

```python
def upgrade():
    op.create_index('idx_user_phone', 'users', ['phone'])

def downgrade():
    op.drop_index('idx_user_phone')
```

## 数据迁移

```python
def upgrade():
    # 更新现有数据
    op.execute("UPDATE users SET role = 'user' WHERE role IS NULL")

def downgrade():
    # 回滚数据
    op.execute("UPDATE users SET role = NULL WHERE role = 'user'")
```
