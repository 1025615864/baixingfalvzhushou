/**
 * 文档管理功能 Query Keys
 * 用于 React Query 的缓存管理
 */

export const documentKeys = {
  // 基础 key
  all: ['documents'] as const,
  
  // 文档列表相关
  lists: () => [...documentKeys.all, 'list'] as const,
  list: (filters: { page?: number; pageSize?: number; documentType?: string; keyword?: string }) => 
    [...documentKeys.lists(), filters] as const,
  
  // 我的文档列表
  myLists: () => [...documentKeys.all, 'my', 'list'] as const,
  myList: (params: { page?: number; pageSize?: number }) => 
    [...documentKeys.myLists(), params] as const,
  myListPaginated: (page?: number, pageSize?: number) => 
    [...documentKeys.myLists(), { page, pageSize }] as const,
  
  // 文档详情
  details: () => [...documentKeys.all, 'detail'] as const,
  detail: (docId: number) => [...documentKeys.details(), docId] as const,
  
  // 文档类型
  types: () => [...documentKeys.all, 'types'] as const,
  
  // 文档生成
  generate: () => [...documentKeys.all, 'generate'] as const,
} as const;