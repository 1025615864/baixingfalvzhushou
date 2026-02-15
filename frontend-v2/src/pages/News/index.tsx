import { useState } from 'react';

import { NewsList, useNews } from '@/features/news';
import type { NewsCategoryType } from '@/features/news';

const categories: { value: NewsCategoryType | ''; label: string }[] = [
  { value: '', label: '全部' },
  { value: 'legal', label: '法律新闻' },
  { value: 'case', label: '典型案例' },
  { value: 'policy', label: '政策法规' },
  { value: 'industry', label: '行业动态' },
];

export function NewsPage(): JSX.Element {
  const [selectedCategory, setSelectedCategory] = useState<NewsCategoryType | ''>('');
  const [searchQuery, setSearchQuery] = useState('');

  const { data: news, isLoading } = useNews({
    category: selectedCategory || undefined,
    searchQuery: searchQuery || undefined,
  });

  return (
    <div className="container mx-auto px-4 py-6 max-w-6xl">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-gray-900 mb-2">法律资讯</h1>
        <p className="text-gray-600">最新法律动态、典型案例和政策法规解读</p>
      </div>

      {/* Featured News */}
      <section className="mb-8">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">精选推荐</h2>
        <NewsList featuredOnly />
      </section>

      {/* Filters */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4 mb-6">
        <div className="flex flex-col gap-4">
          {/* Search */}
          <input
            type="text"
            placeholder="搜索资讯..."
            value={searchQuery}
            onChange={(e): void => setSearchQuery(e.target.value)}
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
          />
          
          {/* Category Filter */}
          <div className="flex gap-2 flex-wrap">
            {categories.map((cat) => (
              <button
                key={cat.value}
                onClick={(): void => setSelectedCategory(cat.value as NewsCategoryType | '')}
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

      {/* All News */}
      <section>
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold text-gray-900">最新资讯</h2>
          <span className="text-sm text-gray-500">
            {isLoading ? '加载中...' : `共 ${news?.length || 0} 条`}
          </span>
        </div>
        <NewsList />
      </section>
    </div>
  );
}