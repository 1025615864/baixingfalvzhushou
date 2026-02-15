import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';

import type { DocumentFilters, UploadDocumentDTO, DocumentFileType, DocumentStatus, DocumentListResponse } from '../types';
import { apiGetMyDocuments } from '../api';
import { apiUploadFile } from '../../upload/api';

// 文档类型名称配置
const typeNames: Record<DocumentFileType, string> = {
  contract: '合同',
  agreement: '协议',
  certificate: '证件',
  evidence: '证据材料',
  other: '其他',
};

// 文档状态配置
const statusConfig: Record<DocumentStatus, { label: string; color: string }> = {
  draft: { label: '草稿', color: 'bg-gray-100 text-gray-800' },
  pending: { label: '审核中', color: 'bg-yellow-100 text-yellow-800' },
  approved: { label: '已通过', color: 'bg-green-100 text-green-800' },
  rejected: { label: '已驳回', color: 'bg-red-100 text-red-800' },
  archived: { label: '已归档', color: 'bg-blue-100 text-blue-800' },
  deleted: { label: '已删除', color: 'bg-gray-200 text-gray-600' },
};

/**
 * 获取文档列表 Hook
 * 使用真实 API 获取文档列表
 */
export function useDocuments(filters?: DocumentFilters) {
  return useQuery<DocumentListResponse>({
    queryKey: ['documents', filters],
    queryFn: async () => {
      const response = await apiGetMyDocuments({
        page: 1,
        pageSize: 100,
      });

      let items = [...response.items];

      // 前端过滤（如果 API 不支持这些过滤参数）
      if (filters?.searchQuery) {
        const query = filters.searchQuery.toLowerCase();
        items = items.filter(
          (doc) => doc.title.toLowerCase().includes(query)
        );
      }

      return {
        items,
        total: items.length,
      };
    },
    staleTime: 5 * 60 * 1000, // 5分钟缓存
  });
}

/**
 * 上传文档 Hook
 * 使用真实 API 上传文件
 */
export function useUploadDocument() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (data: UploadDocumentDTO): Promise<{ url: string; filename: string }> => {
      const response = await apiUploadFile({
        file: data.file,
        onProgress: undefined,
      });
      
      return {
        url: response.url,
        filename: response.filename,
      };
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['documents'] });
    },
  });
}

export { typeNames, statusConfig };