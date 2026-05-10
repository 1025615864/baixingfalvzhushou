// ============================================
// 论坛主页
// ============================================

import { logger } from '@/shared/lib/logger';
import { useState, useCallback, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';

import { usePostList, useHotPosts, useCreatePost } from '../hooks/useForum';
import { PostCard } from '../components/PostCard';
import type { PostCategory, CreatePostRequest } from '../types';

// 分类标签映射
const categoryLabels: Record<PostCategory, string> = {
  legal: '法律咨询',
  consultation: '问题求助',
  experience: '经验分享',
  discussion: '话题讨论',
  help: '求助问答',
};

// 分类选项
const categories: (PostCategory | null)[] = [
  null,
  'legal',
  'consultation',
  'experience',
  'discussion',
  'help',
];

// 图标组件
const SearchIcon = () => (
  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
  </svg>
);

const PlusIcon = () => (
  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
  </svg>
);

const FireIcon = () => (
  <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
    <path fillRule="evenodd" d="M12.395 2.553a1 1 0 00-1.45-.385c-.345.23-.614.558-.822.88-.214.33-.403.713-.57 1.116-.334.804-.614 1.768-.84 2.734a31.365 31.365 0 00-.613 3.58 2.64 2.64 0 01-.945-1.067c-.328-.68-.398-1.534-.398-2.654A1 1 0 005.05 6.05 6.981 6.981 0 003 11a7 7 0 1011.95-4.95c-.592-.591-.98-.985-1.348-1.467-.363-.476-.724-1.063-1.207-2.03zM12.12 15.12A3 3 0 017 13s.879.5 2.5.5c0-1 .5-4 1.25-4.5.5 1 .786 1.293 1.371 1.879A2.99 2.99 0 0113 13a2.99 2.99 0 01-.879 2.121z" clipRule="evenodd" />
  </svg>
);

const CloseIcon = () => (
  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
  </svg>
);

export function ForumHomePage() {
  const navigate = useNavigate();
  
  // 状态管理
  const [selectedCategory, setSelectedCategory] = useState<PostCategory | null>(null);
  const [keyword, setKeyword] = useState('');
  const [searchInput, setSearchInput] = useState('');
  const [page, setPage] = useState(1);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const pageSize = 20;

  // 数据获取
  const { 
    data: postData, 
    isLoading, 
    error, 
    refetch 
  } = usePostList({
    page,
    page_size: pageSize,
    category: selectedCategory,
    keyword: keyword || undefined,
  });

  const { data: hotPostsData } = useHotPosts(5);

  // 创建帖子
  const createPostMutation = useCreatePost();

  // 计算属性
  const totalPages = useMemo(() => {
    return postData ? Math.ceil(postData.total / pageSize) : 0;
  }, [postData]);

  // 事件处理
  const handleCategoryChange = useCallback((category: PostCategory | null) => {
    setSelectedCategory(category);
    setPage(1);
  }, []);

  const handleSearch = useCallback(() => {
    setKeyword(searchInput);
    setPage(1);
  }, [searchInput]);

  const handleSearchKeyDown = useCallback((e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') {
      handleSearch();
    }
  }, [handleSearch]);

  const handleClearSearch = useCallback(() => {
    setSearchInput('');
    setKeyword('');
    setPage(1);
  }, []);

  const handlePostClick = useCallback((postId: number) => {
    navigate(`/forum/post/${postId}`);
  }, [navigate]);

  const handleCreatePost = useCallback(async (data: CreatePostRequest) => {
    try {
      await createPostMutation.mutateAsync(data);
      setShowCreateModal(false);
      void refetch();
    } catch (err) {
      logger.error('创建帖子失败:', err);
    }
  }, [createPostMutation, refetch]);

  return (
    <div className="min-h-screen bg-gray-50">
      {/* 页面头部 */}
      <div className="bg-white border-b border-gray-200">
        <div className="max-w-6xl mx-auto px-4 py-6">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">百姓论坛</h1>
              <p className="text-gray-500 mt-1">
                分享经验，互助解答，共建法律知识社区
              </p>
            </div>
            <div className="flex items-center gap-3">
              <button
                onClick={() => navigate('/forum/favorites')}
                className="px-4 py-2 text-sm text-gray-600 hover:bg-gray-100 rounded-lg transition-colors"
              >
                我的收藏
              </button>
              <button
                onClick={() => setShowCreateModal(true)}
                className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
              >
                <PlusIcon />
                发布帖子
              </button>
            </div>
          </div>

          {/* 搜索栏 */}
          <div className="flex items-center gap-3">
            <div className="flex-1 relative">
              <input
                type="text"
                value={searchInput}
                onChange={(e) => setSearchInput(e.target.value)}
                onKeyDown={handleSearchKeyDown}
                placeholder="搜索帖子标题或内容..."
                className="w-full pl-10 pr-4 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition-all"
              />
              <div className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400">
                <SearchIcon />
              </div>
              {searchInput && (
                <button
                  onClick={handleClearSearch}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
                >
                  <CloseIcon />
                </button>
              )}
            </div>
            <button
              onClick={handleSearch}
              className="px-6 py-2.5 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
            >
              搜索
            </button>
          </div>
        </div>
      </div>

      {/* 分类筛选 */}
      <div className="bg-white border-b border-gray-200 sticky top-0 z-10">
        <div className="max-w-6xl mx-auto px-4 py-3">
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

      {/* 主内容区域 */}
      <div className="max-w-6xl mx-auto px-4 py-6">
        <div className="flex gap-6">
          {/* 帖子列表 */}
          <div className="flex-1">
            {/* 加载状态 */}
            {isLoading && (
              <div className="space-y-4">
                {Array.from({ length: 5 }, (_, index) => (
                  <div
                    key={index}
                    className="bg-white rounded-lg p-5 shadow-sm border border-gray-100 animate-pulse"
                  >
                    <div className="flex items-center gap-2 mb-3">
                      <div className="h-5 w-16 bg-gray-200 rounded" />
                      <div className="h-5 w-12 bg-gray-200 rounded" />
                    </div>
                    <div className="h-6 bg-gray-200 rounded w-3/4 mb-3" />
                    <div className="h-4 bg-gray-200 rounded w-full mb-2" />
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
            {!isLoading && !error && postData?.items.length === 0 && (
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
                    d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10"
                  />
                </svg>
                <h3 className="text-lg font-medium text-gray-900 mb-2">
                  暂无帖子
                </h3>
                <p className="text-gray-500 mb-6">
                  {keyword || selectedCategory
                    ? '没有找到符合条件的帖子，试试其他搜索条件'
                    : '论坛还没有帖子，成为第一个发帖的人吧'}
                </p>
                <button
                  onClick={() => setShowCreateModal(true)}
                  className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
                >
                  发布第一个帖子
                </button>
              </div>
            )}

            {/* 帖子列表 */}
            {!isLoading && !error && postData && postData.items.length > 0 && (
              <>
                <div className="space-y-4">
                  {postData.items.map((post) => (
                    <PostCard
                      key={post.id}
                      post={post}
                      onClick={() => handlePostClick(post.id)}
                      showReactions={false}
                      showFavorite={true}
                    />
                  ))}
                </div>

                {/* 分页 */}
                {totalPages > 1 && (
                  <div className="flex items-center justify-center gap-2 mt-8">
                    <button
                      onClick={() => setPage((p) => Math.max(1, p - 1))}
                      disabled={page === 1}
                      className="px-4 py-2 text-sm font-medium text-gray-600 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                    >
                      上一页
                    </button>
                    <span className="text-sm text-gray-600 px-4">
                      第 {page} / {totalPages} 页
                    </span>
                    <button
                      onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                      disabled={page === totalPages}
                      className="px-4 py-2 text-sm font-medium text-gray-600 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                    >
                      下一页
                    </button>
                  </div>
                )}
              </>
            )}
          </div>

          {/* 侧边栏 */}
          <div className="hidden lg:block w-80">
            {/* 热门帖子 */}
            <div className="bg-white rounded-lg shadow-sm border border-gray-100 p-4 mb-4">
              <div className="flex items-center gap-2 mb-4">
                <span className="text-orange-500">
                  <FireIcon />
                </span>
                <h3 className="font-semibold text-gray-900">热门帖子</h3>
              </div>
              <div className="space-y-3">
                {hotPostsData?.items.slice(0, 5).map((post, index) => (
                  <div
                    key={post.id}
                    onClick={() => handlePostClick(post.id)}
                    className="flex items-start gap-3 cursor-pointer group"
                  >
                    <span className={`flex-shrink-0 w-5 h-5 rounded-full flex items-center justify-center text-xs font-bold ${
                      index < 3 ? 'bg-orange-100 text-orange-600' : 'bg-gray-100 text-gray-500'
                    }`}>
                      {index + 1}
                    </span>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm text-gray-700 line-clamp-2 group-hover:text-blue-600 transition-colors">
                        {post.title}
                      </p>
                      <p className="text-xs text-gray-400 mt-1">
                        {post.view_count} 浏览 · {post.comment_count} 评论
                      </p>
                    </div>
                  </div>
                ))}
                {(!hotPostsData || hotPostsData.items.length === 0) && (
                  <p className="text-sm text-gray-400 text-center py-4">
                    暂无热门帖子
                  </p>
                )}
              </div>
            </div>

            {/* 发帖入口 */}
            <div className="bg-gradient-to-br from-blue-500 to-blue-600 rounded-lg p-4 text-white">
              <h3 className="font-semibold mb-2">分享您的经验</h3>
              <p className="text-sm text-blue-100 mb-4">
                有法律问题需要咨询？或者想分享您的维权经验？
              </p>
              <button
                onClick={() => setShowCreateModal(true)}
                className="w-full py-2 bg-white text-blue-600 rounded-lg font-medium hover:bg-blue-50 transition-colors"
              >
                立即发帖
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* 创建帖子弹窗 */}
      {showCreateModal && (
        <CreatePostModal
          onClose={() => setShowCreateModal(false)}
          onSubmit={handleCreatePost}
          isLoading={createPostMutation.isPending}
        />
      )}
    </div>
  );
}

// 创建帖子弹窗组件
interface CreatePostModalProps {
  onClose: () => void;
  onSubmit: (data: CreatePostRequest) => Promise<void>;
  isLoading: boolean;
}

function CreatePostModal({ onClose, onSubmit, isLoading }: CreatePostModalProps) {
  const [title, setTitle] = useState('');
  const [content, setContent] = useState('');
  const [category, setCategory] = useState<PostCategory>('discussion');
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (!title.trim()) {
      setError('请输入帖子标题');
      return;
    }
    if (!content.trim()) {
      setError('请输入帖子内容');
      return;
    }
    if (title.length < 5) {
      setError('标题至少需要 5 个字符');
      return;
    }
    if (content.length < 10) {
      setError('内容至少需要 10 个字符');
      return;
    }

    onSubmit({ title, content, category }).catch((err) => {
      setError(err instanceof Error ? err.message : '发布失败，请重试');
    });
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50">
      <div className="bg-white rounded-xl shadow-xl w-full max-w-2xl max-h-[90vh] overflow-hidden">
        {/* 弹窗头部 */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-200">
          <h2 className="text-lg font-semibold text-gray-900">发布新帖子</h2>
          <button
            onClick={onClose}
            className="p-1 text-gray-400 hover:text-gray-600 transition-colors"
          >
            <CloseIcon />
          </button>
        </div>

        {/* 表单内容 */}
        <form onSubmit={handleSubmit} className="p-6 space-y-4 overflow-y-auto max-h-[calc(90vh-140px)]">
          {/* 分类选择 */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              帖子分类
            </label>
            <div className="flex flex-wrap gap-2">
              {Object.entries(categoryLabels).map(([key, label]) => (
                <button
                  key={key}
                  type="button"
                  onClick={() => setCategory(key as PostCategory)}
                  className={`px-3 py-1.5 text-sm rounded-full transition-colors ${
                    category === key
                      ? 'bg-blue-600 text-white'
                      : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                  }`}
                >
                  {label}
                </button>
              ))}
            </div>
          </div>

          {/* 标题输入 */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              帖子标题
            </label>
            <input
              type="text"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="请输入帖子标题..."
              className="w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition-all"
              maxLength={100}
            />
            <p className="text-xs text-gray-400 mt-1">{title.length}/100</p>
          </div>

          {/* 内容输入 */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              帖子内容
            </label>
            <textarea
              value={content}
              onChange={(e) => setContent(e.target.value)}
              placeholder="请详细描述您的问题或经验分享..."
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition-all resize-none"
              rows={8}
              maxLength={5000}
            />
            <p className="text-xs text-gray-400 mt-1">{content.length}/5000</p>
          </div>

          {/* 错误提示 */}
          {error && (
            <div className="p-3 bg-red-50 text-red-600 text-sm rounded-lg">
              {error}
            </div>
          )}

          {/* 提交按钮 */}
          <div className="flex items-center justify-end gap-3 pt-4">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 text-gray-600 hover:bg-gray-100 rounded-lg transition-colors"
            >
              取消
            </button>
            <button
              type="submit"
              disabled={isLoading}
              className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {isLoading ? '发布中...' : '发布帖子'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}