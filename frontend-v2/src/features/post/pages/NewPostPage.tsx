/**
 * NewPostPage - 新建帖子页面
 */

import { useCallback } from 'react';
import { useNavigate } from 'react-router-dom';

import type { CreatePostRequest, UpdatePostRequest } from '../types';
import { PostEditor } from '../components/PostEditor';
import { useCreatePost } from '../hooks/usePost';

/**
 * 新建帖子页面
 */
export function NewPostPage(): JSX.Element {
  const navigate = useNavigate();
  const createMutation = useCreatePost();

  /**
   * 处理提交
   */
  const handleSubmit = useCallback(
    async (data: CreatePostRequest | UpdatePostRequest) => {
      // 创建模式下，data必须是CreatePostRequest
      await createMutation.mutateAsync(data as CreatePostRequest, {
        onSuccess: (post) => {
          navigate(`/posts/${post.id}`);
        },
      });
    },
    [createMutation, navigate]
  );

  /**
   * 处理取消
   */
  const handleCancel = useCallback(() => {
    navigate(-1);
  }, [navigate]);

  return (
    <div className="min-h-screen bg-gray-50">
      {/* 页面头部 */}
      <div className="bg-white shadow-sm sticky top-0 z-10">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">新建帖子</h1>
              <p className="text-sm text-gray-500 mt-1">创建新的社区帖子</p>
            </div>
            <button
              onClick={handleCancel}
              className="px-4 py-2 text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200 transition-colors"
            >
              取消
            </button>
          </div>
        </div>
      </div>

      {/* 编辑器 */}
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        <PostEditor
          mode="create"
          onSubmit={handleSubmit}
          onCancel={handleCancel}
          isLoading={createMutation.isPending}
        />
      </div>
    </div>
  );
}