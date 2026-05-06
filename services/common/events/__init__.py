"""Kafka 事件模块"""
from .kafka_events import (
    BaseEvent,
    UserEvent,
    PaymentEvent,
    OrderEvent,
    UserEventTypes,
    PaymentEventTypes,
    OrderEventTypes,
    EventType,
    EventTopic,
    VectorSyncEvent,
    create_knowledge_event,
    create_archive_event,
)
from .event_types import (
    KnowledgeEventType,
    ArchiveEventType,
    UserEventType,
    PaymentEventType,
    NotificationEventType,
    SearchEventType,
    OrderEventType,
    CommunityEventType,
    AIEventType,
    VectorEventType,
)
from .producer import (
    KafkaProducerClient,
    EventBus,
    get_event_bus,
    init_event_bus,
    close_event_bus,
)
from .consumer import (
    KafkaConsumerClient,
    MessageHandler,
    AsyncMessageHandler,
    BatchMessageHandler,
    AsyncBatchMessageHandler,
    register_handler,
    register_batch_handler,
    start_consuming,
)
from .kafka_client import (
    KafkaConfig,
    KafkaProducer,
    KafkaConsumer,
    KafkaConsumerGroup,
    KafkaClient,
    create_producer,
    create_consumer,
)
from .tracing_consumer import (
    TracingKafkaConsumer,
    TracingConsumerFactory,
    TracedMessageHandler,
    AsyncTracedMessageHandler,
)
from .tracing_producer import (
    TracingKafkaProducer,
    TracingProducerFactory,
    TracedEventBus,
)

__all__ = [
    # Events
    "BaseEvent",
    "UserEvent",
    "PaymentEvent",
    "OrderEvent",
    "UserEventTypes",
    "PaymentEventTypes",
    "OrderEventTypes",
    "EventType",
    "EventTopic",
    "VectorSyncEvent",
    "create_knowledge_event",
    "create_archive_event",
    # Event types
    "KnowledgeEventType",
    "ArchiveEventType",
    "UserEventType",
    "PaymentEventType",
    "NotificationEventType",
    "SearchEventType",
    "OrderEventType",
    "CommunityEventType",
    "AIEventType",
    "VectorEventType",
    # Producer
    "KafkaProducerClient",
    "EventBus",
    "get_event_bus",
    "init_event_bus",
    "close_event_bus",
    # Consumer
    "KafkaConsumerClient",
    "MessageHandler",
    "AsyncMessageHandler",
    "BatchMessageHandler",
    "AsyncBatchMessageHandler",
    "register_handler",
    "register_batch_handler",
    "start_consuming",
    # Kafka Client
    "KafkaConfig",
    "KafkaProducer",
    "KafkaConsumer",
    "KafkaConsumerGroup",
    "KafkaClient",
    "create_producer",
    "create_consumer",
    # Tracing
    "TracingKafkaConsumer",
    "TracingConsumerFactory",
    "TracedMessageHandler",
    "AsyncTracedMessageHandler",
    "TracingKafkaProducer",
    "TracingProducerFactory",
    "TracedEventBus",
]
