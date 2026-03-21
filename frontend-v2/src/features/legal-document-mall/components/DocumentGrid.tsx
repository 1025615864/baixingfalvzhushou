/**
 * 文书网格组件
 * 支持网格展示、分页和排序
 */

import { useState, useCallback, useMemo } from 'react';
import {
  Grid,
  ChevronUp,
  ChevronDown,
  FileText,
  LayoutGrid,
  AlignLeft,
  Heart,
  List,
} from 'lucide-react';

// 组合图标组件
function ArrowUpDown({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M7 15l5 5 5-5M7 9l5-5 5 5" />
    </svg>
  );
}
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import { Skeleton } from '@/components/ui/Skeleton';

import type { LegalDocument } from '../types';

import DocumentCard from './DocumentCard';

// 排序选项类型
export type SortOption = {
  key: string;
  label: string;
  direction: 'asc' | 'desc';
};

// 预设排序选项
const DEFAULT_SORT_OPTIONS: SortOption[] = [
  { key: 'created_at', label: '最新发布', direction: 'desc' },
  { key: 'download_count', label: '下载最多', direction: 'desc' },
  { key: 'view_count', label: '浏览最多', direction: 'desc' },
  { key: 'rating', label: '评分最高', direction: 'desc' },
  { key: 'price', label: '价格最低', direction: 'asc' },
  { key: 'price', label: '价格最高', direction: 'desc' },
];

// 视图模式类型
export type ViewMode = 'grid' | 'list' | 'compact';

interface DocumentGridProps {
  documents: LegalDocument[];
  total: number;
  page: number;
  pageSize: number;
  isLoading?: boolean;
  onPageChange: (page: number) => void;
  onSortChange?: (sort: SortOption) => void;
  onPurchase?: (document: LegalDocument) => void;
  onToggleFavorite?: (document: LegalDocument) => void;
  onDocumentClick?: (document: LegalDocument) => void;
  showMemberPrice?: boolean;
  defaultViewMode?: ViewMode;
  defaultSort?: SortOption;
  sortOptions?: SortOption[];
  showViewToggle?: boolean;
  showSort?: boolean;
  showPagination?: boolean;
  columns?: number;
  className?: string;
}

/**
 * 排序选择器组件
 */
function SortSelector({
  currentSort,
  sortOptions,
  onSortChange,
}: {
  currentSort: SortOption;
  sortOptions: SortOption[];
  onSortChange: (sort: SortOption) => void;
}) {
  const [isOpen, setIsOpen] = useState(false);

  const currentLabel = sortOptions.find(
    (opt) => opt.key === currentSort.key && opt.direction === currentSort.direction
  )?.label || '排序';

  return (
    <div className="relative">
      <Button
        variant="outline"
        size="sm"
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center gap-2"
      >
        <ArrowUpDown className="w-4 h-4" />
        {currentLabel}
        {isOpen ? (
          <ChevronUp className="w-3 h-3" />
        ) : (
          <ChevronDown className="w-3 h-3" />
        )}
      </Button>

      {isOpen && (
        <>
          <div
            className="fixed inset-0 z-10"
            onClick={() => setIsOpen(false)}
          />
          <div className="absolute right-0 mt-2 w-40 bg-white rounded-lg shadow-lg border border-gray-100 py-1 z-20">
            {sortOptions.map((option, index) => (
              <button
                key={`${option.key}-${option.direction}-${index}`}
                onClick={() => {
                  onSortChange(option);
                  setIsOpen(false);
                }}
                className={`w-full px-4 py-2 text-left text-sm hover:bg-gray-50 transition-colors ${
                  currentSort.key === option.key &&
                  currentSort.direction === option.direction
                    ? 'text-blue-600 bg-blue-50'
                    : 'text-gray-700'
                }`}
              >
                {option.label}
              </button>
            ))}
          </div>
        </>
      )}
    </div>
  );
}

/**
 * 视图切换组件
 */
function ViewToggle({
  viewMode,
  onViewModeChange,
}: {
  viewMode: ViewMode;
  onViewModeChange: (mode: ViewMode) => void;
}) {
  const modes: { key: ViewMode; icon: React.ElementType; label: string }[] = [
    { key: 'grid', icon: LayoutGrid, label: '网格' },
    { key: 'list', icon: AlignLeft, label: '列表' },
    { key: 'compact', icon: List as React.ElementType, label: '紧凑' },
  ];

  return (
    <div className="flex items-center gap-1 p-1 bg-gray-100 rounded-lg">
      {modes.map((mode) => {
        const Icon = mode.icon;
        return (
          <button
            key={mode.key}
            onClick={() => onViewModeChange(mode.key)}
            className={`p-1.5 rounded transition-colors ${
              viewMode === mode.key
                ? 'bg-white text-blue-600 shadow-sm'
                : 'text-gray-500 hover:text-gray-700'
            }`}
            title={mode.label}
          >
            <Icon className="w-4 h-4" />
          </button>
        );
      })}
    </div>
  );
}

/**
 * 分页组件
 */
function Pagination({
  currentPage,
  totalPages,
  total,
  pageSize,
  onPageChange,
}: {
  currentPage: number;
  totalPages: number;
  total: number;
  pageSize: number;
  onPageChange: (page: number) => void;
}) {
  const startItem = (currentPage - 1) * pageSize + 1;
  const endItem = Math.min(currentPage * pageSize, total);

  // 生成页码数组
  const getPageNumbers = useCallback(() => {
    const pages: (number | string)[] = [];
    const maxVisiblePages = 5;

    if (totalPages <= maxVisiblePages) {
      for (let i = 1; i <= totalPages; i++) {
        pages.push(i);
      }
    } else {
      if (currentPage <= 3) {
        for (let i = 1; i <= 4; i++) {
          pages.push(i);
        }
        pages.push('...');
        pages.push(totalPages);
      } else if (currentPage >= totalPages - 2) {
        pages.push(1);
        pages.push('...');
        for (let i = totalPages - 3; i <= totalPages; i++) {
          pages.push(i);
        }
      } else {
        pages.push(1);
        pages.push('...');
        for (let i = currentPage - 1; i <= currentPage + 1; i++) {
          pages.push(i);
        }
        pages.push('...');
        pages.push(totalPages);
      }
    }

    return pages;
  }, [currentPage, totalPages]);

  if (totalPages <= 1) return null;

  return (
    <div className="flex flex-col sm:flex-row items-center justify-between gap-4 mt-6 pt-6 border-t border-gray-100">
      {/* 统计信息 */}
      <div className="text-sm text-gray-500">
        显示 {startItem}-{endItem} 条，共 {total} 条
      </div>

      {/* 分页按钮 */}
      <div className="flex items-center gap-2">
        {/* 首页 */}
        <Button
          variant="outline"
          size="sm"
          disabled={currentPage === 1}
          onClick={() => onPageChange(1)}
          className="hidden sm:inline-flex"
        >
          首页
        </Button>

        {/* 上一页 */}
        <Button
          variant="outline"
          size="sm"
          disabled={currentPage === 1}
          onClick={() => onPageChange(currentPage - 1)}
        >
          <ChevronUp className="w-4 h-4 rotate-[-90deg]" />
        </Button>

        {/* 页码 */}
        <div className="flex items-center gap-1">
          {getPageNumbers().map((page, index) =>
            typeof page === 'number' ? (
              <button
                key={index}
                onClick={() => onPageChange(page)}
                className={`w-8 h-8 text-sm rounded-lg transition-colors ${
                  currentPage === page
                    ? 'bg-blue-600 text-white'
                    : 'text-gray-600 hover:bg-gray-100'
                }`}
              >
                {page}
              </button>
            ) : (
              <span key={index} className="w-8 h-8 text-center text-gray-400">
                {page}
              </span>
            )
          )}
        </div>

        {/* 下一页 */}
        <Button
          variant="outline"
          size="sm"
          disabled={currentPage === totalPages}
          onClick={() => onPageChange(currentPage + 1)}
        >
          <ChevronDown className="w-4 h-4 rotate-[-90deg]" />
        </Button>

        {/* 末页 */}
        <Button
          variant="outline"
          size="sm"
          disabled={currentPage === totalPages}
          onClick={() => onPageChange(totalPages)}
          className="hidden sm:inline-flex"
        >
          末页
        </Button>
      </div>
    </div>
  );
}

/**
 * 加载骨架屏
 */
function LoadingSkeleton({
  count = 6,
  viewMode,
}: {
  count?: number;
  viewMode: ViewMode;
}) {
  if (viewMode === 'compact') {
    return (
      <div className="space-y-2">
        {Array.from({ length: count }).map((_, i) => (
          <Card key={i} className="p-3">
            <div className="flex items-center gap-3">
              <Skeleton className="w-10 h-10 rounded-lg" />
              <div className="flex-1">
                <Skeleton className="h-4 w-3/4 mb-1" />
                <Skeleton className="h-3 w-1/2" />
              </div>
            </div>
          </Card>
        ))}
      </div>
    );
  }

  if (viewMode === 'list') {
    return (
      <div className="space-y-3">
        {Array.from({ length: count }).map((_, i) => (
          <Card key={i} className="p-4">
            <div className="flex gap-4">
              <Skeleton className="w-24 h-24 rounded-lg flex-shrink-0" />
              <div className="flex-1">
                <Skeleton className="h-5 w-3/4 mb-2" />
                <Skeleton className="h-4 w-full mb-1" />
                <Skeleton className="h-4 w-2/3 mb-3" />
                <div className="flex gap-2">
                  <Skeleton className="h-6 w-16" />
                  <Skeleton className="h-6 w-16" />
                </div>
              </div>
            </div>
          </Card>
        ))}
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      {Array.from({ length: count }).map((_, i) => (
        <Card key={i} className="p-4">
          <div className="flex justify-between mb-3">
            <Skeleton className="h-5 w-20" />
            <Skeleton className="h-5 w-5 rounded-full" />
          </div>
          <Skeleton className="h-5 w-3/4 mb-2" />
          <Skeleton className="h-4 w-full mb-1" />
          <Skeleton className="h-4 w-2/3 mb-3" />
          <div className="flex gap-2 mb-3">
            <Skeleton className="h-4 w-16" />
            <Skeleton className="h-4 w-16" />
          </div>
          <div className="flex justify-between items-center pt-3 border-t border-gray-100">
            <Skeleton className="h-6 w-20" />
            <Skeleton className="h-8 w-20" />
          </div>
        </Card>
      ))}
    </div>
  );
}

/**
 * 空状态组件
 */
function EmptyState() {
  return (
    <div className="text-center py-16">
      <div className="w-20 h-20 mx-auto mb-4 bg-gray-100 rounded-full flex items-center justify-center">
        <FileText className="w-10 h-10 text-gray-300" />
      </div>
      <h3 className="text-lg font-medium text-gray-900 mb-2">暂无文书</h3>
      <p className="text-gray-500">没有找到符合条件的法律文书</p>
    </div>
  );
}

/**
 * 列表视图组件
 */
function ListView({
  documents,
  onPurchase,
  onDocumentClick,
  onToggleFavorite,
  showMemberPrice: _showMemberPrice,
}: {
  documents: LegalDocument[];
  onPurchase?: (document: LegalDocument) => void;
  onDocumentClick?: (document: LegalDocument) => void;
  onToggleFavorite?: (document: LegalDocument) => void;
  showMemberPrice?: boolean;
}) {
  const handleToggleFavorite = useCallback(
    (e: React.MouseEvent, doc: LegalDocument) => {
      e.preventDefault();
      e.stopPropagation();
      onToggleFavorite?.(doc);
    },
    [onToggleFavorite]
  );

  return (
    <div className="space-y-3">
      {documents.map((doc) => (
        <Card
          key={doc.id}
          className="p-4 hover:shadow-md transition-shadow cursor-pointer"
          onClick={() => onDocumentClick?.(doc)}
        >
          <div className="flex gap-4">
            {/* 左侧图标区域 */}
            <div className="w-20 h-20 bg-blue-50 rounded-lg flex items-center justify-center flex-shrink-0">
              <FileText className="w-10 h-10 text-blue-400" />
            </div>

            {/* 中间内容区域 */}
            <div className="flex-1 min-w-0">
              {/* 标签 */}
              <div className="flex items-center gap-2 mb-1">
                {doc.is_featured && (
                  <Badge variant="warning" className="text-xs">
                    推荐
                  </Badge>
                )}
                {doc.is_free && (
                  <Badge variant="success" className="text-xs text-green-600">
                    免费
                  </Badge>
                )}
                {doc.is_purchased && (
                  <Badge variant="primary" className="text-xs text-blue-600">
                    已购买
                  </Badge>
                )}
              </div>

              {/* 标题 */}
              <h3 className="font-medium text-gray-900 mb-1 hover:text-blue-600 transition-colors">
                {doc.name}
              </h3>

              {/* 描述 */}
              <p className="text-sm text-gray-500 line-clamp-2 mb-2">
                {doc.description || '暂无描述'}
              </p>

              {/* 统计 */}
              <div className="flex items-center gap-4 text-xs text-gray-400">
                <span>{doc.view_count} 浏览</span>
                <span>{doc.download_count} 下载</span>
                {doc.rating > 0 && <span>⭐ {doc.rating.toFixed(1)}</span>}
              </div>
            </div>

            {/* 右侧操作区域 */}
            <div className="flex flex-col items-end justify-between">
              {/* 价格 */}
              <div className="text-right mb-2">
                {doc.is_free ? (
                  <span className="text-lg font-bold text-green-600">免费</span>
                ) : (
                  <div>
                    <span className="text-lg font-bold text-orange-600">{doc.price}</span>
                    <span className="text-xs text-gray-500 ml-1">积分</span>
                  </div>
                )}
              </div>

              {/* 按钮 */}
              <div className="flex items-center gap-2">
                {doc.is_purchased ? (
                  <Button size="sm" variant="ghost">
                    查看
                  </Button>
                ) : (
                  <Button
                    size="sm"
                    onClick={(e) => {
                      e.stopPropagation();
                      onPurchase?.(doc);
                    }}
                  >
                    {doc.is_free ? '获取' : '购买'}
                  </Button>
                )}
                <button
                  onClick={(e) => handleToggleFavorite(e, doc)}
                  className="p-1.5 hover:bg-gray-100 rounded-full transition-colors"
                >
                  <Heart
                    className={`w-5 h-5 transition-colors ${
                      doc.is_favorited ? 'fill-red-500 text-red-500' : 'text-gray-300'
                    }`}
                  />
                </button>
              </div>
            </div>
          </div>
        </Card>
      ))}
    </div>
  );
}

/**
 * 文书网格主组件
 */
export default function DocumentGrid({
  documents,
  total,
  page,
  pageSize,
  isLoading = false,
  onPageChange,
  onSortChange,
  onPurchase,
  onToggleFavorite,
  onDocumentClick,
  showMemberPrice = true,
  defaultViewMode = 'grid',
  defaultSort = DEFAULT_SORT_OPTIONS[0],
  sortOptions = DEFAULT_SORT_OPTIONS,
  showViewToggle = true,
  showSort = true,
  showPagination = true,
  columns = 3,
  className = '',
}: DocumentGridProps) {
  const [viewMode, setViewMode] = useState<ViewMode>(defaultViewMode);
  const [currentSort, setCurrentSort] = useState<SortOption>(defaultSort);

  // 计算总页数
  const totalPages = useMemo(
    () => Math.ceil(total / pageSize),
    [total, pageSize]
  );

  // 处理排序变化
  const handleSortChange = useCallback(
    (sort: SortOption) => {
      setCurrentSort(sort);
      onSortChange?.(sort);
    },
    [onSortChange]
  );

  // 处理视图模式变化
  const handleViewModeChange = useCallback((mode: ViewMode) => {
    setViewMode(mode);
  }, []);

  // 网格列数类名
  const gridColumnsClass = useMemo(() => {
    switch (columns) {
      case 2:
        return 'grid-cols-1 md:grid-cols-2';
      case 4:
        return 'grid-cols-1 md:grid-cols-2 lg:grid-cols-4';
      case 3:
      default:
        return 'grid-cols-1 md:grid-cols-2 lg:grid-cols-3';
    }
  }, [columns]);

  return (
    <div className={className}>
      {/* 工具栏 */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 mb-4">
        {/* 左侧标题/统计 */}
        <div className="flex items-center gap-2">
          <Grid className="w-5 h-5 text-gray-400" />
          <span className="font-medium text-gray-900">文书列表</span>
          <Badge variant="default" className="text-xs">
            {total} 份
          </Badge>
        </div>

        {/* 右侧工具 */}
        <div className="flex items-center gap-3">
          {/* 排序 */}
          {showSort && (
            <SortSelector
              currentSort={currentSort}
              sortOptions={sortOptions}
              onSortChange={handleSortChange}
            />
          )}

          {/* 视图切换 */}
          {showViewToggle && (
            <ViewToggle
              viewMode={viewMode}
              onViewModeChange={handleViewModeChange}
            />
          )}
        </div>
      </div>

      {/* 内容区域 */}
      {isLoading ? (
        <LoadingSkeleton count={pageSize} viewMode={viewMode} />
      ) : documents.length === 0 ? (
        <EmptyState />
      ) : viewMode === 'grid' ? (
        <div className={`grid ${gridColumnsClass} gap-4`}>
          {documents.map((doc) => (
            <DocumentCard
              key={doc.id}
              document={doc}
              onPurchase={onPurchase}
              onToggleFavorite={onToggleFavorite}
              onClick={onDocumentClick}
              showMemberPrice={showMemberPrice}
            />
          ))}
        </div>
      ) : viewMode === 'list' ? (
        <ListView
          documents={documents}
          onPurchase={onPurchase}
          onDocumentClick={onDocumentClick}
          onToggleFavorite={onToggleFavorite}
          showMemberPrice={showMemberPrice}
        />
      ) : (
        <div className="space-y-2">
          {documents.map((doc) => (
            <DocumentCard
              key={doc.id}
              document={doc}
              onPurchase={onPurchase}
              onToggleFavorite={onToggleFavorite}
              onClick={onDocumentClick}
              compact
            />
          ))}
        </div>
      )}

      {/* 分页 */}
      {showPagination && totalPages > 1 && (
        <Pagination
          currentPage={page}
          totalPages={totalPages}
          total={total}
          pageSize={pageSize}
          onPageChange={onPageChange}
        />
      )}
    </div>
  );
}

// 导出子组件
export { SortSelector, ViewToggle, Pagination, LoadingSkeleton, EmptyState, ListView };