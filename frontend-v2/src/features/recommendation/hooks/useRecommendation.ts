/**
 * Recommendation（推荐系统）Hooks - 增强版
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';

import type {
  PersonalizedRecommendations,
  EnhancedRecommendations,
  LawyerRecommendation,
  PostRecommendation,
  NewsRecommendation,
  OnboardingAnswers,
  InteractionRequest,
} from '../types';
import {
  apiGetPersonalizedRecommendations,
  apiGetEnhancedRecommendations,
  apiGetEnhancedHome,
  apiGetOnboardingSurvey,
  apiCompleteOnboarding,
  apiCheckShouldOnboarding,
  apiGetRecommendationWeights,
  apiRecommendLawyers,
  apiRecommendPosts,
  apiRecommendNews,
  apiRecommendLawyersByConsultation,
  apiRecommendLawyersByLocation,
  apiRecommendKnowledgeByInterests,
  apiGetHomeRecommendations,
  apiRecordInteraction,
} from '../api';
import { recommendationKeys } from '../api/queryKeys';

// ==================== 个性化推荐 Hooks ====================

/**
 * 获取个性化推荐
 */
export function usePersonalizedRecommendations(
  lawyerLimit: number = 5,
  postLimit: number = 5,
  newsLimit: number = 5
) {
  return useQuery<PersonalizedRecommendations>({
    queryKey: recommendationKeys.personalizedRecommendations(lawyerLimit, postLimit, newsLimit),
    queryFn: () => apiGetPersonalizedRecommendations(lawyerLimit, postLimit, newsLimit),
    staleTime: 3 * 60 * 1000, // 3分钟缓存
  });
}

/**
 * 获取增强版个性化推荐
 */
export function useEnhancedRecommendations(
  recommendationType: string = 'hybrid',
  limit: number = 10
) {
  return useQuery<EnhancedRecommendations>({
    queryKey: recommendationKeys.enhancedRecommendations(recommendationType, limit),
    queryFn: () => apiGetEnhancedRecommendations(recommendationType, limit),
    staleTime: 3 * 60 * 1000,
  });
}

// ==================== 引导问卷 Hooks ====================

/**
 * 获取引导问卷
 */
export function useOnboardingSurvey() {
  return useQuery({
    queryKey: recommendationKeys.survey(),
    queryFn: apiGetOnboardingSurvey,
    staleTime: 60 * 60 * 1000, // 1小时缓存，问卷不常变化
  });
}

/**
 * 完成引导问卷
 */
export function useCompleteOnboarding() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (answers: OnboardingAnswers) =>
      apiCompleteOnboarding(answers as Record<string, unknown>),
    onSuccess: () => {
      // 完成引导后，刷新相关数据
      void queryClient.invalidateQueries({ queryKey: recommendationKeys.all });
    },
  });
}

/**
 * 检查是否需要显示引导
 */
export function useShouldOnboarding() {
  return useQuery<boolean>({
    queryKey: recommendationKeys.shouldOnboarding(),
    queryFn: apiCheckShouldOnboarding,
    staleTime: 30 * 60 * 1000, // 30分钟缓存
  });
}

// ==================== 推荐权重 Hooks ====================

/**
 * 获取推荐权重
 */
export function useRecommendationWeights() {
  return useQuery<Record<string, number>>({
    queryKey: recommendationKeys.weights(),
    queryFn: apiGetRecommendationWeights,
    staleTime: 10 * 60 * 1000, // 10分钟缓存
  });
}

// ==================== 内容推荐 Hooks ====================

/**
 * 推荐律师
 */
export function useRecommendLawyers(limit: number = 10) {
  return useQuery<LawyerRecommendation[]>({
    queryKey: recommendationKeys.lawyerRecommendations(limit),
    queryFn: () => apiRecommendLawyers(limit),
    staleTime: 5 * 60 * 1000,
  });
}

/**
 * 推荐论坛帖子
 */
export function useRecommendPosts(limit: number = 10) {
  return useQuery<PostRecommendation[]>({
    queryKey: recommendationKeys.postRecommendations(limit),
    queryFn: () => apiRecommendPosts(limit),
    staleTime: 5 * 60 * 1000,
  });
}

/**
 * 推荐新闻
 */
export function useRecommendNews(limit: number = 10) {
  return useQuery<NewsRecommendation[]>({
    queryKey: recommendationKeys.newsRecommendations(limit),
    queryFn: () => apiRecommendNews(limit),
    staleTime: 5 * 60 * 1000,
  });
}

// ==================== 增强推荐 Hooks ====================

/**
 * 获取增强版个性化首页
 */
export function useEnhancedHome(
  lawyerLimit: number = 5,
  postLimit: number = 5,
  newsLimit: number = 5,
  knowledgeLimit: number = 5
) {
  return useQuery({
    queryKey: recommendationKeys.enhancedHome(lawyerLimit, postLimit, newsLimit, knowledgeLimit),
    queryFn: () => apiGetEnhancedHome(lawyerLimit, postLimit, newsLimit, knowledgeLimit),
    staleTime: 3 * 60 * 1000,
  });
}

/**
 * 基于咨询历史推荐律师
 */
export function useRecommendLawyersByConsultation(limit: number = 10) {
  return useQuery<LawyerRecommendation[]>({
    queryKey: recommendationKeys.lawyerByConsultation(limit),
    queryFn: () => apiRecommendLawyersByConsultation(limit),
    staleTime: 5 * 60 * 1000,
  });
}

/**
 * 基于位置推荐律师
 */
export function useRecommendLawyersByLocation(city?: string, limit: number = 10) {
  return useQuery<LawyerRecommendation[]>({
    queryKey: recommendationKeys.lawyerByLocation(city, limit),
    queryFn: () => apiRecommendLawyersByLocation(city, limit),
    staleTime: 5 * 60 * 1000,
  });
}

/**
 * 基于兴趣推荐知识文章
 */
export function useRecommendKnowledgeByInterests(limit: number = 10) {
  return useQuery({
    queryKey: recommendationKeys.knowledgeByInterests(limit),
    queryFn: () => apiRecommendKnowledgeByInterests(limit),
    staleTime: 5 * 60 * 1000,
  });
}

/**
 * 获取首页推荐数据
 */
export function useHomeRecommendations(recommendationLimit: number = 10) {
  return useQuery({
    queryKey: recommendationKeys.homeRecommendations(recommendationLimit),
    queryFn: () => apiGetHomeRecommendations(recommendationLimit),
    staleTime: 3 * 60 * 1000,
  });
}

// ==================== 用户交互 Hooks ====================

/**
 * 记录用户交互
 */
export function useRecordInteraction() {
  return useMutation({
    mutationFn: (request: InteractionRequest) =>
      apiRecordInteraction(request.contentId, request.contentType, {
        tags: request.tags,
        interactionType: request.interactionType,
        weight: request.weight,
      }),
  });
}

// ==================== 聚合 Hooks ====================

/**
 * 推荐页面数据聚合 Hook
 * 同时获取个性化推荐、用户画像和权重
 */
export function useRecommendationPageData() {
  const recommendationsQuery = usePersonalizedRecommendations(5, 5, 5);
  const weightsQuery = useRecommendationWeights();

  const isLoading = recommendationsQuery.isLoading || weightsQuery.isLoading;
  const isError = recommendationsQuery.isError || weightsQuery.isError;
  const error = recommendationsQuery.error || weightsQuery.error;

  return {
    recommendations: recommendationsQuery.data,
    weights: weightsQuery.data,
    isLoading,
    isError,
    error,
    refetch: () => {
      void recommendationsQuery.refetch();
      void weightsQuery.refetch();
    },
  };
}

/**
 * 引导页面数据聚合 Hook
 */
export function useOnboardingPageData() {
  const surveyQuery = useOnboardingSurvey();
  const shouldOnboardingQuery = useShouldOnboarding();

  const isLoading = surveyQuery.isLoading || shouldOnboardingQuery.isLoading;
  const isError = surveyQuery.isError || shouldOnboardingQuery.isError;

  return {
    survey: surveyQuery.data ?? [],
    shouldShowOnboarding: shouldOnboardingQuery.data ?? true,
    isLoading,
    isError,
    refetch: () => {
      void surveyQuery.refetch();
      void shouldOnboardingQuery.refetch();
    },
  };
}

/**
 * 首页数据聚合 Hook
 * 同时获取多种推荐数据
 */
export function useHomePageData() {
  const homeQuery = useHomeRecommendations(10);

  return {
    data: homeQuery.data,
    isLoading: homeQuery.isLoading,
    isError: homeQuery.isError,
    error: homeQuery.error,
    refetch: () => {
      void homeQuery.refetch();
    },
  };
}