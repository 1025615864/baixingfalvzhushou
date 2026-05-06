"""events package"""
from .legal_events import (
    LegalEvent,
    LegalEventTypes,
    create_legal_event,
)
from .producer import event_bus
from .consumer import user_event_consumer

__all__ = [
    "LegalEvent",
    "LegalEventTypes",
    "create_legal_event",
    "event_bus",
    "user_event_consumer",
]

import logging
logger = logging.getLogger(__name__)

logger.info("Legal service events module loaded")