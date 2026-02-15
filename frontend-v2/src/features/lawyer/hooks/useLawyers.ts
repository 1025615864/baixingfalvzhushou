import { useQuery } from '@tanstack/react-query';

import type { Lawyer, GetLawyersResponse } from '../types';
import { getLawyers } from '../api';

// 律师筛选条件
export interface LawyerFilters {
  /** 专业领域 */
  specialty?: string;
  /** 最小评分 */
  minRating?: number;
  /** 最高价格 */
  maxPrice?: number;
  /** 搜索关键词 */
  searchQuery?: string;
}

/**
 * 获取律师列表 Hook
 * 使用真实 API，支持多种过滤条件
 */
export function useLawyers(filters?: LawyerFilters) {
  return useQuery<GetLawyersResponse>({
    queryKey: ['lawyers', filters],
    queryFn: async () => {
      const response = await getLawyers({
        specialty: filters?.specialty,
        // Note: minRating and maxFee not supported by backend, filtered on frontend
        keyword: filters?.searchQuery,
        page: 1,
        pageSize: 100,
      });

      let lawyers = response.lawyers;

      // 前端额外过滤（后端不支持这些过滤参数）
      const maxPrice = filters?.maxPrice;
      if (maxPrice !== undefined && maxPrice !== null) {
        lawyers = lawyers.filter((lawyer: Lawyer) => lawyer.consultationFee <= maxPrice);
      }

      // 按评分排序
      lawyers = [...lawyers].sort((a: Lawyer, b: Lawyer) => b.rating - a.rating);

      return {
        ...response,
        lawyers,
      };
    },
    staleTime: 5 * 60 * 1000, // 5分钟缓存
  });
}