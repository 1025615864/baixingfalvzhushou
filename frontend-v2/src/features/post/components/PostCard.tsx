/**
 * PostCard - 帖子卡片组件
 */

import type { PostListItem } from '../types';

interface PostCardProps {
  post: PostListItem;
  className?: string;
  onClick?: (post: PostListItem) => void;
  showActions?: boolean;
  onPin?: (postId: string, isPinned: boolean) => void;
  onFeature?: (postId: string, isFeatured: boolean) => void;
  onDelete?: (postId: string) => void;
}

/**
 * 格式化日期
 */
function formatDate(dateString: string): string {
  const date = new Date(dateString);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffMins = Math.floor(diffMs / (1000 * 60));
  const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
  const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));

  if (diffMins < 1) return '刚刚';
  if (diffMins < 60) return `${diffMins}分钟前`;
  if (diffHours < 24) return `${diffHours}小时前`;
  if (diffDays < 7) return `${diffDays}天前`;
  return date.toLocaleDateString('zh-CN', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  });
}

/**
 * 获取分类显示名称
 */
function getCategoryName(category: string): string {
  const categoryMap: Record<string, string> = {
    general: '综合',
    legal: '法律',
    consultation: '咨询',
    discussion: '讨论',
    announcement: '公告',
  };
  return categoryMap[category] || category;
}

/**
 * 获取分类颜色
 */
function getCategoryColor(category: string): string {
  const colorMap: Record<string, string> = {
    general: 'bg-gray-100 text-gray-700',
    legal: 'bg-blue-100 text-blue-700',
    consultation: 'bg-green-100 text-green-700',
    discussion: 'bg-purple-100 text-purple-700',
    announcement: 'bg-red-100 text-red-700',
  };
  return colorMap[category] || 'bg-gray-100 text-gray-700';
}

/**
 * 帖子卡片组件
 */
export function PostCard({
  post,
  className = '',
  onClick,
  showActions = false,
  onPin,
  onFeature,
  onDelete,
}: PostCardProps): JSX.Element {
  /**
   * 处理卡片点击
   */
  const handleClick = (): void => {
    onClick?.(post);
  };

  /**
   * 处理置顶切换
   */
  const handlePinToggle = (e: React.MouseEvent): void => {
    e.stopPropagation();
    onPin?.(post.id, !post.isPinned);
  };

  /**
   * 处理精华切换
   */
  const handleFeatureToggle = (e: React.MouseEvent): void => {
    e.stopPropagation();
    onFeature?.(post.id, !post.isFeatured);
  };

  /**
   * 处理删除
   */
  const handleDelete = (e: React.MouseEvent): void => {
    e.stopPropagation();
    if (window.confirm('确定要删除这个帖子吗？')) {
      onDelete?.(post.id);
    }
  };

  return (
    <div
      className={`bg-white rounded-lg shadow-sm hover:shadow-md transition-shadow cursor-pointer ${className}`}
      onClick={handleClick}
    >
      <div className="p-5">
        {/* 顶部：分类和标签 */}
        <div className="flex items-center gap-2 mb-3">
          <span
            className={`px-2 py-0.5 text-xs font-medium rounded-full ${getCategoryColor(
              post.category
            )}`}
          >
            {getCategoryName(post.category)}
          </span>
          {post.isPinned && (
            <span className="px-2 py-0.5 text-xs font-medium bg-orange-100 text-orange-700 rounded-full">
              置顶
            </span>
          )}
          {post.isFeatured && (
            <span className="px-2 py-0.5 text-xs font-medium bg-yellow-100 text-yellow-700 rounded-full">
              精华
            </span>
          )}
        </div>

        {/* 标题 */}
        <h3 className="text-lg font-semibold text-gray-900 mb-2 line-clamp-2 hover:text-blue-600 transition-colors">
          {post.title}
        </h3>

        {/* 摘要 */}
        <p className="text-gray-600 text-sm mb-4 line-clamp-2">{post.summary}</p>

        {/* 标签 */}
        {post.tags.length > 0 && (
          <div className="flex flex-wrap gap-1.5 mb-4">
            {post.tags.slice(0, 3).map((tag) => (
              <span
                key={tag}
                className="px-2 py-0.5 text-xs text-gray-500 bg-gray-100 rounded hover:bg-gray-200 transition-colors"
              >
                #{tag}
              </span>
            ))}
            {post.tags.length > 3 && (
              <span className="px-2 py-0.5 text-xs text-gray-400">+{post.tags.length - 3}</span>
            )}
          </div>
        )}

        {/* 底部信息 */}
        <div className="flex items-center justify-between pt-3 border-t border-gray-100">
          <div className="flex items-center gap-3">
            {/* 作者信息 */}
            <div className="flex items-center gap-2">
              {post.author.avatar ? (
                <img
                  src={post.author.avatar}
                  alt={post.author.name}
                  className="w-6 h-6 rounded-full object-cover"
                />
              ) : (
                <div className="w-6 h-6 rounded-full bg-blue-100 flex items-center justify-center text-xs font-medium text-blue-600">
                  {post.author.name.charAt(0)}
                </div>
              )}
              <span className="text-sm text-gray-600">{post.author.name}</span>
            </div>

            {/* 发布时间 */}
            <span className="text-xs text-gray-400">{formatDate(post.createdAt)}</span>
          </div>

          {/* 统计信息 */}
          <div className="flex items-center gap-4 text-sm text-gray-500">
            <span className="flex items-center gap-1">
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"
                />
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"
                />
              </svg>
              {post.viewCount}
            </span>
            <span className="flex items-center gap-1">
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z"
                />
              </svg>
              {post.likeCount}
            </span>
            <span className="flex items-center gap-1">
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"
                />
              </svg>
              {post.commentCount}
            </span>
          </div>
        </div>

        {/* 管理操作按钮 */}
        {showActions && (
          <div className="flex items-center gap-2 mt-3 pt-3 border-t border-gray-100">
            <button
              onClick={handlePinToggle}
              className={`px-3 py-1.5 text-xs font-medium rounded transition-colors ${
                post.isPinned
                  ? 'bg-orange-100 text-orange-700 hover:bg-orange-200'
                  : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
              }`}
            >
              {post.isPinned ? '取消置顶' : '置顶'}
            </button>
            <button
              onClick={handleFeatureToggle}
              className={`px-3 py-1.5 text-xs font-medium rounded transition-colors ${
                post.isFeatured
                  ? 'bg-yellow-100 text-yellow-700 hover:bg-yellow-200'
                  : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
              }`}
            >
              {post.isFeatured ? '取消精华' : '设为精华'}
            </button>
            <button
              onClick={handleDelete}
              className="px-3 py-1.5 text-xs font-medium text-red-600 bg-red-50 rounded hover:bg-red-100 transition-colors ml-auto"
            >
              删除
            </button>
          </div>
        )}
      </div>
    </div>
  );
}

/**
 * 帖子卡片骨架屏
 */
export function PostCardSkeleton(): JSX.Element {
  return (
    <div className="bg-white rounded-lg shadow-sm p-5 animate-pulse">
      <div className="h-4 w-16 bg-gray-200 rounded-full mb-3" />
      <div className="h-6 bg-gray-200 rounded mb-2" />
      <div className="h-4 bg-gray-200 rounded mb-4 w-3/4" />
      <div className="flex gap-2 mb-4">
        <div className="h-5 w-12 bg-gray-200 rounded-full" />
        <div className="h-5 w-12 bg-gray-200 rounded-full" />
      </div>
      <div className="flex items-center justify-between pt-3 border-t border-gray-100">
        <div className="flex items-center gap-3">
          <div className="w-6 h-6 rounded-full bg-gray-200" />
          <div className="h-4 w-20 bg-gray-200 rounded" />
        </div>
        <div className="flex gap-4">
          <div className="h-4 w-10 bg-gray-200 rounded" />
          <div className="h-4 w-10 bg-gray-200 rounded" />
        </div>
      </div>
    </div>
  );
}