/**
 * News（新闻资讯）类型定义
 */

// ==================== 前端展示类型 ====================

/** 新闻分类类型 */
export type NewsCategoryType =
  | 'legal'    // 法律新闻
  | 'case'     // 典型案例
  | 'policy'   // 政策法规
  | 'industry' // 行业动态
  | 'other';   // 其他

/** 资讯条目（前端展示用） */
export interface News {
  id: string;
  title: string;
  summary: string;
  content: string;
  category: NewsCategoryType;
  author: string;
  viewCount: number;
  likeCount: number;
  commentCount: number;
  publishedAt: string;
  createdAt: string;
  updatedAt: string;
  tags: string[];
  isFeatured: boolean;
  coverImage?: string;
}

/** 资讯筛选条件 */
export interface NewsFilters {
  category?: string;
  featured?: boolean;
  searchQuery?: string;
}

/** 点赞资讯DTO */
export interface NewsLikeDTO {
  newsId: string;
}

// ==================== 枚举类型 ====================

/** 新闻审核状态 */
export type NewsReviewStatus = 'pending' | 'approved' | 'rejected';

/** AI风险等级 */
export type AiRiskLevel = 'none' | 'low' | 'medium' | 'high';

/** 订阅类型 */
export type SubscriptionType = 'category' | 'keyword' | 'author';

/** 评论审核状态 */
export type CommentReviewStatus = 'pending' | 'approved' | 'rejected';

// ==================== 核心类型 ====================

/** 新闻文章作者 */
export interface NewsAuthor {
  id: string;
  name: string;
  avatar?: string;
}

/** 新闻文章 */
export interface NewsArticle {
  id: string;
  title: string;
  summary: string;
  content: string;
  coverImage?: string;
  category: NewsCategory;
  source: string;
  sourceUrl?: string;
  author: NewsAuthor;
  viewCount: number;
  favoriteCount: number;
  isFavorited: boolean;
  aiRiskLevel: AiRiskLevel;
  isTop: boolean;
  isPublished: boolean;
  reviewStatus: NewsReviewStatus;
  publishedAt?: string;
  createdAt: string;
  updatedAt: string;
}

/** 新闻分类 */
export interface NewsCategory {
  id: string;
  name: string;
  description?: string;
  icon?: string;
  sortOrder: number;
  isActive: boolean;
}

/** 新闻评论 */
export interface NewsComment {
  id: string;
  newsId: string;
  userId: string;
  content: string;
  reviewStatus: CommentReviewStatus;
  createdAt: string;
  author: NewsAuthor;
}

/** 新闻订阅 */
export interface NewsSubscription {
  id: string;
  subType: SubscriptionType;
  value: string;
  createdAt: string;
}

// ==================== 列表和分页类型 ====================

/** 分页参数 */
export interface PaginationParams {
  page?: number;
  pageSize?: number;
}

/** 分页响应元数据 */
export interface PaginationMeta {
  page: number;
  pageSize: number;
  total: number;
  totalPages: number;
}

/** 新闻列表项（简化版） */
export interface NewsListItem {
  id: string;
  title: string;
  summary: string;
  coverImage?: string;
  categoryName: string;
  source: string;
  viewCount: number;
  favoriteCount: number;
  isFavorited: boolean;
  isTop: boolean;
  publishedAt?: string;
}

// ==================== API 请求/响应类型 ====================

/** 获取新闻列表请求 */
export interface GetNewsListRequest extends PaginationParams {
  categoryId?: string;
  keyword?: string;
  source?: string;
  sortBy?: 'newest' | 'hottest' | 'relevant';
}

/** 获取新闻列表响应 */
export interface GetNewsListResponse {
  items: NewsListItem[];
  meta: PaginationMeta;
}

/** 获取新闻详情请求 */
export interface GetNewsDetailRequest {
  newsId: string;
}

/** 获取新闻详情响应 */
export interface GetNewsDetailResponse {
  article: NewsArticle;
}

/** 获取新闻评论请求 */
export interface GetNewsCommentsRequest extends PaginationParams {
  newsId: string;
}

/** 获取新闻评论响应 */
export interface GetNewsCommentsResponse {
  items: NewsComment[];
  meta: PaginationMeta;
}

/** 创建评论请求 */
export interface CreateCommentRequest {
  newsId: string;
  content: string;
}

/** 创建评论响应 */
export interface CreateCommentResponse {
  comment: NewsComment;
}

/** 订阅新闻请求 */
export interface SubscribeNewsRequest {
  subType: SubscriptionType;
  value: string;
}

/** 订阅新闻响应 */
export interface SubscribeNewsResponse {
  subscription: NewsSubscription;
}

/** 取消订阅请求 */
export interface UnsubscribeNewsRequest {
  subscriptionId: string;
}

/** 取消订阅响应 */
export interface UnsubscribeNewsResponse {
  success: boolean;
}

/** 获取分类列表响应 */
export interface GetCategoriesResponse {
  categories: NewsCategory[];
}

/** 切换收藏请求 */
export interface ToggleFavoriteRequest {
  newsId: string;
}

/** 切换收藏响应 */
export interface ToggleFavoriteResponse {
  isFavorited: boolean;
  favoriteCount: number;
}

/** 获取热门新闻请求 */
export interface GetHotNewsRequest extends PaginationParams {
  period?: 'day' | 'week' | 'month';
}

/** 获取热门新闻响应 */
export interface GetHotNewsResponse {
  items: NewsListItem[];
  meta: PaginationMeta;
}

/** 获取推荐新闻请求 */
export interface GetRecommendedNewsRequest extends PaginationParams {
  userId?: string;
  excludeIds?: string[];
}

/** 获取推荐新闻响应 */
export interface GetRecommendedNewsResponse {
  items: NewsListItem[];
  meta: PaginationMeta;
}

/** 获取用户订阅列表响应 */
export interface GetUserSubscriptionsResponse {
  subscriptions: NewsSubscription[];
}

/** 搜索新闻请求 */
export interface SearchNewsRequest extends PaginationParams {
  keyword: string;
  categoryId?: string;
}

/** 搜索新闻响应 */
export interface SearchNewsResponse {
  items: NewsListItem[];
  meta: PaginationMeta;
}

/** 获取相关新闻请求 */
export interface GetRelatedNewsRequest {
  newsId: string;
  limit?: number;
}

/** 获取相关新闻响应 */
export interface GetRelatedNewsResponse {
  items: NewsListItem[];
}