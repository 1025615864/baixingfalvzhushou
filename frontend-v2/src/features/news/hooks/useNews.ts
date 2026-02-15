import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';

import type { News, NewsFilters, NewsLikeDTO, NewsCategoryType } from '../types';
import { apiGetNewsList, apiGetNewsDetail, apiToggleFavorite } from '../api';

const categoryNames: Record<string, string> = {
  legal: '法律新闻',
  case: '典型案例',
  policy: '政策法规',
  industry: '行业动态',
};

interface UseNewsReturn {
  data: News[] | undefined;
  isLoading: boolean;
  isError: boolean;
  error: Error | null;
}

/**
 * 将API返回的新闻数据转换为前端News格式
 */
function mapListItemToNews(item: {
  id: string;
  title: string;
  summary: string;
  categoryName: string;
  source: string;
  viewCount: number;
  favoriteCount: number;
  isFavorited: boolean;
  isTop: boolean;
  publishedAt?: string;
}): News {
  return {
    id: item.id,
    title: item.title,
    summary: item.summary,
    content: '', // 列表不返回内容
    category: item.categoryName as NewsCategoryType,
    author: item.source,
    viewCount: item.viewCount,
    likeCount: item.favoriteCount,
    commentCount: 0, // 后端暂不返回
    publishedAt: item.publishedAt ?? '',
    createdAt: item.publishedAt ?? '',
    updatedAt: item.publishedAt ?? '',
    tags: [],
    isFeatured: item.isTop,
  };
}

/**
 * 获取资讯列表 Hook
 * 使用真实 API，支持分类和搜索过滤
 */
export function useNews(filters?: NewsFilters): UseNewsReturn {
  const query = useQuery<News[], Error>({
    queryKey: ['news', filters],
    queryFn: async () => {
      const response = await apiGetNewsList({
        categoryId: filters?.category,
        keyword: filters?.searchQuery,
        page: 1,
        pageSize: 50,
        // Note: isTop not supported by backend API, filtered on frontend
      });

      let items = response.items.map(mapListItemToNews);

      // 前端额外过滤
      if (filters?.category && filters.category.length > 0) {
        items = items.filter((item) => item.category === filters.category);
      }

      if (filters?.featured === true) {
        items = items.filter((item) => item.isFeatured);
      }

      // 按发布时间排序
      items = items.sort(
        (a, b) =>
          new Date(b.publishedAt).getTime() - new Date(a.publishedAt).getTime()
      );

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

/**
 * 获取资讯详情 Hook
 * 使用真实 API
 */
export function useNewsDetail(id: string | undefined) {
  return useQuery<News, Error>({
    queryKey: ['news', 'detail', id],
    queryFn: async () => {
      if (!id) throw new Error('News ID is required');

      const article = await apiGetNewsDetail(id);

      return {
        id: article.id,
        title: article.title,
        summary: article.summary,
        content: article.content,
        category: article.category.name as NewsCategoryType,
        author: article.author.name,
        viewCount: article.viewCount,
        likeCount: article.favoriteCount,
        commentCount: 0,
        publishedAt: article.publishedAt ?? '',
        createdAt: article.createdAt,
        updatedAt: article.updatedAt,
        tags: [],
        isFeatured: article.isTop,
      };
    },
    enabled: !!id,
    staleTime: 10 * 60 * 1000, // 10分钟缓存
  });
}

/**
 * 点赞/收藏资讯 Hook
 * 使用真实 API
 */
export function useLikeNews() {
  const queryClient = useQueryClient();

  return useMutation<void, Error, NewsLikeDTO>({
    mutationFn: async (data: NewsLikeDTO): Promise<void> => {
      await apiToggleFavorite(data.newsId);
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['news'] });
    },
  });
}

export { categoryNames };