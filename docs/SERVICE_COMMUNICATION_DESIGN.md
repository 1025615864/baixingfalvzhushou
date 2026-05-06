# 服务间通信架构设计 (gRPC + Kafka)

## 1. 概述

本文档描述百姓助手项目微服务间通信架构改进方案，采用 **gRPC** 作为同步通信协议，**Kafka** 作为异步消息中间件。

## 2. 为什么选择 gRPC + Kafka

### 2.1 gRPC 同步通信

| 特性 | gRPC | REST | 说明 |
|------|------|------|------|
| 传输协议 | HTTP/2 | HTTP/1.1 | gRPC 性能更高 |
| 序列化 | Protocol Buffers | JSON | PB 更小更快 |
| 类型安全 | 强类型 | 弱类型 | 代码生成保证 |
| 双向流 | ✅ 支持 | ❌ 不支持 | gRPC 支持 |
| 代码生成 | 自动 | 手动 | 多语言支持 |

### 2.2 Kafka 异步通信

| 特性 | Kafka | RabbitMQ | 说明 |
|------|-------|----------|------|
| 吞吐量 | 百万级/秒 | 万级/秒 | Kafka 更高 |
| 消息持久化 | ✅ | ✅ | 两者都支持 |
| 消息重放 | ✅ | ❌ | Kafka 支持 |
| 消息顺序 | 分区有序 | 队列有序 | 取决于使用场景 |
| 流处理 | ✅ KStream | ❌ | Kafka 更强 |

## 3. 目标架构

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           服务通信架构                                        │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌──────────────┐                              ┌──────────────┐            │
│  │ User Service │◄────── gRPC (同步) ──────────►│ AI Service │            │
│  │   :8001      │                              │   :8005     │            │
│  └──────┬───────┘                              └──────────────┘            │
│         │                                                                  │
│         │ Kafka (异步事件)                                                 │
│         ▼                                                                  │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │                        Kafka Event Bus                                │  │
│  │  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐   │  │
│  │  │ user.*  │  │payment.*│  │  law.*  │  │  news.* │  │  chat.* │   │  │
│  │  └─────────┘  └─────────┘  └─────────┘  └─────────┘  └─────────┘   │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│         │                                                                  │
│         ▼                                                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐   │
│  │ Notification │  │   Points     │  │Recommendation│  │   Search    │   │
│  │  Service     │  │   Service    │  │   Service   │  │  Service    │   │
│  │   :8009      │  │   :8008      │  │   :8010      │  │   :8011      │   │
│  └──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘   │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

## 4. gRPC 服务定义

### 4.1 目录结构

```
services/
├── common/
│   ├── proto/                    # 共享 Protocol Buffers 定义
│   │   ├── user.proto
│   │   ├── payment.proto
│   │   ├── legal.proto
│   │   └── common.proto
│   ├── grpc/                     # gRPC 客户端/服务端工具
│   │   ├── client.py
│   │   ├── server.py
│   │   └── interceptors.py
│   └── events/                   # Kafka 事件定义
│       ├── producer.py
│       ├── consumer.py
│       └── schemas/
│           ├── user_events.py
│           └── payment_events.py
```

### 4.2 Proto 文件定义

#### 4.2.1 common.proto

```protobuf
syntax = "proto3";

package baixing.common;

message Empty {}

message Timestamp {
  int64 seconds = 1;
  int64 nanos = 2;
}

message Error {
  int32 code = 1;
  string message = 2;
  string details = 3;
}
```

#### 4.2.2 user.proto

```protobuf
syntax = "proto3";

package baixing.user;

import "common.proto";

service UserService {
  rpc GetUser(GetUserRequest) returns (GetUserResponse);
  rpc GetUserProfile(GetUserProfileRequest) returns (UserProfile);
  rpc UpdateUserStatus(UpdateUserStatusRequest) returns (baixing.common.Empty);
  rpc ValidateToken(ValidateTokenRequest) returns (ValidateTokenResponse);
  rpc GetUserQuota(GetUserQuotaRequest) returns (UserQuota);
}

message User {
  string id = 1;
  string email = 2;
  string phone = 3;
  string username = 4;
  UserStatus status = 5;
 baixing.common.Timestamp created_at = 6;
 baixing.common.Timestamp updated_at = 7;
}

enum UserStatus {
  USER_STATUS_UNSPECIFIED = 0;
  USER_STATUS_ACTIVE = 1;
  USER_STATUS_INACTIVE = 2;
  USER_STATUS_BANNED = 3;
}

message GetUserRequest {
  string user_id = 1;
}

message GetUserResponse {
  User user = 1;
}

message GetUserProfileRequest {
  string user_id = 1;
}

message UserProfile {
  string user_id = 1;
  string nickname = 2;
  string avatar_url = 3;
  string bio = 4;
  MembershipInfo membership = 5;
}

message MembershipInfo {
  string membership_type = 1;
  baixing.common.Timestamp expire_at = 2;
}

message UpdateUserStatusRequest {
  string user_id = 1;
  UserStatus status = 2;
  string reason = 3;
}

message ValidateTokenRequest {
  string token = 1;
}

message ValidateTokenResponse {
  bool valid = 1;
  string user_id = 2;
  repeated string roles = 3;
}

message GetUserQuotaRequest {
  string user_id = 1;
}

message UserQuota {
  int32 consultation_quota = 1;
  int32 consultation_used = 2;
  int32 document_quota = 3;
  int32 document_used = 4;
}
```

#### 4.2.3 payment.proto

```protobuf
syntax = "proto3";

package baixing.payment;

import "common.proto";

service PaymentService {
  rpc CreatePayment(CreatePaymentRequest) returns (CreatePaymentResponse);
  rpc QueryPayment(QueryPaymentRequest) returns (Payment);
  rpc ConfirmPayment(ConfirmPaymentRequest) returns (ConfirmPaymentResponse);
  rpc CancelPayment(CancelPaymentRequest) returns (CancelPaymentResponse);
}

message Payment {
  string payment_id = 1;
  string user_id = 2;
  int64 amount = 3;
  string currency = 4;
  PaymentChannel channel = 5;
  PaymentStatus status = 6;
  string order_id = 7;
  baixing.common.Timestamp created_at = 8;
  baixing.common.Timestamp updated_at = 9;
}

enum PaymentChannel {
  PAYMENT_CHANNEL_UNSPECIFIED = 0;
  PAYMENT_CHANNEL_ALIPAY = 1;
  PAYMENT_CHANNEL_WECHAT = 2;
  PAYMENT_CHANNEL_IKUN = 3;
}

enum PaymentStatus {
  PAYMENT_STATUS_UNSPECIFIED = 0;
  PAYMENT_STATUS_PENDING = 1;
  PAYMENT_STATUS_PROCESSING = 2;
  PAYMENT_STATUS_SUCCESS = 3;
  PAYMENT_STATUS_FAILED = 4;
  PAYMENT_STATUS_CANCELLED = 5;
}

message CreatePaymentRequest {
  string user_id = 1;
  int64 amount = 2;
  string currency = 3;
  PaymentChannel channel = 4;
  string order_id = 5;
  map<string, string> metadata = 6;
}

message CreatePaymentResponse {
  string payment_id = 1;
  string pay_url = 2;
  string qr_code = 3;
}

message QueryPaymentRequest {
  string payment_id = 1;
}

message ConfirmPaymentRequest {
  string payment_id = 1;
  string transaction_id = 2;
}

message ConfirmPaymentResponse {
  bool success = 1;
  Payment payment = 2;
}

message CancelPaymentRequest {
  string payment_id = 1;
  string reason = 2;
}
```

#### 4.2.4 legal.proto

```protobuf
syntax = "proto3";

package baixing.legal;

import "common.proto";

service LegalService {
  rpc GetLawyer(GetLawyerRequest) returns (Lawyer);
  rpc GetLawyerSchedule(GetLawyerScheduleRequest) returns (LawyerSchedule);
  rpc CreateConsultation(CreateConsultationRequest) returns (Consultation);
  rpc GetConsultation(GetConsultationRequest) returns (Consultation);
}

message Lawyer {
  string lawyer_id = 1;
  string name = 2;
  string firm_id = 3;
  string title = 4;
  repeated string expertise = 5;
  int32 rating = 6;
  int32 consultation_count = 7;
  int64 price_per_hour = 8;
}

message LawyerSchedule {
  string lawyer_id = 1;
  repeated TimeSlot available_slots = 2;
}

message TimeSlot {
  string slot_id = 1;
  baixing.common.Timestamp start_time = 2;
  baixing.common.Timestamp end_time = 3;
  bool is_available = 4;
}

message Consultation {
  string consultation_id = 1;
  string user_id = 2;
  string lawyer_id = 3;
  ConsultationType type = 4;
  ConsultationStatus status = 5;
  baixing.common.Timestamp scheduled_at = 6;
  string description = 7;
}

enum ConsultationType {
  CONSULTATION_TYPE_UNSPECIFIED = 0;
  CONSULTATION_TYPE_TEXT = 1;
  CONSULTATION_TYPE_VOICE = 2;
  CONSULTATION_TYPE_VIDEO = 3;
}

enum ConsultationStatus {
  CONSULTATION_STATUS_UNSPECIFIED = 0;
  CONSULTATION_STATUS_PENDING = 1;
  CONSULTATION_STATUS_CONFIRMED = 2;
  CONSULTATION_STATUS_IN_PROGRESS = 3;
  CONSULTATION_STATUS_COMPLETED = 4;
  CONSULTATION_STATUS_CANCELLED = 5;
}

message CreateConsultationRequest {
  string user_id = 1;
  string lawyer_id = 2;
  ConsultationType type = 3;
  baixing.common.Timestamp scheduled_at = 4;
  string description = 5;
}

message GetConsultationRequest {
  string consultation_id = 1;
}
```

## 5. gRPC 客户端实现

### 5.1 通用 gRPC 客户端 (services/common/grpc/client.py)

```python
import grpc
from typing import Optional, Any
import logging
from functools import wraps

logger = logging.getLogger(__name__)


class GrpcClient:
    def __init__(
        self,
        host: str,
        port: int,
        stub_class: Any,
        timeout: int = 30,
        max_retries: int = 3,
    ):
        self.host = host
        self.port = port
        self.stub_class = stub_class
        self.timeout = timeout
        self.max_retries = max_retries
        self._channel: Optional[grpc.Channel] = None
        self._stub: Optional[Any] = None

    def connect(self):
        if self._channel is None:
            self._channel = grpc.aio.insecure_channel(
                f"{self.host}:{self.port}",
                options=[
                    ("grpc.max_send_message_length", 50 * 1024 * 1024),
                    ("grpc.max_receive_message_length", 50 * 1024 * 1024),
                    ("grpc.keepalive_time_ms", 30000),
                    ("grpc.keepalive_timeout_ms", 10000),
                ],
            )
            self._stub = self.stub_class(self._channel)
        return self._stub

    async def close(self):
        if self._channel:
            await self._channel.close()
            self._channel = None
            self._stub = None

    async def call_with_retry(self, func_name: str, request: Any):
        last_error = None
        for attempt in range(self.max_retries):
            try:
                stub = self.connect()
                func = getattr(stub, func_name)
                return await func(request, timeout=self.timeout)
            except grpc.RpcError as e:
                last_error = e
                logger.warning(
                    f"gRPC call {func_name} failed (attempt {attempt + 1}): {e}"
                )
                if e.code() == grpc.StatusCode.UNAVAILABLE:
                    await self.close()
        raise last_error


class GrpcClientPool:
    def __init__(self):
        self._clients: dict[str, GrpcClient] = {}

    def register(
        self,
        name: str,
        host: str,
        port: int,
        stub_class: Any,
        timeout: int = 30,
    ):
        self._clients[name] = GrpcClient(host, port, stub_class, timeout)

    def get(self, name: str) -> GrpcClient:
        return self._clients.get(name)

    async def close_all(self):
        for client in self._clients.values():
            await client.close()


grpc_pool = GrpcClientPool()
```

### 5.2 gRPC 拦截器 (services/common/grpc/interceptors.py)

```python
import grpc
import time
import logging
from typing import Callable, Awaitable

logger = logging.getLogger(__name__)


class LoggingInterceptor(grpc.aio.ServerInterceptor):
    async def intercept_service(
        self,
        continuation: Callable[[grpc.HandlerCallDetails], Awaitable[grpc.RpcMethodHandler]],
        handler_call_details: grpc.HandlerCallDetails,
    ) -> grpc.RpcMethodHandler:
        start_time = time.time()
        method = handler_call_details.method
        logger.info(f"gRPC call started: {method}")
        try:
            handler = await continuation(handler_call_details)
            return handler
        finally:
            duration = time.time() - start_time
            logger.info(f"gRPC call finished: {method} ({duration:.3f}s)")


class TracingInterceptor(grpc.aio.ServerInterceptor):
    async def intercept_service(
        self,
        continuation: Callable[[grpc.HandlerCallDetails], Awaitable[grpc.RpcMethodHandler]],
        handler_call_details: grpc.HandlerCallDetails,
    ) -> grpc.RpcMethodHandler:
        metadata = dict(handler_call_details.invocation_metadata)
        trace_id = metadata.get("x-trace-id", "unknown")
        logger.bind(trace_id=trace_id)
        return await continuation(handler_call_details)


class RateLimitInterceptor(grpc.aio.ServerInterceptor):
    def __init__(self, max_rps: int = 100):
        self.max_rps = max_rps
        self._token_bucket = max_rps
        self._last_refill = time.time()

    async def intercept_service(
        self,
        continuation: Callable[[grpc.HandlerCallDetails], Awaitable[grpc.RpcMethodHandler]],
        handler_call_details: grpc.HandlerCallDetails,
    ) -> grpc.RpcMethodHandler:
        self._refill_bucket()
        if self._token_bucket < 1:
            raise grpc.RpcError(
                grpc.StatusCode.RESOURCE_EXHAUSTED, "Rate limit exceeded"
            )
        self._token_bucket -= 1
        return await continuation(handler_call_details)

    def _refill_bucket(self):
        now = time.time()
        elapsed = now - self._last_refill
        self._token_bucket = min(
            self.max_rps, self._token_bucket + elapsed * self.max_rps
        )
        self._last_refill = now
```

## 6. Kafka 事件定义

### 6.1 事件基类 (services/common/events/kafka_events.py)

```python
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Optional, Any
import json
import uuid


@dataclass
class BaseEvent:
    event_id: str
    event_type: str
    timestamp: str
    version: str
    source: str

    def to_json(self) -> str:
        return json.dumps(asdict(self))

    @classmethod
    def from_json(cls, data: str) -> "BaseEvent":
        return cls(**json.loads(data))


@dataclass
class UserEvent(BaseEvent):
    user_id: str
    payload: dict

    def __init__(self, event_type: str, user_id: str, payload: dict, source: str):
        super().__init__(
            event_id=str(uuid.uuid4()),
            event_type=event_type,
            timestamp=datetime.utcnow().isoformat(),
            version="1.0",
            source=source,
        )
        self.user_id = user_id
        self.payload = payload


@dataclass
class PaymentEvent(BaseEvent):
    payment_id: str
    user_id: str
    amount: int
    status: str
    payload: dict

    def __init__(self, event_type: str, payment_id: str, user_id: str,
                 amount: int, status: str, payload: dict, source: str):
        super().__init__(
            event_id=str(uuid.uuid4()),
            event_type=event_type,
            timestamp=datetime.utcnow().isoformat(),
            version="1.0",
            source=source,
        )
        self.payment_id = payment_id
        self.user_id = user_id
        self.amount = amount
        self.status = status
        self.payload = payload


# 事件类型常量
class UserEventTypes:
    USER_REGISTERED = "user.registered"
    USER_UPDATED = "user.updated"
    USER_STATUS_CHANGED = "user.status_changed"
    USER_LOGIN = "user.login"
    USER_LOGOUT = "user.logout"
    MEMBERSHIP_ACTIVATED = "user.membership_activated"
    QUOTA_CHANGED = "user.quota_changed"


class PaymentEventTypes:
    PAYMENT_CREATED = "payment.created"
    PAYMENT_SUCCESS = "payment.success"
    PAYMENT_FAILED = "payment.failed"
    PAYMENT_REFUNDED = "payment.refunded"
```

### 6.2 Kafka 生产者 (services/common/events/producer.py)

```python
import asyncio
import logging
from typing import Optional
from aiokafka import AIOKafkaProducer
from .kafka_events import BaseEvent

logger = logging.getLogger(__name__)


class KafkaProducer:
    def __init__(
        self,
        bootstrap_servers: str,
        client_id: str = "baixing-producer",
    ):
        self.bootstrap_servers = bootstrap_servers
        self.client_id = client_id
        self._producer: Optional[AIOKafkaProducer] = None

    async def start(self):
        if self._producer is None:
            self._producer = AIOKafkaProducer(
                client_id=self.client_id,
                bootstrap_servers=self.bootstrap_servers,
                acks="all",
                enable_idempotence=True,
                max_batch_size=16384,
                linger_ms=10,
            )
            await self._producer.start()
            logger.info(f"Kafka producer started: {self.bootstrap_servers}")

    async def stop(self):
        if self._producer:
            await self._producer.stop()
            self._producer = None
            logger.info("Kafka producer stopped")

    async def send(
        self,
        topic: str,
        event: BaseEvent,
        key: Optional[str] = None,
    ):
        if self._producer is None:
            await self.start()

        try:
            result = await self._producer.send_and_wait(
                topic,
                value=event.to_json().encode("utf-8"),
                key=key.encode("utf-8") if key else None,
                headers=[("event_type", event.event_type.encode("utf-8"))],
            )
            logger.info(
                f"Event sent: topic={topic}, event_id={event.event_id}, "
                f"partition={result.partition}, offset={result.offset}"
            )
            return result
        except Exception as e:
            logger.error(f"Failed to send event: {e}")
            raise


class EventBus:
    def __init__(self, bootstrap_servers: str):
        self.producer = KafkaProducer(bootstrap_servers)
        self._topics = {
            "user": "baixing.user.events",
            "payment": "baixing.payment.events",
            "legal": "baixing.legal.events",
            "news": "baixing.news.events",
            "chat": "baixing.chat.events",
        }

    async def publish_user_event(self, event: BaseEvent, user_id: str):
        await self.producer.send(self._topics["user"], event, key=user_id)

    async def publish_payment_event(self, event: BaseEvent, payment_id: str):
        await self.producer.send(self._topics["payment"], event, key=payment_id)

    async def start(self):
        await self.producer.start()

    async def stop(self):
        await self.producer.stop()


event_bus: Optional[EventBus] = None


def get_event_bus(bootstrap_servers: str = None) -> EventBus:
    global event_bus
    if event_bus is None:
        bootstrap_servers = bootstrap_servers or "localhost:9092"
        event_bus = EventBus(bootstrap_servers)
    return event_bus
```

### 6.3 Kafka 消费者 (services/common/events/consumer.py)

```python
import asyncio
import logging
from typing import Optional, Callable, Awaitable, Dict
from aiokafka import AIOKafkaConsumer
from .kafka_events import BaseEvent
import json

logger = logging.getLogger(__name__)


class KafkaConsumer:
    def __init__(
        self,
        bootstrap_servers: str,
        group_id: str,
        topics: list[str],
        client_id: str = "baixing-consumer",
    ):
        self.bootstrap_servers = bootstrap_servers
        self.group_id = group_id
        self.topics = topics
        self.client_id = client_id
        self._consumer: Optional[AIOKafkaConsumer] = None
        self._handlers: Dict[str, Callable] = {}
        self._running = False

    def register_handler(self, event_type: str, handler: Callable[[BaseEvent], Awaitable[None]]):
        self._handlers[event_type] = handler
        logger.info(f"Registered handler for event type: {event_type}")

    async def start(self):
        if self._consumer is None:
            self._consumer = AIOKafkaConsumer(
                *self.topics,
                client_id=self.client_id,
                group_id=self.group_id,
                bootstrap_servers=self.bootstrap_servers,
                enable_auto_commit=True,
                auto_offset_reset="earliest",
                value_deserializer=lambda m: json.loads(m.decode("utf-8")),
            )
            await self._consumer.start()
            logger.info(f"Kafka consumer started: topics={self.topics}, group={self.group_id}")

    async def stop(self):
        self._running = False
        if self._consumer:
            await self._consumer.stop()
            self._consumer = None
            logger.info("Kafka consumer stopped")

    async def run(self):
        if self._consumer is None:
            await self.start()

        self._running = True
        logger.info("Starting Kafka consumer loop...")

        try:
            async for message in self._consumer:
                if not self._running:
                    break

                try:
                    topic = message.topic
                    event_type = None
                    for header in message.headers or []:
                        if header[0] == "event_type":
                            event_type = header[1].decode("utf-8")
                            break

                    event_data = message.value
                    logger.info(
                        f"Received event: topic={topic}, event_type={event_type}, "
                        f"partition={message.partition}, offset={message.offset}"
                    )

                    if event_type and event_type in self._handlers:
                        await self._handlers[event_type](event_data)
                    else:
                        logger.warning(f"No handler for event type: {event_type}")

                except Exception as e:
                    logger.error(f"Error processing message: {e}", exc_info=e)

        except asyncio.CancelledError:
            logger.info("Kafka consumer cancelled")
        finally:
            await self.stop()
```

## 7. 服务集成示例

### 7.1 User Service 集成 gRPC + Kafka

```python
# services/user-service/app/services/grpc_service.py
from services.common.grpc.client import grpc_pool
from services.common.proto import user_pb2, user_pb2_grpc
from services.common.events.producer import get_event_bus
from services.common.events.kafka_events import UserEvent, UserEventTypes

class UserGrpcService:
    def __init__(self):
        self.user_stub = None
        self.event_bus = None

    async def initialize(self):
        grpc_pool.register(
            "legal",
            host="legal-service",
            port=50051,
            stub_class=user_pb2_grpc.LegalServiceStub,
        )
        self.event_bus = get_event_bus()
        await self.event_bus.start()

    async def get_user_with_lawyer(self, user_id: str, lawyer_id: str):
        # gRPC 调用 Legal Service
        legal_client = grpc_pool.get("legal")
        response = await legal_client.call_with_retry(
            "GetLawyer",
            user_pb2.GetLawyerRequest(lawyer_id=lawyer_id)
        )

        # 发布用户事件到 Kafka
        event = UserEvent(
            event_type=UserEventTypes.USER_LOGIN,
            user_id=user_id,
            payload={"lawyer_id": lawyer_id, "action": "view_profile"},
            source="user-service",
        )
        await self.event_bus.publish_user_event(event, user_id=user_id)

        return {
            "user": await self.get_user(user_id),
            "lawyer": {
                "lawyer_id": response.lawyer_id,
                "name": response.name,
                "expertise": list(response.expertise),
            }
        }
```

## 8. Docker Compose 配置

### 8.1 docker-compose.kafka.yml

```yaml
version: '3.8'

services:
  kafka:
    image: apache/kafka:3.7.0
    container_name: kafka
    ports:
      - "9092:9092"
      - "9101:9101"
    environment:
      KAFKA_NODE_ID: 1
      KAFKA_PROCESS_ROLES: broker,controller
      KAFKA_LISTENERS: PLAINTEXT://0.0.0.0:9092,CONTROLLER://0.0.0.0:9093,EXTERNAL://0.0.0.0:9094
      KAFKA_ADVERTISED_LISTENERS: PLAINTEXT://kafka:9092,EXTERNAL://localhost:9094
      KAFKA_CONTROLLER_LISTENER_NAMES: CONTROLLER
      KAFKA_LISTENER_SECURITY_PROTOCOL_MAP: CONTROLLER:PLAINTEXT,PLAINTEXT:PLAINTEXT,EXTERNAL:PLAINTEXT
      KAFKA_CONTROLLER_QUORUM_VOTERS: 1@kafka:9093
      KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR: 1
      KAFKA_TRANSACTION_STATE_LOG_REPLICATION_FACTOR: 1
      KAFKA_TRANSACTION_STATE_LOG_MIN_ISR: 1
      KAFKA_LOG_DIRS: /var/lib/kafka/data
      KAFKA_AUTO_CREATE_TOPICS_ENABLE: "true"
      KAFKA_GROUP_INITIAL_REBALANCE_DELAY_MS: 0
      CLUSTER_ID: 'MkU3OEVBNTcwNTJENDM2Qk'
    volumes:
      - kafka-data:/var/lib/kafka/data
    networks:
      - baixing-network

  kafka-ui:
    image: provectuslabs/kafka-ui:latest
    container_name: kafka-ui
    ports:
      - "8090:8080"
    environment:
      KAFKA_CLUSTERS_0_NAME: baixing
      KAFKA_CLUSTERS_0_BOOTSTRAPSERVERS: kafka:9092
    depends_on:
      - kafka
    networks:
      - baixing-network

volumes:
  kafka-data:
    driver: local

networks:
  baixing-network:
    external: true
```

## 9. Kafka Topic 配置

| Topic | 分区数 | 副本数 | 保留时间 | 说明 |
|-------|--------|--------|----------|------|
| baixing.user.events | 6 | 3 | 7天 | 用户事件 |
| baixing.payment.events | 6 | 3 | 30天 | 支付事件 (需长期保留) |
| baixing.legal.events | 6 | 3 | 7天 | 法律服务事件 |
| baixing.news.events | 6 | 3 | 3天 | 新闻事件 |
| baixing.chat.events | 6 | 3 | 1天 | 聊天事件 |

## 10. 迁移计划

### Phase 1: 基础设施 (Week 1-2)
1. 部署 Kafka 集群
2. 创建共享 proto 模块
3. 实现通用 gRPC 客户端

### Phase 2: 核心服务集成 (Week 3-4)
1. User Service + Kafka
2. Payment Service + gRPC + Kafka
3. AI Service + gRPC

### Phase 3: 扩展到其他服务 (Week 5-6)
1. Legal Service 集成
2. Notification Service 作为消费者
3. Points Service 集成

### Phase 4: 生产部署 (Week 7-8)
1. K8s 部署 Kafka (使用 Strimzi)
2. 配置监控 (Kafka Manager / Kafka UI)
3. 性能调优
