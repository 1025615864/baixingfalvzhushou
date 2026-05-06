# 分布式事务架构设计 (SAGA + 可靠消息)

## 1. 概述

本文档描述百姓助手项目分布式事务解决方案，采用 **SAGA 模式** 处理长事务，**可靠消息** 实现最终一致性。

## 2. 为什么选择 SAGA + 可靠消息

### 2.1 分布式事务模式对比

| 模式 | 适用场景 | 复杂度 | 一致性 | 性能 |
|------|----------|--------|--------|------|
| 2PC/3PC | 强一致性 | 高 | 强 | 低 |
| TCC | 短事务 | 高 | 强 | 中 |
| **SAGA** | **长事务** | **中** | **最终** | **高** |
| 可靠消息 | 异步场景 | 低 | 最终 | 高 |

### 2.2 选型理由

- **SAGA**: 适合跨多个服务的业务操作（如：下单 → 支付 → 积分 → 库存）
- **可靠消息**: 适合非关键业务的异步通知（如：支付成功 → 通知用户 → 更新统计）

## 3. 目标架构

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         分布式事务处理架构                                     │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌──────────────┐     SAGA Orchestrator      ┌──────────────┐               │
│  │   Client     │──────────────────────────────│  Payment     │               │
│  └──────────────┘     (订单服务)              │   Service   │               │
│         │                                       └──────────────┘               │
│         │ 补偿事务                                                     │
│         ▼                                                              │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │                     SAGA 事务协调                                     │  │
│  │  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐               │  │
│  │  │ Step 1  │──►│ Step 2  │──►│ Step 3  │──►│ Step N  │               │  │
│  │  │ 创建订单 │  │  扣库存  │  │  支付   │  │  积分   │               │  │
│  │  └────┬────┘  └────┬────┘  └────┬────┘  └────┬────┘               │  │
│  │       │            │            │            │                     │  │
│  │       ▼            ▼            ▼            ▼                     │  │
│  │  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐               │  │
│  │  │Compensate│  │Compensate│  │Compensate│  │Compensate│              │  │
│  │  │  取消订单 │  │  回滚库存 │  │  退款   │  │  扣积分 │               │  │
│  │  └─────────┘  └─────────┘  └─────────┘  └─────────┘               │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                                                              │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │                        可靠消息处理                                    │  │
│  │  ┌─────────┐    ┌───────────┐    ┌─────────┐    ┌─────────┐      │  │
│  │  │ Producer│───►│  Message  │───►│ Consumer│───►│  ACK    │      │  │
│  │  │         │    │  Tracker  │    │         │    │         │      │  │
│  │  └─────────┘    └───────────┘    └─────────┘    └─────────┘      │  │
│  │       │              │                               │             │  │
│  │       │              │    ┌───────────┐             │             │  │
│  │       └──────────────┴───►│  Retry    │◄────────────┘             │  │
│  │                           │  Queue    │                          │  │
│  │                           └───────────┘                          │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

## 4. SAGA 模式实现

### 4.1 SAGA 编排器 (services/common/saga/orchestrator.py)

```python
import asyncio
import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, Callable, Awaitable, List
from datetime import datetime
import uuid

logger = logging.getLogger(__name__)


class SagaStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    COMPENSATING = "compensating"
    COMPENSATED = "compensated"


class StepStatus(Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    COMPENSATED = "compensated"


@dataclass
class SagaStep:
    name: str
    forward: Callable[[], Awaitable[dict]]
    compensate: Callable[[dict], Awaitable[None]]
    retry_count: int = 3
    timeout: int = 30


@dataclass
class SagaState:
    saga_id: str
    status: SagaStatus
    steps: List[dict]
    completed_steps: List[str] = field(default_factory=list)
    current_step: Optional[str] = None
    error: Optional[str] = None
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())


class SagaOrchestrator:
    def __init__(self, saga_id: str, steps: List[SagaStep]):
        self.saga_id = saga_id
        self.steps = steps
        self.state = SagaState(
            saga_id=saga_id,
            status=SagaStatus.PENDING,
            steps=[{"name": s.name, "status": StepStatus.PENDING.value} for s in steps],
        )
        self._step_results = {}

    async def execute(self) -> SagaState:
        self.state.status = SagaStatus.RUNNING
        logger.info(f"SAGA {self.saga_id} started")

        try:
            for i, step in enumerate(self.steps):
                self.state.current_step = step.name
                logger.info(f"SAGA {self.saga_id}: Executing step {step.name}")

                try:
                    result = await self._execute_step_with_retry(step)
                    self._step_results[step.name] = result
                    self.state.completed_steps.append(step.name)
                    self._update_step_status(step.name, StepStatus.COMPLETED)

                except Exception as e:
                    logger.error(f"SAGA {self.saga_id}: Step {step.name} failed: {e}")
                    self._update_step_status(step.name, StepStatus.FAILED)
                    self.state.error = str(e)
                    await self._compensate()
                    self.state.status = SagaStatus.FAILED
                    return self.state

            self.state.status = SagaStatus.COMPLETED
            logger.info(f"SAGA {self.saga_id} completed successfully")
            return self.state

        except Exception as e:
            logger.error(f"SAGA {self.saga_id} failed: {e}")
            self.state.status = SagaStatus.FAILED
            self.state.error = str(e)
            return self.state

    async def _execute_step_with_retry(self, step: SagaStep) -> dict:
        last_error = None
        for attempt in range(step.retry_count + 1):
            try:
                result = await asyncio.wait_for(
                    step.forward(),
                    timeout=step.timeout
                )
                return result
            except asyncio.TimeoutError:
                last_error = f"Step {step.name} timed out after {step.timeout}s"
                logger.warning(f"SAGA {self.saga_id}: {last_error} (attempt {attempt + 1})")
            except Exception as e:
                last_error = e
                logger.warning(f"SAGA {self.saga_id}: {str(e)} (attempt {attempt + 1})")

            if attempt < step.retry_count:
                await asyncio.sleep(2 ** attempt)  # 指数退避

        raise last_error

    async def _compensate(self):
        logger.info(f"SAGA {self.saga_id}: Starting compensation")
        self.state.status = SagaStatus.COMPENSATING

        for step_name in reversed(self.state.completed_steps):
            step = next(s for s in self.steps if s.name == step_name)
            try:
                logger.info(f"SAGA {self.saga_id}: Compensating step {step_name}")
                await step.compensate(self._step_results.get(step_name, {}))
                self._update_step_status(step_name, StepStatus.COMPENSATED)
            except Exception as e:
                logger.error(f"SAGA {self.saga_id}: Compensation failed for {step_name}: {e}")

        self.state.status = SagaStatus.COMPENSATED
        logger.info(f"SAGA {self.saga_id}: Compensation completed")

    def _update_step_status(self, step_name: str, status: StepStatus):
        for step_state in self.state.steps:
            if step_state["name"] == step_name:
                step_state["status"] = status.value
                break


class SagaManager:
    def __init__(self):
        self._sagas = {}
        self._persistence: Optional[SagaPersistence] = None

    def set_persistence(self, persistence: "SagaPersistence"):
        self._persistence = persistence

    async def start_saga(self, steps: List[SagaStep]) -> str:
        saga_id = str(uuid.uuid4())
        saga = SagaOrchestrator(saga_id, steps)
        self._sagas[saga_id] = saga

        if self._persistence:
            await self._persistence.save_state(saga.state)

        asyncio.create_task(self._execute_saga(saga))
        return saga_id

    async def _execute_saga(self, saga: SagaOrchestrator):
        await saga.execute()
        if self._persistence:
            await self._persistence.save_state(saga.state)

    async def get_saga_state(self, saga_id: str) -> Optional[SagaState]:
        return self._sagas.get(saga_id)


saga_manager = SagaManager()
```

### 4.2 SAGA 持久化 (services/common/saga/persistence.py)

```python
import logging
from abc import ABC, abstractmethod
from typing import Optional
from .orchestrator import SagaState
import json

logger = logging.getLogger(__name__)


class SagaPersistence(ABC):
    @abstractmethod
    async def save_state(self, state: SagaState) -> None:
        pass

    @abstractmethod
    async def get_state(self, saga_id: str) -> Optional[SagaState]:
        pass


class PostgresSagaPersistence(SagaPersistence):
    def __init__(self, pool):
        self.pool = pool

    async def save_state(self, state: SagaState) -> None:
        async with self.pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO saga_states (saga_id, status, steps, completed_steps, error, created_at, updated_at)
                VALUES ($1, $2, $3, $4, $5, $6, NOW())
                ON CONFLICT (saga_id) DO UPDATE SET
                    status = EXCLUDED.status,
                    steps = EXCLUDED.steps,
                    completed_steps = EXCLUDED.completed_steps,
                    error = EXCLUDED.error,
                    updated_at = NOW()
                """,
                state.saga_id,
                state.status.value,
                json.dumps(state.steps),
                state.completed_steps,
                state.error,
                state.created_at,
            )

    async def get_state(self, saga_id: str) -> Optional[SagaState]:
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM saga_states WHERE saga_id = $1", saga_id
            )
            if row:
                return SagaState(
                    saga_id=row["saga_id"],
                    status=row["status"],
                    steps=row["steps"],
                    completed_steps=row["completed_steps"],
                    error=row["error"],
                    created_at=row["created_at"].isoformat(),
                    updated_at=row["updated_at"].isoformat(),
                )
        return None


class RedisSagaPersistence(SagaPersistence):
    def __init__(self, redis):
        self.redis = redis
        self.key_prefix = "saga:"

    async def save_state(self, state: SagaState) -> None:
        key = f"{self.key_prefix}{state.saga_id}"
        data = {
            "saga_id": state.saga_id,
            "status": state.status.value,
            "steps": json.dumps(state.steps),
            "completed_steps": json.dumps(state.completed_steps),
            "error": state.error,
            "created_at": state.created_at,
            "updated_at": state.updated_at,
        }
        await self.redis.hset(key, mapping=data)
        await self.redis.expire(key, 86400)  # 24小时过期

    async def get_state(self, saga_id: str) -> Optional[SagaState]:
        key = f"{self.key_prefix}{saga_id}"
        data = await self.redis.hgetall(key)
        if data:
            return SagaState(
                saga_id=data["saga_id"],
                status=data["status"],
                steps=json.loads(data["steps"]),
                completed_steps=json.loads(data["completed_steps"]),
                error=data.get("error"),
                created_at=data["created_at"],
                updated_at=data["updated_at"],
            )
        return None
```

### 4.3 订单支付 SAGA 示例 (services/order-service)

```python
# services/order-service/app/sagas/payment_saga.py
from services.common.saga.orchestrator import SagaOrchestrator, SagaStep, SagaStatus
from services.common.grpc.client import grpc_pool
from services.common.events.producer import get_event_bus
from services.common.events.kafka_events import PaymentEvent, PaymentEventTypes
import logging

logger = logging.getLogger(__name__)


class PaymentSaga:
    def __init__(self, order_id: str, user_id: str, amount: int):
        self.order_id = order_id
        self.user_id = user_id
        self.amount = amount
        self.steps = [
            SagaStep(
                name="create_order",
                forward=self._create_order,
                compensate=self._cancel_order,
            ),
            SagaStep(
                name="reserve_inventory",
                forward=self._reserve_inventory,
                compensate=self._release_inventory,
            ),
            SagaStep(
                name="process_payment",
                forward=self._process_payment,
                compensate=self._refund_payment,
            ),
            SagaStep(
                name="award_points",
                forward=self._award_points,
                compensate=self._deduct_points,
            ),
        ]

    async def execute(self):
        saga_id = f"payment_saga_{self.order_id}"
        saga = SagaOrchestrator(saga_id, self.steps)
        result = await saga.execute()

        if result.status == SagaStatus.COMPLETED:
            logger.info(f"Payment saga completed for order {self.order_id}")
        elif result.status == SagaStatus.FAILED:
            logger.error(f"Payment saga failed for order {self.order_id}: {result.error}")

        return result

    async def _create_order(self) -> dict:
        # 创建订单
        order = await OrderService.create(
            order_id=self.order_id,
            user_id=self.user_id,
            amount=self.amount,
            status="pending"
        )
        logger.info(f"Order created: {self.order_id}")
        return {"order_id": self.order_id, "order": order}

    async def _cancel_order(self, result: dict):
        # 取消订单
        await OrderService.cancel(self.order_id)
        logger.info(f"Order cancelled: {self.order_id}")

    async def _reserve_inventory(self) -> dict:
        # 调用库存服务预留库存
        inventory_client = grpc_pool.get("inventory")
        response = await inventory_client.call_with_retry(
            "ReserveInventory",
            {"order_id": self.order_id, "amount": self.amount}
        )
        logger.info(f"Inventory reserved: {self.order_id}")
        return {"inventory_id": response.inventory_id}

    async def _release_inventory(self, result: dict):
        # 释放库存
        inventory_client = grpc_pool.get("inventory")
        await inventory_client.call_with_retry(
            "ReleaseInventory",
            {"inventory_id": result.get("inventory_id")}
        )
        logger.info(f"Inventory released: {result.get('inventory_id')}")

    async def _process_payment(self) -> dict:
        # 调用支付服务
        event_bus = get_event_bus()
        event = PaymentEvent(
            event_type=PaymentEventTypes.PAYMENT_CREATED,
            payment_id=self.order_id,
            user_id=self.user_id,
            amount=self.amount,
            status="pending",
            payload={},
            source="order-service"
        )
        await event_bus.publish_payment_event(event, payment_id=self.order_id)
        logger.info(f"Payment initiated: {self.order_id}")
        return {"payment_id": self.order_id}

    async def _refund_payment(self, result: dict):
        # 退款
        event_bus = get_event_bus()
        event = PaymentEvent(
            event_type=PaymentEventTypes.PAYMENT_REFUNDED,
            payment_id=result.get("payment_id"),
            user_id=self.user_id,
            amount=self.amount,
            status="refunded",
            payload={},
            source="order-service"
        )
        await event_bus.publish_payment_event(event, payment_id=result.get("payment_id"))
        logger.info(f"Payment refunded: {result.get('payment_id')}")

    async def _award_points(self) -> dict:
        # 授予积分
        event_bus = get_event_bus()
        points = self.amount // 100  # 每100元1积分
        event = PaymentEvent(
            event_type="points.awarded",
            payment_id=self.order_id,
            user_id=self.user_id,
            amount=points,
            status="success",
            payload={},
            source="order-service"
        )
        await event_bus.publish_payment_event(event, payment_id=self.order_id)
        logger.info(f"Points awarded: {points} for user {self.user_id}")
        return {"points": points}

    async def _deduct_points(self, result: dict):
        # 扣除积分
        logger.info(f"Points deducted: {result.get('points')}")
```

## 5. 可靠消息实现

### 5.1 消息追踪表 (可靠消息)

```sql
-- 消息追踪表
CREATE TABLE message_tracking (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    message_id VARCHAR(64) NOT NULL UNIQUE,
    topic VARCHAR(128) NOT NULL,
    payload JSONB NOT NULL,
    status VARCHAR(32) NOT NULL DEFAULT 'pending',
    source_service VARCHAR(64) NOT NULL,
    target_service VARCHAR(64),
    retry_count INT DEFAULT 0,
    max_retries INT DEFAULT 3,
    next_retry_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    consumed_at TIMESTAMP,

    CONSTRAINT valid_status CHECK (status IN ('pending', 'sent', 'acknowledged', 'failed', 'dead_letter'))
);

CREATE INDEX idx_message_tracking_status ON message_tracking(status);
CREATE INDEX idx_message_tracking_next_retry ON message_tracking(next_retry_at) WHERE status = 'failed';
CREATE INDEX idx_message_tracking_message_id ON message_tracking(message_id);
```

### 5.2 可靠消息生产者 (services/common/events/reliable_producer.py)

```python
import asyncio
import logging
from typing import Optional
from datetime import datetime, timedelta
from .producer import KafkaProducer, BaseEvent
from .persistence import MessageTracking

logger = logging.getLogger(__name__)


class ReliableProducer:
    def __init__(
        self,
        kafka_producer: KafkaProducer,
        db_pool,
    ):
        self.kafka = kafka_producer
        self.db_pool = db_pool
        self._running = False

    async def send(
        self,
        topic: str,
        event: BaseEvent,
        target_service: Optional[str] = None,
        max_retries: int = 3,
    ) -> str:
        message_id = event.event_id

        # 1. 保存消息到追踪表
        await self._save_message(message_id, topic, event, target_service, max_retries)

        # 2. 发送到 Kafka
        try:
            await self.kafka.send(topic, event, key=message_id)
            await self._update_status(message_id, "sent")
            logger.info(f"Reliable message sent: {message_id}")
        except Exception as e:
            logger.error(f"Failed to send message {message_id}: {e}")
            await self._update_status(message_id, "failed")
            await self._schedule_retry(message_id)

        return message_id

    async def _save_message(
        self,
        message_id: str,
        topic: str,
        event: BaseEvent,
        target_service: Optional[str],
        max_retries: int,
    ):
        async with self.db_pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO message_tracking (message_id, topic, payload, status, source_service, target_service, max_retries)
                VALUES ($1, $2, $3, 'pending', $4, $5, $6)
                ON CONFLICT (message_id) DO NOTHING
                """,
                message_id,
                topic,
                event.to_json(),
                event.source,
                target_service,
                max_retries,
            )

    async def _update_status(self, message_id: str, status: str):
        async with self.db_pool.acquire() as conn:
            await conn.execute(
                """
                UPDATE message_tracking
                SET status = $2, updated_at = NOW(),
                    consumed_at = CASE WHEN $2 = 'acknowledged' THEN NOW() ELSE consumed_at END
                WHERE message_id = $1
                """,
                message_id,
                status,
            )

    async def _schedule_retry(self, message_id: str):
        async with self.db_pool.acquire() as conn:
            await conn.execute(
                """
                UPDATE message_tracking
                SET retry_count = retry_count + 1,
                    next_retry_at = NOW() + INTERVAL '5 minutes' * (retry_count + 1),
                    status = CASE WHEN retry_count + 1 >= max_retries THEN 'dead_letter' ELSE 'failed' END
                WHERE message_id = $1
                """,
                message_id,
            )


class RetryWorker:
    def __init__(self, kafka_producer: KafkaProducer, db_pool):
        self.kafka = kafka_producer
        self.db_pool = db_pool
        self._running = False

    async def start(self):
        self._running = True
        while self._running:
            await self._process_retries()
            await asyncio.sleep(60)  # 每分钟检查一次

    async def stop(self):
        self._running = False

    async def _process_retries(self):
        async with self.db_pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT * FROM message_tracking
                WHERE status = 'failed'
                  AND next_retry_at <= NOW()
                  AND retry_count < max_retries
                LIMIT 100
                """
            )

        for row in rows:
            try:
                await self.kafka.send(
                    row["topic"],
                    BaseEvent.from_json(row["payload"]),
                    key=row["message_id"],
                )
                await self._update_status(row["message_id"], "sent")
                logger.info(f"Message retry successful: {row['message_id']}")
            except Exception as e:
                logger.error(f"Message retry failed: {row['message_id']}: {e}")
                await self._update_retry(row["message_id"])

    async def _update_status(self, message_id: str, status: str):
        async with self.db_pool.acquire() as conn:
            await conn.execute(
                "UPDATE message_tracking SET status = $2, updated_at = NOW() WHERE message_id = $1",
                message_id,
                status,
            )

    async def _update_retry(self, message_id: str):
        async with self.db_pool.acquire() as conn:
            await conn.execute(
                """
                UPDATE message_tracking
                SET retry_count = retry_count + 1,
                    next_retry_at = NOW() + INTERVAL '10 minutes' * (retry_count + 1),
                    status = CASE WHEN retry_count + 1 >= max_retries THEN 'dead_letter' ELSE 'failed' END
                WHERE message_id = $1
                """,
                message_id,
            )
```

### 5.3 可靠消息消费者 (services/common/events/reliable_consumer.py)

```python
import asyncio
import logging
from typing import Callable, Awaitable, Optional
from datetime import datetime
from .consumer import KafkaConsumer
from .kafka_events import BaseEvent

logger = logging.getLogger(__name__)


class ReliableConsumer:
    def __init__(
        self,
        kafka_consumer: KafkaConsumer,
        db_pool,
    ):
        self.kafka = kafka_consumer
        self.db_pool = db_pool
        self._handlers = {}
        self._running = False

    def register(self, event_type: str, handler: Callable[[dict], Awaitable[None]]):
        self._handlers[event_type] = handler
        self.kafka.register_handler(event_type, self._create_reliable_handler(event_type))

    def _create_reliable_handler(self, event_type: str):
        async def handler(event_data: dict):
            message_id = event_data.get("event_id")

            # 检查是否已处理（幂等性）
            if await self._is_processed(message_id):
                logger.info(f"Message already processed: {message_id}")
                return

            try:
                # 执行业务逻辑
                await self._handlers[event_type](event_data)
                # 标记为已处理
                await self._acknowledge(message_id)
                logger.info(f"Message processed: {message_id}")
            except Exception as e:
                logger.error(f"Message processing failed: {message_id}: {e}")
                await self._nack(message_id)

        return handler

    async def _is_processed(self, message_id: str) -> bool:
        async with self.db_pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT 1 FROM message_tracking WHERE message_id = $1 AND status = 'acknowledged'",
                message_id,
            )
            return row is not None

    async def _acknowledge(self, message_id: str):
        async with self.db_pool.acquire() as conn:
            await conn.execute(
                """
                UPDATE message_tracking
                SET status = 'acknowledged', consumed_at = NOW(), updated_at = NOW()
                WHERE message_id = $1
                """,
                message_id,
            )

    async def _nack(self, message_id: str):
        async with self.db_pool.acquire() as conn:
            await conn.execute(
                """
                UPDATE message_tracking
                SET status = 'failed', retry_count = retry_count + 1,
                    next_retry_at = NOW() + INTERVAL '5 minutes' * (retry_count + 1),
                    updated_at = NOW()
                WHERE message_id = $1
                """,
                message_id,
            )

    async def run(self):
        self._running = True
        await self.kafka.run()

    async def stop(self):
        self._running = False
        await self.kafka.stop()
```

## 6. 补偿事务数据库表

```sql
-- SAGA 状态表
CREATE TABLE saga_states (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    saga_id VARCHAR(64) NOT NULL UNIQUE,
    status VARCHAR(32) NOT NULL,
    steps JSONB NOT NULL,
    completed_steps JSONB NOT NULL DEFAULT '[]',
    current_step VARCHAR(64),
    error TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),

    CONSTRAINT valid_saga_status CHECK (status IN (
        'pending', 'running', 'completed', 'failed', 'compensating', 'compensated'
    ))
);

CREATE INDEX idx_saga_states_status ON saga_states(status);
CREATE INDEX idx_saga_states_saga_id ON saga_states(saga_id);
CREATE INDEX idx_saga_states_updated ON saga_states(updated_at);

-- 死信队列
CREATE TABLE dead_letter_queue (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    message_id VARCHAR(64) NOT NULL,
    topic VARCHAR(128) NOT NULL,
    payload JSONB NOT NULL,
    error_message TEXT,
    retry_count INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW(),
    processed_at TIMESTAMP
);

CREATE INDEX idx_dead_letter_queue_message ON dead_letter_queue(message_id);
CREATE INDEX idx_dead_letter_queue_created ON dead_letter_queue(created_at);
```

## 7. 使用场景示例

### 7.1 下单支付流程 (SAGA)

```
用户下单
    │
    ▼
┌─────────────────────────────────────────────────────────────────┐
│                     PaymentSaga                                  │
│                                                                  │
│  Step 1: create_order (订单服务)                                 │
│      ├── forward: 创建pending订单                                 │
│      └── compensate: 取消订单                                     │
│              │                                                    │
│              ▼                                                    │
│  Step 2: reserve_inventory (库存服务 - gRPC)                      │
│      ├── forward: 预留库存                                        │
│      └── compensate: 释放库存                                     │
│              │                                                    │
│              ▼                                                    │
│  Step 3: process_payment (支付服务 - Kafka)                        │
│      ├── forward: 发起支付                                        │
│      └── compensate: 退款                                        │
│              │                                                    │
│              ▼                                                    │
│  Step 4: award_points (积分服务 - Kafka)                          │
│      ├── forward: 发放积分                                        │
│      └── compensate: 扣减积分                                     │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
    │
    ▼
支付成功/失败
```

### 7.2 支付成功通知 (可靠消息)

```
支付服务确认支付成功
    │
    ├──► Kafka: payment.success
    │         │
    │         ▼
    │    ┌─────────────────────────────────────────┐
    │    │ ReliableConsumer (可靠消费者)            │
    │    │                                          │
    │    │ 1. 检查幂等性 (message_id)              │
    │    │ 2. 执行业务逻辑                         │
    │    │ 3. 发送通知 (Notification Service)      │
    │    │ 4. 更新统计 (Analytics Service)         │
    │    │ 5. 确认消息 (ACK)                       │
    │    │                                          │
    │    │ 如果失败:                               │
    │    │ - 重试 (最多3次)                        │
    │    │ - 指数退避                              │
    │    │ - 最终进入死信队列                       │
    │    └─────────────────────────────────────────┘
```

## 8. 迁移计划

### Phase 1: 基础设施 (Week 1)
1. 创建 SAGA 相关数据库表
2. 实现 SAGA Orchestrator
3. 实现可靠消息基础设施

### Phase 2: 核心流程改造 (Week 2-3)
1. 订单支付流程改造为 SAGA
2. 支付回调流程改造为可靠消息
3. 积分变动流程改造

### Phase 3: 扩展和优化 (Week 4)
1. Saga 状态持久化 (PostgreSQL)
2. 死信队列处理
3. 监控告警
