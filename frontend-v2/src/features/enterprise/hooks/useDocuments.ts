/**
 * Documents（文档管理）Hooks
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';

import type {
  EnterpriseDocument,
  GetDocumentsRequest,
  GetDocumentsResponse,
  UploadDocumentRequest,
  UpdateDocumentRequest,
  GetDocumentVersionsResponse,
} from '../types';
import {
  apiGetDocuments,
  apiGetDocumentById,
  apiUploadDocument,
  apiUpdateDocument,
  apiDeleteDocument,
  apiGetDocumentVersions,
} from '../api';

// ==================== Query Keys ====================

const DOCUMENTS_QUERY_KEYS = {
  documents: (accountId: number, params?: GetDocumentsRequest) =>
    ['documents', 'list', accountId, params] as const,
  document: (documentId: number) => ['documents', 'detail', documentId] as const,
  versions: (documentId: number) => ['documents', 'versions', documentId] as const,
} as const;

// ==================== Document Hooks ====================

/**
 * 获取文档列表 Hook
 */
export function useDocuments(accountId: number, params: GetDocumentsRequest = {}) {
  return useQuery<GetDocumentsResponse>({
    queryKey: DOCUMENTS_QUERY_KEYS.documents(accountId, params),
    queryFn: async () => {
      const response = await apiGetDocuments(accountId, params);
      return response;
    },
    staleTime: 60 * 1000, // 1分钟缓存
    enabled: accountId > 0,
  });
}

/**
 * 获取单个文档详情 Hook
 */
export function useDocument(accountId: number, documentId: number) {
  return useQuery<EnterpriseDocument>({
    queryKey: DOCUMENTS_QUERY_KEYS.document(documentId),
    queryFn: () => apiGetDocumentById(accountId, documentId),
    staleTime: 5 * 60 * 1000, // 5分钟缓存
    enabled: documentId > 0,
  });
}

/**
 * 上传文档 Hook
 */
export function useUploadDocument(accountId: number) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (request: UploadDocumentRequest) => apiUploadDocument(accountId, request),
    onSuccess: () => {
      // 上传成功后刷新文档列表
      void queryClient.invalidateQueries({ queryKey: ['documents', 'list', accountId] });
    },
  });
}

/**
 * 更新文档 Hook
 */
export function useUpdateDocument(accountId: number, documentId: number) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (request: UpdateDocumentRequest) => apiUpdateDocument(accountId, documentId, request),
    onSuccess: () => {
      // 更新成功后刷新文档详情和列表
      void queryClient.invalidateQueries({ queryKey: DOCUMENTS_QUERY_KEYS.document(documentId) });
      void queryClient.invalidateQueries({ queryKey: ['documents', 'list', accountId] });
    },
  });
}

/**
 * 删除文档 Hook
 */
export function useDeleteDocument(accountId: number) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (documentId: number) => apiDeleteDocument(accountId, documentId),
    onSuccess: () => {
      // 删除成功后刷新文档列表
      void queryClient.invalidateQueries({ queryKey: ['documents', 'list', accountId] });
    },
  });
}

/**
 * 获取文档版本历史 Hook
 */
export function useDocumentVersions(accountId: number, documentId: number) {
  return useQuery<GetDocumentVersionsResponse>({
    queryKey: DOCUMENTS_QUERY_KEYS.versions(documentId),
    queryFn: async () => {
      const response = await apiGetDocumentVersions(accountId, documentId);
      return response;
    },
    staleTime: 5 * 60 * 1000, // 5分钟缓存
    enabled: documentId > 0,
  });
}