/**
 * Forum-Assistant（论坛助手）Hooks
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';

import type {
  SmartReplySuggestion,
  EnhancedContentRecommendation,
  AssistantConfig,
  UserPreference,
  RecommendationCategory,
  AdoptSmartReplyRequest,
  FeedbackRecommendationRequest,
  UpdateAssistantConfigRequest,
  UpdateUserPreferencesRequest,
} from '../types';
import {
  apiGetSmartReplySuggestions,
  apiGetContentRecommendations,
  apiAdoptSmartReply,
  apiFeedbackRecommendation,
  apiGetAssistantConfig,
  apiUpdateAssistantConfig,
  apiGetUserPreferences,
  apiUpdateUserPreferences,
  apiGetTrendingTopics,
  apiGetRelatedExperts,
} from '../api';

// ==================== Query Keys ====================

const FORUM_ASSISTANT_QUERY_KEYS = {
  smartReplies: (postId: string) => ['forum-assistant', 'smart-replies', postId] as const,
  contentRecommendations: (category?: RecommendationCategory, limit?: number) => 
    ['forum-assistant', 'recommendations', category, limit] as const,
  assistantConfig: ['forum-assistant', 'config'] as const,
  userPreferences: ['forum-assistant', 'preferences'] as const,
  trendingTopics: ['forum-assistant', 'trending-topics'] as const,
  relatedExperts: ['forum-assistant', 'related-experts'] as const,
} as const;

// ==================== Smart Reply Hooks ====================

/**
 * 获取智能回复建议 Hook
 */
export function useSmartReplySuggestions(postId: string, enabled: boolean = true) {
  return useQuery<SmartReplySuggestion[]>({
    queryKey: FORUM_ASSISTANT_QUERY_KEYS.smartReplies(postId),
    queryFn: () => apiGetSmartReplySuggestions({ postId }),
    staleTime: 30 * 1000, // 30秒缓存
    enabled: enabled && postId.length > 0,
  });
}

/**
 * 采纳智能回复 Hook
 */
export function useAdoptSmartReply() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (request: AdoptSmartReplyRequest) => apiAdoptSmartReply(request),
    onSuccess: (_data, variables) => {
      // 采纳成功后刷新智能回复建议
      void queryClient.invalidateQueries({ 
        queryKey: FORUM_ASSISTANT_QUERY_KEYS.smartReplies(variables.postId) 
      });
    },
  });
}

// ==================== Content Recommendation Hooks ====================

/**
 * 获取内容推荐 Hook
 */
export function useContentRecommendations(
  category?: RecommendationCategory,
  limit: number = 10
) {
  return useQuery<EnhancedContentRecommendation[]>({
    queryKey: FORUM_ASSISTANT_QUERY_KEYS.contentRecommendations(category, limit),
    queryFn: async () => {
      const response = await apiGetContentRecommendations({ category, limit });
      return response.recommendations;
    },
    staleTime: 60 * 1000, // 1分钟缓存
  });
}

/**
 * 反馈推荐内容 Hook
 */
export function useFeedbackRecommendation() {
  return useMutation({
    mutationFn: (request: FeedbackRecommendationRequest) => apiFeedbackRecommendation(request),
  });
}

// ==================== Assistant Config Hooks ====================

/**
 * 获取助手配置 Hook
 */
export function useAssistantConfig() {
  return useQuery<AssistantConfig>({
    queryKey: FORUM_ASSISTANT_QUERY_KEYS.assistantConfig,
    queryFn: apiGetAssistantConfig,
    staleTime: 5 * 60 * 1000, // 5分钟缓存
  });
}

/**
 * 更新助手配置 Hook
 */
export function useUpdateAssistantConfig() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (request: UpdateAssistantConfigRequest) => apiUpdateAssistantConfig(request),
    onSuccess: () => {
      // 更新成功后刷新配置
      void queryClient.invalidateQueries({ 
        queryKey: FORUM_ASSISTANT_QUERY_KEYS.assistantConfig 
      });
    },
  });
}

// ==================== User Preferences Hooks ====================

/**
 * 获取用户偏好 Hook
 */
export function useUserPreferences() {
  return useQuery<UserPreference>({
    queryKey: FORUM_ASSISTANT_QUERY_KEYS.userPreferences,
    queryFn: apiGetUserPreferences,
    staleTime: 5 * 60 * 1000, // 5分钟缓存
  });
}

/**
 * 更新用户偏好 Hook
 */
export function useUpdateUserPreferences() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (request: UpdateUserPreferencesRequest) => apiUpdateUserPreferences(request),
    onSuccess: () => {
      // 更新成功后刷新偏好
      void queryClient.invalidateQueries({ 
        queryKey: FORUM_ASSISTANT_QUERY_KEYS.userPreferences 
      });
    },
  });
}

// ==================== Trending Topics Hooks ====================

/**
 * 获取热门话题 Hook
 */
export function useTrendingTopics() {
  return useQuery<{
    topics: Array<{
      id: string;
      name: string;
      hotScore: number;
      postCount: number;
    }>;
  }>({
    queryKey: FORUM_ASSISTANT_QUERY_KEYS.trendingTopics,
    queryFn: apiGetTrendingTopics,
    staleTime: 5 * 60 * 1000, // 5分钟缓存
  });
}

// ==================== Related Experts Hooks ====================

/**
 * 获取相关专家 Hook
 */
export function useRelatedExperts() {
  return useQuery<{
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
  }>({
    queryKey: FORUM_ASSISTANT_QUERY_KEYS.relatedExperts,
    queryFn: apiGetRelatedExperts,
    staleTime: 10 * 60 * 1000, // 10分钟缓存
  });
}