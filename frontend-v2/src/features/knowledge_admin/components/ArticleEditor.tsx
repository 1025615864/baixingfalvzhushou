/**
 * ArticleEditor 组件 - 文章编辑器
 */

import { useState, useEffect } from 'react';

import type {
  KnowledgeArticle,
  KnowledgeArticleListItem,
  KnowledgeType,
  CreateArticleRequest,
  UpdateArticleRequest,
} from '../types';
import { KnowledgeTypeLabels } from '../types';

interface ArticleEditorProps {
  article: KnowledgeArticleListItem | KnowledgeArticle | null;
  categories: string[];
  onSave: (data: CreateArticleRequest | UpdateArticleRequest) => void;
  onCancel: () => void;
  isLoading?: boolean;
}

const KNOWLEDGE_TYPES: { value: KnowledgeType; label: string }[] = [
  { value: 'law', label: KnowledgeTypeLabels.law },
  { value: 'case', label: KnowledgeTypeLabels.case },
  { value: 'regulation', label: KnowledgeTypeLabels.regulation },
  { value: 'interpretation', label: KnowledgeTypeLabels.interpretation },
];

export function ArticleEditor({
  article,
  categories,
  onSave,
  onCancel,
  isLoading = false,
}: ArticleEditorProps): JSX.Element {
  const isEditMode = !!article;

  // 表单状态
  const [title, setTitle] = useState('');
  const [knowledgeType, setKnowledgeType] = useState<KnowledgeType>('law');
  const [category, setCategory] = useState('');
  const [newCategory, setNewCategory] = useState('');
  const [isCreatingCategory, setIsCreatingCategory] = useState(false);
  const [articleNumber, setArticleNumber] = useState('');
  const [content, setContent] = useState('');
  const [summary, setSummary] = useState('');
  const [keywords, setKeywords] = useState('');
  const [source, setSource] = useState('');
  const [sourceVersion, setSourceVersion] = useState('');
  const [effectiveDate, setEffectiveDate] = useState('');

  // 错误状态
  const [errors, setErrors] = useState<Record<string, string>>({});

  // 初始化编辑数据
  useEffect(() => {
    if (article && 'content' in article) {
      // 完整文章对象
      const fullArticle = article;
      setTitle(fullArticle.title);
      setKnowledgeType(fullArticle.knowledgeType);
      setCategory(fullArticle.category);
      setArticleNumber(fullArticle.articleNumber || '');
      setContent(fullArticle.content);
      setSummary(fullArticle.summary || '');
      setKeywords(fullArticle.keywords || '');
      setSource(fullArticle.source || '');
      setSourceVersion(fullArticle.sourceVersion || '');
      setEffectiveDate(fullArticle.effectiveDate || '');
    } else if (article) {
      // 列表项，只设置基本信息
      setTitle(article.title);
      setKnowledgeType(article.knowledgeType);
      setCategory(article.category);
      setArticleNumber(article.articleNumber || '');
    } else {
      // 新建模式，重置表单
      setTitle('');
      setKnowledgeType('law');
      setCategory(categories[0] || '');
      setArticleNumber('');
      setContent('');
      setSummary('');
      setKeywords('');
      setSource('');
      setSourceVersion('');
      setEffectiveDate('');
    }
  }, [article, categories]);

  const validate = (): boolean => {
    const newErrors: Record<string, string> = {};

    if (!title.trim()) {
      newErrors.title = '请输入文章标题';
    }
    if (!category && !newCategory) {
      newErrors.category = '请选择或创建分类';
    }
    if (!content.trim()) {
      newErrors.content = '请输入文章内容';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = (e: React.FormEvent): void => {
    e.preventDefault();

    if (!validate()) return;

    const finalCategory = isCreatingCategory && newCategory ? newCategory : category;

    const data: CreateArticleRequest = {
      knowledgeType,
      title: title.trim(),
      articleNumber: articleNumber.trim() || null,
      content: content.trim(),
      summary: summary.trim() || null,
      category: finalCategory,
      keywords: keywords.trim() || null,
      source: source.trim() || null,
      sourceVersion: sourceVersion.trim() || null,
      effectiveDate: effectiveDate || null,
    };

    onSave(data);
  };

  return (
    <form onSubmit={handleSubmit} className="bg-white rounded-lg shadow">
      {/* 头部 */}
      <div className="px-6 py-4 border-b border-gray-200 flex items-center justify-between">
        <h2 className="text-lg font-semibold text-gray-900">
          {isEditMode ? '编辑文章' : '新建文章'}
        </h2>
        <div className="flex items-center space-x-3">
          <button
            type="button"
            onClick={onCancel}
            className="px-4 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
          >
            取消
          </button>
          <button
            type="submit"
            disabled={isLoading}
            className="px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isLoading ? '保存中...' : '保存'}
          </button>
        </div>
      </div>

      {/* 表单内容 */}
      <div className="p-6 space-y-6">
        {/* 基本信息 */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* 标题 */}
          <div className="md:col-span-2">
            <label className="block text-sm font-medium text-gray-700">
              标题 <span className="text-red-500">*</span>
            </label>
            <input
              type="text"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="输入文章标题"
              className={`mt-1 block w-full border rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm ${
                errors.title ? 'border-red-300' : 'border-gray-300'
              }`}
            />
            {errors.title && <p className="mt-1 text-sm text-red-600">{errors.title}</p>}
          </div>

          {/* 知识类型 */}
          <div>
            <label className="block text-sm font-medium text-gray-700">
              知识类型 <span className="text-red-500">*</span>
            </label>
            <select
              value={knowledgeType}
              onChange={(e) => setKnowledgeType(e.target.value as KnowledgeType)}
              className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
            >
              {KNOWLEDGE_TYPES.map((type) => (
                <option key={type.value} value={type.value}>
                  {type.label}
                </option>
              ))}
            </select>
          </div>

          {/* 分类 */}
          <div>
            <label className="block text-sm font-medium text-gray-700">
              分类 <span className="text-red-500">*</span>
            </label>
            <div className="mt-1 flex space-x-2">
              {isCreatingCategory ? (
                <>
                  <input
                    type="text"
                    value={newCategory}
                    onChange={(e) => setNewCategory(e.target.value)}
                    placeholder="输入新分类名称"
                    className="flex-1 block border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                  />
                  <button
                    type="button"
                    onClick={() => {
                      setIsCreatingCategory(false);
                      setNewCategory('');
                    }}
                    className="px-3 py-2 border border-gray-300 rounded-md text-sm text-gray-700 hover:bg-gray-50"
                  >
                    取消
                  </button>
                </>
              ) : (
                <>
                  <select
                    value={category}
                    onChange={(e) => setCategory(e.target.value)}
                    className={`flex-1 block border rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm ${
                      errors.category ? 'border-red-300' : 'border-gray-300'
                    }`}
                  >
                    <option value="">请选择分类</option>
                    {categories.map((cat) => (
                      <option key={cat} value={cat}>
                        {cat}
                      </option>
                    ))}
                  </select>
                  <button
                    type="button"
                    onClick={() => setIsCreatingCategory(true)}
                    className="px-3 py-2 border border-blue-300 rounded-md text-sm text-blue-600 hover:bg-blue-50"
                  >
                    + 新建
                  </button>
                </>
              )}
            </div>
            {errors.category && <p className="mt-1 text-sm text-red-600">{errors.category}</p>}
          </div>

          {/* 编号 */}
          <div>
            <label className="block text-sm font-medium text-gray-700">
              编号/条号
            </label>
            <input
              type="text"
              value={articleNumber}
              onChange={(e) => setArticleNumber(e.target.value)}
              placeholder="例如：第十条、案例-2024-001"
              className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
            />
          </div>

          {/* 生效日期 */}
          <div>
            <label className="block text-sm font-medium text-gray-700">
              生效日期
            </label>
            <input
              type="date"
              value={effectiveDate}
              onChange={(e) => setEffectiveDate(e.target.value)}
              className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
            />
          </div>
        </div>

        {/* 内容 */}
        <div>
          <label className="block text-sm font-medium text-gray-700">
            内容 <span className="text-red-500">*</span>
          </label>
          <textarea
            value={content}
            onChange={(e) => setContent(e.target.value)}
            placeholder="输入文章内容..."
            rows={12}
            className={`mt-1 block w-full border rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm font-mono ${
              errors.content ? 'border-red-300' : 'border-gray-300'
            }`}
          />
          {errors.content && <p className="mt-1 text-sm text-red-600">{errors.content}</p>}
          <p className="mt-1 text-xs text-gray-500">
            支持纯文本格式，建议分段书写，使用空行分隔段落
          </p>
        </div>

        {/* 摘要 */}
        <div>
          <label className="block text-sm font-medium text-gray-700">
            摘要
          </label>
          <textarea
            value={summary}
            onChange={(e) => setSummary(e.target.value)}
            placeholder="输入文章摘要（可选，用于列表展示）"
            rows={3}
            className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
          />
        </div>

        {/* 关键词 */}
        <div>
          <label className="block text-sm font-medium text-gray-700">
            关键词
          </label>
          <input
            type="text"
            value={keywords}
            onChange={(e) => setKeywords(e.target.value)}
            placeholder="多个关键词用逗号分隔，例如：劳动合同, 加班, 工资"
            className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
          />
        </div>

        {/* 来源信息 */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 border-t border-gray-200 pt-6">
          <div>
            <label className="block text-sm font-medium text-gray-700">
              来源
            </label>
            <input
              type="text"
              value={source}
              onChange={(e) => setSource(e.target.value)}
              placeholder="例如：全国人民代表大会、最高人民法院"
              className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700">
              来源版本
            </label>
            <input
              type="text"
              value={sourceVersion}
              onChange={(e) => setSourceVersion(e.target.value)}
              placeholder="例如：2020年修订、2024版"
              className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
            />
          </div>
        </div>
      </div>

      {/* 底部按钮 */}
      <div className="px-6 py-4 bg-gray-50 border-t border-gray-200 flex items-center justify-end space-x-3 rounded-b-lg">
        <button
          type="button"
          onClick={onCancel}
          className="px-4 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 hover:bg-gray-100 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
        >
          取消
        </button>
        <button
          type="submit"
          disabled={isLoading}
          className="px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {isLoading ? '保存中...' : '保存文章'}
        </button>
      </div>
    </form>
  );
}