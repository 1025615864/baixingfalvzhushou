// ============================================
// 帖子卡片组件
// ============================================

import { FavoriteButton } from '../FavoriteButton';
import { ReactionBar } from '../ReactionBar';
import type { Post } from '../../types';

interface PostCardProps {
  post: Post;
  onClick?: () => void;
  showReactions?: boolean;
  showFavorite?: boolean;
  compact?: boolean;
}

// 图标组件
const HeartIcon = ({ filled }: { filled?: boolean }) => (
  <svg className={`w-4 h-4 ${filled ? 'fill-current' : ''}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z" />
  </svg>
);

const MessageCircleIcon = () => (
  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
  </svg>
);

const EyeIcon = () => (
  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
  </svg>
);

const AwardIcon = () => (
  <svg className="w-3 h-3" fill="currentColor" viewBox="0 0 20 20">
    <path fillRule="evenodd" d="M6.267 3.455a3.066 3.066 0 001.745-.723 3.066 3.066 0 013.976 0 3.066 3.066 0 001.745.723 3.066 3.066 0 012.812 2.812c.051.643.304 1.254.723 1.745a3.066 3.066 0 010 3.976 3.066 3.066 0 00-.723 1.745 3.066 3.066 0 01-2.812 2.812 3.066 3.066 0 00-1.745.723 3.066 3.066 0 01-3.976 0 3.066 3.066 0 00-1.745-.723 3.066 3.066 0 01-2.812-2.812 3.066 3.066 0 00-.723-1.745 3.066 3.066 0 010-3.976 3.066 3.066 0 00.723-1.745 3.066 3.066 0 012.812-2.812zm7.44 5.252a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
  </svg>
);

export function PostCard({ 
  post, 
  onClick, 
  showReactions = false, 
  showFavorite = true,
  compact = false,
}: PostCardProps) {
  const categoryLabels: Record<string, string> = {
    legal: '法律咨询',
    consultation: '问题求助',
    experience: '经验分享',
    discussion: '话题讨论',
    help: '求助问答',
  };

  const formatTime = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const diff = now.getTime() - date.getTime();
    const minutes = Math.floor(diff / 60000);
    const hours = Math.floor(diff / 3600000);
    const days = Math.floor(diff / 86400000);

    if (minutes < 1) return '刚刚';
    if (minutes < 60) return `${minutes}分钟前`;
    if (hours < 24) return `${hours}小时前`;
    if (days < 30) return `${days}天前`;
    return date.toLocaleDateString('zh-CN');
  };

  // 阻止事件冒泡
  const handleActionClick = (e: React.MouseEvent) => {
    e.stopPropagation();
  };

  if (compact) {
    // 紧凑模式 - 用于列表展示
    return (
      <div
        onClick={onClick}
        className="bg-white rounded-lg p-4 shadow-sm border border-gray-100 hover:shadow-md transition-shadow cursor-pointer"
      >
        <div className="flex items-start gap-3">
          {/* 左侧：分类和精华 */}
          <div className="flex flex-col items-center gap-1">
            <span className="px-2 py-0.5 text-xs font-medium bg-blue-50 text-blue-600 rounded">
              {categoryLabels[post.category] || post.category}
            </span>
            {post.is_essence && (
              <span className="flex items-center gap-0.5 px-1.5 py-0.5 text-[10px] font-medium bg-amber-50 text-amber-600 rounded">
                <AwardIcon />
                精
              </span>
            )}
          </div>

          {/* 右侧内容 */}
          <div className="flex-1 min-w-0">
            <h3 className="text-base font-semibold text-gray-900 line-clamp-1 hover:text-blue-600 transition-colors">
              {post.title}
            </h3>
            <div className="flex items-center gap-3 mt-2 text-xs text-gray-500">
              <span>{post.author.nickname}</span>
              <span>{formatTime(post.created_at)}</span>
              <span className="flex items-center gap-1">
                <EyeIcon />
                {post.view_count}
              </span>
              <span className={`flex items-center gap-1 ${post.is_liked ? 'text-red-500' : ''}`}>
                <HeartIcon filled={post.is_liked} />
                {post.like_count}
              </span>
            </div>
          </div>

          {/* 收藏按钮 */}
          {showFavorite && (
            <div onClick={handleActionClick}>
              <FavoriteButton
                postId={post.id}
                isFavorited={post.is_favorited}
                favoriteCount={post.favorite_count}
                size="sm"
                showCount={false}
                variant="ghost"
              />
            </div>
          )}
        </div>
      </div>
    );
  }

  // 完整模式
  return (
    <div
      onClick={onClick}
      className="bg-white rounded-lg p-5 shadow-sm border border-gray-100 hover:shadow-md transition-shadow cursor-pointer"
    >
      {/* 头部：分类和精华标记 */}
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <span className="px-2 py-0.5 text-xs font-medium bg-blue-50 text-blue-600 rounded">
            {categoryLabels[post.category] || post.category}
          </span>
          {post.is_essence && (
            <span className="flex items-center gap-1 px-2 py-0.5 text-xs font-medium bg-amber-50 text-amber-600 rounded">
              <AwardIcon />
              精华
            </span>
          )}
        </div>
        {showFavorite && (
          <div onClick={handleActionClick}>
            <FavoriteButton
              postId={post.id}
              isFavorited={post.is_favorited}
              favoriteCount={post.favorite_count}
              size="sm"
              showCount={false}
              variant="ghost"
            />
          </div>
        )}
      </div>

      {/* 标题 */}
      <h3 className="text-lg font-semibold text-gray-900 mb-2 line-clamp-2 hover:text-blue-600 transition-colors">
        {post.title}
      </h3>

      {/* 内容预览 */}
      <p className="text-gray-600 text-sm line-clamp-2 mb-4">
        {post.content}
      </p>

      {/* 表情反应条 */}
      {showReactions && (
        <div className="mb-4" onClick={handleActionClick}>
          <ReactionBar
            postId={post.id}
            reactions={post.reactions || []}
            userReaction={post.user_reaction}
            size="sm"
          />
        </div>
      )}

      {/* 底部信息 */}
      <div className="flex items-center justify-between text-sm text-gray-500">
        {/* 作者信息 */}
        <div className="flex items-center gap-2">
          {post.author.avatar_url ? (
            <img
              src={post.author.avatar_url}
              alt={post.author.nickname}
              className="w-6 h-6 rounded-full"
            />
          ) : (
            <div className="w-6 h-6 rounded-full bg-gray-200 flex items-center justify-center text-xs">
              {post.author.nickname[0]}
            </div>
          )}
          <span className="font-medium text-gray-700">{post.author.nickname}</span>
          {post.author.title && (
            <span className="text-xs text-blue-600 bg-blue-50 px-1.5 py-0.5 rounded">
              {post.author.title}
            </span>
          )}
          <span className="text-gray-400">·</span>
          <span>{formatTime(post.created_at)}</span>
        </div>

        {/* 互动数据 */}
        <div className="flex items-center gap-4">
          <span className="flex items-center gap-1">
            <EyeIcon />
            {post.view_count}
          </span>
          <span className={`flex items-center gap-1 ${post.is_liked ? 'text-red-500' : ''}`}>
            <HeartIcon filled={post.is_liked} />
            {post.like_count}
          </span>
          <span className="flex items-center gap-1">
            <MessageCircleIcon />
            {post.comment_count}
          </span>
          {showReactions && post.reactions && post.reactions.length > 0 && (
            <span className="flex items-center gap-1">
              <span className="text-xs">
                {post.reactions.reduce((sum, r) => sum + r.count, 0)} 反应
              </span>
            </span>
          )}
        </div>
      </div>
    </div>
  );
}