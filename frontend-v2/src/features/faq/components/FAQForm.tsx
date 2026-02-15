/**
 * FAQForm - FAQ表单组件（管理）
 */

import React, { useState, useCallback } from 'react';

import type { FAQFormProps, FAQItem } from '../types';

/**
 * FAQ表单组件
 */
export const FAQForm: React.FC<FAQFormProps> = ({
  initialData,
  categories = [],
  onSubmit,
  onCancel,
  loading = false,
}) => {
  const isEdit = !!initialData?.id;

  const [formData, setFormData] = useState<Partial<FAQItem>>({
    question: '',
    answer: '',
    category: '',
    tags: [],
    priority: 0,
    isActive: true,
    ...initialData,
  });

  const [tagInput, setTagInput] = useState('');

  // 处理输入变化
  const handleChange = useCallback((field: keyof FAQItem, value: unknown) => {
    setFormData((prev) => ({ ...prev, [field]: value }));
  }, []);

  // 处理添加标签
  const handleAddTag = useCallback(() => {
    const trimmed = tagInput.trim();
    if (trimmed && !formData.tags?.includes(trimmed)) {
      setFormData((prev) => ({
        ...prev,
        tags: [...(prev.tags || []), trimmed],
      }));
      setTagInput('');
    }
  }, [tagInput, formData.tags]);

  // 处理删除标签
  const handleRemoveTag = useCallback((tag: string) => {
    setFormData((prev) => ({
      ...prev,
      tags: prev.tags?.filter((t) => t !== tag) || [],
    }));
  }, []);

  // 处理提交
  const handleSubmit = useCallback((e: React.FormEvent) => {
    e.preventDefault();
    onSubmit({
      question: formData.question || '',
      answer: formData.answer || '',
      category: formData.category || undefined,
      tags: formData.tags ?? undefined,
      priority: formData.priority,
      isActive: formData.isActive,
    });
  }, [formData, onSubmit]);

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      {/* 问题 */}
      <div>
        <label className="block text-sm font-medium text-gray-700">
          问题 <span className="text-red-500">*</span>
        </label>
        <input
          type="text"
          value={formData.question || ''}
          onChange={(e) => handleChange('question', e.target.value)}
          required
          disabled={loading}
          className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500 disabled:bg-gray-100"
          placeholder="输入常见问题"
        />
      </div>

      {/* 答案 */}
      <div>
        <label className="block text-sm font-medium text-gray-700">
          答案 <span className="text-red-500">*</span>
        </label>
        <textarea
          value={formData.answer || ''}
          onChange={(e) => handleChange('answer', e.target.value)}
          required
          disabled={loading}
          rows={6}
          className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500 disabled:bg-gray-100"
          placeholder="输入详细答案"
        />
      </div>

      {/* 分类 */}
      <div>
        <label className="block text-sm font-medium text-gray-700">
          分类
        </label>
        <select
          value={formData.category || ''}
          onChange={(e) => handleChange('category', e.target.value || undefined)}
          disabled={loading}
          className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500 disabled:bg-gray-100"
        >
          <option value="">选择分类</option>
          {categories.map((cat) => (
            <option key={cat} value={cat}>
              {cat}
            </option>
          ))}
          <option value="__new__">+ 新建分类</option>
        </select>
      </div>

      {/* 标签 */}
      <div>
        <label className="block text-sm font-medium text-gray-700">
          标签
        </label>
        <div className="mt-1 flex gap-2">
          <input
            type="text"
            value={tagInput}
            onChange={(e) => setTagInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter') {
                e.preventDefault();
                handleAddTag();
              }
            }}
            disabled={loading}
            className="block flex-1 rounded-md border border-gray-300 px-3 py-2 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500 disabled:bg-gray-100"
            placeholder="输入标签后按回车"
          />
          <button
            type="button"
            onClick={handleAddTag}
            disabled={!tagInput.trim() || loading}
            className="rounded-md bg-gray-100 px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-200 disabled:opacity-50"
          >
            添加
          </button>
        </div>
        {formData.tags && formData.tags.length > 0 && (
          <div className="mt-2 flex flex-wrap gap-2">
            {formData.tags.map((tag) => (
              <span
                key={tag}
                className="inline-flex items-center gap-1 rounded-full bg-blue-50 px-2.5 py-1 text-sm text-blue-700"
              >
                {tag}
                <button
                  type="button"
                  onClick={() => handleRemoveTag(tag)}
                  className="rounded-full p-0.5 hover:bg-blue-100"
                >
                  ×
                </button>
              </span>
            ))}
          </div>
        )}
      </div>

      {/* 优先级 */}
      <div>
        <label className="block text-sm font-medium text-gray-700">
          优先级
        </label>
        <input
          type="number"
          value={formData.priority || 0}
          onChange={(e) => handleChange('priority', parseInt(e.target.value, 10) || 0)}
          disabled={loading}
          min={0}
          className="mt-1 block w-32 rounded-md border border-gray-300 px-3 py-2 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500 disabled:bg-gray-100"
        />
        <p className="mt-1 text-xs text-gray-500">数字越大，排序越靠前</p>
      </div>

      {/* 是否激活 */}
      <div>
        <label className="flex items-center gap-2">
          <input
            type="checkbox"
            checked={formData.isActive ?? true}
            onChange={(e) => handleChange('isActive', e.target.checked)}
            disabled={loading}
            className="h-4 w-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
          />
          <span className="text-sm font-medium text-gray-700">激活状态</span>
        </label>
        <p className="mt-1 text-xs text-gray-500">未激活的FAQ不会在前台显示</p>
      </div>

      {/* 操作按钮 */}
      <div className="flex items-center justify-end gap-3 pt-4 border-t border-gray-200">
        {onCancel && (
          <button
            type="button"
            onClick={onCancel}
            disabled={loading}
            className="rounded-md border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-50"
          >
            取消
          </button>
        )}
        <button
          type="submit"
          disabled={loading || !formData.question?.trim() || !formData.answer?.trim()}
          className="rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50"
        >
          {loading ? '保存中...' : isEdit ? '更新' : '创建'}
        </button>
      </div>
    </form>
  );
};

FAQForm.displayName = 'FAQForm';