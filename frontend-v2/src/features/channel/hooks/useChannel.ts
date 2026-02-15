/**
 * Channel（渠道管理）Hooks
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useCallback } from 'react';

import type {
  Channel,
  ChannelAnalytics,
  ChannelComparison,
  ChannelStatsSummary,
  ChannelStatus,
  CreateChannelRequest,
  UpdateChannelRequest,
  TrackEvent,
} from '../types';
import {
  apiGetChannelList,
  apiGetChannel,
  apiGetChannelByCode,
  apiCreateChannel,
  apiUpdateChannel,
  apiDeleteChannel,
  apiGetChannelAnalytics,
  apiGetSingleChannelAnalytics,
  apiCompareChannels,
  apiTrackEvents,
  apiGetChannelStatsSummary,
} from '../api';

// ==================== Query Keys ====================

const QUERY_KEYS = {
  channels: ['channels'] as const,
  channel: (id: string) => ['channels', id] as const,
  channelByCode: (code: string) => ['channels', 'code', code] as const,
  analytics: ['channels', 'analytics'] as const,
  analyticsById: (id: string) => ['channels', 'analytics', id] as const,
  comparison: (ids: string[]) => ['channels', 'comparison', ids] as const,
  statsSummary: ['channels', 'stats', 'summary'] as const,
};

// ==================== Queries ====================

/**
 * 获取渠道列表
 */
export function useChannelList(status?: ChannelStatus) {
  return useQuery<{ channels: Channel[]; total: number; page: number; pageSize: number }, Error>({
    queryKey: [...QUERY_KEYS.channels, status],
    queryFn: () => apiGetChannelList(status),
    staleTime: 5 * 60 * 1000, // 5分钟
  });
}

/**
 * 获取单个渠道
 */
export function useChannel(channelId: string) {
  return useQuery<Channel, Error>({
    queryKey: QUERY_KEYS.channel(channelId),
    queryFn: () => apiGetChannel(channelId),
    enabled: !!channelId,
    staleTime: 5 * 60 * 1000,
  });
}

/**
 * 通过 code 获取渠道
 */
export function useChannelByCode(code: string) {
  return useQuery<Channel, Error>({
    queryKey: QUERY_KEYS.channelByCode(code),
    queryFn: () => apiGetChannelByCode(code),
    enabled: !!code,
    staleTime: 5 * 60 * 1000,
  });
}

/**
 * 获取渠道分析数据
 */
export function useChannelAnalytics(
  channelIds?: string[],
  startDate?: string,
  endDate?: string
) {
  return useQuery<ChannelAnalytics[], Error>({
    queryKey: [...QUERY_KEYS.analytics, channelIds, startDate, endDate],
    queryFn: () => apiGetChannelAnalytics(channelIds, startDate, endDate),
    staleTime: 5 * 60 * 1000,
  });
}

/**
 * 获取单个渠道分析数据
 */
export function useSingleChannelAnalytics(
  channelId: string,
  startDate?: string,
  endDate?: string
) {
  return useQuery<ChannelAnalytics, Error>({
    queryKey: QUERY_KEYS.analyticsById(channelId),
    queryFn: () => apiGetSingleChannelAnalytics(channelId, startDate, endDate),
    enabled: !!channelId,
    staleTime: 5 * 60 * 1000,
  });
}

/**
 * 获取渠道对比数据
 */
export function useChannelComparison(
  channelIds: string[],
  startDate?: string,
  endDate?: string
) {
  return useQuery<ChannelComparison[], Error>({
    queryKey: QUERY_KEYS.comparison(channelIds),
    queryFn: () => apiCompareChannels(channelIds, startDate, endDate),
    enabled: channelIds.length > 0,
    staleTime: 5 * 60 * 1000,
  });
}

/**
 * 获取渠道统计汇总
 */
export function useChannelStatsSummary() {
  return useQuery<ChannelStatsSummary, Error>({
    queryKey: QUERY_KEYS.statsSummary,
    queryFn: apiGetChannelStatsSummary,
    staleTime: 5 * 60 * 1000,
  });
}

// ==================== Mutations ====================

/**
 * 创建渠道
 */
export function useCreateChannel() {
  const queryClient = useQueryClient();

  return useMutation<Channel, Error, CreateChannelRequest>({
    mutationFn: apiCreateChannel,
    onSuccess: () => {
      // 创建成功后，刷新渠道列表
      void queryClient.invalidateQueries({ queryKey: QUERY_KEYS.channels });
      void queryClient.invalidateQueries({ queryKey: QUERY_KEYS.statsSummary });
    },
  });
}

/**
 * 更新渠道
 */
export function useUpdateChannel() {
  const queryClient = useQueryClient();

  return useMutation<
    Channel,
    Error,
    { channelId: string; data: Omit<UpdateChannelRequest, 'channelId'> }
  >({
    mutationFn: ({ channelId, data }) => apiUpdateChannel(channelId, data),
    onSuccess: (_, variables) => {
      // 更新成功后，刷新相关缓存
      void queryClient.invalidateQueries({ queryKey: QUERY_KEYS.channel(variables.channelId) });
      void queryClient.invalidateQueries({ queryKey: QUERY_KEYS.channels });
      void queryClient.invalidateQueries({ queryKey: QUERY_KEYS.analytics });
      void queryClient.invalidateQueries({ queryKey: QUERY_KEYS.statsSummary });
    },
  });
}

/**
 * 删除渠道
 */
export function useDeleteChannel() {
  const queryClient = useQueryClient();

  return useMutation<void, Error, string>({
    mutationFn: apiDeleteChannel,
    onSuccess: () => {
      // 删除成功后，刷新所有相关缓存
      void queryClient.invalidateQueries({ queryKey: QUERY_KEYS.channels });
      void queryClient.invalidateQueries({ queryKey: QUERY_KEYS.analytics });
      void queryClient.invalidateQueries({ queryKey: QUERY_KEYS.statsSummary });
    },
  });
}

/**
 * 上报埋点事件
 */
export function useTrackEvents() {
  return useMutation<
    { success: boolean; count: number },
    Error,
    TrackEvent[]
  >({
    mutationFn: apiTrackEvents,
  });
}

// ==================== 工具 Hooks ====================

/**
 * 渠道管理综合 Hook
 */
export function useChannelManager() {
  const queryClient = useQueryClient();

  const {
    data: channels,
    isLoading: isLoadingChannels,
    error: channelsError,
    refetch: refetchChannels,
  } = useChannelList();

  const {
    data: statsSummary,
    isLoading: isLoadingStats,
    error: statsError,
    refetch: refetchStats,
  } = useChannelStatsSummary();

  const {
    data: analytics,
    isLoading: isLoadingAnalytics,
    error: analyticsError,
    refetch: refetchAnalytics,
  } = useChannelAnalytics();

  const createChannel = useCreateChannel();
  const updateChannel = useUpdateChannel();
  const deleteChannel = useDeleteChannel();

  /**
   * 刷新所有渠道相关数据
   */
  const refreshAll = useCallback(() => {
    return Promise.all([
      refetchChannels(),
      refetchStats(),
      refetchAnalytics(),
    ]);
  }, [refetchChannels, refetchStats, refetchAnalytics]);

  /**
   * 使缓存失效
   */
  const invalidateCache = useCallback(() => {
    void queryClient.invalidateQueries({ queryKey: QUERY_KEYS.channels });
    void queryClient.invalidateQueries({ queryKey: QUERY_KEYS.analytics });
    void queryClient.invalidateQueries({ queryKey: QUERY_KEYS.statsSummary });
  }, [queryClient]);

  return {
    // 数据
    channels: channels?.channels ?? [],
    statsSummary,
    analytics: analytics ?? [],
    // 加载状态
    isLoading: isLoadingChannels || isLoadingStats || isLoadingAnalytics,
    isLoadingChannels,
    isLoadingStats,
    isLoadingAnalytics,
    // 错误状态
    error: channelsError || statsError || analyticsError,
    channelsError,
    statsError,
    analyticsError,
    // 操作方法
    createChannel,
    updateChannel,
    deleteChannel,
    refreshAll,
    invalidateCache,
  };
}