/**
 * Recommendation（推荐系统）API 层
 * 基于统一的 apiClient，对接后端 /api/v1/recommendation 端点
 */

import { apiClient } from "@/shared/lib/api/client";

// API 基础路径
const API_BASE = '/recommendation';

// ==================== 后端响应类型定义 ====================

/** 律师推荐项 */
interface BackendLawyerRecommendationItem {
  lawyer_id: number;
  lawyer_name: string;
  avatar?: string;
  specialties?: string;
  rating: number;
  review_count: number;
  consultation_count: number;
  is_verified: boolean;
  match_score: number;
}

/** 帖子推荐项 */
interface BackendPostRecommendationItem {
  post_id: number;
  title: string;
  content?: string;
  author_id: number;
  author_name: string;
  view_count: number;
  like_count: number;
  comment_count: number;
  created_at: string;
  match_score: number;
}

/** 新闻推荐项 */
interface BackendNewsRecommendationItem {
  news_id: number;
  title: string;
  summary?: string;
  category?: string;
  view_count: number;
  created_at: string;
  match_score: number;
}

/** 个性化推荐响应 */
interface BackendPersonalizedRecommendationsResponse {
  user_id: number;
  lawyers: BackendLawyerRecommendationItem[];
  posts: BackendPostRecommendationItem[];
  news: BackendNewsRecommendationItem[];
  similar_users_content: Array<Record<string, unknown>>;
}

/** 增强推荐项 */
interface BackendEnhancedRecommendationItem {
  id: string;
  type: string;
  title: string;
  score: number;
  reason: string;
  metadata: Record<string, unknown>;
}

/** 增强推荐响应 */
interface BackendEnhancedRecommendationsResponse {
  items: BackendEnhancedRecommendationItem[];
  total: number;
  source: string;
}

/** 引导问卷响应 */
interface BackendOnboardingSurveyResponse {
  survey: Array<Record<string, unknown>>;
}

/** 引导档案响应 */
interface BackendOnboardingProfileResponse {
  success: boolean;
  profile: {
    interest_tags: string[];
    interest_weights: Record<string, number>;
    preferred_content_types: string[];
    usage_frequency: string;
    onboarding_completed: boolean;
  };
}

/** 是否需要引导响应 */
interface BackendShouldOnboardingResponse {
  should_show: boolean;
}

/** 推荐权重响应 */
interface BackendRecommendationWeightsResponse {
  weights: Record<string, number>;
}

/** 律师推荐响应 */
interface BackendLawyersRecommendationResponse {
  lawyers: BackendLawyerRecommendationItem[];
}

/** 帖子推荐响应 */
interface BackendPostsRecommendationResponse {
  posts: BackendPostRecommendationItem[];
}

/** 新闻推荐响应 */
interface BackendNewsRecommendationResponse {
  news: BackendNewsRecommendationItem[];
}

// ==================== 前端类型定义 ====================

/** 律师推荐项 */
export interface LawyerRecommendation {
  lawyerId: number;
  lawyerName: string;
  avatar?: string;
  specialties?: string;
  rating: number;
  reviewCount: number;
  consultationCount: number;
  isVerified: boolean;
  matchScore: number;
}

/** 帖子推荐项 */
export interface PostRecommendation {
  postId: number;
  title: string;
  content?: string;
  authorId: number;
  authorName: string;
  viewCount: number;
  likeCount: number;
  commentCount: number;
  createdAt: string;
  matchScore: number;
}

/** 新闻推荐项 */
export interface NewsRecommendation {
  newsId: number;
  title: string;
  summary?: string;
  category?: string;
  viewCount: number;
  createdAt: string;
  matchScore: number;
}

/** 个性化推荐结果 */
export interface PersonalizedRecommendations {
  userId: number;
  lawyers: LawyerRecommendation[];
  posts: PostRecommendation[];
  news: NewsRecommendation[];
  similarUsersContent: Array<Record<string, unknown>>;
}

/** 增强推荐项 */
export interface EnhancedRecommendationItem {
  id: string;
  type: string;
  title: string;
  score: number;
  reason: string;
  metadata: Record<string, unknown>;
}

/** 增强推荐结果 */
export interface EnhancedRecommendations {
  items: EnhancedRecommendationItem[];
  total: number;
  source: string;
}

/** 用户画像 */
export interface UserProfile {
  interestTags: string[];
  interestWeights: Record<string, number>;
  preferredContentTypes: string[];
  usageFrequency: string;
  onboardingCompleted: boolean;
}

/** 引导问卷问题 */
export interface SurveyQuestion {
  id: string;
  type: string;
  question: string;
  options?: Array<{
    value: string;
    label: string;
  }>;
  required?: boolean;
}

// ==================== 转换函数 ====================

/**
 * 转换后端律师推荐项到前端格式
 */
function mapBackendToLawyerRecommendation(data: BackendLawyerRecommendationItem): LawyerRecommendation {
  return {
    lawyerId: data.lawyer_id,
    lawyerName: data.lawyer_name,
    avatar: data.avatar,
    specialties: data.specialties,
    rating: data.rating,
    reviewCount: data.review_count,
    consultationCount: data.consultation_count,
    isVerified: data.is_verified,
    matchScore: data.match_score,
  };
}

/**
 * 转换后端帖子推荐项到前端格式
 */
function mapBackendToPostRecommendation(data: BackendPostRecommendationItem): PostRecommendation {
  return {
    postId: data.post_id,
    title: data.title,
    content: data.content,
    authorId: data.author_id,
    authorName: data.author_name,
    viewCount: data.view_count,
    likeCount: data.like_count,
    commentCount: data.comment_count,
    createdAt: data.created_at,
    matchScore: data.match_score,
  };
}

/**
 * 转换后端新闻推荐项到前端格式
 */
function mapBackendToNewsRecommendation(data: BackendNewsRecommendationItem): NewsRecommendation {
  return {
    newsId: data.news_id,
    title: data.title,
    summary: data.summary,
    category: data.category,
    viewCount: data.view_count,
    createdAt: data.created_at,
    matchScore: data.match_score,
  };
}

/**
 * 转换后端增强推荐项到前端格式
 */
function mapBackendToEnhancedRecommendation(data: BackendEnhancedRecommendationItem): EnhancedRecommendationItem {
  return {
    id: data.id,
    type: data.type,
    title: data.title,
    score: data.score,
    reason: data.reason,
    metadata: data.metadata,
  };
}

// ==================== 个性化推荐 API ====================

/**
 * 获取个性化推荐
 */
export async function apiGetPersonalizedRecommendations(
  lawyerLimit: number = 5,
  postLimit: number = 5,
  newsLimit: number = 5
): Promise<PersonalizedRecommendations> {
  const response = await apiClient.get<BackendPersonalizedRecommendationsResponse>(
    `${API_BASE}/personalized`,
    {
      params: {
        lawyer_limit: lawyerLimit,
        post_limit: postLimit,
        news_limit: newsLimit,
      },
    }
  );

  return {
    userId: response.data.user_id,
    lawyers: response.data.lawyers.map(mapBackendToLawyerRecommendation),
    posts: response.data.posts.map(mapBackendToPostRecommendation),
    news: response.data.news.map(mapBackendToNewsRecommendation),
    similarUsersContent: response.data.similar_users_content,
  };
}

// ==================== 增强推荐 API ====================

/**
 * 获取增强版个性化推荐
 */
export async function apiGetEnhancedRecommendations(
  recommendationType: string = 'hybrid',
  limit: number = 10
): Promise<EnhancedRecommendations> {
  const response = await apiClient.get<BackendEnhancedRecommendationsResponse>(
    `${API_BASE}/enhanced`,
    {
      params: {
        recommendation_type: recommendationType,
        limit,
      },
    }
  );

  return {
    items: response.data.items.map(mapBackendToEnhancedRecommendation),
    total: response.data.total,
    source: response.data.source,
  };
}

// ==================== 引导问卷 API ====================

/**
 * 获取引导问卷
 */
export async function apiGetOnboardingSurvey(): Promise<SurveyQuestion[]> {
  const response = await apiClient.get<BackendOnboardingSurveyResponse>(
    `${API_BASE}/survey`
  );

  // 将后端返回的通用对象转换为前端类型
   
  return response.data.survey.map((item: Record<string, unknown>) => ({
    id: String(item.id ?? ''),
    type: String(item.type ?? 'text'),
    question: String(item.question ?? ''),
    options: Array.isArray(item.options) ? item.options as Array<{ value: string; label: string }> : undefined,
    required: Boolean(item.required),
  })) as SurveyQuestion[];
}

/**
 * 完成引导问卷，构建用户画像
 */
export async function apiCompleteOnboarding(
  answers: Record<string, unknown>
): Promise<{ success: boolean; profile: UserProfile }> {
  const response = await apiClient.post<BackendOnboardingProfileResponse>(
    `${API_BASE}/onboarding`,
    { answers }
  );

  return {
    success: response.data.success,
    profile: {
      interestTags: response.data.profile.interest_tags,
      interestWeights: response.data.profile.interest_weights,
      preferredContentTypes: response.data.profile.preferred_content_types,
      usageFrequency: response.data.profile.usage_frequency,
      onboardingCompleted: response.data.profile.onboarding_completed,
    },
  };
}

/**
 * 检查是否需要显示引导问卷
 */
export async function apiCheckShouldOnboarding(): Promise<boolean> {
  const response = await apiClient.get<BackendShouldOnboardingResponse>(
    `${API_BASE}/should-onboarding`
  );

  return response.data.should_show;
}

// ==================== 推荐权重 API ====================

/**
 * 获取推荐权重
 */
export async function apiGetRecommendationWeights(): Promise<Record<string, number>> {
  const response = await apiClient.get<BackendRecommendationWeightsResponse>(
    `${API_BASE}/weights`
  );

  return response.data.weights;
}

// ==================== 内容推荐 API ====================

/**
 * 推荐律师
 */
export async function apiRecommendLawyers(limit: number = 10): Promise<LawyerRecommendation[]> {
  const response = await apiClient.get<BackendLawyersRecommendationResponse>(
    `${API_BASE}/lawyers`,
    {
      params: { limit },
    }
  );

  return response.data.lawyers.map(mapBackendToLawyerRecommendation);
}

/**
 * 推荐论坛帖子
 */
export async function apiRecommendPosts(limit: number = 10): Promise<PostRecommendation[]> {
  const response = await apiClient.get<BackendPostsRecommendationResponse>(
    `${API_BASE}/posts`,
    {
      params: { limit },
    }
  );

  return response.data.posts.map(mapBackendToPostRecommendation);
}

/**
 * 推荐新闻
 */
export async function apiRecommendNews(limit: number = 10): Promise<NewsRecommendation[]> {
  const response = await apiClient.get<BackendNewsRecommendationResponse>(
    `${API_BASE}/news`,
    {
      params: { limit },
    }
  );

  return response.data.news.map(mapBackendToNewsRecommendation);
}

// ==================== 用户交互 API ====================

/**
 * 记录用户交互
 */
export async function apiRecordInteraction(
  contentId: string,
  contentType: string,
  options: {
    tags?: string[];
    interactionType?: string;
    weight?: number;
  } = {}
): Promise<{ success: boolean }> {
  const response = await apiClient.post<{ success: boolean }>(
    `${API_BASE}/interaction`,
    {
      content_id: contentId,
      content_type: contentType,
      tags: options.tags ?? [],
      interaction_type: options.interactionType ?? 'viewed',
      weight: options.weight ?? 1.0,
    }
  );

  return response.data;
}

// ==================== 增强推荐 API ====================

/** 增强版个性化首页响应 */
interface BackendEnhancedHomeResponse {
  user_id: number;
  is_cold_start: boolean;
  profile: {
    interests: string[];
    history_count: number;
  };
  lawyers: Array<Record<string, unknown>>;
  posts: Array<Record<string, unknown>>;
  news: Array<Record<string, unknown>>;
  knowledge: Array<Record<string, unknown>>;
  hot_content: Array<Record<string, unknown>>;
  reason: string;
  recommendation_source: string;
  generated_at: string;
}

/** 知识推荐项 */
interface BackendKnowledgeRecommendationItem {
  knowledge_id: number;
  title: string;
  category?: string;
  summary?: string;
  view_count: number;
  score: number;
}

/** 知识推荐响应 */
interface BackendKnowledgeRecommendationResponse {
  knowledge: BackendKnowledgeRecommendationItem[];
}

/** 首页推荐响应 */
interface BackendHomeRecommendationsResponse {
  lawyers: Array<Record<string, unknown>>;
  posts: Array<Record<string, unknown>>;
  news: Array<Record<string, unknown>>;
  knowledge: Array<Record<string, unknown>>;
}

/**
 * 获取增强版个性化首页数据
 */
export async function apiGetEnhancedHome(
  lawyerLimit: number = 5,
  postLimit: number = 5,
  newsLimit: number = 5,
  knowledgeLimit: number = 5
): Promise<BackendEnhancedHomeResponse> {
  const response = await apiClient.get<BackendEnhancedHomeResponse>(
    `${API_BASE}/enhanced/personalized-home`,
    {
      params: {
        lawyer_limit: lawyerLimit,
        post_limit: postLimit,
        news_limit: newsLimit,
        knowledge_limit: knowledgeLimit,
      },
    }
  );
  return response.data;
}

/**
 * 基于咨询历史推荐律师
 */
export async function apiRecommendLawyersByConsultation(
  limit: number = 10
): Promise<LawyerRecommendation[]> {
  const response = await apiClient.get<{ lawyers: BackendLawyerRecommendationItem[] }>(
    `${API_BASE}/lawyers/by-consultation`,
    {
      params: { limit },
    }
  );

  return response.data.lawyers.map(mapBackendToLawyerRecommendation);
}

/**
 * 基于位置推荐律师
 */
export async function apiRecommendLawyersByLocation(
  city?: string,
  limit: number = 10
): Promise<LawyerRecommendation[]> {
  const response = await apiClient.get<{ lawyers: BackendLawyerRecommendationItem[] }>(
    `${API_BASE}/lawyers/by-location`,
    {
      params: { city, limit },
    }
  );

  return response.data.lawyers.map(mapBackendToLawyerRecommendation);
}

/**
 * 基于兴趣推荐知识文章
 */
export async function apiRecommendKnowledgeByInterests(
  limit: number = 10
): Promise<Array<{
  knowledgeId: number;
  title: string;
  category?: string;
  summary?: string;
  viewCount: number;
  score: number;
}>> {
  const response = await apiClient.get<BackendKnowledgeRecommendationResponse>(
    `${API_BASE}/knowledge/by-interests`,
    {
      params: { limit },
    }
  );

  return response.data.knowledge.map((item) => ({
    knowledgeId: item.knowledge_id,
    title: item.title,
    category: item.category,
    summary: item.summary,
    viewCount: item.view_count,
    score: item.score,
  }));
}

/**
 * 获取首页推荐数据
 */
export async function apiGetHomeRecommendations(
  recommendationLimit: number = 10
): Promise<BackendHomeRecommendationsResponse> {
  const response = await apiClient.get<BackendHomeRecommendationsResponse>(
    `${API_BASE}/home`,
    {
      params: { recommendation_limit: recommendationLimit },
    }
  );
  return response.data;
}

// ==================== 统一导出 ====================

/**
 * Recommendation API 统一导出对象
 */
export const recommendationApi = {
  // 个性化推荐
  getPersonalizedRecommendations: apiGetPersonalizedRecommendations,
  getEnhancedRecommendations: apiGetEnhancedRecommendations,
  getEnhancedHome: apiGetEnhancedHome,

  // 引导问卷
  getOnboardingSurvey: apiGetOnboardingSurvey,
  completeOnboarding: apiCompleteOnboarding,
  checkShouldOnboarding: apiCheckShouldOnboarding,

  // 推荐权重
  getRecommendationWeights: apiGetRecommendationWeights,

  // 内容推荐
  recommendLawyers: apiRecommendLawyers,
  recommendPosts: apiRecommendPosts,
  recommendNews: apiRecommendNews,

  // 增强推荐
  recommendLawyersByConsultation: apiRecommendLawyersByConsultation,
  recommendLawyersByLocation: apiRecommendLawyersByLocation,
  recommendKnowledgeByInterests: apiRecommendKnowledgeByInterests,
  getHomeRecommendations: apiGetHomeRecommendations,

  // 用户交互
  recordInteraction: apiRecordInteraction,
} as const;

export default recommendationApi;