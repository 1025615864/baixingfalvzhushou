/**
 * FAQ（常见问题）类型定义
 */

// ==================== 核心类型 ====================

/** FAQ条目 */
export interface FAQItem {
  id: number;
  question: string;
  answer: string;
  category: string | null;
  tags: string[] | null;
  priority: number;
  isActive: boolean;
  viewCount: number;
  createdAt: string;
  updatedAt: string;
}

/** FAQ分类 */
export interface FAQCategory {
  categories: string[];
}

/** 热门FAQ响应 */
export interface FAQPopularResponse {
  items: FAQItem[];
}

/** FAQ智能搜索结果 */
export interface FAQSmartSearchResult {
  matched: boolean;
  answer: string | null;
  faqId: number | null;
  confidence: number;
  suggestions: FAQItem[];
}

// ==================== API 请求/响应类型 ====================

/** 创建FAQ请求 */
export interface CreateFAQRequest {
  question: string;
  answer: string;
  category?: string;
  tags?: string[];
  priority?: number;
  isActive?: boolean;
}

/** 更新FAQ请求 */
export interface UpdateFAQRequest {
  question?: string;
  answer?: string;
  category?: string;
  tags?: string[];
  priority?: number;
  isActive?: boolean;
}

/** FAQ搜索参数 */
export interface FAQSearchParams {
  keyword?: string;
  category?: string;
  tags?: string[];
  page?: number;
  pageSize?: number;
}

/** FAQ列表响应 */
export interface FAQListResponse {
  items: FAQItem[];
  total: number;
  page: number;
  pageSize: number;
}

/** FAQ智能搜索请求 */
export interface FAQSmartSearchRequest {
  question: string;
  category?: string;
  limit?: number;
}

// ==================== 组件 Props 类型 ====================

/** FAQ列表组件Props */
export interface FAQListProps {
  items: FAQItem[];
  loading?: boolean;
  onItemClick?: (item: FAQItem) => void;
  emptyText?: string;
}

/** FAQ详情组件Props */
export interface FAQDetailProps {
  item: FAQItem | null;
  loading?: boolean;
  onBack?: () => void;
}

/** FAQ搜索组件Props */
export interface FAQSearchProps {
  keyword?: string;
  category?: string;
  categories?: string[];
  onSearch?: (keyword: string) => void;
  onCategoryChange?: (category: string) => void;
  placeholder?: string;
}

/** FAQ表单组件Props */
export interface FAQFormProps {
  initialData?: Partial<FAQItem>;
  categories?: string[];
  onSubmit: (data: CreateFAQRequest | UpdateFAQRequest) => void;
  onCancel?: () => void;
  loading?: boolean;
}

// ==================== Hook 返回类型 ====================

/** FAQ筛选状态 */
export interface FAQFilterState {
  keyword: string;
  category: string;
  page: number;
  pageSize: number;
}

/** FAQ管理Hook返回类型 */
export interface FAQManagerState {
  // 数据
  faqs: FAQItem[];
  categories: string[];
  popularFAQs: FAQItem[];
  selectedFAQ: FAQItem | null;
  
  // 加载状态
  isLoading: boolean;
  isLoadingCategories: boolean;
  isLoadingPopular: boolean;
  
  // 筛选和分页
  filter: FAQFilterState;
  total: number;
  
  // 操作函数
  setFilter: (filter: Partial<FAQFilterState>) => void;
  refetch: () => void;
  selectFAQ: (id: number | null) => void;
  createFAQ: (data: CreateFAQRequest) => Promise<void>;
  updateFAQ: (id: number, data: UpdateFAQRequest) => Promise<void>;
  deleteFAQ: (id: number) => Promise<void>;
}