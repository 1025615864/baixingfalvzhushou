import { useQuery } from '@tanstack/react-query';

import type { Consultation } from '../types';
import { getConsultation } from '../api';

/**
 * 获取咨询详情 Hook
 * 使用真实 API 获取单个咨询详情
 */
export function useConsultationDetail(id: string | undefined) {
  return useQuery<Consultation>({
    queryKey: ['consultation', id],
    queryFn: async () => {
      if (!id) throw new Error('Consultation ID is required');
      return getConsultation(id);
    },
    enabled: !!id,
    staleTime: 5 * 60 * 1000, // 5分钟缓存
  });
}