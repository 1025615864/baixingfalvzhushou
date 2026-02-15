/**
 * 文档管理功能 React Query Hooks
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';

import type {
  CreateDocumentDTO,
  UpdateDocumentDTO,
  ExportDocumentDTO,
  GenerateDocumentDTO,
  DocumentQueryParams,
} from '../types';
import {
  apiGetMyDocuments,
  apiGetDocument,
  apiCreateDocument,
  apiUpdateDocument,
  apiDeleteDocument,
  apiExportDocumentPdf,
  apiExportMyDocument,
  apiGenerateDocument,
  apiGetDocumentTypes,
} from '../api';
import { documentKeys } from '../api/queryKeys';

// ==================== 文档查询 Hooks ====================

/**
 * 获取我的文档列表 Hook
 */
export function useMyDocuments(params?: DocumentQueryParams) {
  return useQuery({
    queryKey: documentKeys.myListPaginated(params?.page, params?.pageSize),
    queryFn: () => apiGetMyDocuments(params),
  });
}

/**
 * 获取文档详情 Hook
 */
export function useDocument(docId: number) {
  return useQuery({
    queryKey: documentKeys.detail(docId),
    queryFn: () => apiGetDocument(docId),
    enabled: docId > 0,
  });
}

/**
 * 获取支持的文档类型列表 Hook
 */
export function useDocumentTypes() {
  return useQuery({
    queryKey: documentKeys.types(),
    queryFn: apiGetDocumentTypes,
  });
}

// ==================== 文档操作 Hooks ====================

/**
 * 创建文档 Hook
 */
export function useCreateDocument() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: CreateDocumentDTO) => apiCreateDocument(data),
    onSuccess: () => {
      // 创建成功后刷新文档列表
      void queryClient.invalidateQueries({ queryKey: documentKeys.myLists() });
    },
  });
}

/**
 * 更新文档 Hook
 */
export function useUpdateDocument() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ docId, data }: { docId: number; data: UpdateDocumentDTO }) =>
      apiUpdateDocument(docId, data),
    onSuccess: (_, variables) => {
      // 更新成功后刷新文档详情和列表
      void queryClient.invalidateQueries({ queryKey: documentKeys.detail(variables.docId) });
      void queryClient.invalidateQueries({ queryKey: documentKeys.myLists() });
    },
  });
}

/**
 * 删除文档 Hook
 */
export function useDeleteDocument() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (docId: number) => apiDeleteDocument(docId),
    onSuccess: () => {
      // 删除成功后刷新文档列表
      void queryClient.invalidateQueries({ queryKey: documentKeys.myLists() });
    },
  });
}

// ==================== 文档导出 Hooks ====================

/**
 * 导出文档为PDF Hook
 */
export function useExportDocumentPdf() {
  return useMutation({
    mutationFn: (data: ExportDocumentDTO) => apiExportDocumentPdf(data),
    onSuccess: (blob, variables) => {
      // 创建下载链接
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `${variables.title}.pdf`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
    },
  });
}

/**
 * 导出我的文档 Hook
 */
export function useExportMyDocument() {
  return useMutation({
    mutationFn: ({ docId, filename }: { docId: number; filename: string }) =>
      apiExportMyDocument(docId).then(blob => ({ blob, filename })),
    onSuccess: ({ blob, filename }) => {
      // 创建下载链接
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `${filename}.pdf`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
    },
  });
}

// ==================== 文档生成 Hooks ====================

/**
 * 生成法律文书 Hook
 */
export function useGenerateDocument() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: GenerateDocumentDTO) => apiGenerateDocument(data),
    onSuccess: () => {
      // 生成成功后刷新文档列表（新生成的文档会自动保存）
      void queryClient.invalidateQueries({ queryKey: documentKeys.myLists() });
    },
  });
}

// ==================== 组合 Hooks ====================

/**
 * 文档管理完整功能 Hook
 */
export function useDocumentManager() {
  const queryClient = useQueryClient();

  const createMutation = useCreateDocument();
  const updateMutation = useUpdateDocument();
  const deleteMutation = useDeleteDocument();
  const exportPdfMutation = useExportDocumentPdf();
  const exportMyMutation = useExportMyDocument();
  const generateMutation = useGenerateDocument();

  return {
    // 查询
    getDocuments: useMyDocuments,
    getDocument: useDocument,
    getDocumentTypes: useDocumentTypes,

    // 操作
    createDocument: createMutation,
    updateDocument: updateMutation,
    deleteDocument: deleteMutation,

    // 导出
    exportDocumentPdf: exportPdfMutation,
    exportMyDocument: exportMyMutation,

    // 生成
    generateDocument: generateMutation,

    // 工具函数
    invalidateDocuments: () => {
      void queryClient.invalidateQueries({ queryKey: documentKeys.myLists() });
    },
    invalidateDocument: (docId: number) => {
      void queryClient.invalidateQueries({ queryKey: documentKeys.detail(docId) });
    },
  };
}