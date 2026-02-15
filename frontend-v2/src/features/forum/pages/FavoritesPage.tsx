// ============================================
// 我的收藏页面
// ============================================

import { useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';

import { useFavorites } from '../hooks/useFavorites';
import { PostCard } from '../components/PostCard';
import { FavoriteButton } from '../components/FavoriteButton';
import type { PostCategory } from '../types';

const categoryLabels: Record<string, string> = {
  legal: '法律咨询',
  consultation: '问题求助',
  experience: '经验分享',
  discussion: '话题讨论',
  help: '求助问答',
};

export function FavoritesPage() {
  const navigate = useNavigate();
  const [selectedCategory, setSelectedCategory] = useState<PostCategory | null>(null);
  const [page, setPage] = useState(1);
  const pageSize = 10;

  const { data, isLoading, error, refetch } = useFavorites({
    page,
    page_size: pageSize,
    category: selectedCategory,
  });

  const handleCategoryChange = useCallback((category: PostCategory | null) => {
    setSelectedCategory(category);
    setPage(1);
  }, []);

  const handlePostClick = useCallback((postId: number) => {
    navigate(`/forum/posts/${postId}`);
  }, [navigate]);

  const categories: (PostCategory | null)[] = [
    null,
    'legal',
    'consultation',
    'experience',
    'discussion',
    'help',
  ];

  const totalPages = data ? Math.ceil(data.total / pageSize) : 0;

  return (
    <div className="min-h-screen bg-gray-50">
      {/* 页面头部 */}
      <div className="bg-white border-b border-gray-200">
        <div className="max-w-4xl mx-auto px-4 py-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">我的收藏</h1>
              <p className="text-gray-500 mt-1">
                共收藏 {data?.total ?? 0} 篇帖子
              </p>
            </div>
            <button
              onClick={() => navigate('/forum')}
              className="px-4 py-2 text-sm text-blue-600 hover:bg-blue-50 rounded-lg transition-colors"
            >
              返回论坛
            </button>
          </div>
        </div>
      </div>

      {/* 分类筛选 */}
      <div className="bg-white border-b border-gray-200 sticky top-0 z-10">
        <div className="max-w-4xl mx-auto px-4 py-3">
          <div className="flex items-center gap-2 overflow-x-auto no-scrollbar">
            {categories.map((category) => (
              <button
                key={category ?? 'all'}
                onClick={() => handleCategoryChange(category)}
                className={`px-4 py-1.5 text-sm font-medium rounded-full whitespace-nowrap transition-colors ${
                  selectedCategory === category
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                }`}
              >
                {category ? categoryLabels[category] : '全部'}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* 内容区域 */}
      <div className="max-w-4xl mx-auto px-4 py-6">
        {/* 加载状态 */}
        {isLoading && (
          <div className="space-y-4">
            {Array.from({ length: 3 }, (_, index) => (
              <div
                key={index}
                className="bg-white rounded-lg p-5 shadow-sm border border-gray-100 animate-pulse"
              >
                <div className="h-4 bg-gray-200 rounded w-20 mb-3" />
                <div className="h-6 bg-gray-200 rounded w-3/4 mb-2" />
                <div className="h-4 bg-gray-200 rounded w-full mb-4" />
                <div className="h-4 bg-gray-200 rounded w-2/3" />
              </div>
            ))}
          </div>
        )}

        {/* 错误状态 */}
        {!isLoading && error && (
          <div className="bg-red-50 rounded-lg p-8 text-center">
            <svg
              className="w-12 h-12 text-red-400 mx-auto mb-3"
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
            <h3 className="text-lg font-medium text-red-900 mb-2">加载失败</h3>
            <p className="text-red-600 mb-4">
              {error instanceof Error ? error.message : '请稍后重试'}
            </p>
            <button
              onClick={() => void refetch()}
              className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors"
            >
              重新加载
            </button>
          </div>
        )}

        {/* 空状态 */}
        {!isLoading && !error && data?.items.length === 0 && (
          <div className="bg-white rounded-lg p-12 text-center border border-gray-100">
            <svg
              className="w-16 h-16 text-gray-300 mx-auto mb-4"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={1.5}
                d="M5 5a2 2 0 012-2h10a2 2 0 012 2v16l-7-3.5L5 21V5z"
              />
            </svg>
            <h3 className="text-lg font-medium text-gray-900 mb-2">
              暂无收藏
            </h3>
            <p className="text-gray-500 mb-6">
              {selectedCategory
                ? '该分类下暂无收藏的帖子'
                : '您还没有收藏任何帖子，快去论坛发现有趣的内容吧'}
            </p>
            <button
              onClick={() => navigate('/forum')}
              className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
            >
              浏览论坛
            </button>
          </div>
        )}

        {/* 帖子列表 */}
        {!isLoading && !error && data && data.items.length > 0 && (
          <>
            <div className="space-y-4">
              {data.items.map((post) => (
                <div
                  key={post.id}
                  className="group relative bg-white rounded-lg shadow-sm border border-gray-100 hover:shadow-md transition-shadow"
                >
                  <div onClick={() => handlePostClick(post.id)}>
                    <PostCard post={post} />
                  </div>
                  {/* 收藏按钮悬浮层 */}
                  <div className="absolute top-4 right-4 opacity-0 group-hover:opacity-100 transition-opacity">
                    <FavoriteButton
                      postId={post.id}
                      isFavorited={post.is_favorited}
                      favoriteCount={post.favorite_count}
                      size="sm"
                      showCount={false}
                      variant="ghost"
                    />
                  </div>
                </div>
              ))}
            </div>

            {/* 分页 */}
            {totalPages > 1 && (
              <div className="flex items-center justify-center gap-2 mt-8">
                <button
                  onClick={() => setPage((p) => Math.max(1, p - 1))}
                  disabled={page === 1}
                  className="px-3 py-2 text-sm font-medium text-gray-600 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                >
                  上一页
                </button>
                <span className="text-sm text-gray-600">
                  第 {page} / {totalPages} 页
                </span>
                <button
                  onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                  disabled={page === totalPages}
                  className="px-3 py-2 text-sm font-medium text-gray-600 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                >
                  下一页
                </button>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}