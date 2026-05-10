/**
 * PostEditor - 帖子编辑器组件
 */

import { useState, useCallback } from 'react';

import type { PostCategory, CreatePostRequest, UpdatePostRequest } from '../types';

interface PostEditorProps {
  initialData?: {
    id?: string;
    title?: string;
    content?: string;
    summary?: string;
    category?: PostCategory;
    tags?: string[];
    coverImage?: string;
  };
  onSubmit: (data: CreatePostRequest | UpdatePostRequest) => void | Promise<void>;
  onCancel?: () => void;
  isLoading?: boolean;
  mode: 'create' | 'edit';
}

const categories: { value: PostCategory; label: string }[] = [
  { value: 'general', label: '综合' },
  { value: 'legal', label: '法律' },
  { value: 'consultation', label: '咨询' },
  { value: 'discussion', label: '讨论' },
  { value: 'announcement', label: '公告' },
];

/**
 * 帖子编辑器组件
 */
export function PostEditor({
  initialData = {},
  onSubmit,
  onCancel,
  isLoading = false,
  mode,
}: PostEditorProps): JSX.Element {
  const [title, setTitle] = useState(initialData.title ?? '');
  const [content, setContent] = useState(initialData.content ?? '');
  const [summary, setSummary] = useState(initialData.summary ?? '');
  const [category, setCategory] = useState<PostCategory>(initialData.category ?? 'general');
  const [tags, setTags] = useState<string[]>(initialData.tags ?? []);
  const [tagInput, setTagInput] = useState('');
  const [coverImage, setCoverImage] = useState(initialData.coverImage ?? '');
  const [errors, setErrors] = useState<Record<string, string>>({});

  /**
   * 验证表单
   */
  const validateForm = useCallback((): boolean => {
    const newErrors: Record<string, string> = {};

    if (!title.trim()) {
      newErrors.title = '请输入标题';
    } else if (title.length > 100) {
      newErrors.title = '标题不能超过100个字符';
    }

    if (!content.trim()) {
      newErrors.content = '请输入内容';
    } else if (content.length < 10) {
      newErrors.content = '内容至少10个字符';
    }

    if (summary && summary.length > 200) {
      newErrors.summary = '摘要不能超过200个字符';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  }, [title, content, summary]);

  /**
   * 处理提交
   */
  const handleSubmit = (publish: boolean): void => {
    if (!validateForm()) {
      return;
    }

    if (mode === 'edit' && initialData?.id) {
      const data: UpdatePostRequest = {
        id: initialData.id,
        title: title.trim(),
        content: content.trim(),
        summary: summary.trim() || undefined,
        category,
        tags: tags.length > 0 ? tags : undefined,
        coverImage: coverImage || undefined,
        status: publish ? 'published' : 'draft',
      };
      void onSubmit(data);
    } else {
      const data: CreatePostRequest = {
        title: title.trim(),
        content: content.trim(),
        summary: summary.trim() || undefined,
        category,
        tags: tags.length > 0 ? tags : undefined,
        coverImage: coverImage || undefined,
        status: publish ? 'published' : 'draft',
      };
      void onSubmit(data);
    }
  };

  /**
   * 处理添加标签
   */
  const handleAddTag = (): void => {
    const trimmed = tagInput.trim();
    if (trimmed && !tags.includes(trimmed) && tags.length < 5) {
      setTags([...tags, trimmed]);
      setTagInput('');
    }
  };

  /**
   * 处理删除标签
   */
  const handleRemoveTag = (tagToRemove: string): void => {
    setTags(tags.filter((tag) => tag !== tagToRemove));
  };

  /**
   * 处理标签输入键盘事件
   */
  const handleTagKeyDown = (e: React.KeyboardEvent): void => {
    if (e.key === 'Enter') {
      e.preventDefault();
      handleAddTag();
    } else if (e.key === 'Backspace' && !tagInput && tags.length > 0) {
      handleRemoveTag(tags[tags.length - 1]);
    }
  };

  /**
   * 处理图片上传（模拟）
   */
  const handleImageUpload = (): void => {
    // 实际项目中应该调用文件上传 API
    const mockImageUrl = `https://picsum.photos/800/400?random=${Date.now()}`;
    setCoverImage(mockImageUrl);
  };

  return (
    <div className="bg-white rounded-lg shadow-sm">
      <div className="p-6 space-y-6">
        {/* 标题 */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            标题 <span className="text-red-500">*</span>
          </label>
          <input
            type="text"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            placeholder="请输入帖子标题"
            className={`w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent ${
              errors.title ? 'border-red-500' : 'border-gray-300'
            }`}
            maxLength={100}
          />
          {errors.title && <p className="mt-1 text-sm text-red-500">{errors.title}</p>}
          <p className="mt-1 text-xs text-gray-400 text-right">{title.length}/100</p>
        </div>

        {/* 分类 */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            分类 <span className="text-red-500">*</span>
          </label>
          <div className="flex flex-wrap gap-2">
            {categories.map((cat) => (
              <button
                key={cat.value}
                type="button"
                onClick={() => setCategory(cat.value)}
                className={`px-4 py-2 text-sm font-medium rounded-full transition-colors ${
                  category === cat.value
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }`}
              >
                {cat.label}
              </button>
            ))}
          </div>
        </div>

        {/* 封面图 */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">封面图</label>
          {coverImage ? (
            <div className="relative w-full h-48 rounded-lg overflow-hidden group">
              <img src={coverImage} alt="封面" className="w-full h-full object-cover" />
              <div className="absolute inset-0 bg-black bg-opacity-50 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity">
                <button
                  type="button"
                  onClick={() => setCoverImage('')}
                  className="px-4 py-2 text-sm text-white bg-red-600 rounded-lg hover:bg-red-700"
                >
                  删除封面
                </button>
              </div>
            </div>
          ) : (
            <button
              type="button"
              onClick={handleImageUpload}
              className="w-full h-48 border-2 border-dashed border-gray-300 rounded-lg flex flex-col items-center justify-center text-gray-500 hover:border-blue-500 hover:text-blue-500 transition-colors"
            >
              <svg className="w-12 h-12 mb-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"
                />
              </svg>
              <span>点击上传封面图</span>
            </button>
          )}
        </div>

        {/* 摘要 */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">摘要</label>
          <textarea
            value={summary}
            onChange={(e) => setSummary(e.target.value)}
            placeholder="请输入帖子摘要（选填，不填将自动提取正文前200字）"
            rows={3}
            className={`w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none ${
              errors.summary ? 'border-red-500' : 'border-gray-300'
            }`}
            maxLength={200}
          />
          {errors.summary && <p className="mt-1 text-sm text-red-500">{errors.summary}</p>}
          <p className="mt-1 text-xs text-gray-400 text-right">{summary.length}/200</p>
        </div>

        {/* 内容 */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            内容 <span className="text-red-500">*</span>
          </label>
          <textarea
            value={content}
            onChange={(e) => setContent(e.target.value)}
            placeholder="请输入帖子内容，支持 Markdown 格式"
            rows={15}
            className={`w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent font-mono text-sm resize-y ${
              errors.content ? 'border-red-500' : 'border-gray-300'
            }`}
          />
          {errors.content && <p className="mt-1 text-sm text-red-500">{errors.content}</p>}
          <p className="mt-1 text-xs text-gray-400 text-right">{content.length} 字符</p>
        </div>

        {/* 标签 */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            标签 <span className="text-gray-400 text-xs">（最多5个）</span>
          </label>
          <div className="flex flex-wrap items-center gap-2 p-2 border border-gray-300 rounded-lg focus-within:ring-2 focus-within:ring-blue-500 focus-within:border-transparent">
            {tags.map((tag) => (
              <span
                key={tag}
                className="inline-flex items-center px-2 py-1 text-sm bg-blue-100 text-blue-700 rounded-full"
              >
                {tag}
                <button
                  type="button"
                  onClick={() => handleRemoveTag(tag)}
                  className="ml-1 text-blue-500 hover:text-blue-700"
                >
                  ×
                </button>
              </span>
            ))}
            {tags.length < 5 && (
              <input
                type="text"
                value={tagInput}
                onChange={(e) => setTagInput(e.target.value)}
                onKeyDown={handleTagKeyDown}
                onBlur={handleAddTag}
                placeholder="输入标签按回车添加"
                className="flex-1 min-w-[120px] outline-none text-sm"
              />
            )}
          </div>
        </div>

        {/* 操作按钮 */}
        <div className="flex items-center justify-end gap-4 pt-4 border-t border-gray-200">
          {onCancel && (
            <button
              type="button"
              onClick={onCancel}
              disabled={isLoading}
              className="px-6 py-2 text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200 disabled:opacity-50 transition-colors"
            >
              取消
            </button>
          )}
          <button
            type="button"
            onClick={() => handleSubmit(false)}
            disabled={isLoading}
            className="px-6 py-2 text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200 disabled:opacity-50 transition-colors"
          >
            {isLoading ? '保存中...' : '保存草稿'}
          </button>
          <button
            type="button"
            onClick={() => handleSubmit(true)}
            disabled={isLoading}
            className="px-6 py-2 text-white bg-blue-600 rounded-lg hover:bg-blue-700 disabled:opacity-50 transition-colors"
          >
            {isLoading ? '发布中...' : mode === 'create' ? '立即发布' : '更新发布'}
          </button>
        </div>
      </div>
    </div>
  );
}