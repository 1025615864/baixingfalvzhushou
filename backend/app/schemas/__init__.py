"""Pydantic模式"""
from .ai import (
    ChatRequest,
    ChatResponse,
    ConsultationCreate,
    ConsultationResponse,
    MessageResponse
)
from .calendar import (
    CalendarReminderCreate,
    CalendarReminderUpdate,
    CalendarReminderResponse,
    CalendarReminderListResponse,
)
from .channel import (
    ChannelCreate,
    ChannelUpdate,
    ChannelResponse,
    ChannelListResponse,
    ChannelStats,
    ChannelMetricsResponse,
    ConversionFunnel,
    ChannelAnalytics,
    ChannelParams,
    TrackEvent,
    ChannelListParams,
)

__all__ = [
    "ChatRequest",
    "ChatResponse",
    "ConsultationCreate",
    "ConsultationResponse",
    "MessageResponse",
    "CalendarReminderCreate",
    "CalendarReminderUpdate",
    "CalendarReminderResponse",
    "CalendarReminderListResponse",
    "ChannelCreate",
    "ChannelUpdate",
    "ChannelResponse",
    "ChannelListResponse",
    "ChannelStats",
    "ChannelMetricsResponse",
    "ConversionFunnel",
    "ChannelAnalytics",
    "ChannelParams",
    "TrackEvent",
    "ChannelListParams",
]
