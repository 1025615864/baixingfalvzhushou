/**
 * PostListPage - 帖子列表页面
 */

import { useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';

import type { PostFilter, PostSortOption, PostListItem } from '../types';
import { PostList, PostFilterBar } from '../components/PostList';
import {
  usePosts,
  usePinPost,
  useFeaturePost,
  useDeletePost,
  DEFAULT_POST_PAGINATION,
} from '../hooks/usePost';

/**
 * 帖子列表页面
 */
export function PostListPage(): JSX.Element {
  const navigate = useNavigate();
  const [filter, setFilter] = useState<PostFilter>({});
  const [sortBy, setSortBy] = useState<PostSortOption>('latest');
  const [page, setPage] = useState(1);

  const { data, isLoading } = usePosts({
    page,
    limit: DEFAULT_POST_PAGINATION.limit,
    filter,
    sortBy,
  });

  const pinMutation = usePinPost();
  const featureMutation = useFeaturePost();
  const deleteMutation = useDeletePost();

  /**
   * 处理帖子点击
   */
  const handlePostClick = useCallback(
    (post: PostListItem) => {
      navigate(`/posts/${post.id}`);
    },
    [navigate]
  );

  /**
   * 处理新建帖子
   */
  const handleCreatePost = useCallback(() => {
    navigate('/posts/new');
  }, [navigate]);

  /**
   * 处理筛选变化
   */
  const handleFilterChange = useCallback((newFilter: PostFilter) => {
    setFilter(newFilter);
    setPage(1);
  }, []);

  /**
   * 处理排序变化
   */
  const handleSortChange = useCallback((newSort: PostSortOption) => {
    setSortBy(newSort);
    setPage(1);
  }, []);

  /**
   * 处理加载更多
   */
  const handleLoadMore = useCallback(() => {
    if (data && page < data.totalPages) {
      setPage((prev) => prev + 1);
    }
  }, [data, page]);

  /**
   * 处理置顶
   */
  const handlePin = useCallback(
    (postId: string, isPinned: boolean) => {
      pinMutation.mutate({ postId, isPinned });
    },
    [pinMutation]
  );

  /**
   * 处理精华
   */
  const handleFeature = useCallback(
    (postId: string, isFeatured: boolean) => {
      featureMutation.mutate({ postId, isFeatured });
    },
    [featureMutation]
  );

  /**
   * 处理删除
   */
  const handleDelete = useCallback(
    (postId: string) => {
      deleteMutation.mutate({ id: postId });
    },
    [deleteMutation]
  );

  const posts = data?.posts ?? [];
  const hasMore = data ? page < data.totalPages : false;

  return (
    <div className="min-h-screen bg-gray-50">
      {/* 页面头部 */}
      <div className="bg-white shadow-sm sticky top-0 z-10">
        <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">帖子管理</h1>
              <p className="text-sm text-gray-500 mt-1">管理社区帖子内容</p>
            </div>
            <button
              onClick={handleCreatePost}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors flex items-center gap-2"
            >
              <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M12 4v16m8-8H4"
                />
              </svg>
              新建帖子
            </button>
          </div>
        </div>
      </div>

      {/* 页面内容 */}
      <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        {/* 筛选栏 */}
        <PostFilterBar
          filter={filter}
          sortBy={sortBy}
          onFilterChange={handleFilterChange}
          onSortChange={handleSortChange}
          className="mb-6"
        />

        {/* 帖子列表 */}
        <PostList
          posts={posts}
          isLoading={isLoading}
          hasMore={hasMore}
          onLoadMore={handleLoadMore}
          onPostClick={handlePostClick}
          showActions={true}
          onPin={handlePin}
          onFeature={handleFeature}
          onDelete={handleDelete}
          emptyText="暂无帖子，点击右上角新建帖子"
        />
      </div>
    </div>
  );
}