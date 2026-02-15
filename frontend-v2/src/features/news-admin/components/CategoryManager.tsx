/**
 * CategoryManager - 分类管理组件
 */

import { useState } from 'react';

import type { CategoryCount, NewsStats } from '../types';

interface CategoryManagerProps {
  categories: CategoryCount[];
  stats: NewsStats | null;
  isLoading: boolean;
  onRefresh: () => void;
}

/**
 * 分类管理组件
 */
export function CategoryManager({
  categories,
  stats,
  isLoading,
  onRefresh,
}: CategoryManagerProps): JSX.Element {
  const [selectedCategory, setSelectedCategory] = useState<string | null>(null);

  // 分类颜色映射
  const categoryColors: Record<string, string> = {
    general: 'bg-blue-500',
    legal: 'bg-purple-500',
    politics: 'bg-red-500',
    economy: 'bg-green-500',
    society: 'bg-yellow-500',
    technology: 'bg-indigo-500',
    other: 'bg-gray-500',
  };

  // 分类标签映射
  const categoryLabels: Record<string, string> = {
    general: '综合',
    legal: '法律',
    politics: '时政',
    economy: '经济',
    society: '社会',
    technology: '科技',
    other: '其他',
  };

  // 获取分类颜色
  const getCategoryColor = (category: string): string => {
    return categoryColors[category] || 'bg-gray-500';
  };

  // 获取分类标签
  const getCategoryLabel = (category: string): string => {
    return categoryLabels[category] || category;
  };

  // 计算百分比
  const calculatePercentage = (count: number): number => {
    if (!stats || stats.totalArticles === 0) return 0;
    return Math.round((count / stats.totalArticles) * 100);
  };

  // 总文章数（分类统计中）
  const totalCategorizedArticles = categories.reduce((sum, cat) => sum + cat.count, 0);

  return (
    <div className="bg-white rounded-lg shadow">
      {/* 头部 */}
      <div className="px-6 py-4 border-b border-gray-200 flex items-center justify-between">
        <div>
          <h2 className="text-lg font-semibold text-gray-900">分类管理</h2>
          <p className="text-sm text-gray-500 mt-1">
            共 {categories.length} 个分类，{totalCategorizedArticles} 篇文章
          </p>
        </div>
        <button
          onClick={onRefresh}
          disabled={isLoading}
          className="p-2 text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-lg disabled:opacity-50"
          title="刷新数据"
        >
          <svg
            className={`w-5 h-5 ${isLoading ? 'animate-spin' : ''}`}
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
            />
          </svg>
        </button>
      </div>

      {/* 统计概览 */}
      {stats && (
        <div className="px-6 py-4 bg-gray-50 grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="bg-white p-4 rounded-lg shadow-sm">
            <p className="text-sm text-gray-500">总文章数</p>
            <p className="text-2xl font-bold text-gray-900">{stats.totalArticles}</p>
          </div>
          <div className="bg-white p-4 rounded-lg shadow-sm">
            <p className="text-sm text-gray-500">已发布</p>
            <p className="text-2xl font-bold text-green-600">{stats.publishedArticles}</p>
          </div>
          <div className="bg-white p-4 rounded-lg shadow-sm">
            <p className="text-sm text-gray-500">待审核</p>
            <p className="text-2xl font-bold text-yellow-600">{stats.pendingReview}</p>
          </div>
          <div className="bg-white p-4 rounded-lg shadow-sm">
            <p className="text-sm text-gray-500">置顶文章</p>
            <p className="text-2xl font-bold text-purple-600">{stats.topArticles}</p>
          </div>
        </div>
      )}

      {/* 分类列表 */}
      <div className="p-6">
        {isLoading ? (
          <div className="flex items-center justify-center h-32">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
          </div>
        ) : categories.length === 0 ? (
          <div className="text-center py-8 text-gray-500">
            <svg
              className="w-12 h-12 mx-auto text-gray-300 mb-3"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A1.994 1.994 0 013 12V7a4 4 0 014-4z"
              />
            </svg>
            <p>暂无分类数据</p>
          </div>
        ) : (
          <div className="space-y-3">
            {categories.map((category) => {
              const percentage = calculatePercentage(category.count);
              const isSelected = selectedCategory === category.category;

              return (
                <div
                  key={category.category}
                  onClick={() => setSelectedCategory(isSelected ? null : category.category)}
                  className={`p-4 rounded-lg border-2 cursor-pointer transition-all ${
                    isSelected
                      ? 'border-blue-500 bg-blue-50'
                      : 'border-gray-200 hover:border-gray-300 hover:bg-gray-50'
                  }`}
                >
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center gap-3">
                      <div
                        className={`w-3 h-3 rounded-full ${getCategoryColor(category.category)}`}
                      ></div>
                      <span className="font-medium text-gray-900">
                        {getCategoryLabel(category.category)}
                      </span>
                      <span className="text-xs text-gray-500 uppercase bg-gray-100 px-2 py-0.5 rounded">
                        {category.category}
                      </span>
                    </div>
                    <div className="flex items-center gap-4">
                      <span className="text-2xl font-bold text-gray-900">
                        {category.count}
                      </span>
                      <span className="text-sm text-gray-500">{percentage}%</span>
                    </div>
                  </div>

                  {/* 进度条 */}
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div
                      className={`h-2 rounded-full transition-all duration-500 ${getCategoryColor(
                        category.category
                      )}`}
                      style={{ width: `${percentage}%` }}
                    ></div>
                  </div>

                  {/* 选中时显示详细信息 */}
                  {isSelected && (
                    <div className="mt-3 pt-3 border-t border-gray-200 text-sm text-gray-600">
                      <p>该分类下共有 {category.count} 篇文章</p>
                      <p className="mt-1">占总文章数的 {percentage}%</p>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* 底部提示 */}
      <div className="px-6 py-3 bg-gray-50 border-t border-gray-200 text-xs text-gray-500">
        <p>提示：点击分类可查看详细信息。分类数据每 5 分钟自动更新一次。</p>
      </div>
    </div>
  );
}