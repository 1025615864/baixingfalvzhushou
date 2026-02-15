/**
 * ArticleList - 新闻文章列表组件
 */

import { useState } from 'react';

import type { NewsAdminListItem } from '../types';

interface ArticleListProps {
  articles: NewsAdminListItem[];
  total: number;
  page: number;
  pageSize: number;
  isLoading: boolean;
  onPageChange: (page: number) => void;
  onEdit: (article: NewsAdminListItem) => void;
  onDelete: (article: NewsAdminListItem) => void;
  onReview: (article: NewsAdminListItem) => void;
  onPublish: (article: NewsAdminListItem) => void;
  onTop: (article: NewsAdminListItem) => void;
}

/**
 * 状态标签组件
 */
function StatusBadge({ status, label }: { status: string; label: string }): JSX.Element {
  const statusStyles: Record<string, string> = {
    pending: 'bg-yellow-100 text-yellow-800',
    approved: 'bg-green-100 text-green-800',
    rejected: 'bg-red-100 text-red-800',
    published: 'bg-blue-100 text-blue-800',
    unpublished: 'bg-gray-100 text-gray-800',
    top: 'bg-purple-100 text-purple-800',
  };

  return (
    <span className={`px-2 py-1 rounded-full text-xs font-medium ${statusStyles[status] || 'bg-gray-100 text-gray-800'}`}>
      {label}
    </span>
  );
}

/**
 * 文章列表组件
 */
export function ArticleList({
  articles,
  total,
  page,
  pageSize,
  isLoading,
  onPageChange,
  onEdit,
  onDelete,
  onReview,
  onPublish,
  onTop,
}: ArticleListProps): JSX.Element {
  const [selectedIds, setSelectedIds] = useState<Set<number>>(new Set());
  const totalPages = Math.ceil(total / pageSize);

  const handleSelectAll = (checked: boolean): void => {
    if (checked) {
      setSelectedIds(new Set(articles.map((a) => a.id)));
    } else {
      setSelectedIds(new Set());
    }
  };

  const handleSelectOne = (id: number, checked: boolean): void => {
    const newSelected = new Set(selectedIds);
    if (checked) {
      newSelected.add(id);
    } else {
      newSelected.delete(id);
    }
    setSelectedIds(newSelected);
  };

  const formatDate = (dateStr: string | null): string => {
    if (!dateStr) return '-';
    return new Date(dateStr).toLocaleString('zh-CN');
  };

  const getReviewStatusLabel = (status: string | null): string => {
    const labels: Record<string, string> = {
      pending: '待审核',
      approved: '已通过',
      rejected: '已拒绝',
    };
    return status ? labels[status] || status : '未设置';
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow">
      {/* 批量操作栏 */}
      {selectedIds.size > 0 && (
        <div className="px-4 py-3 bg-blue-50 border-b border-blue-100 flex items-center gap-4">
          <span className="text-sm text-blue-700">
            已选择 {selectedIds.size} 项
          </span>
          <div className="flex gap-2">
            <button
              onClick={() => onReview({ id: Array.from(selectedIds)[0] } as NewsAdminListItem)}
              className="px-3 py-1 text-xs bg-white text-blue-600 border border-blue-200 rounded hover:bg-blue-50"
            >
              批量审核
            </button>
            <button
              onClick={() => onDelete({ id: Array.from(selectedIds)[0] } as NewsAdminListItem)}
              className="px-3 py-1 text-xs bg-white text-red-600 border border-red-200 rounded hover:bg-red-50"
            >
              批量删除
            </button>
          </div>
        </div>
      )}

      {/* 表格 */}
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead className="bg-gray-50 border-b border-gray-200">
            <tr>
              <th className="px-4 py-3 text-left">
                <input
                  type="checkbox"
                  checked={articles.length > 0 && selectedIds.size === articles.length}
                  onChange={(e) => handleSelectAll(e.target.checked)}
                  className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                />
              </th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">文章</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">分类</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">状态</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">浏览</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">发布时间</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">操作</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-200">
            {articles.map((article) => (
              <tr key={article.id} className="hover:bg-gray-50">
                <td className="px-4 py-3">
                  <input
                    type="checkbox"
                    checked={selectedIds.has(article.id)}
                    onChange={(e) => handleSelectOne(article.id, e.target.checked)}
                    className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                  />
                </td>
                <td className="px-4 py-3">
                  <div className="flex items-center gap-3">
                    {article.coverImage && (
                      <img
                        src={article.coverImage}
                        alt={article.title}
                        className="w-12 h-12 object-cover rounded"
                      />
                    )}
                    <div>
                      <p className="font-medium text-gray-900 line-clamp-1">{article.title}</p>
                      <p className="text-xs text-gray-500">{article.source || '未知来源'}</p>
                      {article.isTop && (
                        <span className="inline-block mt-1 px-1.5 py-0.5 text-xs bg-purple-100 text-purple-700 rounded">
                          置顶
                        </span>
                      )}
                    </div>
                  </div>
                </td>
                <td className="px-4 py-3">
                  <span className="px-2 py-1 text-xs bg-gray-100 text-gray-700 rounded">
                    {article.category}
                  </span>
                </td>
                <td className="px-4 py-3">
                  <div className="flex flex-col gap-1">
                    <StatusBadge
                      status={article.isPublished ? 'published' : 'unpublished'}
                      label={article.isPublished ? '已发布' : '未发布'}
                    />
                    <StatusBadge
                      status={article.reviewStatus || 'pending'}
                      label={getReviewStatusLabel(article.reviewStatus)}
                    />
                  </div>
                </td>
                <td className="px-4 py-3 text-sm text-gray-600">
                  {article.viewCount}
                </td>
                <td className="px-4 py-3 text-sm text-gray-600">
                  {formatDate(article.publishedAt)}
                </td>
                <td className="px-4 py-3">
                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => onEdit(article)}
                      className="p-1 text-blue-600 hover:bg-blue-50 rounded"
                      title="编辑"
                    >
                      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                      </svg>
                    </button>
                    <button
                      onClick={() => onReview(article)}
                      className="p-1 text-yellow-600 hover:bg-yellow-50 rounded"
                      title="审核"
                    >
                      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                      </svg>
                    </button>
                    <button
                      onClick={() => onPublish(article)}
                      className={`p-1 rounded ${article.isPublished ? 'text-gray-600 hover:bg-gray-100' : 'text-green-600 hover:bg-green-50'}`}
                      title={article.isPublished ? '下架' : '发布'}
                    >
                      {article.isPublished ? (
                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 9v6m4-6v6m7-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                        </svg>
                      ) : (
                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z" />
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                        </svg>
                      )}
                    </button>
                    <button
                      onClick={() => onTop(article)}
                      className={`p-1 rounded ${article.isTop ? 'text-purple-600 bg-purple-50' : 'text-gray-600 hover:bg-gray-100'}`}
                      title={article.isTop ? '取消置顶' : '置顶'}
                    >
                      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 15l7-7 7 7" />
                      </svg>
                    </button>
                    <button
                      onClick={() => onDelete(article)}
                      className="p-1 text-red-600 hover:bg-red-50 rounded"
                      title="删除"
                    >
                      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                      </svg>
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* 分页 */}
      {totalPages > 1 && (
        <div className="px-4 py-3 border-t border-gray-200 flex items-center justify-between">
          <div className="text-sm text-gray-500">
            共 {total} 条，第 {page} / {totalPages} 页
          </div>
          <div className="flex gap-1">
            <button
              onClick={() => onPageChange(page - 1)}
              disabled={page <= 1}
              className="px-3 py-1 text-sm border border-gray-300 rounded hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              上一页
            </button>
            {Array.from({ length: Math.min(5, totalPages) }, (_, i) => {
              const pageNum = i + 1;
              return (
                <button
                  key={pageNum}
                  onClick={() => onPageChange(pageNum)}
                  className={`px-3 py-1 text-sm border rounded ${
                    page === pageNum
                      ? 'bg-blue-600 text-white border-blue-600'
                      : 'border-gray-300 hover:bg-gray-50'
                  }`}
                >
                  {pageNum}
                </button>
              );
            })}
            <button
              onClick={() => onPageChange(page + 1)}
              disabled={page >= totalPages}
              className="px-3 py-1 text-sm border border-gray-300 rounded hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              下一页
            </button>
          </div>
        </div>
      )}
    </div>
  );
}