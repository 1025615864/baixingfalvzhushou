/**
 * ArticleEditor - 文章编辑器组件
 */

import { useState, useEffect } from 'react';

import type { NewsArticle, CreateNewsRequest, UpdateNewsRequest } from '../types';

interface ArticleEditorProps {
  article?: NewsArticle | null;
  isOpen: boolean;
  isLoading: boolean;
  onClose: () => void;
  onSave: (data: CreateNewsRequest | UpdateNewsRequest) => void;
}

const CATEGORIES = [
  { value: 'general', label: '综合' },
  { value: 'legal', label: '法律' },
  { value: 'politics', label: '时政' },
  { value: 'economy', label: '经济' },
  { value: 'society', label: '社会' },
  { value: 'technology', label: '科技' },
  { value: 'other', label: '其他' },
];

/**
 * 文章编辑器组件
 */
export function ArticleEditor({
  article,
  isOpen,
  isLoading,
  onClose,
  onSave,
}: ArticleEditorProps): JSX.Element | null {
  const [formData, setFormData] = useState<CreateNewsRequest>({
    title: '',
    summary: '',
    content: '',
    coverImage: '',
    category: 'general',
    source: '',
    sourceUrl: '',
    sourceSite: '',
    author: '',
    isTop: false,
    isPublished: false,
    reviewStatus: 'pending',
    reviewReason: '',
    scheduledPublishAt: null,
    scheduledUnpublishAt: null,
  });

  const [errors, setErrors] = useState<Record<string, string>>({});

  // 当编辑的文章变化时，更新表单数据
  useEffect(() => {
    if (article) {
      setFormData({
        title: article.title,
        summary: article.summary || '',
        content: article.content,
        coverImage: article.coverImage || '',
        category: article.category,
        source: article.source || '',
        sourceUrl: article.sourceUrl || '',
        sourceSite: article.sourceSite || '',
        author: article.author || '',
        isTop: article.isTop,
        isPublished: article.isPublished,
        reviewStatus: article.reviewStatus,
        reviewReason: article.reviewReason || '',
        scheduledPublishAt: article.scheduledPublishAt,
        scheduledUnpublishAt: article.scheduledUnpublishAt,
      });
    } else {
      // 重置为默认值
      setFormData({
        title: '',
        summary: '',
        content: '',
        coverImage: '',
        category: 'general',
        source: '',
        sourceUrl: '',
        sourceSite: '',
        author: '',
        isTop: false,
        isPublished: false,
        reviewStatus: 'pending',
        reviewReason: '',
        scheduledPublishAt: null,
        scheduledUnpublishAt: null,
      });
    }
    setErrors({});
  }, [article, isOpen]);

  if (!isOpen) return null;

  const validateForm = (): boolean => {
    const newErrors: Record<string, string> = {};

    if (!formData.title.trim()) {
      newErrors.title = '标题不能为空';
    } else if (formData.title.length > 200) {
      newErrors.title = '标题不能超过200个字符';
    }

    if (!formData.content.trim()) {
      newErrors.content = '内容不能为空';
    }

    if (formData.summary && formData.summary.length > 500) {
      newErrors.summary = '摘要不能超过500个字符';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = (e: React.FormEvent): void => {
    e.preventDefault();
    if (!validateForm()) return;

    if (article) {
      // 更新模式
      const updateData: UpdateNewsRequest = {
        ...formData,
      };
      onSave(updateData);
    } else {
      // 创建模式
      onSave(formData);
    }
  };

  const handleChange = (field: keyof CreateNewsRequest, value: unknown): void => {
    setFormData((prev) => ({ ...prev, [field]: value }));
    // 清除对应字段的错误
    if (errors[field]) {
      setErrors((prev) => {
        const newErrors = { ...prev };
        delete newErrors[field];
        return newErrors;
      });
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg shadow-xl w-full max-w-4xl max-h-[90vh] overflow-hidden flex flex-col">
        {/* 头部 */}
        <div className="px-6 py-4 border-b border-gray-200 flex items-center justify-between">
          <h2 className="text-xl font-semibold text-gray-900">
            {article ? '编辑文章' : '新建文章'}
          </h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600"
          >
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* 表单内容 */}
        <form onSubmit={handleSubmit} className="flex-1 overflow-y-auto p-6">
          <div className="space-y-6">
            {/* 标题 */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                标题 <span className="text-red-500">*</span>
              </label>
              <input
                type="text"
                value={formData.title}
                onChange={(e) => handleChange('title', e.target.value)}
                className={`w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 ${
                  errors.title ? 'border-red-500' : 'border-gray-300'
                }`}
                placeholder="请输入文章标题"
              />
              {errors.title && (
                <p className="mt-1 text-sm text-red-500">{errors.title}</p>
              )}
            </div>

            {/* 摘要 */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                摘要
              </label>
              <textarea
                value={formData.summary || ''}
                onChange={(e) => handleChange('summary', e.target.value)}
                rows={2}
                className={`w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 ${
                  errors.summary ? 'border-red-500' : 'border-gray-300'
                }`}
                placeholder="请输入文章摘要（可选）"
              />
              {errors.summary && (
                <p className="mt-1 text-sm text-red-500">{errors.summary}</p>
              )}
            </div>

            {/* 内容 */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                内容 <span className="text-red-500">*</span>
              </label>
              <textarea
                value={formData.content}
                onChange={(e) => handleChange('content', e.target.value)}
                rows={10}
                className={`w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 font-mono text-sm ${
                  errors.content ? 'border-red-500' : 'border-gray-300'
                }`}
                placeholder="请输入文章内容（支持Markdown格式）"
              />
              {errors.content && (
                <p className="mt-1 text-sm text-red-500">{errors.content}</p>
              )}
            </div>

            {/* 分类和作者 */}
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  分类
                </label>
                <select
                  value={formData.category}
                  onChange={(e) => handleChange('category', e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                >
                  {CATEGORIES.map((cat) => (
                    <option key={cat.value} value={cat.value}>
                      {cat.label}
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  作者
                </label>
                <input
                  type="text"
                  value={formData.author || ''}
                  onChange={(e) => handleChange('author', e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  placeholder="请输入作者"
                />
              </div>
            </div>

            {/* 来源信息 */}
            <div className="grid grid-cols-3 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  来源
                </label>
                <input
                  type="text"
                  value={formData.source || ''}
                  onChange={(e) => handleChange('source', e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  placeholder="文章来源"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  来源站点
                </label>
                <input
                  type="text"
                  value={formData.sourceSite || ''}
                  onChange={(e) => handleChange('sourceSite', e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  placeholder="来源站点"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  来源链接
                </label>
                <input
                  type="url"
                  value={formData.sourceUrl || ''}
                  onChange={(e) => handleChange('sourceUrl', e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  placeholder="https://"
                />
              </div>
            </div>

            {/* 封面图 */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                封面图URL
              </label>
              <input
                type="url"
                value={formData.coverImage || ''}
                onChange={(e) => handleChange('coverImage', e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                placeholder="https://"
              />
            </div>

            {/* 选项 */}
            <div className="flex gap-6">
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={formData.isTop}
                  onChange={(e) => handleChange('isTop', e.target.checked)}
                  className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                />
                <span className="text-sm text-gray-700">置顶</span>
              </label>
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={formData.isPublished}
                  onChange={(e) => handleChange('isPublished', e.target.checked)}
                  className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                />
                <span className="text-sm text-gray-700">立即发布</span>
              </label>
            </div>

            {/* 定时发布 */}
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  定时发布时间
                </label>
                <input
                  type="datetime-local"
                  value={formData.scheduledPublishAt || ''}
                  onChange={(e) => handleChange('scheduledPublishAt', e.target.value || null)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  定时下线时间
                </label>
                <input
                  type="datetime-local"
                  value={formData.scheduledUnpublishAt || ''}
                  onChange={(e) => handleChange('scheduledUnpublishAt', e.target.value || null)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                />
              </div>
            </div>
          </div>
        </form>

        {/* 底部按钮 */}
        <div className="px-6 py-4 border-t border-gray-200 flex justify-end gap-3">
          <button
            type="button"
            onClick={onClose}
            className="px-4 py-2 text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200"
          >
            取消
          </button>
          <button
            onClick={handleSubmit}
            disabled={isLoading}
            className="px-4 py-2 text-white bg-blue-600 rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
          >
            {isLoading && (
              <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
              </svg>
            )}
            {article ? '保存修改' : '创建文章'}
          </button>
        </div>
      </div>
    </div>
  );
}