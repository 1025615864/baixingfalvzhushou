/**
 * Forum-Assistant（论坛助手）类型定义
 */

// ==================== 核心类型 ====================

/** 智能回复建议 */
export interface SmartReplySuggestion {
  id: string;
  content: string;
  confidence: number;
  category: string;
  context: string;
  tags: string[];
  createdAt: string;
}

/** 内容推荐项 */
export interface ContentRecommendationItem {
  id: string;
  type: 'post' | 'article' | 'question' | 'expert';
  title: string;
  summary: string;
  author?: {
    id: string;
    name: string;
    avatar?: string;
    title?: string;
  };
  tags: string[];
  relevanceScore: number;
  viewCount: number;
  likeCount: number;
  replyCount: number;
  createdAt: string;
  thumbnailUrl?: string;
}

/** 推荐类别 */
export type RecommendationCategory =
  | 'trending'
  | 'related'
  | 'expert'
  | 'new'
  | 'recommended';

/** 智能回复上下文 */
export interface ReplyContext {
  postId: string;
  postTitle: string;
  postContent: string;
  authorName: string;
  existingReplies: number;
  tags: string[];
}

/** 用户偏好 */
export interface UserPreference {
  preferredTopics: string[];
  preferredExperts: string[];
  blockedTags: string[];
  readingHistory: string[];
}

/** 助手配置 */
export interface AssistantConfig {
  enabled: boolean;
  autoSuggest: boolean;
  suggestionCount: number;
  minConfidence: number;
  preferredCategories: RecommendationCategory[];
}

/** 推荐原因 */
export interface RecommendationReason {
  type: 'similar_content' | 'trending' | 'expert_recommendation' | 'user_interest' | 'related_topic';
  description: string;
  matchedTags?: string[];
}

/** 增强的内容推荐 */
export interface EnhancedContentRecommendation {
  item: ContentRecommendationItem;
  reason: RecommendationReason;
  rank: number;
}

// ==================== API 请求/响应类型 ====================

/** 获取智能回复建议请求 */
export interface GetSmartReplySuggestionsRequest {
  postId: string;
  context?: ReplyContext;
  count?: number;
}

/** 获取智能回复建议响应 */
export interface GetSmartReplySuggestionsResponse {
  suggestions: SmartReplySuggestion[];
  total: number;
}

/** 获取内容推荐请求 */
export interface GetContentRecommendationsRequest {
  category?: RecommendationCategory;
  limit?: number;
  offset?: number;
  userPreferences?: UserPreference;
}

/** 获取内容推荐响应 */
export interface GetContentRecommendationsResponse {
  recommendations: EnhancedContentRecommendation[];
  total: number;
  hasMore: boolean;
}

/** 采纳智能回复请求 */
export interface AdoptSmartReplyRequest {
  suggestionId: string;
  postId: string;
  modifiedContent?: string;
}

/** 采纳智能回复响应 */
export interface AdoptSmartReplyResponse {
  success: boolean;
  message: string;
  replyId?: string;
}

/** 反馈推荐请求 */
export interface FeedbackRecommendationRequest {
  recommendationId: string;
  feedback: 'useful' | 'not_useful' | 'irrelevant';
  reason?: string;
}

/** 反馈推荐响应 */
export interface FeedbackRecommendationResponse {
  success: boolean;
  message: string;
}

/** 获取助手配置响应 */
export interface GetAssistantConfigResponse {
  config: AssistantConfig;
}

/** 更新助手配置请求 */
export interface UpdateAssistantConfigRequest {
  enabled?: boolean;
  autoSuggest?: boolean;
  suggestionCount?: number;
  minConfidence?: number;
  preferredCategories?: RecommendationCategory[];
}

/** 更新助手配置响应 */
export interface UpdateAssistantConfigResponse {
  success: boolean;
  config: AssistantConfig;
}

/** 获取用户偏好响应 */
export interface GetUserPreferencesResponse {
  preferences: UserPreference;
}

/** 更新用户偏好请求 */
export interface UpdateUserPreferencesRequest {
  preferredTopics?: string[];
  preferredExperts?: string[];
  blockedTags?: string[];
}

/** 更新用户偏好响应 */
export interface UpdateUserPreferencesResponse {
  success: boolean;
  preferences: UserPreference;
}

/** 获取热门话题响应 */
export interface GetTrendingTopicsResponse {
  topics: Array<{
    id: string;
    name: string;
    hotScore: number;
    postCount: number;
  }>;
}

/** 获取相关专家响应 */
export interface GetRelatedExpertsResponse {
  experts: Array<{
    id: string;
    name: string;
    avatar?: string;
    title: string;
    specialty: string[];
    followerCount: number;
    replyCount: number;
    satisfactionRate: number;
  }>;
}
