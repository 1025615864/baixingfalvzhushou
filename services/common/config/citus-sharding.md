# Citus 分库分表策略

## 1. 分布式表策略

### 1.1 用户域 (user-service)

| 表名 | 分片键 | 分片方式 | 说明 |
|-----|-------|---------|------|
| users | id | hash | 用户主表 |
| user_profiles | user_id | hash | 用户画像 |
| login_audits | user_id | hash | 登录日志 |

```sql
-- 启用分布式表
SELECT create_distributed_table('users', 'id', 'hash');
SELECT create_distributed_table('user_profiles', 'user_id', 'hash');
SELECT create_distributed_table('login_audits', 'user_id', 'hash');

-- 必需索引
CREATE INDEX idx_users_phone ON users(phone) WHERE deleted_at IS NULL;
CREATE INDEX idx_users_email ON users(email) WHERE deleted_at IS NULL;
CREATE INDEX idx_users_created ON users(created_at DESC);
CREATE INDEX idx_login_audits_created ON login_audits(created_at DESC);
```

### 1.2 支付域 (payment-channel-service)

| 表名 | 分片键 | 分片方式 | 说明 |
|-----|-------|---------|------|
| payment_orders | id | hash | 支付订单 |
| payment_callbacks | order_no | hash | 回调记录 |

```sql
SELECT create_distributed_table('payment_orders', 'id', 'hash');
SELECT create_distributed_table('payment_callbacks', 'order_no', 'hash');

CREATE INDEX idx_orders_user_status ON payment_orders(user_id, status);
CREATE INDEX idx_orders_created ON payment_orders(created_at DESC);
CREATE INDEX idx_callbacks_trade_no ON payment_callbacks(callback_no) WHERE callback_no IS NOT NULL;
```

### 1.3 账务域 (payment-accounting-service)

| 表名 | 分片键 | 分片方式 | 说明 |
|-----|-------|---------|------|
| user_balances | user_id | hash | 用户余额 |
| balance_transactions | user_id | hash | 余额变动 |
| lawyer_wallets | lawyer_id | hash | 律师钱包 |
| settlements | lawyer_id | hash | 结算记录 |

```sql
SELECT create_distributed_table('user_balances', 'user_id', 'hash');
SELECT create_distributed_table('balance_transactions', 'user_id', 'hash');
SELECT create_distributed_table('lawyer_wallets', 'lawyer_id', 'hash');
SELECT create_distributed_table('settlements', 'lawyer_id', 'hash');
```

### 1.4 积分域 (points-service)

| 表名 | 分片键 | 分片方式 | 说明 |
|-----|-------|---------|------|
| points_users | user_id | hash | 积分用户 |
| points_history | user_id | hash | 积分变动 |
| points_exchange_orders | user_id | hash | 兑换订单 |

```sql
SELECT create_distributed_table('points_users', 'user_id', 'hash');
SELECT create_distributed_table('points_history', 'user_id', 'hash');
SELECT create_distributed_table('points_exchange_orders', 'user_id', 'hash');
```

## 2. Citus 集群配置

### Coordinator 节点

```ini
# postgresql.conf
shared_preload_libraries = 'citus'
citus.shard_replication_factor = 1
citus.max_shard_connections = 100
citus.multi_task_query_cache_size = 256MB
citus.task_assignment_policy = 'greedy'

# 连接配置
max_connections = 500
superuser_reserved_connections = 5

# 内存配置
shared_buffers = 8GB
effective_cache_size = 24GB
work_mem = 64MB
```

### Worker 节点

```ini
# postgresql.conf
shared_preload_libraries = 'citus'
citus.shard_replication_factor = 1

# 连接配置
max_connections = 400
superuser_reserved_connections = 5

# 内存配置
shared_buffers = 16GB
effective_cache_size = 48GB
work_mem = 128MB
maintenance_work_mem = 2GB
```

## 3. 分片健康检查

```sql
-- 查看分片分布
SELECT * FROM citus_shards;

-- 查看分片位置
SELECT * FROM citus_shard_locations;

-- 检查复制状态
SELECT * FROM citus_shard_replicas;

-- 重新平衡
SELECT rebalance_table_shards('users');

-- 添加新节点后重新分布
SELECT citus_set_node_property('node_name', node_port, 'shouldhaveshards', true);
```

## 4. 容量规划

| 场景 | 分片数 | 每分片预估行数 | 总行数 |
|-----|-------|---------------|-------|
| 用户表 | 8 | 125,000 | 1,000,000 |
| 支付订单 | 16 | 62,500 | 1,000,000 |
| 余额变动 | 32 | 3,125,000 | 100,000,000 |
| 积分变动 | 32 | 3,125,000 | 100,000,000 |
