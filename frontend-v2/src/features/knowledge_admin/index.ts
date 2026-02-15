/**
 * Knowledge-Admin（知识库管理）模块导出
 */

// 类型导出
export type * from './types';

// Hooks 导出
export {
  useArticles,
  useArticle,
  useCategories,
  useKnowledgeStats,
  useKnowledgeSearch,
  useCreateArticle,
  useUpdateArticle,
  useDeleteArticle,
  useCreateCategory,
  useBatchImport,
  useImportSample,
  useKnowledgeAdmin,
} from './hooks/useKnowledgeAdmin';

// API 导出
export {
  apiGetArticles,
  apiGetArticle,
  apiCreateArticle,
  apiUpdateArticle,
  apiDeleteArticle,
  apiGetCategories,
  apiCreateCategory,
  apiGetStats,
  apiSearchKnowledge,
  apiBatchImport,
  apiImportSample,
} from './api';

// 组件导出
export { ArticleList } from './components/ArticleList';
export { ArticleEditor } from './components/ArticleEditor';
export { CategoryManager } from './components/CategoryManager';
export { KnowledgeStatsComponent as KnowledgeStats } from './components/KnowledgeStats';

// 页面导出
export { KnowledgeAdminPage } from './pages/KnowledgeAdminPage';