"""schemas package"""
from pydantic import BaseModel
from typing import Optional, List, Generic, TypeVar
from datetime import datetime


T = TypeVar("T")


class PaginationParams:
    """统一分页参数依赖注入"""
    def __init__(
        self,
        page: int = 1,
        page_size: int = 20,
        sort_by: str = "created_at",
        sort_order: str = "desc",
    ):
        self.page = max(1, page)
        self.page_size = min(100, max(1, page_size))
        self.sort_by = sort_by
        self.sort_order = sort_order
        self.offset = (self.page - 1) * self.page_size
        self._total = 0

    @property
    def has_next(self) -> bool:
        return self.page * self.page_size < self._total

    @property
    def has_prev(self) -> bool:
        return self.page > 1

    def set_total(self, total: int):
        self._total = total


class PaginatedResponse(BaseModel, Generic[T]):
    """统一分页响应"""
    items: List[T]
    total: int
    page: int
    page_size: int
    total_pages: int
    has_next: bool
    has_prev: bool

    @classmethod
    def create(cls, items: List[T], total: int, params: PaginationParams):
        params.set_total(total)
        total_pages = (total + params.page_size - 1) // params.page_size if params.page_size > 0 else 0
        return cls(
            items=items,
            total=total,
            page=params.page,
            page_size=params.page_size,
            total_pages=total_pages,
            has_next=params.has_next,
            has_prev=params.has_prev,
        )


class ConsultationBase(BaseModel):
    category: str
    title: str
    description: str


class ConsultationCreate(ConsultationBase):
    ai_assisted: bool = True


class ConsultationResponse(ConsultationBase):
    id: int
    user_id: int
    lawyer_id: Optional[int] = None
    status: str
    ai_assisted: bool
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class MessageBase(BaseModel):
    role: str
    content: str


class MessageCreate(MessageBase):
    pass


class MessageResponse(MessageBase):
    id: int
    consultation_id: int
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class LawyerBase(BaseModel):
    name: str
    title: Optional[str] = None
    specialties: List[str] = []
    bio: Optional[str] = None
    city: Optional[str] = None


class LawyerCreate(LawyerBase):
    user_id: int


class LawyerUpdate(BaseModel):
    title: Optional[str] = None
    specialties: Optional[List[str]] = None
    bio: Optional[str] = None
    city: Optional[str] = None


class LawyerResponse(LawyerBase):
    id: int
    user_id: int
    rating: float
    consultation_count: int
    status: str
    verified_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class LawyerDetailResponse(LawyerResponse):
    lawfirm_id: Optional[int] = None
    rating_count: int = 0
    response_time: int = 0
    avatar: Optional[str] = None
    price_range: Optional[str] = None
    created_at: Optional[datetime] = None


class LawFirmBase(BaseModel):
    name: str
    license_no: Optional[str] = None
    province: Optional[str] = None
    city: Optional[str] = None
    address: Optional[str] = None


class LawFirmCreate(LawFirmBase):
    pass


class LawFirmResponse(LawFirmBase):
    id: int
    status: str
    lawyer_count: int = 0

    class Config:
        from_attributes = True


class ReviewBase(BaseModel):
    rating: int
    content: Optional[str] = None
    is_anonymous: bool = False


class ReviewCreate(ReviewBase):
    consultation_id: int


class ReviewResponse(ReviewBase):
    id: int
    consultation_id: int
    lawyer_id: int
    user_id: int
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class AppointmentBase(BaseModel):
    consultation_id: int
    lawyer_id: int
    appointment_type: str
    scheduled_at: str
    price: float = 0.0


class AppointmentCreate(AppointmentBase):
    pass


class AppointmentResponse(BaseModel):
    id: int
    consultation_id: int
    lawyer_id: int
    type: str
    status: str
    scheduled_at: Optional[datetime] = None
    price: float
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ScheduleBase(BaseModel):
    date: str
    start_time: str
    end_time: str


class ScheduleCreate(ScheduleBase):
    pass


class ScheduleBulkCreate(BaseModel):
    schedules: List[ScheduleCreate]


class ScheduleResponse(BaseModel):
    id: int
    lawyer_id: int
    date: datetime
    start_time: str
    end_time: str
    is_available: bool

    class Config:
        from_attributes = True


class LawyerStatsResponse(BaseModel):
    lawyer_id: int
    total: int
    avg_rating: float


class MatchingScoreResponse(BaseModel):
    lawyer_id: int
    name: str
    title: Optional[str] = None
    specialties: List[str]
    rating: float
    city: Optional[str] = None
    score: Optional[float] = None
    is_available_today: Optional[bool] = None


class AdminStatsResponse(BaseModel):
    total_lawyers: int
    verified_lawyers: int
    pending_lawyers: int
    total_consultations: int
    active_consultations: int


class DocumentBase(BaseModel):
    consultation_id: int
    document_type: str
    title: str
    content: Optional[str] = None


class DocumentCreate(DocumentBase):
    lawyer_id: Optional[int] = None
    generated_by_ai: bool = False


class DocumentUpdate(BaseModel):
    content: Optional[str] = None
    status: Optional[str] = None


class DocumentResponse(BaseModel):
    id: int
    consultation_id: int
    lawyer_id: Optional[int] = None
    user_id: int
    document_type: str
    title: str
    content: Optional[str] = None
    status: str
    generated_by_ai: bool
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class TemplateBase(BaseModel):
    name: str
    category: str
    required_fields: List[str] = []
    optional_fields: List[str] = []
    description: Optional[str] = None


class TemplateCreate(TemplateBase):
    pass


class TemplateResponse(TemplateBase):
    id: int

    class Config:
        from_attributes = True