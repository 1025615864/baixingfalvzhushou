// Knowledge Feature Module

// 组件导出
export { KnowledgeList } from './components/KnowledgeList';
export { KnowledgeCard } from './components/KnowledgeCard';
export { KnowledgeDetail } from './components/KnowledgeDetail';
export { KnowledgeSearch } from './components/KnowledgeSearch';
export { CategoryFilter } from './components/CategoryFilter';
export { KnowledgeViewer } from './components/KnowledgeViewer';

// Hooks 导出
export {
  useKnowledge,
  useKnowledgeDetail,
  useKnowledgeSearch,
  useCategories,
  useKnowledgeStats,
  useCreateKnowledge,
  useUpdateKnowledge,
  useDeleteKnowledge,
} from './hooks/useKnowledge';

// 保留旧 hook 导出以兼容
export { useKnowledgeItems, categoryNames } from './hooks/useKnowledgeItems';

// 类型导出
export type {
  KnowledgeType,
  KnowledgeCategoryType,
  KnowledgeItem,
  KnowledgeArticle,
  KnowledgeCategory,
  KnowledgeTag,
  KnowledgeSearchFilters,
  KnowledgeListResponse,
  KnowledgeDetailResponse,
  CreateKnowledgeRequest,
  UpdateKnowledgeRequest,
  KnowledgeStats,
} from './types';

// API 导出
export { knowledgeApi, default as knowledgeApiDefault } from './api';
export { knowledgeKeys } from './api/queryKeys';