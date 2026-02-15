/**
 * Lawyer-Matching（律师匹配）类型定义
 */

// ==================== 核心律师类型 ====================

/** 律师状态 */
export type LawyerStatus = 'online' | 'offline' | 'busy';

/** 律师基本信息 */
export interface Lawyer {
  id: string;
  name: string;
  avatar?: string;
  title?: string;
  firmName?: string;
  specialties: string[];
  rating: number;
  completedCount: number;
  status: LawyerStatus;
  isVerified: boolean;
}

/** 律师详情 */
export interface LawyerDetail extends Lawyer {
  phone?: string;
  email?: string;
  introduction?: string;
  experience?: number;
  education?: string[];
  certifications?: string[];
  casesHandled?: number;
  languages?: string[];
  workingHours?: string;
}

/** 律师匹配结果 */
export interface LawyerMatchResult {
  lawyerId: string;
  lawyerName: string;
  specialties: string;
  rating: number;
  completedCount: number;
  matchScore: number;
  overallScore: number;
  matchReasons: string[];
}

// ==================== 匹配条件类型 ====================

/** 法律领域 */
export type LegalDomain = 
  | 'civil'           // 民事
  | 'criminal'        // 刑事
  | 'commercial'      // 商事
  | 'labor'           // 劳动
  | 'family'          // 婚姻家事
  | 'property'        // 房产
  | 'intellectual'    // 知识产权
  | 'administrative'  // 行政
  | 'contract'        // 合同
  | 'tort';           // 侵权

/** 匹配条件 */
export interface MatchingCriteria {
  keywords?: string[];
  domains?: LegalDomain[];
  minRating?: number;
  maxPrice?: number;
  experience?: number;
  location?: string;
  languages?: string[];
}

/** 获取推荐律师请求 */
export interface GetRecommendationsRequest {
  queryText: string;
  keywords?: string[];
  domains?: LegalDomain[];
  limit?: number;
  criteria?: MatchingCriteria;
}

/** 获取推荐律师响应 */
export interface GetRecommendationsResponse {
  recommendations: LawyerMatchResult[];
  total: number;
}

/** 获取律师详情请求 */
export interface GetLawyerDetailRequest {
  lawyerId: string;
}

/** 获取律师详情响应 */
export interface GetLawyerDetailResponse {
  lawyer: LawyerDetail;
}

// ==================== 预约类型 ====================

/** 预约状态 */
export type BookingStatus = 'pending' | 'confirmed' | 'cancelled' | 'completed';

/** 咨询类型 */
export type ConsultationType = 'phone' | 'video' | 'in_person' | 'online';

/** 预约信息 */
export interface Booking {
  id: string;
  lawyerId: string;
  lawyerName: string;
  userId: string;
  consultationType: ConsultationType;
  scheduledTime: string;
  duration: number;
  status: BookingStatus;
  topic: string;
  description?: string;
  price: number;
  createdAt: string;
  updatedAt: string;
}

/** 创建预约请求 */
export interface CreateBookingRequest {
  lawyerId: string;
  consultationType: ConsultationType;
  scheduledTime: string;
  duration: number;
  topic: string;
  description?: string;
}

/** 创建预约响应 */
export interface CreateBookingResponse {
  success: boolean;
  booking: Booking;
  paymentUrl?: string;
}

/** 获取预约列表请求 */
export interface GetBookingsRequest {
  status?: BookingStatus;
  limit?: number;
  offset?: number;
}

/** 获取预约列表响应 */
export interface GetBookingsResponse {
  bookings: Booking[];
  total: number;
}

/** 取消预约请求 */
export interface CancelBookingRequest {
  bookingId: string;
  reason?: string;
}

/** 取消预约响应 */
export interface CancelBookingResponse {
  success: boolean;
  refundAmount?: number;
}

// ==================== 评价类型 ====================

/** 评价维度 */
export interface ReviewDimensions {
  professionalism: number;  // 专业度
  responsiveness: number;   // 响应速度
  attitude: number;         // 服务态度
  valueForMoney: number;    // 性价比
}

/** 评价信息 */
export interface LawyerReview {
  id: string;
  lawyerId: string;
  userId: string;
  userName: string;
  userAvatar?: string;
  bookingId: string;
  rating: number;
  dimensions: ReviewDimensions;
  content: string;
  tags?: string[];
  isAnonymous: boolean;
  isRecommended: boolean;
  createdAt: string;
  replyContent?: string;
  repliedAt?: string;
}

/** 评价统计 */
export interface ReviewStats {
  lawyerId: string;
  totalReviews: number;
  averageRating: number;
  averageDimensions: ReviewDimensions;
  ratingDistribution: Record<number, number>;
  tagCounts: Record<string, number>;
}

/** 获取评价列表请求 */
export interface GetReviewsRequest {
  lawyerId: string;
  limit?: number;
  offset?: number;
  sortBy?: 'newest' | 'rating' | 'helpful';
}

/** 获取评价列表响应 */
export interface GetReviewsResponse {
  reviews: LawyerReview[];
  total: number;
  stats: ReviewStats;
}

/** 提交评价请求 */
export interface SubmitReviewRequest {
  lawyerId: string;
  bookingId: string;
  rating: number;
  dimensions: ReviewDimensions;
  content: string;
  tags?: string[];
  isAnonymous: boolean;
  isRecommended: boolean;
}

/** 提交评价响应 */
export interface SubmitReviewResponse {
  success: boolean;
  review: LawyerReview;
}

// ==================== 在线状态类型 ====================

/** 律师在线状态信息 */
export interface LawyerOnlineInfo {
  lawyerId: string;
  status: LawyerStatus;
  lastActiveAt?: string;
  currentConsultationCount?: number;
  estimatedWaitTime?: number;
}

/** 批量获取在线状态请求 */
export interface GetOnlineStatusRequest {
  lawyerIds: string[];
}

/** 批量获取在线状态响应 */
export interface GetOnlineStatusResponse {
  statuses: LawyerOnlineInfo[];
}

// ==================== 搜索类型 ====================

/** 搜索律师请求 */
export interface SearchLawyersRequest {
  query?: string;
  filters?: MatchingCriteria;
  sortBy?: 'match' | 'rating' | 'experience' | 'price';
  sortOrder?: 'asc' | 'desc';
  limit?: number;
  offset?: number;
}

/** 搜索律师响应 */
export interface SearchLawyersResponse {
  lawyers: Lawyer[];
  total: number;
  hasMore: boolean;
}