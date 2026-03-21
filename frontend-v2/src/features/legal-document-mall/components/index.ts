/**
 * 法律文书商城组件导出索引
 */

// 分类列表组件
export { default as DocumentCategoryList } from './DocumentCategoryList';
export {
  CategoryItem,
  CategoryGroup,
} from './DocumentCategoryList';
export type {
  DocumentCategoryListProps,
  CategoryStats,
} from './DocumentCategoryList';

// 文书卡片组件
export { default as DocumentCard } from './DocumentCard';
export { PriceDisplay } from './DocumentCard';
export type { DocumentCardProps } from './DocumentCard';

// 文书网格组件
export { default as DocumentGrid } from './DocumentGrid';
export {
  SortSelector,
  ViewToggle,
  Pagination,
  LoadingSkeleton,
  EmptyState,
  ListView,
} from './DocumentGrid';
export type {
  SortOption,
  ViewMode,
} from './DocumentGrid';

// 文书详情组件
export { default as DocumentDetail } from './DocumentDetail';
export {
  PriceInfo,
  DocumentPreview,
  DetailSkeleton,
} from './DocumentDetail';
export type { DocumentDetailProps } from './DocumentDetail';

// 购买流程组件
export { default as DocumentPurchaseFlow } from './DocumentPurchaseFlow';
export {
  PriceSummary,
  PaymentMethodSelector,
  PointsDeduction,
  ConfirmStep,
  ProcessingStep,
  SuccessStep,
  ErrorStep,
} from './DocumentPurchaseFlow';
export type {
  DocumentPurchaseFlowProps,
  PaymentMethod,
} from './DocumentPurchaseFlow';