/**
 * News Content Feature Module
 * 新闻内容管理和 AI 辅助编辑功能模块
 */

export { NewsEditor } from './components/NewsEditor';
export { NewsDashboard } from './components/NewsDashboard';
export { AIContentAssistant } from './components/AIContentAssistant';
export { CategoryManager } from './components/CategoryManager';
export { TagManager } from './components/TagManager';
export { DraftsManager } from './components/DraftsManager';
export { ImageGallery } from './components/ImageGallery';

export {
  useArticles,
  useArticle,
  useCreateArticle,
  useUpdateArticle,
  useDeleteArticle,
  usePublishArticle,
  useArchiveArticle,
  useDrafts,
  useDraft,
  useSaveDraft,
  useDeleteDraft,
  useCategories,
  useCategory,
  useCreateCategory,
  useUpdateCategory,
  useDeleteCategory,
  useReorderCategories,
  useTags,
  useTag,
  useCreateTag,
  useUpdateTag,
  useDeleteTag,
  useAISummary,
  useAIAnalysis,
  useAITags,
  useImproveWithAI,
  useGenerateWithAI,
  useUploadImage,
  useDeleteImage,
} from './hooks';

export type {
  ArticleEditor,
  ArticleDraft,
  NewsCategory,
  NewsTag,
  AIContentAssistance,
  CreateArticleRequest,
  UpdateArticleRequest,
  ArticleListParams,
  DraftListParams,
  TagListParams,
  AiRiskLevel,
  NewsAIAnnotation,
} from './types';
