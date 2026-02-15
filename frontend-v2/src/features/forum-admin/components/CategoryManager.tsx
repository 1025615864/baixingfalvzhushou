/**
 * CategoryManager - 板块管理组件
 */

import { useState } from 'react';

import type { ForumCategory, CategoryStatus, CreateCategoryRequest, UpdateCategoryRequest } from '../types';
import {
  useForumCategories,
  useCreateCategory,
  useUpdateCategory,
  useDeleteCategory,
} from '../hooks/useForumAdmin';

const statusLabels: Record<CategoryStatus, string> = {
  active: '正常',
  inactive: '停用',
  archived: '归档',
};

const statusColors: Record<CategoryStatus, string> = {
  active: 'bg-green-100 text-green-800',
  inactive: 'bg-yellow-100 text-yellow-800',
  archived: 'bg-gray-100 text-gray-800',
};

/**
 * 板块管理组件
 */
export function CategoryManager(): JSX.Element {
  const [showCreateModal, setShowCreateModal] = useState<boolean>(false);
  const [editingCategory, setEditingCategory] = useState<ForumCategory | null>(null);

  // 表单状态
  const [formData, setFormData] = useState<CreateCategoryRequest>({
    name: '',
    slug: '',
    description: '',
    icon: '',
    color: '#3B82F6',
    sortOrder: 0,
    allowPost: true,
    needAudit: false,
    minLevelToPost: 0,
  });

  const { data: categories, isLoading, error } = useForumCategories();
  const createMutation = useCreateCategory();
  const updateMutation = useUpdateCategory();
  const deleteMutation = useDeleteCategory();

  const handleOpenCreate = (): void => {
    setFormData({
      name: '',
      slug: '',
      description: '',
      icon: '',
      color: '#3B82F6',
      sortOrder: categories?.length || 0,
      allowPost: true,
      needAudit: false,
      minLevelToPost: 0,
    });
    setShowCreateModal(true);
  };

  const handleOpenEdit = (category: ForumCategory): void => {
    setEditingCategory(category);
    setFormData({
      name: category.name,
      slug: category.slug,
      description: category.description,
      icon: category.icon || '',
      color: category.color || '#3B82F6',
      sortOrder: category.sortOrder,
      allowPost: category.allowPost,
      needAudit: category.needAudit,
      minLevelToPost: category.minLevelToPost,
    });
  };

  const handleCloseModal = (): void => {
    setShowCreateModal(false);
    setEditingCategory(null);
  };

  const handleSubmit = (): void => {
    if (!formData.name.trim() || !formData.slug.trim()) return;

    if (editingCategory) {
      const updateRequest: UpdateCategoryRequest = {
        name: formData.name,
        description: formData.description,
        icon: formData.icon,
        color: formData.color,
        sortOrder: formData.sortOrder,
        allowPost: formData.allowPost,
        needAudit: formData.needAudit,
        minLevelToPost: formData.minLevelToPost,
      };
      void updateMutation.mutateAsync({
        categoryId: editingCategory.id,
        request: updateRequest,
      }).then(() => {
        handleCloseModal();
      });
    } else {
      void createMutation.mutateAsync(formData).then(() => {
        handleCloseModal();
      });
    }
  };

  const handleDelete = (categoryId: number, categoryName: string): void => {
    if (!window.confirm(`确定要删除板块 "${categoryName}" 吗？此操作不可撤销。`)) return;

    void deleteMutation.mutateAsync(categoryId);
  };

  const isSubmitting = createMutation.isPending || updateMutation.isPending;

  if (isLoading) {
    return (
      <div className="p-6 bg-white rounded-lg shadow-sm">
        <div className="animate-pulse space-y-4">
          <div className="h-4 bg-gray-200 rounded w-1/4" />
          <div className="space-y-2">
            <div className="h-12 bg-gray-200 rounded" />
            <div className="h-12 bg-gray-200 rounded" />
            <div className="h-12 bg-gray-200 rounded" />
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-6 bg-white rounded-lg shadow-sm">
        <div className="text-red-500">加载板块列表失败</div>
      </div>
    );
  }

  return (
    <div className="p-6 bg-white rounded-lg shadow-sm">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-xl font-semibold text-gray-900">板块管理</h2>
          <p className="text-sm text-gray-500 mt-1">共 {categories?.length || 0} 个板块</p>
        </div>
        <button
          onClick={handleOpenCreate}
          className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700 transition-colors"
        >
          创建板块
        </button>
      </div>

      {/* 板块列表 */}
      <div className="overflow-x-auto">
        <table className="w-full text-left">
          <thead>
            <tr className="border-b border-gray-200">
              <th className="pb-3 font-medium text-gray-700">板块名称</th>
              <th className="pb-3 font-medium text-gray-700">标识</th>
              <th className="pb-3 font-medium text-gray-700">状态</th>
              <th className="pb-3 font-medium text-gray-700">帖子数</th>
              <th className="pb-3 font-medium text-gray-700">关注者</th>
              <th className="pb-3 font-medium text-gray-700">需要审核</th>
              <th className="pb-3 font-medium text-gray-700 text-right">操作</th>
            </tr>
          </thead>
          <tbody>
            {categories?.map((category) => (
              <tr key={category.id} className="border-b border-gray-100 last:border-0">
                <td className="py-4">
                  <div className="flex items-center gap-3">
                    {category.icon ? (
                      <span className="text-2xl">{category.icon}</span>
                    ) : (
                      <div
                        className="w-8 h-8 rounded-full"
                        style={{ backgroundColor: category.color || '#3B82F6' }}
                      />
                    )}
                    <div>
                      <p className="font-medium text-gray-900">{category.name}</p>
                      <p className="text-sm text-gray-500 truncate max-w-xs">{category.description}</p>
                    </div>
                  </div>
                </td>
                <td className="py-4 text-gray-600 font-mono text-sm">{category.slug}</td>
                <td className="py-4">
                  <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${statusColors[category.status]}`}>
                    {statusLabels[category.status]}
                  </span>
                </td>
                <td className="py-4 text-gray-600">{category.postCount.toLocaleString()}</td>
                <td className="py-4 text-gray-600">{category.followerCount.toLocaleString()}</td>
                <td className="py-4">
                  <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${category.needAudit ? 'bg-orange-100 text-orange-800' : 'bg-green-100 text-green-800'}`}>
                    {category.needAudit ? '是' : '否'}
                  </span>
                </td>
                <td className="py-4 text-right">
                  <div className="flex items-center justify-end gap-2">
                    <button
                      onClick={() => handleOpenEdit(category)}
                      className="px-3 py-1 text-sm text-blue-600 hover:bg-blue-50 rounded transition-colors"
                    >
                      编辑
                    </button>
                    <button
                      onClick={() => handleDelete(category.id, category.name)}
                      className="px-3 py-1 text-sm text-red-600 hover:bg-red-50 rounded transition-colors"
                    >
                      删除
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* 创建/编辑弹窗 */}
      {(showCreateModal || editingCategory) && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-lg max-h-[90vh] overflow-y-auto">
            <h3 className="text-lg font-semibold mb-4">
              {editingCategory ? '编辑板块' : '创建板块'}
            </h3>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  板块名称 <span className="text-red-500">*</span>
                </label>
                <input
                  type="text"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  placeholder="请输入板块名称"
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  标识 (Slug) <span className="text-red-500">*</span>
                </label>
                <input
                  type="text"
                  value={formData.slug}
                  onChange={(e) => setFormData({ ...formData, slug: e.target.value.toLowerCase().replace(/[^a-z0-9-]/g, '-') })}
                  placeholder="请输入板块标识，如：general-discussion"
                  disabled={!!editingCategory}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-100"
                />
                <p className="text-xs text-gray-500 mt-1">用于URL，只能包含小写字母、数字和连字符</p>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">描述</label>
                <textarea
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  placeholder="请输入板块描述"
                  rows={3}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">图标</label>
                  <input
                    type="text"
                    value={formData.icon}
                    onChange={(e) => setFormData({ ...formData, icon: e.target.value })}
                    placeholder="表情符号，如：💬"
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">颜色</label>
                  <div className="flex items-center gap-2">
                    <input
                      type="color"
                      value={formData.color}
                      onChange={(e) => setFormData({ ...formData, color: e.target.value })}
                      className="w-10 h-10 rounded border border-gray-300 cursor-pointer"
                    />
                    <input
                      type="text"
                      value={formData.color}
                      onChange={(e) => setFormData({ ...formData, color: e.target.value })}
                      className="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                  </div>
                </div>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">排序</label>
                <input
                  type="number"
                  value={formData.sortOrder}
                  onChange={(e) => setFormData({ ...formData, sortOrder: parseInt(e.target.value) || 0 })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    id="allowPost"
                    checked={formData.allowPost}
                    onChange={(e) => setFormData({ ...formData, allowPost: e.target.checked })}
                    className="w-4 h-4 text-blue-600 rounded border-gray-300 focus:ring-blue-500"
                  />
                  <label htmlFor="allowPost" className="text-sm text-gray-700">允许发帖</label>
                </div>
                <div className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    id="needAudit"
                    checked={formData.needAudit}
                    onChange={(e) => setFormData({ ...formData, needAudit: e.target.checked })}
                    className="w-4 h-4 text-blue-600 rounded border-gray-300 focus:ring-blue-500"
                  />
                  <label htmlFor="needAudit" className="text-sm text-gray-700">需要审核</label>
                </div>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">最低发帖等级</label>
                <input
                  type="number"
                  value={formData.minLevelToPost}
                  onChange={(e) => setFormData({ ...formData, minLevelToPost: parseInt(e.target.value) || 0 })}
                  min={0}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
                <p className="text-xs text-gray-500 mt-1">0表示无限制</p>
              </div>
            </div>
            <div className="flex justify-end gap-3 mt-6">
              <button
                onClick={handleCloseModal}
                className="px-4 py-2 text-sm font-medium text-gray-600 bg-gray-100 rounded-md hover:bg-gray-200 transition-colors"
              >
                取消
              </button>
              <button
                onClick={handleSubmit}
                disabled={isSubmitting || !formData.name.trim() || !formData.slug.trim()}
                className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700 transition-colors disabled:opacity-50"
              >
                {isSubmitting ? '保存中...' : (editingCategory ? '保存' : '创建')}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}