import { Suspense, lazy } from 'react';

import type { NewsAdminListItem } from '../types';

const LazyArticleList = lazy(() =>
  import('./ArticleList').then((module) => ({
    default: module.ArticleList,
  }))
);

function NewsAdminSectionSkeleton({ rows = 3 }: { rows?: number }): JSX.Element {
  return (
    <div className="space-y-4">
      {Array.from({ length: rows }).map((_, index) => (
        <div key={index} className="h-24 animate-pulse rounded-lg bg-slate-100" />
      ))}
    </div>
  );
}

interface NewsArticlesPanelProps {
  items: NewsAdminListItem[];
  total: number;
  page: number;
  pageSize: number;
  category?: string;
  keyword: string;
  reviewStatus?: 'pending' | 'approved' | 'rejected';
  isLoading: boolean;
  onPageChange: (page: number) => void;
  onKeywordChange: (value: string) => void;
  onCategoryChange: (value: string | undefined) => void;
  onReviewStatusChange: (value: 'pending' | 'approved' | 'rejected' | undefined) => void;
  onResetFilters: () => void;
  onEdit: (article: NewsAdminListItem) => void;
  onDelete: (article: NewsAdminListItem) => void;
  onReview: (article: NewsAdminListItem) => void;
  onPublish: (article: NewsAdminListItem) => void;
  onTop: (article: NewsAdminListItem) => void;
}

export function NewsArticlesPanel({
  items,
  total,
  page,
  pageSize,
  category,
  keyword,
  reviewStatus,
  isLoading,
  onPageChange,
  onKeywordChange,
  onCategoryChange,
  onReviewStatusChange,
  onResetFilters,
  onEdit,
  onDelete,
  onReview,
  onPublish,
  onTop,
}: NewsArticlesPanelProps): JSX.Element {
  return (
    <div className="space-y-4">
      <div className="bg-white p-4 rounded-lg shadow flex flex-wrap gap-4 items-center">
        <div className="flex-1 min-w-[200px]">
          <input
            type="text"
            value={keyword}
            onChange={(e) => onKeywordChange(e.target.value)}
            placeholder="搜索文章标题..."
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          />
        </div>
        <select
          value={category || ''}
          onChange={(e) => onCategoryChange(e.target.value || undefined)}
          className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
        >
          <option value="">全部分类</option>
          <option value="general">综合</option>
          <option value="legal">法律</option>
          <option value="politics">时政</option>
          <option value="economy">经济</option>
          <option value="society">社会</option>
          <option value="technology">科技</option>
          <option value="other">其他</option>
        </select>
        <select
          value={reviewStatus || ''}
          onChange={(e) =>
            onReviewStatusChange((e.target.value as 'pending' | 'approved' | 'rejected') || undefined)
          }
          className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
        >
          <option value="">全部状态</option>
          <option value="pending">待审核</option>
          <option value="approved">已通过</option>
          <option value="rejected">已拒绝</option>
        </select>
        <button
          onClick={onResetFilters}
          className="px-4 py-2 text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-lg"
        >
          重置
        </button>
      </div>

      <Suspense fallback={<NewsAdminSectionSkeleton rows={4} />}>
        <LazyArticleList
          articles={items}
          total={total}
          page={page}
          pageSize={pageSize}
          isLoading={isLoading}
          onPageChange={onPageChange}
          onEdit={onEdit}
          onDelete={onDelete}
          onReview={onReview}
          onPublish={onPublish}
          onTop={onTop}
        />
      </Suspense>
    </div>
  );
}
