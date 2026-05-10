/**
 * Lawyer-Matching（律师匹配）API 层
 *
 * 使用统一的 apiClient 进行 HTTP 请求
 * 后端路由: /api/v1/lawyer-recommendation, /api/v1/lawfirm
 */

import { apiClient } from "@/shared/lib/api/client";

import type {
  GetRecommendationsRequest,
  GetRecommendationsResponse,
  GetLawyerDetailRequest,
  GetLawyerDetailResponse,
  CreateBookingRequest,
  CreateBookingResponse,
  GetBookingsRequest,
  GetBookingsResponse,
  CancelBookingRequest,
  CancelBookingResponse,
  GetReviewsRequest,
  GetReviewsResponse,
  SubmitReviewRequest,
  SubmitReviewResponse,
  SearchLawyersRequest,
  SearchLawyersResponse,
  GetOnlineStatusRequest,
  GetOnlineStatusResponse,
  LawyerOnlineInfo,
  Lawyer,
  LawyerDetail,
  LawyerMatchResult,
  Booking,
  LawyerReview,
  ReviewStats,
  ReviewDimensions,
} from '../types';


// API 基础路径
const RECOMMENDATION_BASE = '/lawyer-recommendation';
const LAWFIRM_BASE = '/lawfirm';

// ==================== 后端响应类型定义 ====================

/** 后端律师基础数据 */
interface BackendLawyerBase {
  id: number | string;
  name: string;
  avatar?: string;
  title?: string;
  firm_name?: string;
  specialties: string[];
  rating: number;
  completed_count: number;
  status: 'online' | 'offline' | 'busy';
  is_verified: boolean;
}

/** 后端律师详情数据 */
interface BackendLawyerDetail extends BackendLawyerBase {
  phone?: string;
  email?: string;
  introduction?: string;
  experience?: number;
  education?: string[];
  certifications?: string[];
  cases_handled?: number;
  languages?: string[];
  working_hours?: string;
  firm_name?: string;
  license_no?: string;
  experience_years?: number;
  case_count?: number;
  review_count?: number;
  consultation_fee?: number;
}

/** 后端推荐结果数据 */
interface BackendMatchResult {
  lawyer_id: string;
  lawyer_name: string;
  specialties: string;
  rating: number;
  completed_count: number;
  match_score: number;
  overall_score: number;
  match_reasons: string[];
  response_time_score?: number;
  case_similarity_score?: number;
  is_cold_start?: boolean;
  experiment_group?: string;
}

/** 后端预约/咨询数据 */
interface BackendConsultation {
  id: number | string;
  lawyer_id: number | string;
  lawyer_name?: string;
  user_id: number | string;
  subject: string;
  description?: string;
  category?: string;
  contact_phone?: string;
  preferred_time?: string;
  status: 'pending' | 'confirmed' | 'completed' | 'cancelled';
  admin_note?: string;
  created_at: string;
  updated_at: string;
  payment_order_no?: string;
  payment_status?: string;
  payment_amount?: number;
  review_id?: number;
  can_review?: boolean;
}

/** 后端评价维度数据 */
interface BackendReviewDimensions {
  professionalism: number;
  responsiveness: number;
  attitude: number;
  value_for_money?: number;
}

/** 后端评价数据 */
interface BackendReview {
  id: number | string;
  lawyer_id: number | string;
  user_id: number | string;
  user_name?: string;
  user_avatar?: string;
  consultation_id: number | string;
  rating: number;
  professionalism?: number;
  responsiveness?: number;
  attitude?: number;
  dimensions?: BackendReviewDimensions;
  content: string;
  tags?: string[];
  is_anonymous: boolean;
  is_recommended?: boolean;
  created_at: string;
  reply_content?: string;
  replied_at?: string;
}

/** 后端评价统计数据 */
interface BackendReviewStats {
  lawyer_id: number | string;
  total_reviews: number;
  average_rating: number;
  average_dimensions?: BackendReviewDimensions;
  rating_distribution?: Record<string, number>;
  tag_stats?: Record<string, number>;
  dimension_stats?: Record<string, number>;
}

/** 后端在线状态数据 */
interface BackendOnlineStatus {
  lawyer_id: string;
  status: 'online' | 'offline' | 'busy';
  last_active_at?: string;
  current_consultation_count?: number;
  estimated_wait_time?: number;
}

/** 后端律师推荐响应 */
interface BackendRecommendResponse {
  query?: string;
  keywords?: string[];
  domains?: string[];
  algorithm?: string;
  experiment_id?: string | null;
  count: number;
  lawyers: BackendMatchResult[];
}

/** 后端律师列表响应 */
interface BackendLawyerListResponse {
  items: BackendLawyerDetail[];
  total: number;
  page: number;
  page_size: number;
}

/** 后端咨询列表响应 */
interface BackendConsultationListResponse {
  items: BackendConsultation[];
  total: number;
  page: number;
  page_size: number;
}

/** 后端评价列表响应 */
interface BackendReviewListResponse {
  items: BackendReview[];
  total: number;
  page: number;
  page_size: number;
  average_rating?: number;
}

// ==================== 数据转换函数 ====================

/**
 * 转换后端律师基础数据为前端格式
 */
function transformLawyerBase(backend: BackendLawyerBase): Lawyer {
  return {
    id: String(backend.id),
    name: backend.name,
    avatar: backend.avatar,
    title: backend.title,
    firmName: backend.firm_name,
    specialties: typeof backend.specialties === 'string'
      ? (backend.specialties as string).split(',').map((s: string) => s.trim())
      : Array.isArray(backend.specialties)
        ? backend.specialties
        : [],
    rating: backend.rating,
    completedCount: backend.completed_count,
    status: backend.status,
    isVerified: backend.is_verified,
  };
}

/**
 * 转换后端律师详情数据为前端格式
 */
function transformLawyerDetail(backend: BackendLawyerDetail): LawyerDetail {
  return {
    ...transformLawyerBase(backend),
    phone: backend.phone,
    email: backend.email,
    introduction: backend.introduction,
    experience: backend.experience_years || backend.experience || 0,
    education: backend.education,
    certifications: backend.certifications,
    casesHandled: backend.case_count || backend.cases_handled,
    languages: backend.languages,
    workingHours: backend.working_hours,
  };
}

/**
 * 转换后端推荐结果为前端格式
 */
function transformMatchResult(backend: BackendMatchResult): LawyerMatchResult {
  return {
    lawyerId: backend.lawyer_id,
    lawyerName: backend.lawyer_name,
    specialties: backend.specialties.split(',').map((s: string) => s.trim()),
    rating: backend.rating,
    completedCount: backend.completed_count,
    matchScore: backend.match_score,
    overallScore: backend.overall_score,
    matchReasons: backend.match_reasons,
  };
}

/**
 * 转换后端咨询数据为预约格式
 */
function transformConsultationToBooking(backend: BackendConsultation): Booking {
  return {
    id: String(backend.id),
    lawyerId: String(backend.lawyer_id),
    lawyerName: backend.lawyer_name || '',
    userId: String(backend.user_id),
    consultationType: 'online',
    scheduledTime: backend.preferred_time || backend.created_at,
    duration: 60,
    status: backend.status,
    topic: backend.subject,
    description: backend.description,
    price: backend.payment_amount || 0,
    createdAt: backend.created_at,
    updatedAt: backend.updated_at,
  };
}

/**
 * 转换后端评价维度为前端格式
 */
function transformReviewDimensions(backend?: BackendReviewDimensions): ReviewDimensions {
  return {
    professionalism: backend?.professionalism ?? 0,
    responsiveness: backend?.responsiveness ?? 0,
    attitude: backend?.attitude ?? 0,
    valueForMoney: backend?.value_for_money ?? 0,
  };
}

/**
 * 转换后端评价数据为前端格式
 */
function transformReview(backend: BackendReview): LawyerReview {
  const dimensions = backend.dimensions || {
    professionalism: backend.professionalism ?? 0,
    responsiveness: backend.responsiveness ?? 0,
    attitude: backend.attitude ?? 0,
    value_for_money: 0,
  };

  return {
    id: String(backend.id),
    lawyerId: String(backend.lawyer_id),
    userId: String(backend.user_id),
    userName: backend.user_name || '',
    userAvatar: backend.user_avatar,
    bookingId: String(backend.consultation_id),
    rating: backend.rating,
    dimensions: transformReviewDimensions(dimensions),
    content: backend.content,
    tags: backend.tags,
    isAnonymous: backend.is_anonymous,
    isRecommended: backend.is_recommended ?? false,
    createdAt: backend.created_at,
    replyContent: backend.reply_content,
    repliedAt: backend.replied_at,
  };
}

/**
 * 转换后端评价统计为前端格式
 */
function transformReviewStats(backend: BackendReviewStats): ReviewStats {
  return {
    lawyerId: String(backend.lawyer_id),
    totalReviews: backend.total_reviews,
    averageRating: backend.average_rating,
    averageDimensions: transformReviewDimensions(backend.average_dimensions),
    ratingDistribution: backend.rating_distribution || {},
    tagCounts: backend.tag_stats || {},
  };
}

/**
 * 转换后端在线状态为前端格式
 */
function _transformOnlineStatus(backend: BackendOnlineStatus): LawyerOnlineInfo {
  return {
    lawyerId: String(backend.lawyer_id),
    status: backend.status,
    lastActiveAt: backend.last_active_at,
    currentConsultationCount: backend.current_consultation_count,
    estimatedWaitTime: backend.estimated_wait_time,
  };
}

// ==================== API 函数 ====================

/**
 * 获取推荐律师
 * POST /lawyer-recommendation/recommend-by-keywords
 */
export async function apiGetRecommendations(
  request: GetRecommendationsRequest
): Promise<GetRecommendationsResponse> {
  const { data } = await apiClient.get<BackendRecommendResponse>(
    `${RECOMMENDATION_BASE}/recommend-by-keywords`,
    {
      params: {
        keywords: request.keywords || [],
        domains: request.domains || [],
        limit: request.limit || 10,
      },
    }
  );
  return {
    // eslint-disable-next-line @typescript-eslint/no-unsafe-assignment
    recommendations: data.lawyers.map(transformMatchResult) as unknown as LawyerMatchResult[],
    total: data.count,
  };
}

/**
 * 根据查询文本获取推荐律师
 * GET /lawyer-recommendation/recommend
 */
export async function apiGetRecommendationsByQuery(
  query: string,
  limit: number = 10
): Promise<GetRecommendationsResponse> {
  const { data } = await apiClient.get<BackendRecommendResponse>(
    `${RECOMMENDATION_BASE}/recommend`,
    {
      params: { query, limit },
    }
  );
  return {
    // eslint-disable-next-line @typescript-eslint/no-unsafe-assignment
    recommendations: data.lawyers.map(transformMatchResult) as unknown as LawyerMatchResult[],
    total: data.count,
  };
}

/**
 * 获取律师详情
 * GET /lawfirm/lawyers/:id
 */
export async function apiGetLawyerDetail(
  request: GetLawyerDetailRequest
): Promise<GetLawyerDetailResponse> {
  const { data } = await apiClient.get<BackendLawyerDetail>(
    `${LAWFIRM_BASE}/lawyers/${request.lawyerId}`
  );
  return {
    // eslint-disable-next-line @typescript-eslint/no-unsafe-assignment
    lawyer: transformLawyerDetail(data) as unknown as LawyerDetail,
  };
}

/**
 * 搜索律师列表
 * GET /lawfirm/lawyers
 */
export async function apiSearchLawyers(
  request: SearchLawyersRequest
): Promise<SearchLawyersResponse> {
  const { data } = await apiClient.get<BackendLawyerListResponse>(
    `${LAWFIRM_BASE}/lawyers`,
    {
      params: {
        keyword: request.query,
        page: request.offset ? Math.floor(request.offset / (request.limit || 20)) + 1 : 1,
        page_size: request.limit || 20,
        specialty: request.filters?.domains?.[0],
      },
    }
  );

  return {
    lawyers: data.items.map(transformLawyerDetail) as unknown as Lawyer[],
    total: data.total,
    hasMore: data.items.length === (request.limit || 20),
  };
}

/**
 * 创建预约/咨询
 * POST /lawfirm/consultations
 */
export async function apiCreateBooking(
  request: CreateBookingRequest
): Promise<CreateBookingResponse> {
  const { data } = await apiClient.post<BackendConsultation>(
    `${LAWFIRM_BASE}/consultations`,
    {
      lawyer_id: parseInt(request.lawyerId, 10),
      subject: request.topic,
      description: request.description,
      preferred_time: request.scheduledTime,
      category: request.consultationType,
      contact_phone: '',
    }
  );
  return {
    success: true,
    booking: transformConsultationToBooking(data) as unknown as Booking, // eslint-disable-line @typescript-eslint/no-unsafe-assignment
  };
}

/**
 * 获取我的预约/咨询列表
 * GET /lawfirm/consultations
 */
export async function apiGetBookings(
  request: GetBookingsRequest = {}
): Promise<GetBookingsResponse> {
  const { data } = await apiClient.get<BackendConsultationListResponse>(
    `${LAWFIRM_BASE}/consultations`,
    {
      params: {
        page: request.offset ? Math.floor(request.offset / (request.limit || 20)) + 1 : 1,
        page_size: request.limit || 20,
        status_filter: request.status,
      },
    }
  );
  return {
    // eslint-disable-next-line @typescript-eslint/no-unsafe-assignment
    bookings: data.items.map(transformConsultationToBooking) as unknown as Booking[],
    total: data.total,
  };
}

/**
 * 取消预约/咨询
 * POST /lawfirm/consultations/:id/cancel
 */
export async function apiCancelBooking(
  request: CancelBookingRequest
): Promise<CancelBookingResponse> {
  await apiClient.post(`${LAWFIRM_BASE}/consultations/${request.bookingId}/cancel`);

  return {
    success: true,
  };
}

/**
 * 获取律师评价列表
 * GET /lawfirm/reviews/lawyers/:id
 */
export async function apiGetReviews(
  request: GetReviewsRequest
): Promise<GetReviewsResponse> {
  const { data } = await apiClient.get<BackendReviewListResponse>(
    `${LAWFIRM_BASE}/reviews/lawyers/${request.lawyerId}`,
    {
      params: {
        page: request.offset ? Math.floor(request.offset / (request.limit || 10)) + 1 : 1,
        page_size: request.limit || 10,
      },
    }
  );
  const summaryResponse = await apiClient.get<BackendReviewStats>(
    `${LAWFIRM_BASE}/reviews/lawyers/${request.lawyerId}/summary`
  ).catch(() => ({ data: null as BackendReviewStats | null }));
  const summaryData = summaryResponse.data;

  return {
    reviews: data.items.map(transformReview) as unknown as LawyerReview[], // eslint-disable-line @typescript-eslint/no-unsafe-assignment
    total: data.total,
    // eslint-disable-next-line @typescript-eslint/no-unsafe-assignment
    stats: summaryData ? transformReviewStats(summaryData) : {
      lawyerId: request.lawyerId,
      totalReviews: data.total,
      averageRating: data.average_rating || 0,
      averageDimensions: { professionalism: 0, responsiveness: 0, attitude: 0, valueForMoney: 0 },
      ratingDistribution: {},
      tagCounts: {},
    },
  };
}

/**
 * 提交评价
 * POST /lawfirm/reviews
 */
export async function apiSubmitReview(
  request: SubmitReviewRequest
): Promise<SubmitReviewResponse> {
  const { data } = await apiClient.post<BackendReview>(`${LAWFIRM_BASE}/reviews`, {
    lawyer_id: parseInt(request.lawyerId, 10),
    consultation_id: parseInt(request.bookingId, 10),
    rating: request.rating,
    content: request.content,
    professionalism: request.dimensions.professionalism,
    responsiveness: request.dimensions.responsiveness,
    attitude: request.dimensions.attitude,
    tags: request.tags,
    is_anonymous: request.isAnonymous,
  });
  return {
    success: true,
    review: transformReview(data) as unknown as LawyerReview, // eslint-disable-line @typescript-eslint/no-unsafe-assignment
  };
}

/**
 * 获取律师可用时段
 * GET /lawyer/schedules/lawyers/:id/available-slots
 */
export async function apiGetLawyerAvailableSlots(
  lawyerId: string,
  date: string
): Promise<{ date: string; slots: Array<{ start_time: string; end_time: string }> }> {
  const { data } = await apiClient.get<{
    lawyer_id: number;
    date: string;
    slots: Array<{ start_time: string; end_time: string }>;
  }>(`/lawyer/schedules/lawyers/${lawyerId}/available-slots`, {
    params: { date },
  });

  return {
    date: data.date,
    slots: data.slots,
  };
}

/**
 * 获取律师在线状态（批量）
 * Note: 后端暂未实现，使用模拟数据
 */
export function apiGetOnlineStatus(
  request: GetOnlineStatusRequest
): Promise<GetOnlineStatusResponse> {
  // TODO: 后端实现后替换为真实 API
  // const { data } = await apiClient.post(`${RECOMMENDATION_BASE}/online-status`, {
  //   lawyer_ids: request.lawyerIds,
  // });

  // 模拟数据
  return Promise.resolve({
    statuses: request.lawyerIds.map(id => ({
      lawyerId: id,
      status: 'online' as const,
      lastActiveAt: new Date().toISOString(),
      currentConsultationCount: 0,
      estimatedWaitTime: 0,
    })),
  });
}

/**
 * 获取单个律师在线状态
 * Note: 后端暂未实现，使用模拟数据
 */
export function apiGetLawyerOnlineStatus(
  lawyerId: string
): Promise<LawyerOnlineInfo> {
  // TODO: 后端实现后替换为真实 API
  return Promise.resolve({
    lawyerId,
    status: 'online',
    lastActiveAt: new Date().toISOString(),
    currentConsultationCount: 0,
    estimatedWaitTime: 0,
  });
}

// ==================== 导出 API 对象 ====================

export const lawyerMatchingApi = {
  // 推荐相关
  getRecommendations: apiGetRecommendations,
  getRecommendationsByQuery: apiGetRecommendationsByQuery,

  // 律师相关
  getLawyerDetail: apiGetLawyerDetail,
  searchLawyers: apiSearchLawyers,
  getLawyerOnlineStatus: apiGetLawyerOnlineStatus,
  getOnlineStatus: apiGetOnlineStatus,
  getLawyerAvailableSlots: apiGetLawyerAvailableSlots,

  // 预约相关
  createBooking: apiCreateBooking,
  getBookings: apiGetBookings,
  cancelBooking: apiCancelBooking,

  // 评价相关
  getReviews: apiGetReviews,
  submitReview: apiSubmitReview,
};

export default lawyerMatchingApi;