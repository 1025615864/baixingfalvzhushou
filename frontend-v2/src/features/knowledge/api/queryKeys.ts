/**
 * Knowledge（知识库）Query Keys
 * 用于 React Query 的缓存管理
 */

/**
 * 知识库模块的基础 query key
 */
export const knowledgeKeys = {
  all: ['knowledge'] as const,

  /** 知识条目列表 */
  lists: () => [...knowledgeKeys.all, 'list'] as const,
  list: (filters: {
    page?: number;
    pageSize?: number;
    knowledgeType?: string;
    category?: string;
    keyword?: string;
    isActive?: boolean;
  } = {}) => [...knowledgeKeys.lists(), filters] as const,

  /** 单个知识条目详情 */
  details: () => [...knowledgeKeys.all, 'detail'] as const,
  detail: (articleId: string | number) => [...knowledgeKeys.details(), articleId] as const,

  /** 搜索结果 */
  search: (filters: {
    query: string;
    category?: string;
    knowledgeType?: string;
    limit?: number;
  }) => [...knowledgeKeys.all, 'search', filters] as const,

  /** 分类列表 */
  categories: () => [...knowledgeKeys.all, 'categories'] as const,

  /** 统计信息 */
  stats: () => [...knowledgeKeys.all, 'stats'] as const,

  /** 批量操作 */
  batch: () => [...knowledgeKeys.all, 'batch'] as const,

  /** 向量化 */
  vectorize: () => [...knowledgeKeys.all, 'vectorize'] as const,
} as const;

export default knowledgeKeys;