import { useQuery } from '@tanstack/react-query';

import type { KnowledgeItem, KnowledgeSearchFilters } from '../types';
import { apiGetArticles, apiSearchArticles } from '../api';

// 分类名称映射
const categoryNames: Record<string, string> = {
  labor: '劳动纠纷',
  contract: '合同纠纷',
  marriage: '婚姻家庭',
  property: '房产纠纷',
  consumer: '消费者权益',
  criminal: '刑事辩护',
  traffic: '交通事故',
  intellectual: '知识产权',
  inheritance: '继承纠纷',
  other: '其他',
};

interface UseKnowledgeItemsReturn {
  data: KnowledgeItem[] | undefined;
  isLoading: boolean;
  isError: boolean;
  error: Error | null;
}

/**
 * 将后端知识文章转换为前端展示格式
 */
function mapArticleToItem(article: {
  id: string;
  title: string;
  content: string;
  summary?: string;
  category: string;
  keywords?: string;
  createdAt: string;
  updatedAt: string;
}): KnowledgeItem {
  return {
    id: article.id,
    title: article.title,
    content: article.content,
    summary: article.summary ?? '',
    category: article.category,
    tags: article.keywords ? article.keywords.split(',').map(k => k.trim()).filter(Boolean) : [],
    viewCount: 0, // 后端暂不支持
    likeCount: 0, // 后端暂不支持
    createdAt: article.createdAt,
    updatedAt: article.updatedAt,
    relatedLaws: [], // 后端暂不支持
  };
}

/**
 * 获取知识库列表 Hook
 * 使用真实 API，支持搜索和分类过滤
 */
export function useKnowledgeItems(
  filters?: KnowledgeSearchFilters
): UseKnowledgeItemsReturn {
  const query = useQuery<KnowledgeItem[], Error>({
    queryKey: ['knowledge-items', filters],
    queryFn: async () => {
      // 如果有搜索关键词，使用搜索 API
      if (filters?.searchQuery && filters.searchQuery.trim().length > 0) {
        const response = await apiSearchArticles({
          query: filters.searchQuery,
          category: filters.category,
        });
        return response.items.map(mapArticleToItem);
      }

      // 否则使用列表 API
      const response = await apiGetArticles({
        category: filters?.category,
        isActive: true,
        pageSize: 100,
      });

      let items = response.items.map(mapArticleToItem);

      // 前端额外过滤（如果有）
      if (filters?.category) {
        items = items.filter(item => item.category === filters.category);
      }

      return items;
    },
    staleTime: 5 * 60 * 1000, // 5分钟缓存
  });

  return {
    data: query.data,
    isLoading: query.isLoading,
    isError: query.isError,
    error: query.error,
  };
}

export { categoryNames };