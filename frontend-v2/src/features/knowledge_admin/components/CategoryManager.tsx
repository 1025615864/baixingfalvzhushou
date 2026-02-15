/**
 * CategoryManager 组件 - 分类管理
 */

import { useState } from 'react';

import type { KnowledgeCategory } from '../types';

interface CategoryManagerProps {
  categories: KnowledgeCategory[];
  onCreateCategory: (name: string, description?: string) => void;
  onDeleteCategory?: (categoryId: number) => void;
  isLoading?: boolean;
}

export function CategoryManager({
  categories,
  onCreateCategory,
  onDeleteCategory,
  isLoading = false,
}: CategoryManagerProps): JSX.Element {
  const [newCategoryName, setNewCategoryName] = useState('');
  const [newCategoryDesc, setNewCategoryDesc] = useState('');
  const [isCreating, setIsCreating] = useState(false);

  const handleCreate = (): void => {
    if (!newCategoryName.trim()) {
      return;
    }

    onCreateCategory(newCategoryName.trim(), newCategoryDesc.trim() || undefined);
    setNewCategoryName('');
    setNewCategoryDesc('');
    setIsCreating(false);
  };

  const handleDelete = (category: KnowledgeCategory): void => {
    if (category.articleCount > 0) {
      alert(`该分类下有 ${category.articleCount} 篇文章，无法删除。请先移动或删除这些文章。`);
      return;
    }

    if (window.confirm(`确定要删除分类 "${category.name}" 吗？`)) {
      onDeleteCategory?.(category.id);
    }
  };

  if (isLoading) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <div className="animate-pulse space-y-4">
          <div className="h-8 bg-gray-200 rounded w-1/4"></div>
          <div className="space-y-3">
            {[1, 2, 3].map((i) => (
              <div key={i} className="h-12 bg-gray-200 rounded"></div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow">
      {/* 头部 */}
      <div className="p-6 border-b border-gray-200">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-lg font-semibold text-gray-900">分类管理</h2>
            <p className="mt-1 text-sm text-gray-500">
              共 {categories.length} 个分类
            </p>
          </div>
          <button
            onClick={() => setIsCreating(!isCreating)}
            className="inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
          >
            {isCreating ? '取消' : '+ 新建分类'}
          </button>
        </div>
      </div>

      {/* 创建新分类表单 */}
      {isCreating && (
        <div className="p-6 border-b border-gray-200 bg-blue-50">
          <h3 className="text-sm font-medium text-gray-900 mb-4">新建分类</h3>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700">
                分类名称 <span className="text-red-500">*</span>
              </label>
              <input
                type="text"
                value={newCategoryName}
                onChange={(e) => setNewCategoryName(e.target.value)}
                placeholder="输入分类名称"
                className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700">
                描述
              </label>
              <input
                type="text"
                value={newCategoryDesc}
                onChange={(e) => setNewCategoryDesc(e.target.value)}
                placeholder="输入分类描述（可选）"
                className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
              />
            </div>
            <div className="flex justify-end">
              <button
                onClick={handleCreate}
                disabled={!newCategoryName.trim()}
                className="px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                确认创建
              </button>
            </div>
          </div>
        </div>
      )}

      {/* 分类列表 */}
      <div className="divide-y divide-gray-200">
        {categories.length === 0 ? (
          <div className="p-12 text-center">
            <svg className="w-16 h-16 mx-auto text-gray-300 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A1.994 1.994 0 013 12V7a4 4 0 014-4z" />
            </svg>
            <p className="text-gray-500 mb-2">暂无分类</p>
            <p className="text-sm text-gray-400">点击上方&ldquo;新建分类&rdquo;按钮创建第一个分类</p>
          </div>
        ) : (
          categories.map((category) => (
            <div
              key={category.id}
              className="p-6 flex items-center justify-between hover:bg-gray-50 transition-colors"
            >
              <div className="flex-1">
                <div className="flex items-center gap-3">
                  <h3 className="text-base font-medium text-gray-900">
                    {category.name}
                  </h3>
                  <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                    {category.articleCount} 篇文章
                  </span>
                </div>
                {category.description && (
                  <p className="mt-1 text-sm text-gray-500">
                    {category.description}
                  </p>
                )}
                <p className="mt-1 text-xs text-gray-400">
                  创建时间: {new Date(category.createdAt).toLocaleString('zh-CN')}
                </p>
              </div>

              <div className="flex items-center space-x-2">
                {onDeleteCategory && category.articleCount === 0 && (
                  <button
                    onClick={() => handleDelete(category)}
                    className="p-2 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors"
                    title="删除分类"
                  >
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                    </svg>
                  </button>
                )}
              </div>
            </div>
          ))
        )}
      </div>

      {/* 提示信息 */}
      <div className="p-4 border-t border-gray-200 bg-gray-50">
        <div className="flex items-start space-x-2 text-sm text-gray-500">
          <svg className="w-5 h-5 text-blue-500 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <p>
            提示：只有当分类下没有文章时才能删除分类。删除分类不会影响已发布的文章。
          </p>
        </div>
      </div>
    </div>
  );
}