/**
 * Lawyer（律师模块）类型定义
 */

// ==================== 核心类型 ====================

/** 律师信息 */
export interface Lawyer {
  id: string;
  name: string;
  avatar: string | null;
  title: string | null;
  licenseNo: string | null;
  phone: string | null;
  email: string | null;
  introduction: string | null;
  specialties: string | null;
  experienceYears: number;
  caseCount: number;
  rating: number;
  reviewCount: number;
  consultationFee: number;
  isVerified: boolean;
  isActive: boolean;
  createdAt: string;
  firmName: string | null;
  userId?: string | null;
  firmId?: string | null;
}

/** 律师详细资料 */
export interface LawyerProfile extends Lawyer {
  /** 专业领域标签列表 */
  specialtyList: string[];
  /** 教育背景 */
  education?: string;
  /** 执业证书照片 */
  licenseImage?: string;
  /** 律所详细信息 */
  firmInfo?: {
    id: string;
    name: string;
    address?: string;
    phone?: string;
  };
  /** 成功案例数 */
  successCases?: number;
  /** 服务地区 */
  serviceAreas?: string[];
  /** 工作语言 */
  languages?: string[];
}

/** 律师评价 */
export interface LawyerReview {
  id: string;
  lawyerId: string;
  userId: string;
  consultationId: string | null;
  rating: number;
  content: string | null;
  isAnonymous: boolean;
  /** 专业性评分 1-5 */
  professionalism: number | null;
  /** 响应速度评分 1-5 */
  responsiveness: number | null;
  /** 服务态度评分 1-5 */
  attitude: number | null;
  /** 标签列表 */
  tags: string[];
  createdAt: string;
  /** 用户名（匿名时不显示） */
  username: string | null;
}

/** 律师日程 */
export interface LawyerSchedule {
  id: string;
  lawyerId: string;
  date: string;
  startTime: string;
  endTime: string;
  isAvailable: boolean;
  consultationId: string | null;
  note: string | null;
  createdAt: string;
  updatedAt: string;
}

/** 可用时段 */
export interface AvailableSlot {
  date: string;
  startTime: string;
  endTime: string;
}

/** 咨询预约 */
export interface Consultation {
  id: string;
  userId: string;
  lawyerId: string;
  subject: string;
  description: string | null;
  category: string | null;
  contactPhone: string | null;
  preferredTime: string | null;
  status: 'pending' | 'confirmed' | 'completed' | 'cancelled';
  adminNote: string | null;
  createdAt: string;
  updatedAt: string;
  lawyerName: string | null;
  paymentOrderNo: string | null;
  paymentStatus: string | null;
  paymentAmount: number | null;
  reviewId: string | null;
  canReview: boolean;
}

/** 评价维度统计 */
export interface ReviewDimensionStats {
  professionalismAvg: number;
  responsivenessAvg: number;
  attitudeAvg: number;
}

/** 评分分布 */
export interface RatingDistribution {
  rating5Count: number;
  rating4Count: number;
  rating3Count: number;
  rating2Count: number;
  rating1Count: number;
}

/** 标签统计 */
export interface TagStat {
  tag: string;
  count: number;
}

/** 评价摘要 */
export interface ReviewSummary {
  lawyerId: string;
  lawyerName: string;
  totalReviews: number;
  averageRating: number;
  dimensionStats: ReviewDimensionStats;
  ratingDistribution: RatingDistribution;
  tagStats: TagStat[];
  popularTags: TagStat[];
}

// ==================== 律师认证相关类型 ====================

/** 认证申请状态 */
export type VerificationStatus = 'pending' | 'approved' | 'rejected';

/** 律师认证申请 */
export interface LawyerVerification {
  id: string;
  userId: string;
  realName: string;
  idCardNo: string;
  licenseNo: string;
  firmName: string;
  idCardFront: string | null;
  idCardBack: string | null;
  licensePhoto: string | null;
  specialties: string | null;
  introduction: string | null;
  experienceYears: number | null;
  status: VerificationStatus;
  rejectReason: string | null;
  createdAt: string;
  reviewedAt: string | null;
}

/** 提交认证申请请求 */
export interface SubmitVerificationRequest {
  realName: string;
  idCardNo: string;
  licenseNo: string;
  firmName: string;
  idCardFront?: string;
  idCardBack?: string;
  licensePhoto?: string;
  specialties?: string;
  introduction?: string;
  experienceYears?: number;
}

/** 提交认证申请响应 */
export interface SubmitVerificationResponse {
  detail: string;
  verificationId: number;
}

/** 认证状态响应 */
export interface VerificationStatusResponse {
  hasVerification: boolean;
  verificationStatus: VerificationStatus | null;
  verificationId: number | null;
  submittedAt: string | null;
  reviewedAt: string | null;
  rejectReason: string | null;
  isVerifiedLawyer: boolean;
}

// ==================== 律师主页相关类型 ====================

/** 律师主页 */
export interface LawyerHomepage {
  id: string;
  lawyerId: string;
  bannerImage: string | null;
  profileImage: string | null;
  slogan: string | null;
  bio: string | null;
  specialtiesDisplay: string | null;
  achievements: string | null;
  education: string | null;
  serviceAreas: string | null;
  serviceHours: string | null;
  responseTime: string | null;
  contactPhone: string | null;
  contactEmail: string | null;
  wechatQrcode: string | null;
  weiboUrl: string | null;
  linkedinUrl: string | null;
  zhihuUrl: string | null;
  caseStudies: string | null;
  videoUrl: string | null;
  videoCover: string | null;
  seoTitle: string | null;
  seoDescription: string | null;
  seoKeywords: string | null;
  themeColor: string | null;
  backgroundColor: string | null;
  isPublished: boolean;
  viewCount: number;
  createdAt: string;
  updatedAt: string;
}

/** 成功案例 */
export interface HomepageCase {
  title: string;
  description: string;
  outcome?: string;
}

/** 客户评价 */
export interface HomepageReview {
  userName: string;
  rating: number;
  content: string;
  createdAt: string;
}

/** 律师主页（公开视图） */
export interface LawyerHomepagePublic {
  // 律师基本信息
  name: string;
  avatarUrl: string | null;
  title: string | null;
  firmName: string | null;
  location: string | null;
  isVerified: boolean;
  
  // 联系方式
  phone: string | null;
  email: string | null;
  weixin: string | null;
  
  // 个人简介
  bio: string | null;
  
  // 专长领域
  specialties: string[];
  
  // 成功案例
  cases: HomepageCase[];
  
  // 客户评价
  reviews: HomepageReview[];
  
  // 统计数据
  consultationCount: number;
  reviewCount: number;
  responseRate: number;
}

/** 创建律师主页请求 */
export interface CreateHomepageRequest {
  bannerImage?: string;
  profileImage?: string;
  slogan?: string;
  bio?: string;
  specialtiesDisplay?: string;
  achievements?: string;
  education?: string;
  serviceAreas?: string;
  serviceHours?: string;
  responseTime?: string;
  contactPhone?: string;
  contactEmail?: string;
  wechatQrcode?: string;
  weiboUrl?: string;
  linkedinUrl?: string;
  zhihuUrl?: string;
  caseStudies?: string;
  videoUrl?: string;
  videoCover?: string;
  seoTitle?: string;
  seoDescription?: string;
  seoKeywords?: string;
  themeColor?: string;
  backgroundColor?: string;
  isPublished?: boolean;
}

/** 更新律师主页请求 */
export interface UpdateHomepageRequest {
  bannerImage?: string;
  profileImage?: string;
  slogan?: string;
  bio?: string;
  specialtiesDisplay?: string;
  achievements?: string;
  education?: string;
  serviceAreas?: string;
  serviceHours?: string;
  responseTime?: string;
  contactPhone?: string;
  contactEmail?: string;
  wechatQrcode?: string;
  weiboUrl?: string;
  linkedinUrl?: string;
  zhihuUrl?: string;
  caseStudies?: string;
  videoUrl?: string;
  videoCover?: string;
  seoTitle?: string;
  seoDescription?: string;
  seoKeywords?: string;
  themeColor?: string;
  backgroundColor?: string;
  isPublished?: boolean;
}

// ==================== 推广链接相关类型 ====================

/** 推广链接 */
export interface LawyerPromotionLink {
  id: string;
  lawyerId: string;
  linkCode: string;
  linkName: string | null;
  description: string | null;
  isActive: boolean;
  clickCount: number;
  consultationCount: number;
  conversionCount: number;
  createdAt: string;
  updatedAt: string;
}

/** 创建推广链接请求 */
export interface CreatePromotionLinkRequest {
  linkName?: string;
  description?: string;
}

/** 更新推广链接请求 */
export interface UpdatePromotionLinkRequest {
  linkName?: string;
  description?: string;
  isActive?: boolean;
}

/** 推广链接列表响应 */
export interface PromotionLinkListResponse {
  items: LawyerPromotionLink[];
  total: number;
  page: number;
  pageSize: number;
}

/** 推广链接统计 */
export interface PromotionLinkStats {
  linkId: string;
  linkCode: string;
  linkName: string | null;
  clickCount: number;
  consultationCount: number;
  conversionCount: number;
  conversionRate: number;
}

// ==================== 快捷回复模板相关类型 ====================

/** 快捷回复模板 */
export interface LawyerReplyTemplate {
  id: string;
  lawyerId: string;
  title: string;
  content: string;
  category: string | null;
  isActive: boolean;
  useCount: number;
  createdAt: string;
  updatedAt: string;
}

/** 创建快捷回复模板请求 */
export interface CreateReplyTemplateRequest {
  title: string;
  content: string;
  category?: string;
}

/** 更新快捷回复模板请求 */
export interface UpdateReplyTemplateRequest {
  title?: string;
  content?: string;
  category?: string;
  isActive?: boolean;
}

/** 快捷回复模板列表响应 */
export interface ReplyTemplateListResponse {
  items: LawyerReplyTemplate[];
  total: number;
  page: number;
  pageSize: number;
}

/** 模板分类响应 */
export interface ReplyTemplateCategoriesResponse {
  categories: string[];
}

/** 使用模板响应 */
export interface UseReplyTemplateResponse {
  content: string;
}

// ==================== API 请求/响应类型 ====================

/** 获取律师列表请求 */
export interface GetLawyersRequest {
  page?: number;
  pageSize?: number;
  firmId?: string;
  specialty?: string;
  keyword?: string;
}

/** 获取律师列表响应 */
export interface GetLawyersResponse {
  lawyers: Lawyer[];
  total: number;
  page: number;
  pageSize: number;
}

/** 获取律师详情请求 */
export interface GetLawyerRequest {
  lawyerId: string;
}

/** 获取律师详情响应 */
export interface GetLawyerResponse {
  lawyer: Lawyer;
}

/** 获取律师评价列表请求 */
export interface GetLawyerReviewsRequest {
  page?: number;
  pageSize?: number;
}

/** 获取律师评价列表响应 */
export interface GetLawyerReviewsResponse {
  reviews: LawyerReview[];
  total: number;
  page: number;
  pageSize: number;
  averageRating: number;
}

/** 创建评价请求 */
export interface CreateReviewRequest {
  lawyerId: string;
  consultationId: string;
  rating: number;
  content?: string;
  isAnonymous?: boolean;
  professionalism?: number;
  responsiveness?: number;
  attitude?: number;
  tags?: string[];
}

/** 创建评价响应 */
export interface CreateReviewResponse {
  review: LawyerReview;
}

/** 获取律师日程请求 */
export interface GetLawyerScheduleRequest {
  dateFrom?: string;
  dateTo?: string;
  page?: number;
  pageSize?: number;
}

/** 获取律师日程响应 */
export interface GetLawyerScheduleResponse {
  schedules: LawyerSchedule[];
  total: number;
  page: number;
  pageSize: number;
}

/** 获取可用时段请求 */
export interface GetAvailableSlotsRequest {
  lawyerId: string;
  date: string;
}

/** 获取可用时段响应 */
export interface GetAvailableSlotsResponse {
  lawyerId: string;
  date: string;
  slots: AvailableSlot[];
}

/** 预约咨询请求 */
export interface BookingRequest {
  lawyerId: string;
  subject: string;
  description?: string;
  category?: string;
  contactPhone?: string;
  preferredTime?: string;
}

/** 预约咨询响应 */
export interface BookingResponse {
  consultation: Consultation;
  paymentOrderNo: string | null;
  paymentStatus: string | null;
  paymentAmount: number | null;
}

/** 获取我的咨询列表请求 */
export interface GetMyConsultationsRequest {
  page?: number;
  pageSize?: number;
  statusFilter?: string;
}

/** 获取我的咨询列表响应 */
export interface GetMyConsultationsResponse {
  consultations: Consultation[];
  total: number;
  page: number;
  pageSize: number;
}

/** 取消咨询请求 */
export interface CancelConsultationRequest {
  consultationId: string;
}

/** 取消咨询响应 */
export interface CancelConsultationResponse {
  consultation: Consultation;
}

/** 律师排行榜项 */
export interface LawyerRankingItem {
  lawyerId: string;
  lawyerName: string;
  rating: number;
  value: number;
}

/** 获取律师排行榜响应 */
export interface GetLawyerRankingResponse {
  metric: string;
  days: number;
  lawyers: LawyerRankingItem[];
}

/** 后端原始响应类型（用于数据转换） */
export interface LawyerResponseSnake {
  id: number;
  user_id?: number | null;
  firm_id?: number | null;
  name: string;
  avatar: string | null;
  title: string | null;
  license_no: string | null;
  phone: string | null;
  email: string | null;
  introduction: string | null;
  specialties: string | null;
  experience_years: number;
  case_count: number;
  rating: number;
  review_count: number;
  consultation_fee: number;
  is_verified: boolean;
  is_active: boolean;
  created_at: string;
  firm_name: string | null;
}

export interface ReviewResponseSnake {
  id: number;
  lawyer_id: number;
  user_id: number;
  consultation_id: number | null;
  rating: number;
  content: string | null;
  is_anonymous: boolean;
  professionalism: number | null;
  responsiveness: number | null;
  attitude: number | null;
  tags: string[];
  created_at: string;
  username: string | null;
}

export interface ScheduleResponseSnake {
  id: number;
  lawyer_id: number;
  date: string;
  start_time: string;
  end_time: string;
  is_available: boolean;
  consultation_id: number | null;
  note: string | null;
  created_at: string;
  updated_at: string;
}

export interface ConsultationResponseSnake {
  id: number;
  user_id: number;
  lawyer_id: number;
  subject: string;
  description: string | null;
  category: string | null;
  contact_phone: string | null;
  preferred_time: string | null;
  status: string;
  admin_note: string | null;
  created_at: string;
  updated_at: string;
  lawyer_name: string | null;
  payment_order_no: string | null;
  payment_status: string | null;
  payment_amount: number | null;
  review_id: number | null;
  can_review: boolean;
}

export interface ReviewSummaryResponseSnake {
  lawyer_id: number;
  lawyer_name: string;
  total_reviews: number;
  average_rating: number;
  dimension_stats: {
    professionalism_avg: number;
    responsiveness_avg: number;
    attitude_avg: number;
  };
  rating_distribution: {
    rating_5_count: number;
    rating_4_count: number;
    rating_3_count: number;
    rating_2_count: number;
    rating_1_count: number;
  };
  tag_stats: Array<{ tag: string; count: number }>;
  popular_tags: Array<{ tag: string; count: number }>;
}

export interface AvailableSlotResponseSnake {
  date: string;
  start_time: string;
  end_time: string;
}

export interface LawyerRankingItemSnake {
  lawyer_id: number;
  lawyer_name: string;
  rating: number;
  value: number;
}

/** 律师认证后端原始响应 */
export interface VerificationResponseSnake {
  id: number;
  user_id: number;
  real_name: string;
  id_card_no: string;
  license_no: string;
  firm_name: string;
  id_card_front: string | null;
  id_card_back: string | null;
  license_photo: string | null;
  specialties: string | null;
  introduction: string | null;
  experience_years: number | null;
  status: string;
  reject_reason: string | null;
  created_at: string;
  reviewed_at: string | null;
}

/** 认证状态后端原始响应 */
export interface VerificationStatusResponseSnake {
  has_verification: boolean;
  verification_status: string | null;
  verification_id: number | null;
  submitted_at: string | null;
  reviewed_at: string | null;
  reject_reason: string | null;
  is_verified_lawyer: boolean;
}

/** 律师主页后端原始响应 */
export interface LawyerHomepageResponseSnake {
  id: number;
  lawyer_id: number;
  banner_image: string | null;
  profile_image: string | null;
  slogan: string | null;
  bio: string | null;
  specialties_display: string | null;
  achievements: string | null;
  education: string | null;
  service_areas: string | null;
  service_hours: string | null;
  response_time: string | null;
  contact_phone: string | null;
  contact_email: string | null;
  wechat_qrcode: string | null;
  weibo_url: string | null;
  linkedin_url: string | null;
  zhihu_url: string | null;
  case_studies: string | null;
  video_url: string | null;
  video_cover: string | null;
  seo_title: string | null;
  seo_description: string | null;
  seo_keywords: string | null;
  theme_color: string | null;
  background_color: string | null;
  is_published: boolean;
  view_count: number;
  created_at: string;
  updated_at: string;
}

/** 律师主页公开视图后端原始响应 */
export interface LawyerHomepagePublicResponseSnake extends LawyerHomepageResponseSnake {
  lawyer_name: string | null;
  lawyer_avatar: string | null;
  lawyer_title: string | null;
  lawyer_specialties: string | null;
  lawyer_experience_years: number;
  lawyer_rating: number;
  lawyer_review_count: number;
  lawyer_consultation_fee: number;
}

/** 推广链接后端原始响应 */
export interface PromotionLinkResponseSnake {
  id: number;
  lawyer_id: number;
  link_code: string;
  link_name: string | null;
  description: string | null;
  is_active: boolean;
  click_count: number;
  consultation_count: number;
  conversion_count: number;
  created_at: string;
  updated_at: string;
}

/** 推广链接统计后端原始响应 */
export interface PromotionLinkStatsResponseSnake {
  link_id: number;
  link_code: string;
  link_name: string | null;
  click_count: number;
  consultation_count: number;
  conversion_count: number;
  conversion_rate: number;
}

/** 快捷回复模板后端原始响应 */
export interface ReplyTemplateResponseSnake {
  id: number;
  lawyer_id: number;
  title: string;
  content: string;
  category: string | null;
  is_active: boolean;
  use_count: number;
  created_at: string;
  updated_at: string;
}

// ==================== 律所管理类型 ====================

/** 律所信息 */
export interface LawFirm {
  id: string;
  name: string;
  city: string | null;
  phone: string | null;
  address: string | null;
  description: string | null;
  isVerified: boolean;
  isActive: boolean;
  lawyerCount: number;
  rating: number;
  createdAt: string;
}

/** 创建律所请求 */
export interface CreateLawFirmRequest {
  name: string;
  city?: string;
  phone?: string;
  address?: string;
  description?: string;
}

/** 更新律所请求 */
export interface UpdateLawFirmRequest {
  name?: string;
  city?: string;
  phone?: string;
  address?: string;
  description?: string;
}

/** 律所后端原始响应 */
export interface LawFirmResponseSnake {
  id: number;
  name: string;
  city: string | null;
  phone: string | null;
  address: string | null;
  description: string | null;
  is_verified: boolean;
  is_active: boolean;
  lawyer_count: number;
  rating: number;
  created_at: string;
}