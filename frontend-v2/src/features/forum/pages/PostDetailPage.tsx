// ============================================
// 帖子详情页面
// ============================================

import { useState, useCallback, useMemo } from 'react';
import { useNavigate, useParams } from 'react-router-dom';

import {
  usePostDetail,
  useCommentList,
  useCreateComment,
} from '../hooks/useForum';
import { FavoriteButton } from '../components/FavoriteButton';
import { ReactionBar } from '../components/ReactionBar';
import type { CreateCommentRequest, ForumComment, PostCategory } from '../types';

// 分类标签映射
const categoryLabels: Record<PostCategory, string> = {
  legal: '法律咨询',
  consultation: '问题求助',
  experience: '经验分享',
  discussion: '话题讨论',
  help: '求助问答',
};

// 图标组件
const ArrowLeftIcon = () => (
  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
  </svg>
);

const HeartIcon = ({ filled }: { filled?: boolean }) => (
  <svg className={`w-5 h-5 ${filled ? 'fill-current text-red-500' : ''}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z" />
  </svg>
);

const MessageCircleIcon = () => (
  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
  </svg>
);

const EyeIcon = () => (
  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
  </svg>
);

const AwardIcon = () => (
  <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
    <path fillRule="evenodd" d="M6.267 3.455a3.066 3.066 0 001.745-.723 3.066 3.066 0 013.976 0 3.066 3.066 0 001.745.723 3.066 3.066 0 012.812 2.812c.051.643.304 1.254.723 1.745a3.066 3.066 0 010 3.976 3.066 3.066 0 00-.723 1.745 3.066 3.066 0 01-2.812 2.812 3.066 3.066 0 00-1.745.723 3.066 3.066 0 01-3.976 0 3.066 3.066 0 00-1.745-.723 3.066 3.066 0 01-2.812-2.812 3.066 3.066 0 00-.723-1.745 3.066 3.066 0 010-3.976 3.066 3.066 0 00.723-1.745 3.066 3.066 0 012.812-2.812zm7.44 5.252a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
  </svg>
);

const SendIcon = () => (
  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
  </svg>
);

const ReplyIcon = () => (
  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 10h10a8 8 0 018 8v2M3 10l6 6m-6-6l6-6" />
  </svg>
);

export function PostDetailPage() {
  const navigate = useNavigate();
  const { postId } = useParams<{ postId: string }>();
  const numericPostId = useMemo(() => parseInt(postId || '0', 10), [postId]);

  // 状态管理
  const [replyTo, setReplyTo] = useState<ForumComment | null>(null);
  const [commentContent, setCommentContent] = useState('');
  const [commentError, setCommentError] = useState<string | null>(null);

  // 数据获取
  const { 
    data: post, 
    isLoading: isPostLoading, 
    error: postError, 
    refetch: refetchPost 
  } = usePostDetail(numericPostId);

  const { 
    data: commentsData, 
    isLoading: isCommentsLoading,
    refetch: refetchComments 
  } = useCommentList(numericPostId);

  // 操作 Hooks
  const createCommentMutation = useCreateComment();

  // 计算属性
  const isLoading = isPostLoading || isCommentsLoading;
  const comments = useMemo(() => commentsData?.items ?? [], [commentsData]);

  // 格式化时间
  const formatTime = useCallback((dateString: string) => {
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
  }, []);

  // 事件处理
  const handleBack = useCallback(() => {
    navigate('/forum');
  }, [navigate]);

  const handleReply = useCallback((comment: ForumComment) => {
    setReplyTo(comment);
    setCommentContent(`@${comment.author.nickname} `);
    setCommentError(null);
  }, []);

  const handleCancelReply = useCallback(() => {
    setReplyTo(null);
    setCommentContent('');
    setCommentError(null);
  }, []);

  const handleSubmitComment = useCallback(() => {
    setCommentError(null);

    if (!commentContent.trim()) {
      setCommentError('请输入评论内容');
      return;
    }
    if (commentContent.length < 2) {
      setCommentError('评论内容至少需要 2 个字符');
      return;
    }

    const requestData: CreateCommentRequest = {
      content: commentContent,
      ...(replyTo && { parent_id: replyTo.id }),
    };

    createCommentMutation.mutate(
      { postId: numericPostId, data: requestData },
      {
        onSuccess: () => {
          setCommentContent('');
          setReplyTo(null);
          void refetchComments();
          void refetchPost();
        },
        onError: (err) => {
          setCommentError(err instanceof Error ? err.message : '评论发布失败');
        },
      }
    );
  }, [commentContent, replyTo, createCommentMutation, numericPostId, refetchComments, refetchPost]);

  const handleCommentKeyDown = useCallback((e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) {
      handleSubmitComment();
    }
  }, [handleSubmitComment]);

  const handleToggleFavorite = useCallback(() => {
    // 收藏状态由 FavoriteButton 组件内部处理
  }, []);

  // 加载状态
  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50">
        <div className="bg-white border-b border-gray-200">
          <div className="max-w-4xl mx-auto px-4 py-4">
            <div className="w-10 h-10 bg-gray-200 rounded animate-pulse" />
          </div>
        </div>
        <div className="max-w-4xl mx-auto px-4 py-6">
          <div className="bg-white rounded-lg p-6 shadow-sm animate-pulse">
            <div className="h-6 bg-gray-200 rounded w-24 mb-4" />
            <div className="h-8 bg-gray-200 rounded w-3/4 mb-6" />
            <div className="space-y-3">
              <div className="h-4 bg-gray-200 rounded w-full" />
              <div className="h-4 bg-gray-200 rounded w-full" />
              <div className="h-4 bg-gray-200 rounded w-2/3" />
            </div>
          </div>
        </div>
      </div>
    );
  }

  // 错误状态
  if (postError || !post) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <svg
            className="w-16 h-16 text-red-400 mx-auto mb-4"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
            />
          </svg>
          <h3 className="text-lg font-medium text-gray-900 mb-2">帖子不存在</h3>
          <p className="text-gray-500 mb-6">
            {postError instanceof Error ? postError.message : '该帖子可能已被删除或不存在'}
          </p>
          <button
            onClick={handleBack}
            className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            返回论坛
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* 顶部导航 */}
      <div className="bg-white border-b border-gray-200 sticky top-0 z-20">
        <div className="max-w-4xl mx-auto px-4 py-3">
          <div className="flex items-center justify-between">
            <button
              onClick={handleBack}
              className="flex items-center gap-2 text-gray-600 hover:text-gray-900 transition-colors"
            >
              <ArrowLeftIcon />
              <span>返回论坛</span>
            </button>
            <div className="flex items-center gap-3">
              <FavoriteButton
                postId={post.id}
                isFavorited={post.is_favorited}
                favoriteCount={post.favorite_count}
                size="md"
                showCount={true}
                variant="default"
                onToggle={handleToggleFavorite}
              />
            </div>
          </div>
        </div>
      </div>

      {/* 主内容区 */}
      <div className="max-w-4xl mx-auto px-4 py-6">
        {/* 帖子内容 */}
        <article className="bg-white rounded-lg shadow-sm border border-gray-100 overflow-hidden">
          {/* 帖子头部 */}
          <div className="p-6 border-b border-gray-100">
            {/* 分类和标记 */}
            <div className="flex items-center gap-2 mb-4">
              <span className="px-2.5 py-1 text-xs font-medium bg-blue-50 text-blue-600 rounded-full">
                {categoryLabels[post.category] || post.category}
              </span>
              {post.is_essence && (
                <span className="flex items-center gap-1 px-2.5 py-1 text-xs font-medium bg-amber-50 text-amber-600 rounded-full">
                  <AwardIcon />
                  精华
                </span>
              )}
            </div>

            {/* 标题 */}
            <h1 className="text-2xl font-bold text-gray-900 mb-4">{post.title}</h1>

            {/* 作者信息 */}
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                {post.author.avatar_url ? (
                  <img
                    src={post.author.avatar_url}
                    alt={post.author.nickname}
                    className="w-10 h-10 rounded-full"
                  />
                ) : (
                  <div className="w-10 h-10 rounded-full bg-gradient-to-br from-blue-400 to-blue-600 flex items-center justify-center text-white font-medium">
                    {post.author.nickname[0]}
                  </div>
                )}
                <div>
                  <div className="flex items-center gap-2">
                    <span className="font-medium text-gray-900">{post.author.nickname}</span>
                    {post.author.title && (
                      <span className="text-xs text-blue-600 bg-blue-50 px-1.5 py-0.5 rounded">
                        {post.author.title}
                      </span>
                    )}
                  </div>
                  <span className="text-sm text-gray-500">{formatTime(post.created_at)}</span>
                </div>
              </div>
            </div>
          </div>

          {/* 帖子正文 */}
          <div className="p-6">
            <div className="prose prose-sm max-w-none text-gray-700 leading-relaxed whitespace-pre-wrap">
              {post.content}
            </div>
          </div>

          {/* 帖子底部：互动区域 */}
          <div className="px-6 py-4 bg-gray-50 border-t border-gray-100">
            <div className="flex items-center justify-between">
              {/* 统计信息 */}
              <div className="flex items-center gap-6 text-sm text-gray-500">
                <span className="flex items-center gap-1.5">
                  <EyeIcon />
                  {post.view_count} 浏览
                </span>
                <span className="flex items-center gap-1.5">
                  <MessageCircleIcon />
                  {post.comment_count} 评论
                </span>
              </div>

              {/* 表情反应 */}
              <ReactionBar
                postId={post.id}
                reactions={post.reactions || []}
                userReaction={post.user_reaction}
                size="md"
                showCounts={true}
              />
            </div>
          </div>
        </article>

        {/* 评论区 */}
        <div className="mt-6">
          {/* 评论标题 */}
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-gray-900">
              评论 ({comments.length})
            </h2>
          </div>

          {/* 发表评论 */}
          <div className="bg-white rounded-lg shadow-sm border border-gray-100 p-4 mb-6">
            {replyTo && (
              <div className="flex items-center justify-between mb-3 p-2 bg-blue-50 rounded-lg">
                <span className="text-sm text-blue-600">
                  回复 @{replyTo.author.nickname}
                </span>
                <button
                  onClick={handleCancelReply}
                  className="text-sm text-gray-500 hover:text-gray-700"
                >
                  取消
                </button>
              </div>
            )}
            <textarea
              value={commentContent}
              onChange={(e) => setCommentContent(e.target.value)}
              onKeyDown={handleCommentKeyDown}
              placeholder={replyTo ? `回复 @${replyTo.author.nickname}...` : '发表您的看法...'}
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition-all resize-none"
              rows={3}
              maxLength={1000}
            />
            <div className="flex items-center justify-between mt-3">
              <span className="text-xs text-gray-400">{commentContent.length}/1000</span>
              <div className="flex items-center gap-3">
                {commentError && (
                  <span className="text-sm text-red-500">{commentError}</span>
                )}
                <button
                  onClick={handleSubmitComment}
                  disabled={createCommentMutation.isPending || !commentContent.trim()}
                  className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                >
                  <SendIcon />
                  {createCommentMutation.isPending ? '发送中...' : '发送'}
                </button>
              </div>
            </div>
            <p className="text-xs text-gray-400 mt-2">提示：按 Ctrl+Enter 快速发送</p>
          </div>

          {/* 评论列表 */}
          {comments.length === 0 ? (
            <div className="bg-white rounded-lg shadow-sm border border-gray-100 p-8 text-center">
              <MessageCircleIcon />
              <div className="mt-2">
                <p className="text-gray-500">暂无评论，成为第一个评论的人吧</p>
              </div>
            </div>
          ) : (
            <div className="space-y-4">
              {comments.map((comment) => (
                <CommentItem
                  key={comment.id}
                  comment={comment}
                  onReply={handleReply}
                  formatTime={formatTime}
                />
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

// 评论项组件
interface CommentItemProps {
  comment: ForumComment;
  onReply: (comment: ForumComment) => void;
  formatTime: (dateString: string) => string;
}

function CommentItem({ comment, onReply, formatTime }: CommentItemProps) {
  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-100 p-4">
      <div className="flex items-start gap-3">
        {/* 头像 */}
        {comment.author.avatar_url ? (
          <img
            src={comment.author.avatar_url}
            alt={comment.author.nickname}
            className="w-8 h-8 rounded-full"
          />
        ) : (
          <div className="w-8 h-8 rounded-full bg-gradient-to-br from-gray-400 to-gray-600 flex items-center justify-center text-white text-sm font-medium">
            {comment.author.nickname[0]}
          </div>
        )}

        {/* 评论内容 */}
        <div className="flex-1 min-w-0">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span className="font-medium text-gray-900 text-sm">
                {comment.author.nickname}
              </span>
              {comment.author.title && (
                <span className="text-xs text-blue-600 bg-blue-50 px-1.5 py-0.5 rounded">
                  {comment.author.title}
                </span>
              )}
            </div>
            <span className="text-xs text-gray-400">{formatTime(comment.created_at)}</span>
          </div>
          <p className="text-gray-700 mt-2 text-sm leading-relaxed whitespace-pre-wrap">
            {comment.content}
          </p>
          <div className="flex items-center gap-4 mt-3">
            <button
              onClick={() => onReply(comment)}
              className="flex items-center gap-1 text-xs text-gray-500 hover:text-blue-600 transition-colors"
            >
              <ReplyIcon />
              回复
            </button>
            <span className="flex items-center gap-1 text-xs text-gray-500">
              <HeartIcon filled={comment.is_liked} />
              {comment.like_count}
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}