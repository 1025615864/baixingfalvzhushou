/**
 * 快捷回复模板管理组件
 */

import React, { useState } from 'react';

import {
  useReplyTemplates,
  useCreateReplyTemplate,
  useUpdateReplyTemplate,
  useDeleteReplyTemplate,
  useReplyTemplateCategories,
} from '../hooks/useReplyTemplates';
import type { LawyerReplyTemplate } from '../types';

interface ReplyTemplatesProps {
  onSelectTemplate?: (content: string) => void;
  showSelectButton?: boolean;
}

export const ReplyTemplates: React.FC<ReplyTemplatesProps> = ({
  onSelectTemplate,
  showSelectButton = false,
}) => {
  const [isCreating, setIsCreating] = useState(false);
  const [editingTemplate, setEditingTemplate] = useState<LawyerReplyTemplate | null>(null);
  const [selectedCategory, setSelectedCategory] = useState<string>('');
  const [formData, setFormData] = useState({
    title: '',
    content: '',
    category: '',
  });

  const { data: templatesData, isLoading } = useReplyTemplates({
    category: selectedCategory || undefined,
  });
  const { data: categoriesData } = useReplyTemplateCategories();

  const createMutation = useCreateReplyTemplate();
  const updateMutation = useUpdateReplyTemplate();
  const deleteMutation = useDeleteReplyTemplate();

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();

    void (async () => {
      try {
        if (editingTemplate) {
          await updateMutation.mutateAsync({
            templateId: editingTemplate.id,
            data: formData,
          });
          setEditingTemplate(null);
        } else {
          await createMutation.mutateAsync(formData);
          setIsCreating(false);
        }
        setFormData({ title: '', content: '', category: '' });
      } catch {
        // 错误已在hook中处理
      }
    })();
  };

  const handleEdit = (template: LawyerReplyTemplate) => {
    setEditingTemplate(template);
    setFormData({
      title: template.title,
      content: template.content,
      category: template.category || '',
    });
    setIsCreating(true);
  };

  const handleDelete = async (templateId: string) => {
    if (window.confirm('确定要删除这个模板吗？')) {
      try {
        await deleteMutation.mutateAsync(templateId);
      } catch {
        // 错误已在hook中处理
      }
    }
  };

  const handleCancel = () => {
    setIsCreating(false);
    setEditingTemplate(null);
    setFormData({ title: '', content: '', category: '' });
  };

  const handleUseTemplate = (template: LawyerReplyTemplate) => {
    if (onSelectTemplate) {
      onSelectTemplate(template.content);
    }
  };

  // 按分类分组模板
  const groupedTemplates = React.useMemo(() => {
    if (!templatesData?.items) return {};

    return templatesData.items.reduce((acc, template) => {
      const category = template.category || '未分类';
      if (!acc[category]) {
        acc[category] = [];
      }
      acc[category].push(template);
      return acc;
    }, {} as Record<string, LawyerReplyTemplate[]>);
  }, [templatesData]);

  return (
    <div className="space-y-6">
      {/* 标题和创建按钮 */}
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-medium text-gray-900">快捷回复模板</h2>
        {!isCreating && (
          <button
            onClick={() => setIsCreating(true)}
            className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700"
          >
            <svg
              className="w-4 h-4 mr-2"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M12 4v16m8-8H4"
              />
            </svg>
            新建模板
          </button>
        )}
      </div>

      {/* 创建/编辑表单 */}
      {isCreating && (
        <div className="bg-gray-50 rounded-lg p-4">
          <h3 className="text-sm font-medium text-gray-900 mb-4">
            {editingTemplate ? '编辑模板' : '新建模板'}
          </h3>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label
                htmlFor="template-title"
                className="block text-sm font-medium text-gray-700"
              >
                模板标题
              </label>
              <input
                type="text"
                id="template-title"
                value={formData.title}
                onChange={(e) =>
                  setFormData((prev) => ({ ...prev, title: e.target.value }))
                }
                className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
                placeholder="例如：咨询确认回复"
                required
              />
            </div>

            <div>
              <label
                htmlFor="template-category"
                className="block text-sm font-medium text-gray-700"
              >
                分类
              </label>
              <div className="mt-1 flex items-center space-x-2">
                <input
                  type="text"
                  id="template-category"
                  value={formData.category}
                  onChange={(e) =>
                    setFormData((prev) => ({ ...prev, category: e.target.value }))
                  }
                  className="block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
                  placeholder="例如：咨询回复"
                  list="categories"
                />
                <datalist id="categories">
                  {categoriesData?.categories.map((cat) => (
                    <option key={cat} value={cat} />
                  ))}
                </datalist>
              </div>
            </div>

            <div>
              <label
                htmlFor="template-content"
                className="block text-sm font-medium text-gray-700"
              >
                模板内容
              </label>
              <textarea
                id="template-content"
                rows={4}
                value={formData.content}
                onChange={(e) =>
                  setFormData((prev) => ({ ...prev, content: e.target.value }))
                }
                className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
                placeholder="请输入模板内容..."
                required
              />
            </div>

            <div className="flex justify-end space-x-3">
              <button
                type="button"
                onClick={handleCancel}
                className="px-4 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 hover:bg-gray-50"
              >
                取消
              </button>
              <button
                type="submit"
                disabled={
                  createMutation.isPending || updateMutation.isPending
                }
                className="px-4 py-2 border border-transparent rounded-md text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 disabled:opacity-50"
              >
                {createMutation.isPending || updateMutation.isPending
                  ? '保存中...'
                  : '保存'}
              </button>
            </div>
          </form>
        </div>
      )}

      {/* 分类筛选 */}
      <div className="flex items-center space-x-2">
        <span className="text-sm text-gray-500">筛选：</span>
        <select
          value={selectedCategory}
          onChange={(e) => setSelectedCategory(e.target.value)}
          className="rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
        >
          <option value="">全部分类</option>
          {categoriesData?.categories.map((cat) => (
            <option key={cat} value={cat}>
              {cat}
            </option>
          ))}
        </select>
      </div>

      {/* 模板列表 */}
      {isLoading ? (
        <div className="text-center py-8">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
        </div>
      ) : templatesData?.items.length === 0 ? (
        <div className="text-center py-8 text-gray-500">
          暂无模板，点击上方按钮创建
        </div>
      ) : (
        <div className="space-y-6">
          {Object.entries(groupedTemplates).map(([category, templates]) => (
            <div key={category}>
              <h3 className="text-sm font-medium text-gray-500 mb-3">
                {category}
              </h3>
              <div className="space-y-3">
                {templates.map((template) => (
                  <div
                    key={template.id}
                    className="bg-white border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow"
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <h4 className="text-sm font-medium text-gray-900">
                          {template.title}
                        </h4>
                        <p className="mt-1 text-sm text-gray-600 whitespace-pre-wrap">
                          {template.content}
                        </p>
                        <div className="mt-2 flex items-center text-xs text-gray-400">
                          <span>使用 {template.useCount} 次</span>
                          <span className="mx-2">•</span>
                          <span>
                            {new Date(template.updatedAt).toLocaleDateString(
                              'zh-CN'
                            )}
                          </span>
                        </div>
                      </div>
                      <div className="ml-4 flex items-center space-x-2">
                        {showSelectButton && onSelectTemplate && (
                          <button
                            onClick={() => handleUseTemplate(template)}
                            className="px-3 py-1 text-xs font-medium text-blue-600 bg-blue-50 rounded hover:bg-blue-100"
                          >
                            使用
                          </button>
                        )}
                        <button
                          onClick={() => handleEdit(template)}
                          className="p-1 text-gray-400 hover:text-gray-600"
                          title="编辑"
                        >
                          <svg
                            className="w-4 h-4"
                            fill="none"
                            stroke="currentColor"
                            viewBox="0 0 24 24"
                          >
                            <path
                              strokeLinecap="round"
                              strokeLinejoin="round"
                              strokeWidth={2}
                              d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"
                            />
                          </svg>
                        </button>
                        <button
                          onClick={() => void handleDelete(template.id)}
                          className="p-1 text-gray-400 hover:text-red-600"
                          title="删除"
                        >
                          <svg
                            className="w-4 h-4"
                            fill="none"
                            stroke="currentColor"
                            viewBox="0 0 24 24"
                          >
                            <path
                              strokeLinecap="round"
                              strokeLinejoin="round"
                              strokeWidth={2}
                              d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"
                            />
                          </svg>
                        </button>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default ReplyTemplates;