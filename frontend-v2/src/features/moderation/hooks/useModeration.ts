/**
 * Moderation（内容审核）Hooks
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useCallback, useState } from 'react';

import type {
  ModerationQueueItem,
  ModerationRecord,
  ModerationStats,
  ContentType,
  ModerationStatus,
  RiskLevel,
  ReviewAction,
  GetModerationQueueRequest,
  GetModerationRecordsRequest,
  SubmitReviewRequest,
  BatchReviewRequest,
} from '../types';
import {
  apiGetModerationQueue,
  apiGetModerationRecords,
  apiSubmitReview,
  apiBatchReview,
  apiGetModerationStats,
  apiGetContentDetail,
  apiCheckKeywords,
} from '../api';

// ==================== Query Keys ====================

const QUERY_KEYS = {
  queue: ['moderation', 'queue'] as const,
  queueFiltered: (filters: GetModerationQueueRequest) => ['moderation', 'queue', filters] as const,
  records: ['moderation', 'records'] as const,
  recordsFiltered: (filters: GetModerationRecordsRequest) => ['moderation', 'records', filters] as const,
  stats: ['moderation', 'stats'] as const,
  statsByDate: (startDate?: string, endDate?: string) => ['moderation', 'stats', startDate, endDate] as const,
  contentDetail: (contentId: string, contentType: string) => ['moderation', 'content', contentId, contentType] as const,
};

// ==================== Queries ====================

/**
 * 获取审核队列
 */
export function useModerationQueue(params?: GetModerationQueueRequest) {
  return useQuery<{ items: ModerationQueueItem[]; total: number }, Error>({
    queryKey: params ? QUERY_KEYS.queueFiltered(params) : QUERY_KEYS.queue,
    queryFn: () => apiGetModerationQueue(params),
    staleTime: 30 * 1000, // 30秒
  });
}

/**
 * 获取审核记录
 */
export function useModerationRecords(params?: GetModerationRecordsRequest) {
  return useQuery<{ records: ModerationRecord[]; total: number }, Error>({
    queryKey: params ? QUERY_KEYS.recordsFiltered(params) : QUERY_KEYS.records,
    queryFn: () => apiGetModerationRecords(params),
    staleTime: 60 * 1000, // 1分钟
  });
}

/**
 * 获取审核统计
 */
export function useModerationStats(startDate?: string, endDate?: string) {
  return useQuery<ModerationStats, Error>({
    queryKey: QUERY_KEYS.statsByDate(startDate, endDate),
    queryFn: () => apiGetModerationStats(startDate, endDate),
    staleTime: 5 * 60 * 1000, // 5分钟
  });
}

/**
 * 获取内容详情
 */
export function useContentDetail(contentId: string, contentType: string) {
  return useQuery({
    queryKey: QUERY_KEYS.contentDetail(contentId, contentType),
    queryFn: () => apiGetContentDetail(contentId, contentType),
    enabled: !!contentId && !!contentType,
    staleTime: 2 * 60 * 1000, // 2分钟
  });
}

// ==================== Mutations ====================

/**
 * 提交审核
 */
export function useSubmitReview() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (request: SubmitReviewRequest) => apiSubmitReview(request),
    onSuccess: () => {
      // 审核成功后，刷新队列和统计
      void queryClient.invalidateQueries({ queryKey: QUERY_KEYS.queue });
      void queryClient.invalidateQueries({ queryKey: QUERY_KEYS.records });
      void queryClient.invalidateQueries({ queryKey: QUERY_KEYS.stats });
    },
  });
}

/**
 * 批量审核
 */
export function useBatchReview() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (request: BatchReviewRequest) => apiBatchReview(request),
    onSuccess: () => {
      // 批量审核成功后，刷新队列和统计
      void queryClient.invalidateQueries({ queryKey: QUERY_KEYS.queue });
      void queryClient.invalidateQueries({ queryKey: QUERY_KEYS.records });
      void queryClient.invalidateQueries({ queryKey: QUERY_KEYS.stats });
    },
  });
}

/**
 * 关键词检查
 */
export function useCheckKeywords() {
  return useMutation({
    mutationFn: ({ content, categories }: { content: string; categories?: string[] }) =>
      apiCheckKeywords({ content, categories }),
  });
}

// ==================== 综合 Hook ====================

/**
 * 审核管理综合 Hook
 */
export function useModerationManager() {
  const _queryClient = useQueryClient();
  const [selectedItems, setSelectedItems] = useState<string[]>([]);

  // 查询参数状态
  const [queueFilters, setQueueFilters] = useState<GetModerationQueueRequest>({
    page: 1,
    pageSize: 20,
  });

  const [recordFilters, setRecordFilters] = useState<GetModerationRecordsRequest>({
    page: 1,
    pageSize: 20,
  });

  // 数据查询
  const {
    data: queueData,
    isLoading: isLoadingQueue,
    error: queueError,
    refetch: refetchQueue,
  } = useModerationQueue(queueFilters);

  const {
    data: recordsData,
    isLoading: isLoadingRecords,
    error: recordsError,
    refetch: refetchRecords,
  } = useModerationRecords(recordFilters);

  const {
    data: stats,
    isLoading: isLoadingStats,
    error: statsError,
    refetch: refetchStats,
  } = useModerationStats();

  // Mutations
  const submitReview = useSubmitReview();
  const batchReview = useBatchReview();

  /**
   * 刷新所有数据
   */
  const refreshAll = useCallback(() => {
    return Promise.all([
      refetchQueue(),
      refetchRecords(),
      refetchStats(),
    ]);
  }, [refetchQueue, refetchRecords, refetchStats]);

  /**
   * 选择/取消选择项目
   */
  const toggleSelectItem = useCallback((id: string) => {
    setSelectedItems((prev) =>
      prev.includes(id) ? prev.filter((item) => item !== id) : [...prev, id]
    );
  }, []);

  /**
   * 全选/取消全选
   */
  const toggleSelectAll = useCallback((ids: string[]) => {
    setSelectedItems((prev) => {
      const allSelected = ids.every((id) => prev.includes(id));
      if (allSelected) {
        return prev.filter((id) => !ids.includes(id));
      }
      return [...new Set([...prev, ...ids])];
    });
  }, []);

  /**
   * 清空选择
   */
  const clearSelection = useCallback(() => {
    setSelectedItems([]);
  }, []);

  /**
   * 更新队列筛选条件
   */
  const updateQueueFilters = useCallback((filters: Partial<GetModerationQueueRequest>) => {
    setQueueFilters((prev) => ({ ...prev, ...filters, page: 1 }));
  }, []);

  /**
   * 更新记录筛选条件
   */
  const updateRecordFilters = useCallback((filters: Partial<GetModerationRecordsRequest>) => {
    setRecordFilters((prev) => ({ ...prev, ...filters, page: 1 }));
  }, []);

  /**
   * 处理分页
   */
  const setQueuePage = useCallback((page: number) => {
    setQueueFilters((prev) => ({ ...prev, page }));
  }, []);

  const setRecordPage = useCallback((page: number) => {
    setRecordFilters((prev) => ({ ...prev, page }));
  }, []);

  /**
   * 执行单个审核
   */
  const handleReview = useCallback(
    async (id: string, action: ReviewAction, reason?: string, note?: string) => {
      await submitReview.mutateAsync({ id, action, reason, note });
    },
    [submitReview]
  );

  /**
   * 执行批量审核
   */
  const handleBatchReview = useCallback(
    async (action: ReviewAction, reason?: string, note?: string) => {
      if (selectedItems.length === 0) return;
      await batchReview.mutateAsync({
        ids: selectedItems,
        action,
        reason,
        note,
      });
      clearSelection();
    },
    [batchReview, selectedItems, clearSelection]
  );

  return {
    // 队列数据
    queueItems: queueData?.items ?? [],
    queueTotal: queueData?.total ?? 0,
    isLoadingQueue,
    queueError,

    // 记录数据
    records: recordsData?.records ?? [],
    recordsTotal: recordsData?.total ?? 0,
    isLoadingRecords,
    recordsError,

    // 统计数据
    stats,
    isLoadingStats,
    statsError,

    // 筛选条件
    queueFilters,
    recordFilters,
    updateQueueFilters,
    updateRecordFilters,

    // 分页
    setQueuePage,
    setRecordPage,

    // 选择功能
    selectedItems,
    toggleSelectItem,
    toggleSelectAll,
    clearSelection,

    // 操作
    handleReview,
    handleBatchReview,
    isSubmitting: submitReview.isPending || batchReview.isPending,

    // 刷新
    refreshAll,
    refetchQueue,
    refetchRecords,
    refetchStats,
  };
}

// ==================== 工具 Hooks ====================

/**
 * 审核筛选器 Hook
 */
export function useModerationFilters() {
  const [contentType, setContentType] = useState<ContentType | undefined>();
  const [status, setStatus] = useState<ModerationStatus | undefined>();
  const [riskLevel, setRiskLevel] = useState<RiskLevel | undefined>();
  const [dateRange, setDateRange] = useState<[string, string] | undefined>();

  const resetFilters = useCallback(() => {
    setContentType(undefined);
    setStatus(undefined);
    setRiskLevel(undefined);
    setDateRange(undefined);
  }, []);

  return {
    contentType,
    status,
    riskLevel,
    dateRange,
    setContentType,
    setStatus,
    setRiskLevel,
    setDateRange,
    resetFilters,
  };
}

/**
 * 审核详情 Hook
 */
export function useModerationDetail(item?: ModerationQueueItem) {
  const [isDetailVisible, setIsDetailVisible] = useState(false);
  const [activeTab, setActiveTab] = useState<'content' | 'history' | 'ai'>('content');

  const showDetail = useCallback(() => {
    setIsDetailVisible(true);
  }, []);

  const hideDetail = useCallback(() => {
    setIsDetailVisible(false);
  }, []);

  const { data: contentDetail, isLoading: isLoadingDetail } = useContentDetail(
    item?.contentId ?? '',
    item?.contentType ?? ''
  );

  return {
    isDetailVisible,
    activeTab,
    setActiveTab,
    showDetail,
    hideDetail,
    contentDetail,
    isLoadingDetail,
  };
}