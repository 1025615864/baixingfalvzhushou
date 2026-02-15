/**
 * UI 组件库索引
 *
 * 统一导出所有通用 UI 组件
 */

// ==================== 分页组件 ====================
export { Pagination } from './Pagination';
export type { PaginationProps } from './Pagination';
export { usePagination } from './usePagination';
export type {
  PaginationOptions,
  PaginationState,
  PaginationResult,
} from './usePagination';

// ==================== 筛选组件 ====================
export { FilterDropdown } from './FilterDropdown';
export type {
  FilterOption,
  FilterDropdownProps,
} from './FilterDropdown';

export { DateRangePicker } from './DateRangePicker';
export type {
  DateRange,
  PresetRange,
  DateRangePickerProps,
} from './DateRangePicker';

// ==================== 错误边界组件 ====================
export { ErrorBoundary, withErrorBoundary } from './ErrorBoundary';
export type { ErrorBoundaryProps } from './ErrorBoundary';

export { ErrorFallback } from './ErrorFallback';
export type { ErrorFallbackProps } from './ErrorFallback';

// ==================== 基础组件 ====================
export { EmptyState } from './EmptyState';
export type {
  EmptyIconType,
  EmptyStateProps,
} from './EmptyState';

export {
  Skeleton,
  TextSkeleton,
  CardSkeleton,
  ListItemSkeleton,
  StatCardSkeleton,
  TableSkeleton,
} from './Skeleton';
export type { SkeletonProps } from './Skeleton';

// ==================== Toast 组件 ====================
export { ToastProvider } from './ToastProvider';
export { useToast } from './useToast';

// ==================== 基础UI组件 ====================
export {
  Card,
  CardHeader,
  CardTitle,
  CardDescription,
  CardContent,
  CardFooter,
  FeatureCard,
  StatCard,
} from './Card';
export type {
  CardProps,
  CardHeaderProps,
  CardTitleProps,
  CardDescriptionProps,
  CardContentProps,
  CardFooterProps,
  FeatureCardProps,
  StatCardProps,
} from './Card';

export {
  Button,
  IconButton,
} from './Button';
export type {
  ButtonProps,
  IconButtonProps,
} from './Button';

export {
  Input,
  Textarea,
  Select,
  SearchInput,
} from './Input';
export type {
  InputProps,
  TextareaProps,
  SelectProps,
  SelectOption,
  SearchInputProps,
} from './Input';

export { Badge } from './Badge';

// ==================== Tabs组件 ====================
export { Tabs, TabsList, TabsTrigger, TabsContent } from './Tabs';

// ==================== 新增组件 ====================
export { Avatar, AvatarGroup } from './Avatar';
export type { AvatarProps, AvatarGroupProps } from './Avatar';

export {
  LoadingSpinner,
  LoadingDots,
  LoadingOverlay,
  LoadingCard,
  LoadingList,
  LoadingPage,
} from './Loading';

export { Modal, ConfirmModal } from './Modal';
export type { ModalProps, ConfirmModalProps } from './Modal';
