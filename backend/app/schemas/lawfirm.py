"""法律咨询所相关的Pydantic模式"""
from typing import ClassVar
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


# ============ 律所相关 ============

class LawFirmCreate(BaseModel):
    """创建律所"""
    name: str = Field(..., min_length=1, max_length=200)
    description: str | None = None
    address: str | None = None
    city: str | None = None
    province: str | None = None
    phone: str | None = None
    email: str | None = None
    website: str | None = None
    logo: str | None = None
    license_no: str | None = None
    specialties: str | None = None


class LawFirmUpdate(BaseModel):
    """更新律所"""
    name: str | None = Field(None, max_length=200)
    description: str | None = None
    address: str | None = None
    city: str | None = None
    province: str | None = None
    phone: str | None = None
    email: str | None = None
    website: str | None = None
    logo: str | None = None
    license_no: str | None = None
    specialties: str | None = None
    is_verified: bool | None = None
    is_active: bool | None = None


class LawFirmResponse(BaseModel):
    """律所响应"""
    id: int
    name: str
    description: str | None = None
    address: str | None = None
    city: str | None = None
    province: str | None = None
    phone: str | None = None
    email: str | None = None
    website: str | None = None
    logo: str | None = None
    license_no: str | None = None
    specialties: list[str] = []
    rating: float
    review_count: int
    is_verified: bool
    is_active: bool
    created_at: datetime
    lawyer_count: int = 0

    model_config: ClassVar[ConfigDict] = {"from_attributes": True}


class LawFirmListResponse(BaseModel):
    """律所列表响应"""
    items: list[LawFirmResponse]
    total: int
    page: int
    page_size: int


# ============ 律师相关 ============

class LawyerCreate(BaseModel):
    """创建律师"""
    firm_id: int | None = None
    name: str = Field(..., min_length=1, max_length=50)
    avatar: str | None = None
    title: str | None = None
    license_no: str | None = None
    phone: str | None = None
    email: str | None = None
    introduction: str | None = None
    specialties: str | None = None
    experience_years: int = 0
    consultation_fee: float = 0.0


class LawyerUpdate(BaseModel):
    """更新律师"""
    firm_id: int | None = None
    name: str | None = Field(None, max_length=50)
    avatar: str | None = None
    title: str | None = None
    license_no: str | None = None
    phone: str | None = None
    email: str | None = None
    introduction: str | None = None
    specialties: str | None = None
    experience_years: int | None = None
    consultation_fee: float | None = None
    is_verified: bool | None = None
    is_active: bool | None = None


class LawyerResponse(BaseModel):
    """律师响应"""
    id: int
    user_id: int | None = None
    firm_id: int | None = None
    name: str
    avatar: str | None = None
    title: str | None = None
    license_no: str | None = None
    phone: str | None = None
    email: str | None = None
    introduction: str | None = None
    specialties: str | None = None
    experience_years: int
    case_count: int
    rating: float
    review_count: int
    consultation_fee: float
    is_verified: bool
    is_active: bool
    created_at: datetime
    firm_name: str | None = None

    model_config: ClassVar[ConfigDict] = {"from_attributes": True}


class LawyerListResponse(BaseModel):
    """律师列表响应"""
    items: list[LawyerResponse]
    total: int
    page: int
    page_size: int


# ============ 咨询预约相关 ============

class ConsultationCreate(BaseModel):
    """创建咨询预约"""
    lawyer_id: int
    subject: str = Field(..., min_length=1, max_length=200)
    description: str | None = None
    category: str | None = None
    contact_phone: str | None = None
    preferred_time: datetime | None = None


class ConsultationUpdate(BaseModel):
    """更新咨询状态"""
    status: str | None = None
    admin_note: str | None = None


class ConsultationResponse(BaseModel):
    """咨询预约响应"""
    id: int
    user_id: int
    lawyer_id: int
    subject: str
    description: str | None = None
    category: str | None = None
    contact_phone: str | None = None
    preferred_time: datetime | None = None
    status: str
    admin_note: str | None = None
    created_at: datetime
    updated_at: datetime
    lawyer_name: str | None = None
    payment_order_no: str | None = None
    payment_status: str | None = None
    payment_amount: float | None = None
    review_id: int | None = None
    can_review: bool = False

    model_config: ClassVar[ConfigDict] = {"from_attributes": True}


class ConsultationListResponse(BaseModel):
    """咨询列表响应"""
    items: list[ConsultationResponse]
    total: int
    page: int
    page_size: int


# ============ 评价相关 ============

class ReviewCreate(BaseModel):
    """创建评价"""
    lawyer_id: int
    consultation_id: int | None = None
    rating: int = Field(..., ge=1, le=5)
    content: str | None = None
    is_anonymous: bool = False
    tags: list[str] | None = None
    # 多维度评价
    professionalism: int | None = Field(
        None, ge=1, le=5, description="专业性 1-5")
    responsiveness: int | None = Field(
        None, ge=1, le=5, description="响应速度 1-5")
    attitude: int | None = Field(None, ge=1, le=5, description="服务态度 1-5")


class ReviewResponse(BaseModel):
    """评价响应"""
    id: int
    lawyer_id: int
    user_id: int
    consultation_id: int | None = None
    rating: int
    content: str | None = None
    is_anonymous: bool
    # 多维度评价
    professionalism: int | None = None
    responsiveness: int | None = None
    attitude: int | None = None
    tags: list[str] = []
    created_at: datetime
    username: str | None = None

    model_config: ClassVar[ConfigDict] = {"from_attributes": True}


class ReviewListResponse(BaseModel):
    """评价列表响应"""
    items: list[ReviewResponse]
    total: int
    page: int
    page_size: int
    average_rating: float


class ReviewDimensionStats(BaseModel):
    """评价维度统计"""
    professionalism_avg: float
    responsiveness_avg: float
    attitude_avg: float


class ReviewRatingDistribution(BaseModel):
    """评价评分分布"""
    rating_5_count: int
    rating_4_count: int
    rating_3_count: int
    rating_2_count: int
    rating_1_count: int


class ReviewTagStats(BaseModel):
    """评价标签统计"""
    tag: str
    count: int


class ReviewSummaryResponse(BaseModel):
    """律师评价摘要响应"""
    lawyer_id: int
    lawyer_name: str
    total_reviews: int
    average_rating: float
    dimension_stats: ReviewDimensionStats
    rating_distribution: ReviewRatingDistribution
    tag_stats: list[ReviewTagStats]
    popular_tags: list[ReviewTagStats]


# ============ 律师日程相关 ============

class LawyerScheduleCreate(BaseModel):
    """创建律师日程"""
    date: datetime = Field(..., description="日期")
    start_time: str = Field(...,
                            pattern=r'^([01]?[0-9]|2[0-3]):[0-5][0-9]$',
                            description="开始时间 HH:MM")
    end_time: str = Field(...,
                          pattern=r'^([01]?[0-9]|2[0-3]):[0-5][0-9]$',
                          description="结束时间 HH:MM")
    is_available: bool = True
    note: str | None = Field(None, max_length=500, description="备注")


class LawyerScheduleUpdate(BaseModel):
    """更新律师日程"""
    date: datetime | None = None
    start_time: str | None = Field(
        None, pattern=r'^([01]?[0-9]|2[0-3]):[0-5][0-9]$')
    end_time: str | None = Field(
        None, pattern=r'^([01]?[0-9]|2[0-3]):[0-5][0-9]$')
    is_available: bool | None = None
    note: str | None = Field(None, max_length=500)


class LawyerScheduleResponse(BaseModel):
    """律师日程响应"""
    id: int
    lawyer_id: int
    date: datetime
    start_time: str
    end_time: str
    is_available: bool
    consultation_id: int | None = None
    note: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config: ClassVar[ConfigDict] = {"from_attributes": True}


class LawyerScheduleListResponse(BaseModel):
    """律师日程列表响应"""
    items: list[LawyerScheduleResponse]
    total: int
    page: int
    page_size: int


class AvailableSlotResponse(BaseModel):
    """可用时段响应"""
    date: datetime
    start_time: str
    end_time: str


class AvailableSlotsResponse(BaseModel):
    """可用时段列表响应"""
    lawyer_id: int
    date: datetime
    slots: list[AvailableSlotResponse]


# ============ 律师数据看板相关 ============

class LawyerWalletInfo(BaseModel):
    """律师钱包信息"""
    balance: float
    frozen: float
    total_income: float
    total_withdrawn: float
    pending_withdrawal: float


class LawyerConsultationStats(BaseModel):
    """律师咨询统计"""
    total: int
    pending: int
    confirmed: int
    completed: int
    cancelled: int
    today_count: int


class LawyerReviewStats(BaseModel):
    """律师评价统计"""
    total_reviews: int
    average_rating: float
    rating_5_count: int
    rating_4_count: int
    rating_3_count: int
    rating_2_count: int
    rating_1_count: int


class LawyerDashboardResponse(BaseModel):
    """律师数据看板响应"""
    wallet: LawyerWalletInfo
    consultation_stats: LawyerConsultationStats
    review_stats: LawyerReviewStats
    recent_consultations: list[ConsultationResponse]
    recent_reviews: list[ReviewResponse]
    unread_notifications: int


class LawyerWorkbenchResponse(BaseModel):
    """律师工作台响应"""
    wallet: LawyerWalletInfo
    pending_consultations: list[ConsultationResponse]
    pending_withdrawals: int
    pending_withdrawal_amount: float
    recent_reviews: list[ReviewResponse]
    unread_notifications: int
    today_stats: LawyerConsultationStats


# ============ 律师统计相关 ============

class IncomeTrendItem(BaseModel):
    """收入趋势项"""
    date: str
    income: float


class IncomeTrendResponse(BaseModel):
    """收入趋势响应"""
    lawyer_id: int
    days: int
    trend: list[IncomeTrendItem]
    total_income: float


class ConsultationStatsResponse(BaseModel):
    """咨询统计响应"""
    lawyer_id: int
    total: int
    completed: int
    cancelled: int
    completion_rate: float
    avg_response_minutes: float


# ============ 律师绩效分析相关 ============

class LawyerPerformanceConsultationStats(BaseModel):
    """律师绩效-咨询统计"""
    total: int
    completed: int
    cancelled: int
    completion_rate: float


class LawyerPerformanceIncomeStats(BaseModel):
    """律师绩效-收入统计"""
    total: float
    avg_per_consultation: float


class LawyerPerformanceReviewStats(BaseModel):
    """律师绩效-评价统计"""
    count: int
    avg_rating: float


class LawyerPerformanceResponseStats(BaseModel):
    """律师绩效-响应统计"""
    avg_response_minutes: float


class LawyerPerformanceDailyConsultation(BaseModel):
    """律师绩效-每日咨询量"""
    date: str
    count: int


class LawyerPerformanceResponse(BaseModel):
    """律师绩效分析响应"""
    lawyer_id: int
    period_days: int
    consultation: LawyerPerformanceConsultationStats
    income: LawyerPerformanceIncomeStats
    review: LawyerPerformanceReviewStats
    response: LawyerPerformanceResponseStats
    daily_consultations: list[LawyerPerformanceDailyConsultation]


class LawyerRankingItem(BaseModel):
    """律师排行榜项"""
    lawyer_id: int
    lawyer_name: str
    rating: float
    value: float


class LawyerRankingResponse(BaseModel):
    """律师排行榜响应"""
    metric: str
    days: int
    items: list[LawyerRankingItem]


# ============ 律师快捷回复模板相关 ============

class LawyerReplyTemplateCreate(BaseModel):
    """创建律师快捷回复模板"""
    title: str = Field(..., min_length=1, max_length=100, description="模板标题")
    content: str = Field(..., min_length=1, description="模板内容")
    category: str | None = Field(None, max_length=50, description="分类")


class LawyerReplyTemplateUpdate(BaseModel):
    """更新律师快捷回复模板"""
    title: str | None = Field(None, max_length=100)
    content: str | None = Field(None, min_length=1)
    category: str | None = Field(None, max_length=50)
    is_active: bool | None = None


class LawyerReplyTemplateResponse(BaseModel):
    """律师快捷回复模板响应"""
    id: int
    lawyer_id: int
    title: str
    content: str
    category: str | None = None
    is_active: bool
    use_count: int
    created_at: datetime
    updated_at: datetime

    model_config: ClassVar[ConfigDict] = {"from_attributes": True}


class LawyerReplyTemplateListResponse(BaseModel):
    """律师快捷回复模板列表响应"""
    items: list[LawyerReplyTemplateResponse]
    total: int
    page: int
    page_size: int


# ============ 律师主页定制相关 ============

class LawyerHomepageCreate(BaseModel):
    """创建律师主页"""
    banner_image: str | None = Field(None, max_length=255, description="横幅图片")
    profile_image: str | None = Field(
        None, max_length=255, description="个人形象照")
    slogan: str | None = Field(None, max_length=200, description="个人标语")
    bio: str | None = Field(None, description="个人简介（富文本）")
    specialties_display: str | None = Field(None, description="擅长领域展示（富文本）")
    achievements: str | None = Field(None, description="成就荣誉（富文本）")
    education: str | None = Field(None, description="教育背景（富文本）")
    service_areas: str | None = Field(None, description="服务区域（富文本）")
    service_hours: str | None = Field(None, max_length=200, description="服务时间")
    response_time: str | None = Field(
        None, max_length=100, description="响应时间承诺")
    contact_phone: str | None = Field(None, max_length=50, description="联系电话")
    contact_email: str | None = Field(None, max_length=100, description="联系邮箱")
    wechat_qrcode: str | None = Field(
        None, max_length=255, description="微信二维码")
    weibo_url: str | None = Field(None, max_length=255, description="微博链接")
    linkedin_url: str | None = Field(
        None, max_length=255, description="LinkedIn链接")
    zhihu_url: str | None = Field(None, max_length=255, description="知乎链接")
    case_studies: str | None = Field(None, description="案例展示（富文本）")
    video_url: str | None = Field(None, max_length=255, description="视频链接")
    video_cover: str | None = Field(None, max_length=255, description="视频封面")
    seo_title: str | None = Field(None, max_length=100, description="SEO标题")
    seo_description: str | None = Field(
        None, max_length=500, description="SEO描述")
    seo_keywords: str | None = Field(
        None, max_length=500, description="SEO关键词")
    theme_color: str | None = Field(None, max_length=20, description="主题颜色")
    background_color: str | None = Field(
        None, max_length=20, description="背景颜色")
    is_published: bool = Field(default=False, description="是否发布")


class LawyerHomepageUpdate(BaseModel):
    """更新律师主页"""
    banner_image: str | None = Field(None, max_length=255)
    profile_image: str | None = Field(None, max_length=255)
    slogan: str | None = Field(None, max_length=200)
    bio: str | None = None
    specialties_display: str | None = None
    achievements: str | None = None
    education: str | None = None
    service_areas: str | None = None
    service_hours: str | None = Field(None, max_length=200)
    response_time: str | None = Field(None, max_length=100)
    contact_phone: str | None = Field(None, max_length=50)
    contact_email: str | None = Field(None, max_length=100)
    wechat_qrcode: str | None = Field(None, max_length=255)
    weibo_url: str | None = Field(None, max_length=255)
    linkedin_url: str | None = Field(None, max_length=255)
    zhihu_url: str | None = Field(None, max_length=255)
    case_studies: str | None = None
    video_url: str | None = Field(None, max_length=255)
    video_cover: str | None = Field(None, max_length=255)
    seo_title: str | None = Field(None, max_length=100)
    seo_description: str | None = Field(None, max_length=500)
    seo_keywords: str | None = Field(None, max_length=500)
    theme_color: str | None = Field(None, max_length=20)
    background_color: str | None = Field(None, max_length=20)
    is_published: bool | None = None


class LawyerHomepageResponse(BaseModel):
    """律师主页响应"""
    id: int
    lawyer_id: int
    banner_image: str | None = None
    profile_image: str | None = None
    slogan: str | None = None
    bio: str | None = None
    specialties_display: str | None = None
    achievements: str | None = None
    education: str | None = None
    service_areas: str | None = None
    service_hours: str | None = None
    response_time: str | None = None
    contact_phone: str | None = None
    contact_email: str | None = None
    wechat_qrcode: str | None = None
    weibo_url: str | None = None
    linkedin_url: str | None = None
    zhihu_url: str | None = None
    case_studies: str | None = None
    video_url: str | None = None
    video_cover: str | None = None
    seo_title: str | None = None
    seo_description: str | None = None
    seo_keywords: str | None = None
    theme_color: str | None = None
    background_color: str | None = None
    is_published: bool
    view_count: int
    created_at: datetime
    updated_at: datetime


# ============ 律师推广链接相关 ============

class LawyerPromotionLinkCreate(BaseModel):
    """创建律师推广链接"""
    link_name: str | None = Field(None, max_length=100, description="链接名称")
    description: str | None = Field(None, description="描述")


class LawyerPromotionLinkUpdate(BaseModel):
    """更新律师推广链接"""
    link_name: str | None = Field(None, max_length=100)
    description: str | None = None
    is_active: bool | None = None


class LawyerPromotionLinkResponse(BaseModel):
    """律师推广链接响应"""
    id: int
    lawyer_id: int
    link_code: str
    link_name: str | None = None
    description: str | None = None
    is_active: bool
    click_count: int
    consultation_count: int
    conversion_count: int
    created_at: datetime
    updated_at: datetime

    model_config: ClassVar[ConfigDict] = {"from_attributes": True}


class LawyerPromotionLinkListResponse(BaseModel):
    """律师推广链接列表响应"""
    items: list[LawyerPromotionLinkResponse]
    total: int
    page: int
    page_size: int


class LawyerPromotionLinkStatsResponse(BaseModel):
    """律师推广链接统计响应"""
    link_id: int
    link_code: str
    link_name: str | None = None
    click_count: int
    consultation_count: int
    conversion_count: int
    conversion_rate: float  # 转化率 = conversion_count / click_count

    model_config: ClassVar[ConfigDict] = {"from_attributes": True}


class LawyerHomepagePublicResponse(BaseModel):
    """律师主页公开响应（用于用户查看）"""
    id: int
    lawyer_id: int
    lawyer_name: str | None = None
    lawyer_avatar: str | None = None
    lawyer_title: str | None = None
    lawyer_specialties: str | None = None
    lawyer_experience_years: int = 0
    lawyer_rating: float = 0.0
    lawyer_review_count: int = 0
    lawyer_consultation_fee: float = 0.0
    banner_image: str | None = None
    profile_image: str | None = None
    slogan: str | None = None
    bio: str | None = None
    specialties_display: str | None = None
    achievements: str | None = None
    education: str | None = None
    service_areas: str | None = None
    service_hours: str | None = None
    response_time: str | None = None
    contact_phone: str | None = None
    contact_email: str | None = None
    wechat_qrcode: str | None = None
    weibo_url: str | None = None
    linkedin_url: str | None = None
    zhihu_url: str | None = None
    case_studies: str | None = None
    video_url: str | None = None
    video_cover: str | None = None
    view_count: int
    created_at: datetime
    updated_at: datetime


# ============ 律师分享卡片相关 ============

class LawyerShareCardTemplate(BaseModel):
    """律师分享卡片模板"""
    template: str = Field(..., description="模板类型: simple/professional/elegant")
    name: str = Field(..., description="模板名称")
    description: str = Field(..., description="模板描述")


class LawyerShareCardTemplatesResponse(BaseModel):
    """律师分享卡片模板列表响应"""
    templates: list[LawyerShareCardTemplate]


class LawyerShareCardURLRequest(BaseModel):
    """律师分享卡片URL请求"""
    template: str = Field(
        default="simple",
        description="模板类型: simple/professional/elegant")


# ============ 律师认证相关 ============

class VerificationCreate(BaseModel):
    """创建律师认证申请"""
    real_name: str = Field(...,
                           min_length=1,
                           max_length=50,
                           description="真实姓名")
    id_card_no: str = Field(...,
                            min_length=18,
                            max_length=18,
                            description="身份证号")
    license_no: str = Field(...,
                            min_length=10,
                            max_length=20,
                            description="执业证号")
    firm_name: str = Field(...,
                           min_length=1,
                           max_length=200,
                           description="所属律所名称")
    id_card_front: str | None = Field(None, description="身份证正面图片URL")
    id_card_back: str | None = Field(None, description="身份证背面图片URL")
    license_photo: str | None = Field(None, description="执业证图片URL")
    specialties: str | None = Field(None, description="专业领域")
    introduction: str | None = Field(None, description="个人简介")
    experience_years: int | None = Field(None, ge=0, le=50, description="执业年限")


class VerificationResponse(BaseModel):
    """律师认证响应"""
    id: int
    user_id: int
    real_name: str
    firm_name: str
    license_no: str
    specialties: str | None
    introduction: str | None
    experience_years: int | None
    status: str
    reject_reason: str | None
    created_at: datetime
    reviewed_at: datetime | None


class VerificationListResponse(BaseModel):
    """律师认证列表响应"""
    items: list[VerificationResponse]
    total: int
    page: int
    page_size: int


class VerificationStatusResponse(BaseModel):
    """认证状态响应"""
    has_verification: bool
    verification_status: str | None
    verification_id: int | None
    submitted_at: datetime | None
    reviewed_at: datetime | None
    reject_reason: str | None
    is_verified_lawyer: bool


# ============ 咨询留言相关 ============

class ConsultationMessageCreate(BaseModel):
    """创建咨询留言"""
    content: str = Field(..., min_length=1, max_length=2000)


class ConsultationMessageResponse(BaseModel):
    """咨询留言响应"""
    id: int
    consultation_id: int
    sender_user_id: int
    sender_role: str
    content: str
    created_at: datetime
    sender_name: str | None = None

    model_config: ClassVar[ConfigDict] = {"from_attributes": True}


class ConsultationMessageListResponse(BaseModel):
    """咨询留言列表响应"""
    items: list[ConsultationMessageResponse]
    total: int
    page: int
    page_size: int
