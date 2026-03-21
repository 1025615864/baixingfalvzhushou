"""视频咨询相关的Pydantic模式"""
from typing import ClassVar
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


class VideoConsultationCreate(BaseModel):
    """创建视频咨询预约"""
    lawyer_id: int = Field(..., description="律师ID")
    subject: str = Field(..., min_length=1, max_length=200, description="咨询主题")
    description: str | None = Field(None, description="问题描述")
    category: str | None = Field(None, description="案件类型")
    scheduled_time: datetime = Field(..., description="预约时间")


class VideoConsultationUpdate(BaseModel):
    """更新视频咨询"""
    status: str | None = None
    meeting_url: str | None = None


class VideoConsultationResponse(BaseModel):
    """视频咨询响应"""
    id: int
    user_id: int
    lawyer_id: int
    subject: str
    description: str | None = None
    category: str | None = None
    scheduled_time: datetime
    duration_minutes: int
    meeting_room_id: str | None = None
    meeting_password: str | None = None
    meeting_url: str | None = None
    status: str
    payment_status: str
    payment_amount: float
    is_free: bool
    discount_rate: float
    started_at: datetime | None = None
    ended_at: datetime | None = None
    completed_at: datetime | None = None
    cancelled_at: datetime | None = None
    created_at: datetime
    updated_at: datetime
    lawyer_name: str | None = None

    model_config: ClassVar[ConfigDict] = {"from_attributes": True}


class VideoConsultationListResponse(BaseModel):
    """视频咨询列表响应"""
    items: list[VideoConsultationResponse]
    total: int
    page: int
    page_size: int


class VideoScheduleCreate(BaseModel):
    """创建视频咨询排班"""
    date: datetime = Field(..., description="日期")
    start_time: str = Field(..., pattern=r'^([01]?[0-9]|2[0-3]):[0-5][0-9]$', description="开始时间 HH:MM")
    end_time: str = Field(..., pattern=r'^([01]?[0-9]|2[0-3]):[0-5][0-9]$', description="结束时间 HH:MM")
    video_consultation_enabled: bool = True
    consultation_fee: float = Field(0.0, ge=0, description="视频咨询费用")
    max_bookings: int = Field(3, ge=1, le=10, description="最大预约数")
    note: str | None = Field(None, max_length=500, description="备注")


class VideoScheduleUpdate(BaseModel):
    """更新视频咨询排班"""
    date: datetime | None = None
    start_time: str | None = Field(None, pattern=r'^([01]?[0-9]|2[0-3]):[0-5][0-9]$')
    end_time: str | None = Field(None, pattern=r'^([01]?[0-9]|2[0-3]):[0-5][0-9]$')
    is_available: bool | None = None
    video_consultation_enabled: bool | None = None
    consultation_fee: float | None = None
    max_bookings: int | None = None
    note: str | None = None


class VideoScheduleResponse(BaseModel):
    """视频咨询排班响应"""
    id: int
    lawyer_id: int
    date: datetime
    start_time: str
    end_time: str
    is_available: bool
    max_bookings: int
    current_bookings: int
    video_consultation_enabled: bool
    consultation_fee: float
    note: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config: ClassVar[ConfigDict] = {"from_attributes": True}


class VideoScheduleListResponse(BaseModel):
    """视频咨询排班列表响应"""
    items: list[VideoScheduleResponse]
    total: int
    page: int
    page_size: int


class VideoSlotResponse(BaseModel):
    """视频咨询可用时段"""
    schedule_id: int
    date: datetime
    start_time: str
    end_time: str
    consultation_fee: float
    available_count: int


class VideoAvailableSlotsResponse(BaseModel):
    """视频咨询可用时段列表"""
    lawyer_id: int
    date: datetime
    slots: list[VideoSlotResponse]


class MemberDiscountResponse(BaseModel):
    """会员折扣响应"""
    tier: str
    discount_rate: float
    free_monthly_count: int
    is_free: bool


class VideoConsultationFeeResponse(BaseModel):
    """视频咨询费用响应"""
    fee: float
    duration: int
    enabled: bool


class UserUsageResponse(BaseModel):
    """用户使用情况响应"""
    year_month: str
    free_used: int
    paid_count: int
    remaining_free: int
    tier: str | None = None