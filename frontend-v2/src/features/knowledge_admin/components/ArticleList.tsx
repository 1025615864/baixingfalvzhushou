/**
 * ArticleList 组件 - 知识库文章列表
 */

import { useState } from 'react';

import type {
  KnowledgeArticleListItem,
  KnowledgeType,
} from '../types';
import {
  KnowledgeTypeLabels,
} from '../types';

interface ArticleListProps {
  articles: KnowledgeArticleListItem[];
  total: number;
  page: number;
  pageSize: number;
  onPageChange: (page: number) => void;
  onEdit: (article: KnowledgeArticleListItem) => void;
  onDelete: (article: KnowledgeArticleListItem) => void;
  onView: (article: KnowledgeArticleListItem) => void;
  isLoading?: boolean;
  categories: string[];
  onCategoryChange?: (category: string | undefined) => void;
  selectedCategory?: string;
  onKeywordChange?: (keyword: string) => void;
  keyword?: string;
}

interface TypeBadgeProps {
  type: KnowledgeType;
}

function TypeBadge({ type }: TypeBadgeProps): JSX.Element {
  const colorMap: Record<KnowledgeType, string> = {
    law: 'bg-blue-100 text-blue-800',
    case: 'bg-green-100 text-green-800',
    regulation: 'bg-purple-100 text-purple-800',
    interpretation: 'bg-orange-100 text-orange-800',
  };

  return (
    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${colorMap[type]}`}>
      {KnowledgeTypeLabels[type]}
    </span>
  );
}

interface VectorizedBadgeProps {
  isVectorized: boolean;
}

function VectorizedBadge({ isVectorized }: VectorizedBadgeProps): JSX.Element {
  if (isVectorized) {
    return (
      <span className="inline-flex items-center px-2 py-0.5 rounded text-xs bg-green-50 text-green-700 border border-green-200">
        <svg className="w-3 h-3 mr-1" fill="currentColor" viewBox="0 0 20 20">
          <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
        </svg>
        已向量化
      </span>
    );
  }

  return (
    <span className="inline-flex items-center px-2 py-0.5 rounded text-xs bg-gray-100 text-gray-600 border border-gray-200">
      <svg className="w-3 h-3 mr-1" fill="currentColor" viewBox="0 0 20 20">
        <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm1-12a1 1 0 10-2 0v4a1 1 0 00.293.707l2.828 2.829a1 1 0 101.415-1.415L11 9.586V6z" clipRule="evenodd" />
      </svg>
      未向量化
    </span>
  );
}

export function ArticleList({
  articles,
  total,
  page,
  pageSize,
  onPageChange,
  onEdit,
  onDelete,
  onView,
  isLoading = false,
  categories,
  onCategoryChange,
  selectedCategory,
  onKeywordChange,
  keyword = '',
}: ArticleListProps): JSX.Element {
  const [localKeyword, setLocalKeyword] = useState(keyword);
  const totalPages = Math.ceil(total / pageSize);

  const handleSearch = (): void => {
    onKeywordChange?.(localKeyword);
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>): void => {
    if (e.key === 'Enter') {
      handleSearch();
    }
  };

  if (isLoading) {
    return (
      <div className="bg-white rounded-lg shadow">
        <div className="p-6 animate-pulse">
          <div className="h-8 bg-gray-200 rounded w-1/4 mb-4"></div>
          <div className="space-y-3">
            {[1, 2, 3, 4, 5].map((i) => (
              <div key={i} className="h-20 bg-gray-200 rounded"></div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow">
      {/* 头部和筛选器 */}
      <div className="p-6 border-b border-gray-200">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <h2 className="text-lg font-semibold text-gray-900">
            文章列表
            <span className="ml-2 text-sm font-normal text-gray-500">
              (共 {total} 篇)
            </span>
          </h2>
          
          {/* 搜索框 */}
          <div className="flex items-center space-x-2">
            <input
              type="text"
              value={localKeyword}
              onChange={(e) => setLocalKeyword(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="搜索标题、内容..."
              className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-sm w-64"
            />
            <button
              onClick={handleSearch}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 text-sm font-medium"
            >
              搜索
            </button>
          </div>
        </div>

        {/* 分类筛选 */}
        {categories.length > 0 && (
          <div className="mt-4 flex flex-wrap items-center gap-2">
            <span className="text-sm text-gray-500">分类筛选：</span>
            <button
              onClick={() => onCategoryChange?.(undefined)}
              className={`px-3 py-1 rounded-full text-sm ${
                !selectedCategory
                  ? 'bg-blue-100 text-blue-700'
                  : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
              }`}
            >
              全部
            </button>
            {categories.map((cat) => (
              <button
                key={cat}
                onClick={() => onCategoryChange?.(cat)}
                className={`px-3 py-1 rounded-full text-sm ${
                  selectedCategory === cat
                    ? 'bg-blue-100 text-blue-700'
                    : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                }`}
              >
                {cat}
              </button>
            ))}
          </div>
        )}
      </div>

      {/* 文章列表 */}
      <div className="divide-y divide-gray-200">
        {articles.length === 0 ? (
          <div className="p-12 text-center">
            <svg className="w-16 h-16 mx-auto text-gray-300 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
            <p className="text-gray-500 mb-2">暂无文章数据</p>
            <p className="text-sm text-gray-400">点击上方&ldquo;新建文章&rdquo;按钮创建第一篇知识文章</p>
          </div>
        ) : (
          articles.map((article) => (
            <div
              key={article.id}
              className="p-6 hover:bg-gray-50 transition-colors"
            >
              <div className="flex items-start justify-between">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-3 mb-2">
                    <TypeBadge type={article.knowledgeType} />
                    <VectorizedBadge isVectorized={article.isVectorized} />
                    <span className="text-sm text-gray-500">
                      {article.category}
                    </span>
                  </div>
                  
                  <h3 
                    className="text-base font-medium text-gray-900 mb-1 cursor-pointer hover:text-blue-600"
                    onClick={() => onView(article)}
                  >
                    {article.title}
                  </h3>
                  
                  {article.articleNumber && (
                    <p className="text-sm text-gray-500 mb-1">
                      编号: {article.articleNumber}
                    </p>
                  )}
                  
                  {article.summary && (
                    <p className="text-sm text-gray-600 line-clamp-2 mb-2">
                      {article.summary}
                    </p>
                  )}
                  
                  {article.keywords && (
                    <div className="flex flex-wrap gap-1 mt-2">
                      {article.keywords.split(',').map((keyword, idx) => (
                        <span
                          key={idx}
                          className="px-2 py-0.5 bg-gray-100 text-gray-600 text-xs rounded"
                        >
                          {keyword.trim()}
                        </span>
                      ))}
                    </div>
                  )}
                  
                  <p className="text-xs text-gray-400 mt-2">
                    创建时间: {new Date(article.createdAt).toLocaleString('zh-CN')}
                  </p>
                </div>
                
                <div className="flex items-center space-x-2 ml-4">
                  <button
                    onClick={() => onView(article)}
                    className="p-2 text-gray-400 hover:text-blue-600 hover:bg-blue-50 rounded-lg transition-colors"
                    title="查看详情"
                  >
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                    </svg>
                  </button>
                  <button
                    onClick={() => onEdit(article)}
                    className="p-2 text-gray-400 hover:text-green-600 hover:bg-green-50 rounded-lg transition-colors"
                    title="编辑"
                  >
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                    </svg>
                  </button>
                  <button
                    onClick={() => onDelete(article)}
                    className="p-2 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors"
                    title="删除"
                  >
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                    </svg>
                  </button>
                </div>
              </div>
            </div>
          ))
        )}
      </div>

      {/* 分页 */}
      {totalPages > 1 && (
        <div className="p-4 border-t border-gray-200 flex items-center justify-between">
          <p className="text-sm text-gray-500">
            显示第 {(page - 1) * pageSize + 1} - {Math.min(page * pageSize, total)} 条，共 {total} 条
          </p>
          <div className="flex items-center space-x-2">
            <button
              onClick={() => onPageChange(page - 1)}
              disabled={page <= 1}
              className="px-3 py-1 border border-gray-300 rounded-md text-sm disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50"
            >
              上一页
            </button>
            <span className="text-sm text-gray-600">
              第 {page} / {totalPages} 页
            </span>
            <button
              onClick={() => onPageChange(page + 1)}
              disabled={page >= totalPages}
              className="px-3 py-1 border border-gray-300 rounded-md text-sm disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50"
            >
              下一页
            </button>
          </div>
        </div>
      )}
    </div>
  );
}