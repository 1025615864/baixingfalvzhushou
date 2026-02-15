import { useQuery } from '@tanstack/react-query';

import type { Consultation, ConsultationFilters, ConsultationStatus } from '../types';
import { getConsultations } from '../api';

/**
 * 获取咨询列表 Hook
 * 使用真实 API，支持状态过滤
 */
export function useConsultations(filters?: ConsultationFilters) {
  return useQuery<{
    items: Consultation[];
    total: number;
    page: number;
    pageSize: number;
  }>({
    queryKey: ['consultations', filters],
    queryFn: async () => {
      const response = await getConsultations({
        status: filters?.status as ConsultationStatus | undefined,
        page: 1,
        pageSize: 100,
      });

      let items = response.items;

      // 前端额外过滤（category 和 searchQuery 不在后端支持）
      if (filters?.category) {
        items = items.filter((c) => c.category === filters.category);
      }
      if (filters?.searchQuery) {
        const query = filters.searchQuery.toLowerCase();
        items = items.filter(
          (c) =>
            c.subject.toLowerCase().includes(query) ||
            (c.description && c.description.toLowerCase().includes(query))
        );
      }

      return {
        ...response,
        items,
      };
    },
    staleTime: 30 * 1000, // 30秒缓存
  });
}