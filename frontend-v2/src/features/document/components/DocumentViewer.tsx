/**
 * 文档查看器组件
 * 用于查看文档详情内容
 */

import React from 'react';

import type { DocumentDetail } from '../types';
import { getDocumentTypeLabel, getDocumentTypeClass } from '../types';

export interface DocumentViewerProps {
  /** 文档数据 */
  document: DocumentDetail | null;
  /** 加载状态 */
  isLoading?: boolean;
  /** 关闭回调 */
  onClose?: () => void;
  /** 编辑回调 */
  onEdit?: () => void;
  /** 导出回调 */
  onExport?: () => void;
  /** 删除回调 */
  onDelete?: () => void;
  /** 额外样式类 */
  className?: string;
}

/**
 * 文档查看器组件
 */
export function DocumentViewer({
  document,
  isLoading = false,
  onClose,
  onEdit,
  onExport,
  onDelete,
  className = '',
}: DocumentViewerProps): React.ReactElement {
  // 格式化日期
  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr);
    return date.toLocaleString('zh-CN', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  // 渲染加载状态
  if (isLoading) {
    return (
      <div className={`bg-white rounded-xl border border-gray-200 p-6 ${className}`}>
        <div className="animate-pulse space-y-4">
          <div className="h-8 bg-gray-200 rounded w-3/4" />
          <div className="h-4 bg-gray-200 rounded w-1/4" />
          <div className="h-64 bg-gray-200 rounded" />
        </div>
      </div>
    );
  }

  // 渲染空状态
  if (!document) {
    return (
      <div className={`bg-white rounded-xl border border-gray-200 p-8 ${className}`}>
        <div className="text-center text-gray-500">
          <svg className="w-16 h-16 mx-auto mb-4 text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
          <p>选择文档查看详情</p>
        </div>
      </div>
    );
  }

  return (
    <div className={`bg-white rounded-xl border border-gray-200 overflow-hidden ${className}`}>
      {/* 头部：标题和操作按钮 */}
      <div className="px-6 py-4 border-b border-gray-200 bg-gray-50">
        <div className="flex items-start justify-between gap-4">
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 mb-2">
              <span
                className={`
                  inline-flex items-center px-2 py-0.5 rounded text-xs font-medium
                  ${getDocumentTypeClass(document.documentType)}
                `}
              >
                {getDocumentTypeLabel(document.documentType)}
              </span>
              {document.version > 1 && (
                <span className="text-xs text-gray-500">
                  版本 {document.version}
                </span>
              )}
            </div>
            <h2 className="text-xl font-semibold text-gray-900 break-words">
              {document.title}
            </h2>
          </div>

          {/* 操作按钮组 */}
          <div className="flex items-center gap-2">
            {onExport && (
              <button
                onClick={onExport}
                className="p-2 text-gray-600 hover:text-blue-600 hover:bg-blue-50 rounded-lg transition-colors"
                title="导出PDF"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                </svg>
              </button>
            )}
            {onEdit && (
              <button
                onClick={onEdit}
                className="p-2 text-gray-600 hover:text-indigo-600 hover:bg-indigo-50 rounded-lg transition-colors"
                title="编辑"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                </svg>
              </button>
            )}
            {onDelete && (
              <button
                onClick={onDelete}
                className="p-2 text-gray-600 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors"
                title="删除"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                </svg>
              </button>
            )}
            {onClose && (
              <button
                onClick={onClose}
                className="p-2 text-gray-600 hover:text-gray-900 hover:bg-gray-200 rounded-lg transition-colors"
                title="关闭"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            )}
          </div>
        </div>

        {/* 元信息 */}
        <div className="flex items-center gap-4 mt-3 text-sm text-gray-500">
          <span className="flex items-center gap-1">
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
            </svg>
            创建于 {formatDate(document.createdAt)}
          </span>
          <span className="flex items-center gap-1">
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            更新于 {formatDate(document.updatedAt)}
          </span>
        </div>
      </div>

      {/* 文档内容 */}
      <div className="p-6">
        <div className="prose prose-blue max-w-none">
          <div className="whitespace-pre-wrap text-gray-800 leading-relaxed font-mono text-sm bg-gray-50 p-4 rounded-lg border border-gray-200">
            {document.content}
          </div>
        </div>

        {/* 额外信息（如果有） */}
        {document.payloadJson && (
          <div className="mt-6 pt-6 border-t border-gray-200">
            <h3 className="text-sm font-medium text-gray-700 mb-2">附加信息</h3>
            <pre className="text-xs text-gray-600 bg-gray-100 p-3 rounded-lg overflow-x-auto">
              {JSON.stringify(JSON.parse(document.payloadJson), null, 2)}
            </pre>
          </div>
        )}
      </div>
    </div>
  );
}