/**
 * FAQ（常见问题）Hooks
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useCallback, useState } from 'react';

import type {
  FAQItem,
  CreateFAQRequest,
  UpdateFAQRequest,
  FAQSearchParams,
  FAQSmartSearchRequest,
  FAQFilterState,
  FAQManagerState,
} from '../types';
import {
  apiGetFAQs,
  apiGetFAQ,
  apiGetFAQCcategories,
  apiGetPopularFAQs,
  apiSmartSearchFAQ,
  apiCreateFAQ,
  apiUpdateFAQ,
  apiDeleteFAQ,
  apiGetAdminFAQs,
} from '../api';

// ==================== Query Keys ====================

const QUERY_KEYS = {
  faqs: ['faqs'] as const,
  faq: (id: number) => ['faqs', id] as const,
  categories: ['faqs', 'categories'] as const,
  popular: ['faqs', 'popular'] as const,
  search: (params: FAQSearchParams) => ['faqs', 'search', params] as const,
  adminFAQs: ['faqs', 'admin'] as const,
};

// ==================== Queries ====================

/**
 * 获取FAQ列表
 */
export function useFAQs(params: FAQSearchParams = {}) {
  return useQuery<FAQItem[], Error>({
    queryKey: QUERY_KEYS.search(params),
    queryFn: async () => {
      const response = await apiGetFAQs(params);
      return response.items;
    },
    staleTime: 5 * 60 * 1000, // 5分钟
  });
}

/**
 * 获取FAQ列表（带分页�?
 */
export function useFAQsWithPagination(params: FAQSearchParams = {}) {
  return useQuery({
    queryKey: QUERY_KEYS.search(params),
    queryFn: () => apiGetFAQs(params),
    staleTime: 5 * 60 * 1000,
  });
}

/**
 * 获取单个FAQ
 */
export function useFAQ(id: number | null) {
  return useQuery<FAQItem, Error>({
    queryKey: QUERY_KEYS.faq(id ?? 0),
    queryFn: () => apiGetFAQ(id!),
    enabled: !!id,
    staleTime: 5 * 60 * 1000,
  });
}

/**
 * 获取FAQ分类列表
 */
export function useFAQCategories() {
  return useQuery<string[], Error>({
    queryKey: QUERY_KEYS.categories,
    queryFn: apiGetFAQCcategories,
    staleTime: 10 * 60 * 1000, // 10分钟
  });
}

/**
 * 获取热门FAQ
 */
export function usePopularFAQs(category?: string, limit: number = 10) {
  return useQuery<FAQItem[], Error>({
    queryKey: [...QUERY_KEYS.popular, category, limit],
    queryFn: () => apiGetPopularFAQs(category, limit),
    staleTime: 10 * 60 * 1000,
  });
}

/**
 * FAQ智能搜索
 */
export function useSmartSearchFAQ() {
  return useMutation({
    mutationFn: (request: FAQSmartSearchRequest) => apiSmartSearchFAQ(request),
  });
}

// ==================== Admin Queries ====================

/**
 * 管理�?获取FAQ列表（包含未激活的�?
 */
export function useAdminFAQs(params: FAQSearchParams = {}) {
  return useQuery({
    queryKey: [...QUERY_KEYS.adminFAQs, params],
    queryFn: () => apiGetAdminFAQs(params),
    staleTime: 5 * 60 * 1000,
  });
}

// ==================== Mutations ====================

/**
 * 创建FAQ
 */
export function useCreateFAQ() {
  const queryClient = useQueryClient();

  return useMutation<FAQItem, Error, CreateFAQRequest>({
    mutationFn: apiCreateFAQ,
    onSuccess: () => {
      // 创建成功后，刷新FAQ列表和分�?
      void queryClient.invalidateQueries({ queryKey: QUERY_KEYS.faqs });
      void queryClient.invalidateQueries({ queryKey: QUERY_KEYS.adminFAQs });
      void queryClient.invalidateQueries({ queryKey: QUERY_KEYS.categories });
    },
  });
}

/**
 * 更新FAQ
 */
export function useUpdateFAQ() {
  const queryClient = useQueryClient();

  return useMutation<
    FAQItem,
    Error,
    { id: number; data: UpdateFAQRequest }
  >({
    mutationFn: ({ id, data }) => apiUpdateFAQ(id, data),
    onSuccess: (_, variables) => {
      // 更新成功后，刷新相关缓存
      void queryClient.invalidateQueries({
        queryKey: QUERY_KEYS.faq(variables.id),
      });
      void queryClient.invalidateQueries({ queryKey: QUERY_KEYS.faqs });
      void queryClient.invalidateQueries({ queryKey: QUERY_KEYS.adminFAQs });
      void queryClient.invalidateQueries({ queryKey: QUERY_KEYS.categories });
    },
  });
}

/**
 * 删除FAQ
 */
export function useDeleteFAQ() {
  const queryClient = useQueryClient();

  return useMutation<void, Error, number>({
    mutationFn: apiDeleteFAQ,
    onSuccess: () => {
      // 删除成功后，刷新所有相关缓�?
      void queryClient.invalidateQueries({ queryKey: QUERY_KEYS.faqs });
      void queryClient.invalidateQueries({ queryKey: QUERY_KEYS.adminFAQs });
      void queryClient.invalidateQueries({ queryKey: QUERY_KEYS.popular });
    },
  });
}

// ==================== 综合 Hooks ====================

/**
 * FAQ筛选状态管�?
 */
export function useFAQFilter(initialState?: Partial<FAQFilterState>) {
  const [filter, setFilterState] = useState<FAQFilterState>({
    keyword: '',
    category: '',
    page: 1,
    pageSize: 20,
    ...initialState,
  });

  const setFilter = useCallback((updates: Partial<FAQFilterState>) => {
    setFilterState((prev) => ({ ...prev, ...updates }));
  }, []);

  const resetFilter = useCallback(() => {
    setFilterState({
      keyword: '',
      category: '',
      page: 1,
      pageSize: 20,
    });
  }, []);

  return {
    filter,
    setFilter,
    resetFilter,
  };
}

/**
 * FAQ管理综合 Hook
 */
export function useFAQManager(): FAQManagerState {
  const [selectedId, setSelectedId] = useState<number | null>(null);

  // 筛选状�?
  const { filter, setFilter } = useFAQFilter();

  // 数据查询
  const {
    data: faqsData,
    isLoading: isLoadingFAQs,
    refetch: refetchFAQs,
  } = useFAQsWithPagination({
    keyword: filter.keyword || undefined,
    category: filter.category || undefined,
    page: filter.page,
    pageSize: filter.pageSize,
  });

  const {
    data: categories = [],
    isLoading: isLoadingCategories,
  } = useFAQCategories();

  const {
    data: popularFAQs = [],
    isLoading: isLoadingPopular,
  } = usePopularFAQs();

  const {
    data: selectedFAQ,
    isLoading: isLoadingSelected,
  } = useFAQ(selectedId);

  // Mutations
  const createMutation = useCreateFAQ();
  const updateMutation = useUpdateFAQ();
  const deleteMutation = useDeleteFAQ();

  // 操作函数
  const selectFAQ = useCallback((id: number | null) => {
    setSelectedId(id);
  }, []);

  const refetch = useCallback(() => {
    void refetchFAQs();
  }, [refetchFAQs]);

  const createFAQ = useCallback(
    async (data: CreateFAQRequest) => {
      await createMutation.mutateAsync(data);
    },
    [createMutation]
  );

  const updateFAQ = useCallback(
    async (id: number, data: UpdateFAQRequest) => {
      await updateMutation.mutateAsync({ id, data });
    },
    [updateMutation]
  );

  const deleteFAQ = useCallback(
    async (id: number) => {
      await deleteMutation.mutateAsync(id);
      if (selectedId === id) {
        setSelectedId(null);
      }
    },
    [deleteMutation, selectedId]
  );

  return {
    // 数据
    faqs: faqsData?.items ?? [],
    categories,
    popularFAQs,
    selectedFAQ: selectedFAQ ?? null,

    // 加载状�?
    isLoading: isLoadingFAQs || isLoadingSelected,
    isLoadingCategories,
    isLoadingPopular,

    // 筛选和分页
    filter,
    total: faqsData?.total ?? 0,

    // 操作函数
    setFilter,
    refetch,
    selectFAQ,
    createFAQ,
    updateFAQ,
    deleteFAQ,
  };
}

/**
 * 管理员FAQ管理 Hook
 */
export function useFAQAdminManager() {
  const [selectedId, setSelectedId] = useState<number | null>(null);

  // 筛选状?
  const { filter, setFilter } = useFAQFilter();

  // 数据查询
  const {
    data: faqsData,
    isLoading: isLoadingFAQs,
    refetch: refetchFAQs,
  } = useAdminFAQs({
    keyword: filter.keyword || undefined,
    category: filter.category || undefined,
    page: filter.page,
    pageSize: filter.pageSize,
  });

  const {
    data: categories = [],
    isLoading: isLoadingCategories,
  } = useFAQCategories();

  const {
    data: selectedFAQ,
    isLoading: isLoadingSelected,
  } = useFAQ(selectedId);

  // Mutations
  const createMutation = useCreateFAQ();
  const updateMutation = useUpdateFAQ();
  const deleteMutation = useDeleteFAQ();

  // 操作函数
  const selectFAQ = useCallback((id: number | null) => {
    setSelectedId(id);
  }, []);

  const refetch = useCallback(() => {
    void refetchFAQs();
  }, [refetchFAQs]);

  const createFAQ = useCallback(
    async (data: CreateFAQRequest) => {
      await createMutation.mutateAsync(data);
    },
    [createMutation]
  );

  const updateFAQ = useCallback(
    async (id: number, data: UpdateFAQRequest) => {
      await updateMutation.mutateAsync({ id, data });
    },
    [updateMutation]
  );

  const deleteFAQ = useCallback(
    async (id: number) => {
      await deleteMutation.mutateAsync(id);
      if (selectedId === id) {
        setSelectedId(null);
      }
    },
    [deleteMutation, selectedId]
  );

  return {
    // 数据
    faqs: faqsData?.items ?? [],
    categories,
    selectedFAQ: selectedFAQ ?? null,

    // 加载状�?
    isLoading: isLoadingFAQs || isLoadingSelected,
    isLoadingCategories,

    // 筛选和分页
    filter,
    total: faqsData?.total ?? 0,

    // 操作函数
    setFilter,
    refetch,
    selectFAQ,
    createFAQ,
    updateFAQ,
    deleteFAQ,

    // 额外状�?
    isCreating: createMutation.isPending,
    isUpdating: updateMutation.isPending,
    isDeleting: deleteMutation.isPending,
  };
}
