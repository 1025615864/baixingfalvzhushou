/**
 * 法律文书商城 Hooks
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useState, useCallback } from 'react';

import * as api from '../api';
import type {
  LegalDocumentQueryParams,
} from '../types';

// 查询 keys
export const queryKeys = {
  categories: ['legal-documents', 'categories'] as const,
  documents: (params: LegalDocumentQueryParams) => 
    ['legal-documents', 'list', params] as const,
  featured: (limit: number) => 
    ['legal-documents', 'featured', limit] as const,
  free: (limit: number) => 
    ['legal-documents', 'free', limit] as const,
  document: (id: number) => 
    ['legal-documents', 'detail', id] as const,
  documentContent: (id: number) => 
    ['legal-documents', 'content', id] as const,
  price: (id: number) => 
    ['legal-documents', 'price', id] as const,
  favorites: ['legal-documents', 'favorites'] as const,
  orders: ['legal-documents', 'orders'] as const,
};

/**
 * 获取文书分类
 */
export function useCategories() {
  return useQuery({
    queryKey: queryKeys.categories,
    queryFn: api.apiGetCategories,
  });
}

/**
 * 获取文书列表
 */
export function useDocuments(params: LegalDocumentQueryParams = {}) {
  return useQuery({
    queryKey: queryKeys.documents(params),
    queryFn: () => api.apiGetDocuments(params),
  });
}

/**
 * 获取推荐文书
 */
export function useFeaturedDocuments(limit: number = 6) {
  return useQuery({
    queryKey: queryKeys.featured(limit),
    queryFn: () => api.apiGetFeaturedDocuments(limit),
  });
}

/**
 * 获取免费文书
 */
export function useFreeDocuments(limit: number = 10) {
  return useQuery({
    queryKey: queryKeys.free(limit),
    queryFn: () => api.apiGetFreeDocuments(limit),
  });
}

/**
 * 获取文书详情
 */
export function useDocument(documentId: number) {
  return useQuery({
    queryKey: queryKeys.document(documentId),
    queryFn: () => api.apiGetDocument(documentId),
    enabled: documentId > 0,
  });
}

/**
 * 获取文书内容（需要已购买）
 */
export function useDocumentContent(documentId: number) {
  return useQuery({
    queryKey: queryKeys.documentContent(documentId),
    queryFn: () => api.apiGetDocumentContent(documentId),
    enabled: documentId > 0,
  });
}

/**
 * 计算文书价格
 */
export function useDocumentPrice(documentId: number) {
  return useQuery({
    queryKey: queryKeys.price(documentId),
    queryFn: () => api.apiCalculatePrice(documentId),
    enabled: documentId > 0,
  });
}

/**
 * 获取收藏列表
 */
export function useFavorites() {
  return useQuery({
    queryKey: queryKeys.favorites,
    queryFn: api.apiGetFavorites,
  });
}

/**
 * 获取购买记录
 */
export function useDocumentOrders(page: number = 1, pageSize: number = 20) {
  return useQuery({
    queryKey: [...queryKeys.orders, page, pageSize],
    queryFn: () => api.apiGetDocumentOrders(page, pageSize),
  });
}

/**
 * 购买文书
 */
export function usePurchaseDocument() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: ({ documentId, paymentMethod }: { 
      documentId: number; 
      paymentMethod: 'points' | 'free' | 'member_free';
    }) => api.apiPurchaseDocument(documentId, { payment_method: paymentMethod }),
    onSuccess: () => {
      // 刷新相关数据
      void queryClient.invalidateQueries({ queryKey: queryKeys.orders });
    },
  });
}

/**
 * 收藏/取消收藏文书
 */
export function useToggleFavorite() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: ({ documentId, isFavorited }: { 
      documentId: number; 
      isFavorited: boolean;
    }) => {
      if (isFavorited) {
        return api.apiRemoveFavorite(documentId);
      }
      return api.apiAddFavorite(documentId);
    },
    onSuccess: (_, variables) => {
      // 刷新相关数据
      void queryClient.invalidateQueries({ queryKey: queryKeys.favorites });
      void queryClient.invalidateQueries({ queryKey: queryKeys.document(variables.documentId) });
    },
  });
}

/**
 * 法律文书商城主 Hook
 */
export function useLegalDocumentMall() {
  const [selectedCategory, setSelectedCategory] = useState<string | null>(null);
  const [keyword, setKeyword] = useState('');
  const [page, setPage] = useState(1);
  
  const categoriesQuery = useCategories();
  const documentsQuery = useDocuments({
    category: selectedCategory || undefined,
    keyword: keyword || undefined,
    page,
    page_size: 20,
  });
  const featuredQuery = useFeaturedDocuments(6);
  const freeQuery = useFreeDocuments(10);
  
  const search = useCallback((kw: string) => {
    setKeyword(kw);
    setPage(1);
  }, []);
  
  const selectCategory = useCallback((category: string | null) => {
    setSelectedCategory(category);
    setPage(1);
  }, []);
  
  const goToPage = useCallback((newPage: number) => {
    setPage(newPage);
  }, []);
  
  return {
    // 状态
    selectedCategory,
    keyword,
    page,
    
    // 数据
    categories: categoriesQuery.data,
    documents: documentsQuery.data,
    featured: featuredQuery.data?.items,
    free: freeQuery.data?.items,
    
    // 加载状态
    categoriesLoading: categoriesQuery.isLoading,
    documentsLoading: documentsQuery.isLoading,
    featuredLoading: featuredQuery.isLoading,
    freeLoading: freeQuery.isLoading,
    
    // 操作
    search,
    selectCategory,
    goToPage,
    
    // 刷新
    refetchDocuments: documentsQuery.refetch,
  };
}