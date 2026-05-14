/**
 * Lawyer（律师模块）API 层
 * 对接后端 /api/v1/lawfirm 端点
 */

import { apiClient } from '@/shared/lib/api/client';

import type {
  Lawyer,
  LawyerReview,
  LawyerSchedule,
  AvailableSlot,
  Consultation,
  ReviewSummary,
  GetLawyersRequest,
  GetLawyersResponse,
  GetLawyerReviewsResponse,
  GetLawyerScheduleResponse,
  GetAvailableSlotsResponse,
  BookingResponse,
  GetMyConsultationsResponse,
  CreateReviewRequest,
  CreateReviewResponse,
  BookingRequest,
  GetMyConsultationsRequest,
  CancelConsultationResponse,
  GetLawyerRankingResponse,
  LawyerResponseSnake,
  ReviewResponseSnake,
  ScheduleResponseSnake,
  ConsultationResponseSnake,
  ReviewSummaryResponseSnake,
  AvailableSlotResponseSnake,
  LawyerRankingItemSnake,
  // 认证相关
  SubmitVerificationRequest,
  SubmitVerificationResponse,
  VerificationStatusResponse,
  LawyerVerification,
  VerificationResponseSnake,
  VerificationStatusResponseSnake,
  // 主页相关
  LawyerHomepage,
  LawyerHomepagePublic,
  CreateHomepageRequest,
  UpdateHomepageRequest,
  LawyerHomepageResponseSnake,
  LawyerHomepagePublicResponseSnake,
  // 推广链接相关
  LawyerPromotionLink,
  CreatePromotionLinkRequest,
  UpdatePromotionLinkRequest,
  PromotionLinkListResponse,
  PromotionLinkStats,
  PromotionLinkResponseSnake,
  PromotionLinkStatsResponseSnake,
  // 快捷回复模板相关
  LawyerReplyTemplate,
  CreateReplyTemplateRequest,
  UpdateReplyTemplateRequest,
  ReplyTemplateListResponse,
  ReplyTemplateCategoriesResponse,
  UseReplyTemplateResponse,
  ReplyTemplateResponseSnake,
  // 律所管理相关
  LawFirm,
  CreateLawFirmRequest,
  UpdateLawFirmRequest,
  LawFirmResponseSnake,
} from '../types';


// API 基础路径 - 修正为与后端一致
// 后端路由: /lawyers (律师管理), /lawyer/schedules (日程), /consultations (咨询)
const API_BASE = '/lawyers';  // 修正: 后端 prefix="/lawyers"
const REVIEW_API_BASE = '/reviews';
const SCHEDULE_API_BASE = '/lawyer/schedules';
const CONSULTATION_API_BASE = '/consultations';
const LAWFIRM_API_BASE = '/lawfirm';  // 律所基础路径
const VERIFICATION_API_BASE = '/verification';

/** API 错误响应 */
interface ApiErrorResponse {
  detail?: string;
}

/**
 * 获取 API 错误信息
 */
function _getErrorMessage(error: unknown, defaultMsg: string): string {
  if (typeof error === 'object' && error !== null && 'detail' in error) {
    return (error as ApiErrorResponse).detail || defaultMsg;
  }
  return defaultMsg;
}

/**
 * 转换律师数据 snake_case → camelCase
 */
function transformLawyer(data: LawyerResponseSnake): Lawyer {
  return {
    id: String(data.id),
    userId: data.user_id ? String(data.user_id) : null,
    firmId: data.firm_id ? String(data.firm_id) : null,
    name: data.name,
    avatar: data.avatar,
    title: data.title,
    licenseNo: data.license_no,
    phone: data.phone,
    email: data.email,
    introduction: data.introduction,
    specialties: data.specialties,
    experienceYears: data.experience_years,
    caseCount: data.case_count,
    rating: data.rating,
    reviewCount: data.review_count,
    consultationFee: data.consultation_fee,
    isVerified: data.is_verified,
    isActive: data.is_active,
    createdAt: data.created_at,
    firmName: data.firm_name,
  };
}

/**
 * 转换评价数据 snake_case → camelCase
 */
function transformReview(data: ReviewResponseSnake): LawyerReview {
  return {
    id: String(data.id),
    lawyerId: String(data.lawyer_id),
    userId: String(data.user_id),
    consultationId: data.consultation_id ? String(data.consultation_id) : null,
    rating: data.rating,
    content: data.content,
    isAnonymous: data.is_anonymous,
    professionalism: data.professionalism,
    responsiveness: data.responsiveness,
    attitude: data.attitude,
    tags: data.tags ?? [],
    createdAt: data.created_at,
    username: data.username,
  };
}

/**
 * 转换日程数据 snake_case → camelCase
 */
function transformSchedule(data: ScheduleResponseSnake): LawyerSchedule {
  return {
    id: String(data.id),
    lawyerId: String(data.lawyer_id),
    date: data.date,
    startTime: data.start_time,
    endTime: data.end_time,
    isAvailable: data.is_available,
    consultationId: data.consultation_id ? String(data.consultation_id) : null,
    note: data.note,
    createdAt: data.created_at,
    updatedAt: data.updated_at,
  };
}

/**
 * 转换咨询数据 snake_case → camelCase
 */
function transformConsultation(data: ConsultationResponseSnake): Consultation {
  return {
    id: String(data.id),
    userId: String(data.user_id),
    lawyerId: String(data.lawyer_id),
    subject: data.subject,
    description: data.description,
    category: data.category,
    contactPhone: data.contact_phone,
    preferredTime: data.preferred_time,
    status: data.status as 'pending' | 'confirmed' | 'completed' | 'cancelled',
    adminNote: data.admin_note,
    createdAt: data.created_at,
    updatedAt: data.updated_at,
    lawyerName: data.lawyer_name,
    paymentOrderNo: data.payment_order_no,
    paymentStatus: data.payment_status,
    paymentAmount: data.payment_amount,
    reviewId: data.review_id ? String(data.review_id) : null,
    canReview: data.can_review,
  };
}

/**
 * 转换评价摘要数据 snake_case → camelCase
 */
function transformReviewSummary(data: ReviewSummaryResponseSnake): ReviewSummary {
  return {
    lawyerId: String(data.lawyer_id),
    lawyerName: data.lawyer_name,
    totalReviews: data.total_reviews,
    averageRating: data.average_rating,
    dimensionStats: {
      professionalismAvg: data.dimension_stats.professionalism_avg,
      responsivenessAvg: data.dimension_stats.responsiveness_avg,
      attitudeAvg: data.dimension_stats.attitude_avg,
    },
    ratingDistribution: {
      rating5Count: data.rating_distribution.rating_5_count,
      rating4Count: data.rating_distribution.rating_4_count,
      rating3Count: data.rating_distribution.rating_3_count,
      rating2Count: data.rating_distribution.rating_2_count,
      rating1Count: data.rating_distribution.rating_1_count,
    },
    tagStats: data.tag_stats,
    popularTags: data.popular_tags,
  };
}

/**
 * 转换可用时段数据 snake_case → camelCase
 */
function transformAvailableSlot(data: AvailableSlotResponseSnake): AvailableSlot {
  return {
    date: data.date,
    startTime: data.start_time,
    endTime: data.end_time,
  };
}

/**
 * 转换认证数据 snake_case → camelCase
 */
function _transformVerification(data: VerificationResponseSnake): LawyerVerification {
  return {
    id: String(data.id),
    userId: String(data.user_id),
    realName: data.real_name,
    idCardNo: data.id_card_no,
    licenseNo: data.license_no,
    firmName: data.firm_name,
    idCardFront: data.id_card_front,
    idCardBack: data.id_card_back,
    licensePhoto: data.license_photo,
    specialties: data.specialties,
    introduction: data.introduction,
    experienceYears: data.experience_years,
    status: data.status as 'pending' | 'approved' | 'rejected',
    rejectReason: data.reject_reason,
    createdAt: data.created_at,
    reviewedAt: data.reviewed_at,
  };
}

/**
 * 转换认证状态数据 snake_case → camelCase
 */
function transformVerificationStatus(data: VerificationStatusResponseSnake): VerificationStatusResponse {
  return {
    hasVerification: data.has_verification,
    verificationStatus: data.verification_status as 'pending' | 'approved' | 'rejected' | null,
    verificationId: data.verification_id,
    submittedAt: data.submitted_at,
    reviewedAt: data.reviewed_at,
    rejectReason: data.reject_reason,
    isVerifiedLawyer: data.is_verified_lawyer,
  };
}

/**
 * 转换主页数据 snake_case → camelCase
 */
function transformHomepage(data: LawyerHomepageResponseSnake): LawyerHomepage {
  return {
    id: String(data.id),
    lawyerId: String(data.lawyer_id),
    bannerImage: data.banner_image,
    profileImage: data.profile_image,
    slogan: data.slogan,
    bio: data.bio,
    specialtiesDisplay: data.specialties_display,
    achievements: data.achievements,
    education: data.education,
    serviceAreas: data.service_areas,
    serviceHours: data.service_hours,
    responseTime: data.response_time,
    contactPhone: data.contact_phone,
    contactEmail: data.contact_email,
    wechatQrcode: data.wechat_qrcode,
    weiboUrl: data.weibo_url,
    linkedinUrl: data.linkedin_url,
    zhihuUrl: data.zhihu_url,
    caseStudies: data.case_studies,
    videoUrl: data.video_url,
    videoCover: data.video_cover,
    seoTitle: data.seo_title,
    seoDescription: data.seo_description,
    seoKeywords: data.seo_keywords,
    themeColor: data.theme_color,
    backgroundColor: data.background_color,
    isPublished: data.is_published,
    viewCount: data.view_count,
    createdAt: data.created_at,
    updatedAt: data.updated_at,
  };
}

/**
 * 转换主页公开数据 snake_case → camelCase
 */
function transformHomepagePublic(data: LawyerHomepagePublicResponseSnake): LawyerHomepagePublic {
  // 从后端数据构建公开主页数据
  // 注意：这里假设后端返回的数据结构，实际可能需要根据后端API调整
  return {
    name: data.lawyer_name || '',
    avatarUrl: data.lawyer_avatar,
    title: data.lawyer_title,
    firmName: null, // 需要从其他API获取
    location: data.service_areas,
    isVerified: true, // 公开主页默认为已认证律师
    phone: data.contact_phone,
    email: data.contact_email,
    weixin: data.wechat_qrcode,
    bio: data.bio,
    specialties: data.lawyer_specialties ? data.lawyer_specialties.split(',').map(s => s.trim()).filter(Boolean) : [],
    cases: [], // 需要从其他API获取
    reviews: [], // 需要从其他API获取
    consultationCount: 0,
    reviewCount: data.lawyer_review_count || 0,
    responseRate: 0,
  };
}

/**
 * 转换推广链接数据 snake_case → camelCase
 */
function transformPromotionLink(data: PromotionLinkResponseSnake): LawyerPromotionLink {
  return {
    id: String(data.id),
    lawyerId: String(data.lawyer_id),
    linkCode: data.link_code,
    linkName: data.link_name,
    description: data.description,
    isActive: data.is_active,
    clickCount: data.click_count,
    consultationCount: data.consultation_count,
    conversionCount: data.conversion_count,
    createdAt: data.created_at,
    updatedAt: data.updated_at,
  };
}

/**
 * 转换推广链接统计数据 snake_case → camelCase
 */
function transformPromotionLinkStats(data: PromotionLinkStatsResponseSnake): PromotionLinkStats {
  return {
    linkId: String(data.link_id),
    linkCode: data.link_code,
    linkName: data.link_name,
    clickCount: data.click_count,
    consultationCount: data.consultation_count,
    conversionCount: data.conversion_count,
    conversionRate: data.conversion_rate,
  };
}

/**
 * 转换快捷回复模板数据 snake_case → camelCase
 */
function transformReplyTemplate(data: ReplyTemplateResponseSnake): LawyerReplyTemplate {
  return {
    id: String(data.id),
    lawyerId: String(data.lawyer_id),
    title: data.title,
    content: data.content,
    category: data.category,
    isActive: data.is_active,
    useCount: data.use_count,
    createdAt: data.created_at,
    updatedAt: data.updated_at,
  };
}

// ==================== 基础律师API ====================

/**
 * 获取律师列表
 * 注意：修正API基础路径
 */
export async function getLawyers(params: GetLawyersRequest = {}): Promise<GetLawyersResponse> {
  const { data } = await apiClient.get<{
    items: LawyerResponseSnake[];
    total: number;
    page: number;
    page_size: number;
  }>(`/lawyers`, {  // 修正: 后端 prefix="/lawyers"
    params: {
      ...(params.page && { page: params.page }),
      ...(params.pageSize && { page_size: params.pageSize }),
      ...(params.firmId && { firm_id: params.firmId }),
      ...(params.specialty && { specialty: params.specialty }),
      ...(params.keyword && { keyword: params.keyword }),
    },
  });

  return {
    lawyers: data.items.map(transformLawyer),
    total: data.total,
    page: data.page,
    pageSize: data.page_size,
  };
}

/**
 * 获取律师详情
 * 注意：修正API路径
 */
export async function getLawyer(lawyerId: string): Promise<Lawyer> {
  const { data } = await apiClient.get<LawyerResponseSnake>(`/lawyers/${lawyerId}`);
  return transformLawyer(data);
}

/**
 * 获取律师评价列表
 * 注意：修正API路径 - 后端使用 /reviews 前缀
 */
export async function getLawyerReviews(
  lawyerId: string,
  params: { page?: number; pageSize?: number } = {}
): Promise<GetLawyerReviewsResponse> {
  const { data } = await apiClient.get<{
    items: ReviewResponseSnake[];
    total: number;
    page: number;
    page_size: number;
    average_rating: number;
  }>(`/reviews`, {  // 修正: 后端 reviews 路由 prefix="/reviews"
    params: {
      lawyer_id: lawyerId,  // 添加律师ID参数
      ...(params.page && { page: params.page }),
      ...(params.pageSize && { page_size: params.pageSize }),
    },
  });

  return {
    reviews: data.items.map(transformReview),
    total: data.total,
    page: data.page,
    pageSize: data.page_size,
    averageRating: data.average_rating,
  };
}

/**
 * 创建评价
 */
export async function createReview(request: CreateReviewRequest): Promise<CreateReviewResponse> {
  const response = await apiClient.post<ReviewResponseSnake>(`${API_BASE}/${request.lawyerId}/reviews`, {
    lawyer_id: Number(request.lawyerId),
    consultation_id: Number(request.consultationId),
    rating: request.rating,
    content: request.content,
    is_anonymous: request.isAnonymous ?? false,
    professionalism: request.professionalism,
    responsiveness: request.responsiveness,
    attitude: request.attitude,
    tags: request.tags,
  });

  return {
    review: transformReview(response.data),
  };
}

/**
 * 获取律师日程
 * 注意：修正API路径与后端对齐 - 后端使用 /lawyer/schedules 前缀
 */
export async function getLawyerSchedule(
  lawyerId: string,
  params: { dateFrom?: string; dateTo?: string; page?: number; pageSize?: number } = {}
): Promise<GetLawyerScheduleResponse> {
  const { data } = await apiClient.get<{
    items: ScheduleResponseSnake[];
    total: number;
    page: number;
    page_size: number;
  }>(`/lawyer/schedules`, {  // 修正：后端 prefix="/lawyer/schedules"
    params: {
      ...(params.dateFrom && { date_from: params.dateFrom }),
      ...(params.dateTo && { date_to: params.dateTo }),
      ...(params.page && { page: params.page }),
      ...(params.pageSize && { page_size: params.pageSize }),
    },
  });

  return {
    schedules: data.items.map(transformSchedule),
    total: data.total,
    page: data.page,
    pageSize: data.page_size,
  };
}

/**
 * 获取律师可用时段
 */
export async function getLawyerAvailableSlots(lawyerId: string, date: string): Promise<GetAvailableSlotsResponse> {
  const { data } = await apiClient.get<{
    lawyer_id: number;
    date: string;
    slots: AvailableSlotResponseSnake[];
  }>(`${API_BASE}/${lawyerId}/available-slots`, {
    params: { date },
  });

  return {
    lawyerId: String(data.lawyer_id),
    date: data.date,
    slots: data.slots.map(transformAvailableSlot),
  };
}

/**
 * 创建预约
 */
export async function createBooking(request: BookingRequest): Promise<BookingResponse> {
  const response = await apiClient.post<ConsultationResponseSnake & {
    payment_order_no: string | null;
    payment_status: string | null;
    payment_amount: number | null;
  }>(`${LAWFIRM_API_BASE}/consultations`, {
    lawyer_id: Number(request.lawyerId),
    subject: request.subject,
    description: request.description,
    category: request.category,
    contact_phone: request.contactPhone,
    preferred_time: request.preferredTime,
  });

  const data = response.data;

  return {
    consultation: transformConsultation(data),
    paymentOrderNo: data.payment_order_no,
    paymentStatus: data.payment_status,
    paymentAmount: data.payment_amount,
  };
}

/**
 * 获取我的咨询列表
 */
export async function getMyConsultations(params: GetMyConsultationsRequest = {}): Promise<GetMyConsultationsResponse> {
  const { data } = await apiClient.get<{
    items: ConsultationResponseSnake[];
    total: number;
    page: number;
    page_size: number;
  }>(`${CONSULTATION_API_BASE}`, {
    params: {
      ...(params.page && { page: params.page }),
      ...(params.pageSize && { page_size: params.pageSize }),
      ...(params.statusFilter && { status_filter: params.statusFilter }),
    },
  });

  return {
    consultations: data.items.map(transformConsultation),
    total: data.total,
    page: data.page,
    pageSize: data.page_size,
  };
}

/**
 * 取消咨询
 */
export async function cancelConsultation(consultationId: string): Promise<CancelConsultationResponse> {
  const response = await apiClient.post<ConsultationResponseSnake>(`${CONSULTATION_API_BASE}/${consultationId}/cancel`);

  return {
    consultation: transformConsultation(response.data),
  };
}

/**
 * 获取律师排行榜
 */
export async function getLawyerRanking(limit: number = 10, period?: string): Promise<GetLawyerRankingResponse> {
  const { data } = await apiClient.get<{
    metric: string;
    days: number;
    items: LawyerRankingItemSnake[];
  }>(`${API_BASE}/ranking`, {
    params: {
      limit,
      ...(period && { period }),
    },
  });

  return {
    metric: data.metric,
    days: data.days,
    lawyers: data.items.map(item => ({
      lawyerId: String(item.lawyer_id),
      lawyerName: item.lawyer_name,
      rating: item.rating,
      value: item.value,
    })),
  };
}

/**
 * 获取律师评价摘要
 */
export async function getLawyerReviewSummary(lawyerId: string): Promise<ReviewSummary> {
  const { data } = await apiClient.get<ReviewSummaryResponseSnake>(`${API_BASE}/${lawyerId}/reviews/summary`);
  return transformReviewSummary(data);
}

// ==================== 律师认证API ====================

/**
 * 提交律师认证申请
 */
export async function submitVerification(request: SubmitVerificationRequest): Promise<SubmitVerificationResponse> {
  const response = await apiClient.post<SubmitVerificationResponse>(`${VERIFICATION_API_BASE}/submit`, {
    real_name: request.realName,
    id_card_no: request.idCardNo,
    license_no: request.licenseNo,
    firm_name: request.firmName,
    id_card_front: request.idCardFront,
    id_card_back: request.idCardBack,
    license_photo: request.licensePhoto,
    specialties: request.specialties,
    introduction: request.introduction,
    experience_years: request.experienceYears,
  });

  return response.data;
}

/**
 * 获取认证状态
 */
export async function getVerificationStatus(): Promise<VerificationStatusResponse> {
  const { data } = await apiClient.get<VerificationStatusResponseSnake>(`${VERIFICATION_API_BASE}/status`);
  return transformVerificationStatus(data);
}

// ==================== 律师主页API ====================

/**
 * 获取我的律师主页
 */
export async function getMyHomepage(lawyerId: string): Promise<LawyerHomepage> {
  const { data } = await apiClient.get<LawyerHomepageResponseSnake>(`${API_BASE}/${lawyerId}/homepage`);
  return transformHomepage(data);
}

/**
 * 创建律师主页
 */
export async function createHomepage(lawyerId: string, request: CreateHomepageRequest): Promise<LawyerHomepage> {
  const response = await apiClient.post<LawyerHomepageResponseSnake>(`${API_BASE}/${lawyerId}/homepage`, {
    banner_image: request.bannerImage,
    profile_image: request.profileImage,
    slogan: request.slogan,
    bio: request.bio,
    specialties_display: request.specialtiesDisplay,
    achievements: request.achievements,
    education: request.education,
    service_areas: request.serviceAreas,
    service_hours: request.serviceHours,
    response_time: request.responseTime,
    contact_phone: request.contactPhone,
    contact_email: request.contactEmail,
    wechat_qrcode: request.wechatQrcode,
    weibo_url: request.weiboUrl,
    linkedin_url: request.linkedinUrl,
    zhihu_url: request.zhihuUrl,
    case_studies: request.caseStudies,
    video_url: request.videoUrl,
    video_cover: request.videoCover,
    seo_title: request.seoTitle,
    seo_description: request.seoDescription,
    seo_keywords: request.seoKeywords,
    theme_color: request.themeColor,
    background_color: request.backgroundColor,
    is_published: request.isPublished,
  });

  return transformHomepage(response.data);
}

/**
 * 更新律师主页
 */
export async function updateHomepage(lawyerId: string, request: UpdateHomepageRequest): Promise<LawyerHomepage> {
  const response = await apiClient.put<LawyerHomepageResponseSnake>(`${API_BASE}/${lawyerId}/homepage`, {
    banner_image: request.bannerImage,
    profile_image: request.profileImage,
    slogan: request.slogan,
    bio: request.bio,
    specialties_display: request.specialtiesDisplay,
    achievements: request.achievements,
    education: request.education,
    service_areas: request.serviceAreas,
    service_hours: request.serviceHours,
    response_time: request.responseTime,
    contact_phone: request.contactPhone,
    contact_email: request.contactEmail,
    wechat_qrcode: request.wechatQrcode,
    weibo_url: request.weiboUrl,
    linkedin_url: request.linkedinUrl,
    zhihu_url: request.zhihuUrl,
    case_studies: request.caseStudies,
    video_url: request.videoUrl,
    video_cover: request.videoCover,
    seo_title: request.seoTitle,
    seo_description: request.seoDescription,
    seo_keywords: request.seoKeywords,
    theme_color: request.themeColor,
    background_color: request.backgroundColor,
    is_published: request.isPublished,
  });

  return transformHomepage(response.data);
}

/**
 * 发布律师主页
 */
export async function publishHomepage(lawyerId: string): Promise<LawyerHomepage> {
  const response = await apiClient.post<LawyerHomepageResponseSnake>(`${API_BASE}/${lawyerId}/homepage/publish`);
  return transformHomepage(response.data);
}

/**
 * 取消发布律师主页
 */
export async function unpublishHomepage(lawyerId: string): Promise<LawyerHomepage> {
  const response = await apiClient.post<LawyerHomepageResponseSnake>(`${API_BASE}/${lawyerId}/homepage/unpublish`);
  return transformHomepage(response.data);
}

/**
 * 获取律师公开主页
 */
export async function getPublicHomepage(lawyerId: string): Promise<LawyerHomepagePublic> {
  const { data } = await apiClient.get<LawyerHomepagePublicResponseSnake>(`${API_BASE}/${lawyerId}/homepage/public`);
  return transformHomepagePublic(data);
}

// ==================== 推广链接API ====================

/**
 * 获取推广链接列表
 */
export async function getPromotionLinks(
  lawyerId: string,
  params: {
    isActive?: boolean;
    page?: number;
    pageSize?: number;
  } = {}
): Promise<PromotionLinkListResponse> {
  const { data } = await apiClient.get<{
    items: PromotionLinkResponseSnake[];
    total: number;
    page: number;
    page_size: number;
  }>(`${API_BASE}/${lawyerId}/promotion-links`, {
    params: {
      ...(params.isActive !== undefined && { is_active: params.isActive }),
      ...(params.page && { page: params.page }),
      ...(params.pageSize && { page_size: params.pageSize }),
    },
  });

  return {
    items: data.items.map(transformPromotionLink),
    total: data.total,
    page: data.page,
    pageSize: data.page_size,
  };
}

/**
 * 创建推广链接
 */
export async function createPromotionLink(
  lawyerId: string,
  request: CreatePromotionLinkRequest
): Promise<LawyerPromotionLink> {
  const response = await apiClient.post<PromotionLinkResponseSnake>(`${API_BASE}/${lawyerId}/promotion-links`, {
    link_name: request.linkName,
    description: request.description,
  });

  return transformPromotionLink(response.data);
}

/**
 * 获取推广链接详情
 */
export async function getPromotionLink(lawyerId: string, linkId: string): Promise<LawyerPromotionLink> {
  const response = await apiClient.get<PromotionLinkResponseSnake>(`${API_BASE}/${lawyerId}/promotion-links/${linkId}`);
  return transformPromotionLink(response.data);
}

/**
 * 更新推广链接
 */
export async function updatePromotionLink(
  linkId: string,
  request: UpdatePromotionLinkRequest
): Promise<LawyerPromotionLink> {
  const response = await apiClient.put<PromotionLinkResponseSnake>(`${LAWFIRM_API_BASE}/lawyer/promotion-links/${linkId}`, {
    link_name: request.linkName,
    description: request.description,
    is_active: request.isActive,
  });

  return transformPromotionLink(response.data);
}

/**
 * 删除推广链接
 */
export async function deletePromotionLink(linkId: string): Promise<void> {
  await apiClient.delete(`${LAWFIRM_API_BASE}/lawyer/promotion-links/${linkId}`);
}

/**
 * 获取推广链接统计
 */
export async function getPromotionLinkStats(linkId: string): Promise<PromotionLinkStats> {
  const { data } = await apiClient.get<PromotionLinkStatsResponseSnake>(`${LAWFIRM_API_BASE}/lawyer/promotion-links/stats/${linkId}`);
  return transformPromotionLinkStats(data);
}

// ==================== 快捷回复模板API ====================

/**
 * 获取快捷回复模板列表
 */
export async function getReplyTemplates(params: {
  category?: string;
  isActive?: boolean;
  page?: number;
  pageSize?: number;
} = {}): Promise<ReplyTemplateListResponse> {
  const { data } = await apiClient.get<{
    items: ReplyTemplateResponseSnake[];
    total: number;
    page: number;
    page_size: number;
  }>(`${LAWFIRM_API_BASE}/lawyer/reply-templates`, {
    params: {
      ...(params.category && { category: params.category }),
      ...(params.isActive !== undefined && { is_active: params.isActive }),
      ...(params.page && { page: params.page }),
      ...(params.pageSize && { page_size: params.pageSize }),
    },
  });

  return {
    items: data.items.map(transformReplyTemplate),
    total: data.total,
    page: data.page,
    pageSize: data.page_size,
  };
}

/**
 * 获取模板分类列表
 */
export async function getReplyTemplateCategories(): Promise<ReplyTemplateCategoriesResponse> {
  const { data } = await apiClient.get<ReplyTemplateCategoriesResponse>(`${LAWFIRM_API_BASE}/lawyer/reply-templates/categories`);
  return data;
}

/**
 * 创建快捷回复模板
 */
export async function createReplyTemplate(request: CreateReplyTemplateRequest): Promise<LawyerReplyTemplate> {
  const response = await apiClient.post<ReplyTemplateResponseSnake>(`${LAWFIRM_API_BASE}/lawyer/reply-templates`, {
    title: request.title,
    content: request.content,
    category: request.category,
  });

  return transformReplyTemplate(response.data);
}

/**
 * 获取快捷回复模板详情
 */
export async function getReplyTemplate(templateId: string): Promise<LawyerReplyTemplate> {
  const response = await apiClient.get<ReplyTemplateResponseSnake>(`${LAWFIRM_API_BASE}/lawyer/reply-templates/${templateId}`);
  return transformReplyTemplate(response.data);
}

/**
 * 更新快捷回复模板
 */
export async function updateReplyTemplate(
  templateId: string,
  request: UpdateReplyTemplateRequest
): Promise<LawyerReplyTemplate> {
  const response = await apiClient.put<ReplyTemplateResponseSnake>(`${LAWFIRM_API_BASE}/lawyer/reply-templates/${templateId}`, {
    title: request.title,
    content: request.content,
    category: request.category,
    is_active: request.isActive,
  });

  return transformReplyTemplate(response.data);
}

/**
 * 删除快捷回复模板
 */
export async function deleteReplyTemplate(templateId: string): Promise<void> {
  await apiClient.delete(`${LAWFIRM_API_BASE}/lawyer/reply-templates/${templateId}`);
}

/**
 * 使用快捷回复模板
 */
export async function useReplyTemplate(templateId: string): Promise<UseReplyTemplateResponse> {
  const response = await apiClient.post<UseReplyTemplateResponse>(`${LAWFIRM_API_BASE}/lawyer/reply-templates/${templateId}/use`);
  return response.data;
}

// ==================== 管理员认证管理API ====================

/**
 * 转换认证数据 snake_case → camelCase
 */
function transformVerification(data: VerificationResponseSnake): LawyerVerification {
  return {
    id: String(data.id),
    userId: String(data.user_id),
    realName: data.real_name,
    idCardNo: data.id_card_no,
    licenseNo: data.license_no,
    firmName: data.firm_name,
    idCardFront: data.id_card_front,
    idCardBack: data.id_card_back,
    licensePhoto: data.license_photo,
    specialties: data.specialties,
    introduction: data.introduction,
    experienceYears: data.experience_years,
    status: data.status as 'pending' | 'approved' | 'rejected',
    rejectReason: data.reject_reason,
    createdAt: data.created_at,
    reviewedAt: data.reviewed_at,
  };
}

interface GetVerificationListParams {
  page?: number;
  pageSize?: number;
  status?: 'pending' | 'approved' | 'rejected';
  keyword?: string;
}

/**
 * 获取认证列表（管理员用）
 */
export async function getVerificationList(params: GetVerificationListParams = {}): Promise<{
  items: LawyerVerification[];
  total: number;
  page: number;
  pageSize: number;
}> {
  const { data } = await apiClient.get<{
    items: VerificationResponseSnake[];
    total: number;
    page: number;
    page_size: number;
  }>(`${VERIFICATION_API_BASE}/list`, {
    params: {
      ...(params.page && { page: params.page }),
      ...(params.pageSize && { page_size: params.pageSize }),
      ...(params.status && { status: params.status }),
      ...(params.keyword && { keyword: params.keyword }),
    },
  });

  return {
    items: data.items.map(transformVerification),
    total: data.total,
    page: data.page,
    pageSize: data.page_size,
  };
}

interface ReviewVerificationRequest {
  approved: boolean;
  rejectReason?: string;
}

/**
 * 审核认证申请（管理员用）
 */
export async function reviewVerification(
  id: string,
  request: ReviewVerificationRequest
): Promise<LawyerVerification> {
  const response = await apiClient.post<VerificationResponseSnake>(`${VERIFICATION_API_BASE}/${id}/review`, {
    approved: request.approved,
    reject_reason: request.rejectReason,
  });

  return transformVerification(response.data);
}

// ==================== 律所管理API ====================

/**
 * 转换律所数据 snake_case → camelCase
 */
function transformLawFirm(data: LawFirmResponseSnake): LawFirm {
  return {
    id: String(data.id),
    name: data.name,
    city: data.city,
    phone: data.phone,
    address: data.address,
    description: data.description,
    isVerified: data.is_verified,
    isActive: data.is_active,
    lawyerCount: data.lawyer_count,
    rating: data.rating,
    createdAt: data.created_at,
  };
}

interface GetLawFirmsParams {
  keyword?: string;
  includeInactive?: boolean;
}

/**
 * 获取律所列表（管理员用）
 */
export async function getLawFirms(params: GetLawFirmsParams = {}): Promise<LawFirm[]> {
  const { data } = await apiClient.get<{ items: LawFirmResponseSnake[] }>(`${LAWFIRM_API_BASE}/admin/firms`, {
    params: {
      ...(params.includeInactive && { include_inactive: 'true' }),
      ...(params.keyword && { keyword: params.keyword }),
    },
  });
  return (data.items ?? []).map(transformLawFirm);
}

/**
 * 创建律所（管理员用）
 */
export async function createLawFirm(request: CreateLawFirmRequest): Promise<LawFirm> {
  const response = await apiClient.post<LawFirmResponseSnake>(`${LAWFIRM_API_BASE}/admin/firms`, {
    name: request.name,
    city: request.city,
    phone: request.phone,
    address: request.address,
    description: request.description,
  });

  return transformLawFirm(response.data);
}

/**
 * 更新律所（管理员用）
 */
export async function updateLawFirm(id: string, request: UpdateLawFirmRequest): Promise<LawFirm> {
  const response = await apiClient.put<LawFirmResponseSnake>(`${LAWFIRM_API_BASE}/admin/firms/${id}`, {
    name: request.name,
    city: request.city,
    phone: request.phone,
    address: request.address,
    description: request.description,
  });

  return transformLawFirm(response.data);
}

/**
 * 删除律所（管理员用）
 */
export async function deleteLawFirm(id: string): Promise<void> {
  await apiClient.delete(`${LAWFIRM_API_BASE}/admin/firms/${id}`);
}

/**
 * 验证律所（管理员用）
 */
export async function verifyLawFirm(id: string, verified: boolean): Promise<LawFirm> {
  const response = await apiClient.post<LawFirmResponseSnake>(`${LAWFIRM_API_BASE}/admin/firms/${id}/verify`, {
    verified,
  });

  return transformLawFirm(response.data);
}

/**
 * 启用/禁用律所（管理员用）
 */
export async function toggleLawFirmActive(id: string, isActive: boolean): Promise<LawFirm> {
  const response = await apiClient.post<LawFirmResponseSnake>(`${LAWFIRM_API_BASE}/admin/firms/${id}/active`, {
    is_active: isActive,
  });

  return transformLawFirm(response.data);
}