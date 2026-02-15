/**
 * Forum-Assistant（论坛助手）API 层
 */

import { apiClient } from "@/shared/lib/api/client";

import type {
  SmartReplySuggestion,
  ContentRecommendationItem,
  EnhancedContentRecommendation,
  AssistantConfig,
  UserPreference,
  GetSmartReplySuggestionsRequest,
  GetContentRecommendationsRequest,
  GetContentRecommendationsResponse,
  AdoptSmartReplyRequest,
  AdoptSmartReplyResponse,
  FeedbackRecommendationRequest,
  FeedbackRecommendationResponse,
  UpdateAssistantConfigRequest,
  UpdateAssistantConfigResponse,
  UpdateUserPreferencesRequest,
  UpdateUserPreferencesResponse,
  GetTrendingTopicsResponse,
  GetRelatedExpertsResponse,
} from '../types';



// API 基础路径
const API_BASE = '/forum/assistant';

/** API 错误响应 */
interface ApiErrorResponse {
  detail?: string;
}

/**
 * 获取 API 错误信息
 */
function getErrorMessage(error: unknown, defaultMsg: string): string {
  if (typeof error === 'object' && error !== null && 'detail' in error) {
    return (error as ApiErrorResponse).detail || defaultMsg;
  }
  return defaultMsg;
}

/**
 * 获取智能回复建议
 */
export async function apiGetSmartReplySuggestions(
  request: GetSmartReplySuggestionsRequest
): Promise<SmartReplySuggestion[]> {
  const response = await apiClient.post<{
    suggestions: Array<{
      id: string;
      content: string;
      confidence: number;
      category: string;
      context: string;
      tags: string[];
      created_at: string;
    }>;
    total: number;
  }>(`${API_BASE}/replies`, {
    post_id: request.postId,
    context: request.context,
    count: request.count,
  });

  const data = response.data;

  return data.suggestions.map((item) => ({
    id: item.id,
    content: item.content,
    confidence: item.confidence,
    category: item.category,
    context: item.context,
    tags: item.tags,
    createdAt: item.created_at,
  }));
}

/**
 * 获取内容推荐
 */
export async function apiGetContentRecommendations(
  request: GetContentRecommendationsRequest = {}
): Promise<GetContentRecommendationsResponse> {
  const searchParams = new URLSearchParams();
  if (request.category) searchParams.set('category', request.category);
  if (request.limit) searchParams.set('limit', String(request.limit));
  if (request.offset) searchParams.set('offset', String(request.offset));

  const url = `${API_BASE}/recommendations${searchParams.toString() ? `?${searchParams.toString()}` : ''}`;

  try {
    const response = await apiClient.get<{
      recommendations: Array<{
        item: {
          id: string;
          type: string;
          title: string;
          summary: string;
          author?: {
            id: string;
            name: string;
            avatar?: string;
            title?: string;
          };
          tags: string[];
          relevance_score: number;
          view_count: number;
          like_count: number;
          reply_count: number;
          created_at: string;
          thumbnail_url?: string;
        };
        reason: {
          type: string;
          description: string;
          matched_tags?: string[];
        };
        rank: number;
      }>;
      total: number;
      has_more: boolean;
    }>(url);

    const data = response.data;

    return {
      recommendations: data.recommendations.map((rec) => ({
        item: {
          id: rec.item.id,
          type: rec.item.type as ContentRecommendationItem['type'],
          title: rec.item.title,
          summary: rec.item.summary,
          author: rec.item.author,
          tags: rec.item.tags,
          relevanceScore: rec.item.relevance_score,
          viewCount: rec.item.view_count,
          likeCount: rec.item.like_count,
          replyCount: rec.item.reply_count,
          createdAt: rec.item.created_at,
          thumbnailUrl: rec.item.thumbnail_url,
        },
        reason: {
          type: rec.reason.type as EnhancedContentRecommendation['reason']['type'],
          description: rec.reason.description,
          matchedTags: rec.reason.matched_tags,
        },
        rank: rec.rank,
      })),
      total: data.total,
      hasMore: data.has_more,
    };
  } catch (error) {
    throw new Error(getErrorMessage(error, '获取内容推荐失败'));
  }
}

/**
 * 采纳智能回复
 */
export async function apiAdoptSmartReply(
  request: AdoptSmartReplyRequest
): Promise<AdoptSmartReplyResponse> {
  const response = await apiClient.post<AdoptSmartReplyResponse>(`${API_BASE}/replies/adopt`, {
    suggestion_id: request.suggestionId,
    post_id: request.postId,
    modified_content: request.modifiedContent,
  });

  return response.data;
}

/**
 * 反馈推荐内容
 */
export async function apiFeedbackRecommendation(
  request: FeedbackRecommendationRequest
): Promise<FeedbackRecommendationResponse> {
  const response = await apiClient.post<FeedbackRecommendationResponse>(`${API_BASE}/recommendations/feedback`, {
    recommendation_id: request.recommendationId,
    feedback: request.feedback,
    reason: request.reason,
  });

  return response.data;
}

/**
 * 获取助手配置
 */
export async function apiGetAssistantConfig(): Promise<AssistantConfig> {
  const response = await apiClient.get<{
    config: {
      enabled: boolean;
      auto_suggest: boolean;
      suggestion_count: number;
      min_confidence: number;
      preferred_categories: string[];
    };
  }>(`${API_BASE}/config`);

  const data = response.data;

  return {
    enabled: data.config.enabled,
    autoSuggest: data.config.auto_suggest,
    suggestionCount: data.config.suggestion_count,
    minConfidence: data.config.min_confidence,
    preferredCategories: data.config.preferred_categories as AssistantConfig['preferredCategories'],
  };
}

/**
 * 更新助手配置
 */
export async function apiUpdateAssistantConfig(
  request: UpdateAssistantConfigRequest
): Promise<UpdateAssistantConfigResponse> {
  const response = await apiClient.put<UpdateAssistantConfigResponse>(`${API_BASE}/config`, {
    enabled: request.enabled,
    auto_suggest: request.autoSuggest,
    suggestion_count: request.suggestionCount,
    min_confidence: request.minConfidence,
    preferred_categories: request.preferredCategories,
  });

  return response.data;
}

/**
 * 获取用户偏好
 */
export async function apiGetUserPreferences(): Promise<UserPreference> {
  const response = await apiClient.get<{
    preferences: {
      preferred_topics: string[];
      preferred_experts: string[];
      blocked_tags: string[];
      reading_history: string[];
    };
  }>(`${API_BASE}/preferences`);

  const data = response.data;

  return {
    preferredTopics: data.preferences.preferred_topics,
    preferredExperts: data.preferences.preferred_experts,
    blockedTags: data.preferences.blocked_tags,
    readingHistory: data.preferences.reading_history,
  };
}

/**
 * 更新用户偏好
 */
export async function apiUpdateUserPreferences(
  request: UpdateUserPreferencesRequest
): Promise<UpdateUserPreferencesResponse> {
  const response = await apiClient.put<UpdateUserPreferencesResponse>(`${API_BASE}/preferences`, {
    preferred_topics: request.preferredTopics,
    preferred_experts: request.preferredExperts,
    blocked_tags: request.blockedTags,
  });

  return response.data;
}

/**
 * 获取热门话题
 */
export async function apiGetTrendingTopics(): Promise<GetTrendingTopicsResponse> {
  const response = await apiClient.get<GetTrendingTopicsResponse>(`${API_BASE}/trending-topics`);
  return response.data;
}

/**
 * 获取相关专家
 */
export async function apiGetRelatedExperts(): Promise<GetRelatedExpertsResponse> {
  const response = await apiClient.get<GetRelatedExpertsResponse>(`${API_BASE}/related-experts`);
  return response.data;
}