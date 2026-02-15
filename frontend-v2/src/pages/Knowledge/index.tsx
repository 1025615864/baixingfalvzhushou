import { useState } from 'react';

import { useKnowledgeItems } from '@/features/knowledge';
import type { KnowledgeCategoryType, KnowledgeItem } from '@/features/knowledge';

const categories: { value: KnowledgeCategoryType | ''; label: string }[] = [
  { value: '', label: '全部' },
  { value: 'labor', label: '劳动纠纷' },
  { value: 'contract', label: '合同纠纷' },
  { value: 'marriage', label: '婚姻家庭' },
  { value: 'property', label: '房产纠纷' },
  { value: 'consumer', label: '消费者权益' },
  { value: 'traffic', label: '交通事故' },
  { value: 'inheritance', label: '继承纠纷' },
  { value: 'other', label: '其他' },
];

// 知识卡片组件
function KnowledgeCard({ item }: { item: KnowledgeItem }) {
  return (
    <article className="bg-white rounded-lg shadow-sm border border-gray-200 p-5 cursor-pointer hover:shadow-md transition-shadow">
      <div className="flex items-start justify-between gap-4">
        <div className="flex-1">
          {/* 分类标签 */}
          <div className="flex items-center gap-2 mb-2">
            <span className="px-2 py-0.5 bg-primary-50 text-primary-700 text-xs font-medium rounded">
              {item.category}
            </span>
          </div>

          {/* 标题 */}
          <h3 className="text-lg font-semibold text-gray-900 mb-2 line-clamp-2 hover:text-primary-600">
            {item.title}
          </h3>

          {/* 摘要 */}
          {item.summary && (
            <p className="text-sm text-gray-600 line-clamp-2 mb-3">
              {item.summary}
            </p>
          )}

          {/* 关键词 */}
          {item.tags && item.tags.length > 0 && (
            <div className="flex flex-wrap gap-2 mb-3">
              {item.tags.slice(0, 5).map((tag) => (
                <span
                  key={tag}
                  className="px-2 py-0.5 bg-gray-100 text-gray-600 text-xs rounded"
                >
                  {tag}
                </span>
              ))}
            </div>
          )}

          {/* 元信息 */}
          <div className="flex items-center gap-4 text-xs text-gray-400">
            <time dateTime={item.updatedAt}>
              更新于 {new Date(item.updatedAt).toLocaleDateString('zh-CN')}
            </time>
            <span>浏览 {item.viewCount}</span>
            <span>点赞 {item.likeCount}</span>
          </div>
        </div>
      </div>
    </article>
  );
}

// 知识列表组件
function KnowledgeList({ items, isLoading }: { items: KnowledgeItem[]; isLoading: boolean }) {
  if (isLoading) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {Array.from({ length: 4 }, (_, index) => (
          <div
            key={index}
            className="bg-white rounded-lg shadow-sm border border-gray-200 p-5 animate-pulse"
          >
            <div className="h-4 bg-gray-200 rounded w-20 mb-3" />
            <div className="h-6 bg-gray-200 rounded w-3/4 mb-2" />
            <div className="h-4 bg-gray-200 rounded w-full mb-2" />
            <div className="h-4 bg-gray-200 rounded w-2/3" />
          </div>
        ))}
      </div>
    );
  }

  if (!items?.length) {
    return (
      <div className="text-center py-8 bg-white rounded-lg border border-gray-200">
        <p className="text-gray-500">暂无相关内容</p>
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
      {items.map((item) => (
        <KnowledgeCard key={item.id} item={item} />
      ))}
    </div>
  );
}

export function KnowledgePage(): JSX.Element {
  const [selectedCategory, setSelectedCategory] = useState<KnowledgeCategoryType | ''>('');
  const [searchQuery, setSearchQuery] = useState('');

  const { data: items, isLoading } = useKnowledgeItems({
    category: selectedCategory || undefined,
    searchQuery: searchQuery || undefined,
  });

  return (
    <div className="container mx-auto px-4 py-6 max-w-6xl">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-gray-900 mb-2">法律知识库</h1>
        <p className="text-gray-600">专业、全面的法律知识，帮您解决各类法律问题</p>
      </div>

      {/* Search and Filter */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4 mb-6">
        <div className="flex flex-col md:flex-row gap-4">
          {/* Search Input */}
          <div className="flex-1">
            <input
              type="text"
              placeholder="搜索法律知识..."
              value={searchQuery}
              onChange={(e): void => setSearchQuery(e.target.value)}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
            />
          </div>
          
          {/* Category Filter */}
          <div className="flex gap-2 flex-wrap">
            {categories.map((cat) => (
              <button
                key={cat.value}
                onClick={(): void => setSelectedCategory(cat.value as KnowledgeCategoryType | '')}
                className={`px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                  selectedCategory === cat.value
                    ? 'bg-primary-600 text-white'
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }`}
                type="button"
              >
                {cat.label}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Stats */}
      <div className="flex items-center justify-between mb-4 text-sm text-gray-500">
        <span>
          {isLoading ? '加载中...' : `共 ${items?.length || 0} 条法律知识`}
        </span>
      </div>

      {/* Knowledge List */}
      <KnowledgeList items={items || []} isLoading={isLoading} />
    </div>
  );
}
