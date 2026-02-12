/**
 * EditPostPage - 编辑帖子页面
 */

import { useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';

import type { CreatePostRequest, UpdatePostRequest } from '../types';
import { PostEditor } from '../components/PostEditor';
import { usePostDetail, useUpdatePost } from '../hooks/usePost';

/**
 * 编辑帖子页面
 */
export function EditPostPage(): JSX.Element {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { data: post, isLoading: isLoadingPost } = usePostDetail(id ?? '');
  const updateMutation = useUpdatePost();

  /**
   * 处理提交
   */
  const handleSubmit = useCallback(
    async (data: CreatePostRequest | UpdatePostRequest) => {
      if (!id) return;

      const updateData: UpdatePostRequest = {
        ...(data as CreatePostRequest),
        id,
      };
      await updateMutation.mutateAsync(updateData, {
        onSuccess: () => {
          navigate(`/posts/${id}`);
        },
      });
    },
    [updateMutation, navigate, id]
  );

  /**
   * 处理取消
   */
  const handleCancel = useCallback(() => {
    navigate(-1);
  }, [navigate]);

  // 加载中
  if (isLoadingPost) {
    return (
      <div className="min-h-screen bg-gray-50">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="bg-white rounded-lg shadow-sm p-8 animate-pulse">
            <div className="h-8 w-1/3 bg-gray-200 rounded mb-6" />
            <div className="h-10 bg-gray-200 rounded mb-4" />
            <div className="h-32 bg-gray-200 rounded" />
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

  return (
    <div className="min-h-screen bg-gray-50">
      {/* 页面头部 */}
      <div className="bg-white shadow-sm sticky top-0 z-10">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">编辑帖子</h1>
              <p className="text-sm text-gray-500 mt-1">修改帖子内容</p>
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
          mode="edit"
          initialData={{
            title: post.title,
            content: post.content,
            summary: post.summary,
            category: post.category,
            tags: post.tags,
            coverImage: post.coverImage,
          }}
          onSubmit={handleSubmit}
          onCancel={handleCancel}
          isLoading={updateMutation.isPending}
        />
      </div>
    </div>
  );
}