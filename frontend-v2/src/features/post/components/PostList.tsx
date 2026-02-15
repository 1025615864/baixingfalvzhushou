/**
 * PostList - 帖子列表组件
 */

import type { PostListItem, PostFilter, PostSortOption } from '../types';

import { PostCard, PostCardSkeleton } from './PostCard';

interface PostListProps {
  posts: PostListItem[];
  isLoading?: boolean;
  hasMore?: boolean;
  onLoadMore?: () => void;
  onPostClick?: (post: PostListItem) => void;
  showActions?: boolean;
  onPin?: (postId: string, isPinned: boolean) => void;
  onFeature?: (postId: string, isFeatured: boolean) => void;
  onDelete?: (postId: string) => void;
  emptyText?: string;
  className?: string;
}

/**
 * 帖子列表组件
 */
export function PostList({
  posts,
  isLoading = false,
  hasMore = false,
  onLoadMore,
  onPostClick,
  showActions = false,
  onPin,
  onFeature,
  onDelete,
  emptyText = '暂无帖子',
  className = '',
}: PostListProps): JSX.Element {
  /**
   * 处理加载更多
   */
  const handleLoadMore = (): void => {
    onLoadMore?.();
  };

  // 加载中状态
  if (isLoading && posts.length === 0) {
    return (
      <div className={`space-y-4 ${className}`}>
        {[1, 2, 3].map((index) => (
          <PostCardSkeleton key={index} />
        ))}
      </div>
    );
  }

  // 空状态
  if (!isLoading && posts.length === 0) {
    return (
      <div className={`flex flex-col items-center justify-center py-16 ${className}`}>
        <div className="w-24 h-24 mb-4 bg-gray-100 rounded-full flex items-center justify-center">
          <svg
            className="w-12 h-12 text-gray-400"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={1.5}
              d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10"
            />
          </svg>
        </div>
        <p className="text-gray-500 text-lg">{emptyText}</p>
      </div>
    );
  }

  return (
    <div className={`space-y-4 ${className}`}>
      {posts.map((post) => (
        <PostCard
          key={post.id}
          post={post}
          onClick={onPostClick}
          showActions={showActions}
          onPin={onPin}
          onFeature={onFeature}
          onDelete={onDelete}
        />
      ))}

      {/* 加载更多 */}
      {hasMore && (
        <div className="flex justify-center pt-4">
          <button
            onClick={handleLoadMore}
            disabled={isLoading}
            className="px-6 py-2 text-sm font-medium text-gray-600 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {isLoading ? (
              <span className="flex items-center gap-2">
                <svg
                  className="animate-spin h-4 w-4"
                  xmlns="http://www.w3.org/2000/svg"
                  fill="none"
                  viewBox="0 0 24 24"
                >
                  <circle
                    className="opacity-25"
                    cx="12"
                    cy="12"
                    r="10"
                    stroke="currentColor"
                    strokeWidth="4"
                  />
                  <path
                    className="opacity-75"
                    fill="currentColor"
                    d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                  />
                </svg>
                加载中...
              </span>
            ) : (
              '加载更多'
            )}
          </button>
        </div>
      )}
    </div>
  );
}

interface PostFilterBarProps {
  filter: PostFilter;
  sortBy: PostSortOption;
  onFilterChange: (filter: PostFilter) => void;
  onSortChange: (sort: PostSortOption) => void;
  className?: string;
}

/**
 * 帖子筛选栏组件
 */
export function PostFilterBar({
  filter,
  sortBy,
  onFilterChange,
  onSortChange,
  className = '',
}: PostFilterBarProps): JSX.Element {
  const categories: { value: string; label: string }[] = [
    { value: '', label: '全部分类' },
    { value: 'general', label: '综合' },
    { value: 'legal', label: '法律' },
    { value: 'consultation', label: '咨询' },
    { value: 'discussion', label: '讨论' },
    { value: 'announcement', label: '公告' },
  ];

  const sortOptions: { value: PostSortOption; label: string }[] = [
    { value: 'latest', label: '最新发布' },
    { value: 'popular', label: '最受欢迎' },
    { value: 'mostViewed', label: '最多浏览' },
    { value: 'mostCommented', label: '最多评论' },
    { value: 'oldest', label: '最早发布' },
  ];

  return (
    <div className={`flex flex-wrap items-center gap-4 bg-white p-4 rounded-lg shadow-sm ${className}`}>
      {/* 分类筛选 */}
      <div className="flex items-center gap-2">
        <span className="text-sm text-gray-500">分类：</span>
        <div className="flex flex-wrap gap-2">
          {categories.map((cat) => (
            <button
              key={cat.value}
              onClick={() =>
                onFilterChange({
                  ...filter,
                  category: cat.value as PostFilter['category'],
                })
              }
              className={`px-3 py-1.5 text-sm rounded-full transition-colors ${
                filter.category === cat.value || (!filter.category && cat.value === '')
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
              }`}
            >
              {cat.label}
            </button>
          ))}
        </div>
      </div>

      {/* 分隔线 */}
      <div className="hidden sm:block w-px h-6 bg-gray-200" />

      {/* 排序选项 */}
      <div className="flex items-center gap-2 ml-auto">
        <span className="text-sm text-gray-500">排序：</span>
        <select
          value={sortBy}
          onChange={(e) => onSortChange(e.target.value as PostSortOption)}
          className="px-3 py-1.5 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
        >
          {sortOptions.map((opt) => (
            <option key={opt.value} value={opt.value}>
              {opt.label}
            </option>
          ))}
        </select>
      </div>
    </div>
  );
}