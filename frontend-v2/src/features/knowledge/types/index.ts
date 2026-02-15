/**
 * Knowledge（知识库）类型定义
 */

// ==================== 核心类型 ====================

/** 知识类型 */
export type KnowledgeType = 'law' | 'case' | 'regulation' | 'interpretation';

/** 知识分类类型 */
export type KnowledgeCategoryType = 
  | 'labor'      // 劳动纠纷
  | 'contract'   // 合同纠纷
  | 'marriage'   // 婚姻家庭
  | 'property'   // 房产纠纷
  | 'consumer'   // 消费者权益
  | 'traffic'    // 交通事故
  | 'inheritance'// 继承纠纷
  | 'other';     // 其他

/** 知识库条目（前端展示用） */
export interface KnowledgeItem {
  id: string;
  title: string;
  content: string;
  summary: string;
  category: string;
  tags: string[];
  viewCount: number;
  likeCount: number;
  createdAt: string;
  updatedAt: string;
  relatedLaws?: string[];
}

/** 知识搜索筛选 */
export interface KnowledgeSearchFilters {
  category?: string;
  searchQuery?: string;
}

/** 法律知识条目 */
export interface KnowledgeArticle {
  id: string;
  knowledgeType: KnowledgeType;
  title: string;
  articleNumber?: string;
  content: string;
  summary?: string;
  category: string;
  keywords?: string;
  source?: string;
  sourceUrl?: string;
  sourceVersion?: string;
  effectiveDate?: string;
  weight: number;
  isActive: boolean;
  isVectorized: boolean;
  createdAt: string;
  updatedAt: string;
}

/** 知识分类 */
export interface KnowledgeCategory {
  id: string;
  name: string;
  description?: string;
  parentId?: string;
  icon: string;
  sortOrder: number;
  isActive: boolean;
  createdAt: string;
}

/** 知识标签 */
export interface KnowledgeTag {
  id: string;
  name: string;
  color?: string;
  usageCount: number;
  createdAt: string;
}

/** 咨询模板问题项 */
export interface TemplateQuestionItem {
  question: string;
  hint?: string;
}

/** 咨询模板 */
export interface ConsultationTemplate {
  id: string;
  name: string;
  description?: string;
  category: string;
  icon: string;
  questions: TemplateQuestionItem[];
  sortOrder: number;
  isActive: boolean;
  createdAt: string;
  updatedAt: string;
}

// ==================== API 请求/响应类型 ====================

/** 创建法律知识请求 */
export interface CreateArticleRequest {
  knowledgeType: KnowledgeType;
  title: string;
  articleNumber?: string;
  content: string;
  summary?: string;
  category: string;
  keywords?: string;
  source?: string;
  sourceUrl?: string;
  effectiveDate?: string;
  weight?: number;
  isActive?: boolean;
}

/** 更新法律知识请求 */
export interface UpdateArticleRequest {
  knowledgeType?: KnowledgeType;
  title?: string;
  articleNumber?: string;
  content?: string;
  summary?: string;
  category?: string;
  keywords?: string;
  source?: string;
  sourceUrl?: string;
  effectiveDate?: string;
  weight?: number;
  isActive?: boolean;
}

/** 获取文章列表请求 */
export interface GetArticlesRequest {
  page?: number;
  pageSize?: number;
  knowledgeType?: string;
  category?: string;
  keyword?: string;
  isActive?: boolean;
}

/** 获取文章列表响应 */
export interface GetArticlesResponse {
  items: KnowledgeArticle[];
  total: number;
  page: number;
  pageSize: number;
}

/** 搜索文章请求 */
export interface SearchArticlesRequest {
  query: string;
  category?: string;
  knowledgeType?: string;
  limit?: number;
}

/** 搜索文章响应 */
export interface SearchArticlesResponse {
  items: KnowledgeArticle[];
  total: number;
}

/** 获取分类列表响应 */
export interface GetCategoriesResponse {
  categories: KnowledgeCategory[];
}

/** 分类统计 */
export interface CategoryCount {
  category: string;
  count: number;
}

/** 知识库统计 */
export interface KnowledgeStats {
  totalLaws: number;
  totalCases: number;
  totalRegulations: number;
  totalInterpretations: number;
  vectorizedCount: number;
  categories: CategoryCount[];
}

/** 批量操作请求 */
export interface BatchOperationRequest {
  ids: string[];
}

/** 批量操作响应 */
export interface BatchOperationResponse {
  successCount: number;
  failedCount: number;
  message: string;
}

/** 批量导入请求 */
export interface BatchImportRequest {
  items: CreateArticleRequest[];
  dryRun?: boolean;
}

/** 批量导入响应 */
export interface BatchImportResponse {
  successCount: number;
  failedCount: number;
  message: string;
}

// ==================== 兼容类型（用于旧代码） ====================

/** 知识列表响应（兼容旧代码） */
export interface KnowledgeListResponse {
  items: KnowledgeItem[];
  total: number;
  page: number;
  pageSize: number;
}

/** 知识详情响应（兼容旧代码） */
export interface KnowledgeDetailResponse {
  id: string;
  title: string;
  content: string;
  summary: string;
  category: string;
  tags: string[];
  viewCount: number;
  likeCount: number;
  createdAt: string;
  updatedAt: string;
}

/** 创建知识请求（兼容旧代码） */
export interface CreateKnowledgeRequest {
  title: string;
  content: string;
  category: string;
  tags?: string[];
}

/** 更新知识请求（兼容旧代码） */
export interface UpdateKnowledgeRequest {
  title?: string;
  content?: string;
  category?: string;
  tags?: string[];
}