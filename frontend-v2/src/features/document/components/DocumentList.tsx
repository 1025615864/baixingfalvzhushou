/**
 * 文档列表组件
 * 展示文档列表，支持分页和筛选
 */

import React from 'react';

import type { DocumentItem } from '../types';

import { DocumentCard } from './DocumentCard';

export interface DocumentListProps {
  /** 文档列表 */
  documents: DocumentItem[];
  /** 是否加载中 */
  isLoading?: boolean;
  /** 当前页 */
  currentPage?: number;
  /** 每页数量 */
  pageSize?: number;
  /** 总数 */
  total?: number;
  /** 点击文档回调 */
  onDocumentClick?: (doc: DocumentItem) => void;
  /** 编辑文档回调 */
  onDocumentEdit?: (doc: DocumentItem) => void;
  /** 删除文档回调 */
  onDocumentDelete?: (doc: DocumentItem) => void;
  /** 导出文档回调 */
  onDocumentExport?: (doc: DocumentItem) => void;
  /** 页码变化回调 */
  onPageChange?: (page: number) => void;
  /** 空状态文本 */
  emptyText?: string;
  /** 选中的文档类型筛选 */
  _selectedType?: string | null;
  /** 类型筛选变化回调 */
  _onTypeChange?: (type: string | null) => void;
  /** 搜索关键词 */
  searchKeyword?: string;
  /** 搜索回调 */
  onSearch?: (keyword: string) => void;
}

/**
 * 文档列表组件
 */
export function DocumentList({
  documents,
  isLoading = false,
  currentPage = 1,
  pageSize = 10,
  total = 0,
  onDocumentClick,
  onDocumentEdit,
  onDocumentDelete,
  onDocumentExport,
  onPageChange,
  emptyText = '暂无文档',
  _selectedType,
  _onTypeChange,
  searchKeyword = '',
  onSearch,
}: DocumentListProps): React.ReactElement {
  const totalPages = Math.ceil(total / pageSize);

  // 渲染分页按钮
  const renderPagination = () => {
    if (totalPages <= 1) return null;

    const pages: number[] = [];
    const maxVisiblePages = 5;
    
    let startPage = Math.max(1, currentPage - Math.floor(maxVisiblePages / 2));
    const endPage = Math.min(totalPages, startPage + maxVisiblePages - 1);
    
    if (endPage - startPage < maxVisiblePages - 1) {
      startPage = Math.max(1, endPage - maxVisiblePages + 1);
    }

    for (let i = startPage; i <= endPage; i++) {
      pages.push(i);
    }

    return (
      <div className="flex items-center justify-center gap-2 mt-6">
        <button
          onClick={() => onPageChange?.(currentPage - 1)}
          disabled={currentPage === 1}
          className="px-3 py-1.5 text-sm rounded-lg border border-gray-300 disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50 transition-colors"
        >
          上一页
        </button>
        
        {startPage > 1 && (
          <>
            <button
              onClick={() => onPageChange?.(1)}
              className="px-3 py-1.5 text-sm rounded-lg border border-gray-300 hover:bg-gray-50 transition-colors"
            >
              1
            </button>
            {startPage > 2 && <span className="px-2 text-gray-500">...</span>}
          </>
        )}
        
        {pages.map(page => (
          <button
            key={page}
            onClick={() => onPageChange?.(page)}
            className={`
              px-3 py-1.5 text-sm rounded-lg transition-colors
              ${currentPage === page 
                ? 'bg-blue-600 text-white border border-blue-600' 
                : 'border border-gray-300 hover:bg-gray-50'}
            `}
          >
            {page}
          </button>
        ))}
        
        {endPage < totalPages && (
          <>
            {endPage < totalPages - 1 && <span className="px-2 text-gray-500">...</span>}
            <button
              onClick={() => onPageChange?.(totalPages)}
              className="px-3 py-1.5 text-sm rounded-lg border border-gray-300 hover:bg-gray-50 transition-colors"
            >
              {totalPages}
            </button>
          </>
        )}
        
        <button
          onClick={() => onPageChange?.(currentPage + 1)}
          disabled={currentPage === totalPages}
          className="px-3 py-1.5 text-sm rounded-lg border border-gray-300 disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50 transition-colors"
        >
          下一页
        </button>
      </div>
    );
  };

  // 渲染加载骨架屏
  const renderSkeleton = () => (
    <div className="space-y-4">
      {Array.from({ length: pageSize }).map((_, index) => (
        <div key={index} className="bg-white rounded-xl border border-gray-200 p-4 animate-pulse">
          <div className="flex items-start gap-4">
            <div className="w-10 h-10 bg-gray-200 rounded-lg" />
            <div className="flex-1 space-y-2">
              <div className="flex items-center justify-between">
                <div className="h-4 bg-gray-200 rounded w-1/3" />
                <div className="h-4 bg-gray-200 rounded w-16" />
              </div>
              <div className="h-3 bg-gray-200 rounded w-1/4" />
            </div>
          </div>
        </div>
      ))}
    </div>
  );

  // 渲染空状态
  const renderEmpty = () => (
    <div className="flex flex-col items-center justify-center py-16 text-center">
      <div className="w-20 h-20 bg-gray-100 rounded-full flex items-center justify-center mb-4">
        <svg className="w-10 h-10 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
        </svg>
      </div>
      <h3 className="text-lg font-medium text-gray-900 mb-1">{emptyText}</h3>
      <p className="text-sm text-gray-500">您可以创建新文档或生成法律文书</p>
    </div>
  );

  return (
    <div className="space-y-4">
      {/* 搜索栏 */}
      {onSearch && (
        <div className="flex items-center gap-4 bg-white p-4 rounded-xl border border-gray-200">
          <div className="flex-1 relative">
            <input
              type="text"
              placeholder="搜索文档标题..."
              value={searchKeyword}
              onChange={(e) => onSearch(e.target.value)}
              className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none"
            />
            <svg className="w-5 h-5 text-gray-400 absolute left-3 top-1/2 -translate-y-1/2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
          </div>
        </div>
      )}

      {/* 统计信息 */}
      {!isLoading && documents.length > 0 && (
        <div className="flex items-center justify-between text-sm text-gray-500 px-1">
          <span>共 {total} 个文档</span>
          <span>第 {currentPage}/{totalPages || 1} 页</span>
        </div>
      )}

      {/* 文档列表 */}
      {isLoading ? (
        renderSkeleton()
      ) : documents.length === 0 ? (
        renderEmpty()
      ) : (
        <div className="grid grid-cols-1 gap-4">
          {documents.map((doc) => (
            <DocumentCard
              key={doc.id}
              document={doc}
              onClick={onDocumentClick}
              onEdit={onDocumentEdit}
              onDelete={onDocumentDelete}
              onExport={onDocumentExport}
            />
          ))}
        </div>
      )}

      {/* 分页 */}
      {!isLoading && documents.length > 0 && renderPagination()}
    </div>
  );
}
