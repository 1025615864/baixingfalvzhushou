/**
 * 文档卡片组件
 * 展示单个文档的简要信息
 */

import React from 'react';

import type { DocumentItem, DocumentType } from '../types';
import { getDocumentTypeLabel, getDocumentTypeClass } from '../types';

export interface DocumentCardProps {
  /** 文档数据 */
  document: DocumentItem;
  /** 点击卡片回调 */
  onClick?: (doc: DocumentItem) => void;
  /** 点击编辑按钮回调 */
  onEdit?: (doc: DocumentItem) => void;
  /** 点击删除按钮回调 */
  onDelete?: (doc: DocumentItem) => void;
  /** 点击导出按钮回调 */
  onExport?: (doc: DocumentItem) => void;
  /** 是否显示操作按钮 */
  showActions?: boolean;
  /** 额外样式类 */
  className?: string;
}

/**
 * 文档卡片组件
 */
export function DocumentCard({
  document,
  onClick,
  onEdit,
  onDelete,
  onExport,
  showActions = true,
  className = '',
}: DocumentCardProps): React.ReactElement {
  const handleClick = () => {
    onClick?.(document);
  };

  const handleEdit = (e: React.MouseEvent) => {
    e.stopPropagation();
    onEdit?.(document);
  };

  const handleDelete = (e: React.MouseEvent) => {
    e.stopPropagation();
    onDelete?.(document);
  };

  const handleExport = (e: React.MouseEvent) => {
    e.stopPropagation();
    onExport?.(document);
  };

  // 格式化日期
  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr);
    return date.toLocaleDateString('zh-CN', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    });
  };

  // 获取文档类型图标
  const getDocumentIcon = (type: DocumentType) => {
    const iconClass = 'w-10 h-10 rounded-lg flex items-center justify-center text-lg font-bold';
    const colors: Record<DocumentType, string> = {
      contract: 'bg-blue-100 text-blue-600',
      agreement: 'bg-green-100 text-green-600',
      memo: 'bg-yellow-100 text-yellow-600',
      letter: 'bg-purple-100 text-purple-600',
      complaint: 'bg-red-100 text-red-600',
      defense: 'bg-orange-100 text-orange-600',
      appeal: 'bg-pink-100 text-pink-600',
      application: 'bg-cyan-100 text-cyan-600',
      other: 'bg-gray-100 text-gray-600',
    };

    const firstLetter = getDocumentTypeLabel(type).charAt(0);

    return (
      <div className={`${iconClass} ${colors[type] || colors.other}`}>
        {firstLetter}
      </div>
    );
  };

  return (
    <div
      onClick={handleClick}
      className={`
        group bg-white rounded-xl border border-gray-200 p-4
        hover:shadow-md hover:border-blue-300
        transition-all duration-200 cursor-pointer
        ${className}
      `}
    >
      <div className="flex items-start gap-4">
        {/* 文档类型图标 */}
        {getDocumentIcon(document.documentType)}

        {/* 文档信息 */}
        <div className="flex-1 min-w-0">
          <div className="flex items-start justify-between gap-2">
            <h3 className="font-medium text-gray-900 truncate pr-2" title={document.title}>
              {document.title}
            </h3>
            <span
              className={`
                inline-flex items-center px-2 py-0.5 rounded text-xs font-medium whitespace-nowrap
                ${getDocumentTypeClass(document.documentType)}
              `}
            >
              {getDocumentTypeLabel(document.documentType)}
            </span>
          </div>
          <p className="text-sm text-gray-500 mt-1">
            创建于 {formatDate(document.createdAt)}
          </p>
        </div>
      </div>

      {/* 操作按钮 */}
      {showActions && (
        <div className="flex items-center justify-end gap-2 mt-4 pt-3 border-t border-gray-100 opacity-0 group-hover:opacity-100 transition-opacity">
          <button
            onClick={handleExport}
            className="p-1.5 text-gray-500 hover:text-blue-600 hover:bg-blue-50 rounded transition-colors"
            title="导出"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
            </svg>
          </button>
          <button
            onClick={handleEdit}
            className="p-1.5 text-gray-500 hover:text-indigo-600 hover:bg-indigo-50 rounded transition-colors"
            title="编辑"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
            </svg>
          </button>
          <button
            onClick={handleDelete}
            className="p-1.5 text-gray-500 hover:text-red-600 hover:bg-red-50 rounded transition-colors"
            title="删除"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
            </svg>
          </button>
        </div>
      )}
    </div>
  );
}
