/**
 * PostDetailPage - 帖子详情页面
 */

import { useState, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';

import { usePostDetail, useComments, useCreateComment, useLikePost, useUnlikePost, useDeletePost } from '../hooks/usePost';
import type { CreateCommentRequest } from '../types';

/**
 * 格式化日期
 */
function formatDate(dateString: string): string {
  const date = new Date(dateString);
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
}

/**
 * 帖子详情页面
 */
export function PostDetailPage(): JSX.Element {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const postId = id ?? '';

  const { data: post, isLoading: isLoadingPost } = usePostDetail(postId);
  const { data: commentsData, isLoading: isLoadingComments } = useComments(postId, { limit: 20 });
  const createCommentMutation = useCreateComment();
  const likeMutation = useLikePost();
  const unlikeMutation = useUnlikePost();
  const deleteMutation = useDeletePost();

  const [commentContent, setCommentContent] = useState('');

  /**
   * 处理返回
   */
  const handleBack = useCallback(() => {
    navigate(-1);
  }, [navigate]);

  /**
   * 处理编辑
   */
  const handleEdit = useCallback(() => {
    navigate(`/posts/${postId}/edit`);
  }, [navigate, postId]);

  /**
   * 处理删除
   */
  const handleDelete = useCallback(() => {
    if (window.confirm('确定要删除这个帖子吗？此操作不可恢复。')) {
      deleteMutation.mutate({ id: postId }, {
        onSuccess: () => {
          navigate('/posts');
        },
      });
    }
  }, [deleteMutation, navigate, postId]);

  /**
   * 处理评论提交
   */
  const handleCommentSubmit = useCallback(() => {
    if (!commentContent.trim()) return;

    const request: CreateCommentRequest = {
      postId,
      content: commentContent.trim(),
    };

    createCommentMutation.mutate(request, {
      onSuccess: () => {
        setCommentContent('');
      },
    });
  }, [commentContent, postId, createCommentMutation]);

  /**
   * 处理点赞
   */
  const handleLike = useCallback(() => {
    if (!post) return;
    
    if (post.likeCount > 0) {
      unlikeMutation.mutate(postId);
    } else {
      likeMutation.mutate(postId);
    }
  }, [post, postId, likeMutation, unlikeMutation]);

  // 加载中
  if (isLoadingPost) {
    return (
      <div className="min-h-screen bg-gray-50">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="bg-white rounded-lg shadow-sm p-8 animate-pulse">
            <div className="h-8 w-3/4 bg-gray-200 rounded mb-4" />
            <div className="h-4 w-1/2 bg-gray-200 rounded mb-8" />
            <div className="h-4 w-full bg-gray-200 rounded mb-2" />
            <div className="h-4 w-full bg-gray-200 rounded mb-2" />
            <div className="h-4 w-2/3 bg-gray-200 rounded" />
          </div>
        </div>
      </div>
    );
  }

  // 帖子不存在
  if (!post) {
    return (
      <div className="min-h-screen bg-gray-50">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="bg-white rounded-lg shadow-sm p-8 text-center">
            <p className="text-gray-500">帖子不存在或已被删除</p>
            <button
              onClick={() => navigate('/posts')}
              className="mt-4 px-4 py-2 text-blue-600 hover:text-blue-700"
            >
              返回帖子列表
            </button>
          </div>
        </div>
      </div>
    );
  }

  const comments = commentsData?.comments ?? [];

  return (
    <div className="min-h-screen bg-gray-50">
      {/* 页面头部 */}
      <div className="bg-white shadow-sm sticky top-0 z-10">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <button
              onClick={handleBack}
              className="flex items-center text-gray-600 hover:text-gray-900 transition-colors"
            >
              <svg className="w-5 h-5 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
              </svg>
              返回
            </button>
            <div className="flex items-center gap-2">
              <button
                onClick={handleEdit}
                className="px-4 py-2 text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200 transition-colors"
              >
                编辑
              </button>
              <button
                onClick={handleDelete}
                className="px-4 py-2 text-red-600 bg-red-50 rounded-lg hover:bg-red-100 transition-colors"
              >
                删除
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* 帖子内容 */}
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        <article className="bg-white rounded-lg shadow-sm overflow-hidden">
          {/* 封面图 */}
          {post.coverImage && (
            <div className="w-full h-64 sm:h-80">
              <img
                src={post.coverImage}
                alt={post.title}
                className="w-full h-full object-cover"
              />
            </div>
          )}

          <div className="p-6 sm:p-8">
            {/* 标题和标签 */}
            <header className="mb-6">
              <div className="flex flex-wrap gap-2 mb-4">
                <span className="px-3 py-1 text-sm font-medium bg-blue-100 text-blue-700 rounded-full">
                  {post.category}
                </span>
                {post.isPinned && (
                  <span className="px-3 py-1 text-sm font-medium bg-orange-100 text-orange-700 rounded-full">
                    置顶
                  </span>
                )}
                {post.isFeatured && (
                  <span className="px-3 py-1 text-sm font-medium bg-yellow-100 text-yellow-700 rounded-full">
                    精华
                  </span>
                )}
              </div>
              <h1 className="text-2xl sm:text-3xl font-bold text-gray-900 mb-4">
                {post.title}
              </h1>
              <div className="flex items-center justify-between text-sm text-gray-500">
                <div className="flex items-center gap-4">
                  <span className="flex items-center gap-2">
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
                    {post.author.name}
                  </span>
                  <span>{formatDate(post.createdAt)}</span>
                </div>
                <div className="flex items-center gap-4">
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
                  <button
                    onClick={handleLike}
                    className="flex items-center gap-1 hover:text-red-500 transition-colors"
                  >
                    <svg
                      className={`w-4 h-4 ${post.likeCount > 0 ? 'text-red-500 fill-current' : ''}`}
                      fill="none"
                      viewBox="0 0 24 24"
                      stroke="currentColor"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z"
                      />
                    </svg>
                    {post.likeCount}
                  </button>
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
            </header>

            {/* 标签 */}
            {post.tags.length > 0 && (
              <div className="flex flex-wrap gap-2 mb-6 pb-6 border-b border-gray-100">
                {post.tags.map((tag) => (
                  <span
                    key={tag}
                    className="px-3 py-1 text-sm text-gray-600 bg-gray-100 rounded-full"
                  >
                    #{tag}
                  </span>
                ))}
              </div>
            )}

            {/* 正文内容 */}
            <div className="prose prose-blue max-w-none mb-8">
              <div className="text-gray-800 leading-relaxed whitespace-pre-wrap">
                {post.content}
              </div>
            </div>
          </div>
        </article>

        {/* 评论区 */}
        <div className="mt-6 bg-white rounded-lg shadow-sm p-6 sm:p-8">
          <h2 className="text-xl font-bold text-gray-900 mb-6">
            评论 ({post.commentCount})
          </h2>

          {/* 评论输入框 */}
          <div className="mb-8">
            <textarea
              value={commentContent}
              onChange={(e) => setCommentContent(e.target.value)}
              placeholder="发表你的评论..."
              rows={4}
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
            />
            <div className="flex justify-end mt-2">
              <button
                onClick={handleCommentSubmit}
                disabled={!commentContent.trim() || createCommentMutation.isPending}
                className="px-6 py-2 text-white bg-blue-600 rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                {createCommentMutation.isPending ? '发布中...' : '发布评论'}
              </button>
            </div>
          </div>

          {/* 评论列表 */}
          {isLoadingComments ? (
            <div className="space-y-4">
              {[1, 2, 3].map((i) => (
                <div key={i} className="animate-pulse flex gap-4">
                  <div className="w-10 h-10 rounded-full bg-gray-200" />
                  <div className="flex-1 space-y-2">
                    <div className="h-4 w-24 bg-gray-200 rounded" />
                    <div className="h-3 w-full bg-gray-200 rounded" />
                    <div className="h-3 w-2/3 bg-gray-200 rounded" />
                  </div>
                </div>
              ))}
            </div>
          ) : comments.length === 0 ? (
            <div className="text-center py-8 text-gray-500">
              暂无评论，来说两句吧~
            </div>
          ) : (
            <div className="space-y-6">
              {comments.map((comment) => (
                <div key={comment.id} className="flex gap-4 pb-6 border-b border-gray-100 last:border-0">
                  <div className="flex-shrink-0">
                    {comment.author.avatar ? (
                      <img
                        src={comment.author.avatar}
                        alt={comment.author.name}
                        className="w-10 h-10 rounded-full object-cover"
                      />
                    ) : (
                      <div className="w-10 h-10 rounded-full bg-blue-100 flex items-center justify-center text-sm font-medium text-blue-600">
                        {comment.author.name.charAt(0)}
                      </div>
                    )}
                  </div>
                  <div className="flex-1">
                    <div className="flex items-center justify-between mb-2">
                      <span className="font-medium text-gray-900">{comment.author.name}</span>
                      <span className="text-sm text-gray-400">
                        {formatDate(comment.createdAt)}
                      </span>
                    </div>
                    <p className="text-gray-700 leading-relaxed">{comment.content}</p>
                    <div className="flex items-center gap-4 mt-3 text-sm text-gray-500">
                      <button className="flex items-center gap-1 hover:text-blue-600 transition-colors">
                        <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            strokeWidth={2}
                            d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z"
                          />
                        </svg>
                        {comment.likeCount}
                      </button>
                      <button className="hover:text-blue-600 transition-colors">
                        回复
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}