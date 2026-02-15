/**
 * 文档操作组件
 * 提供文档的编辑、删除、导出等操作按钮组
 */

import React, { useState } from 'react';

import type { DocumentItem } from '../types';

export interface DocumentActionsProps {
  /** 文档数据 */
  document: DocumentItem;
  /** 编辑回调 */
  onEdit?: (doc: DocumentItem) => void;
  /** 删除回调 */
  onDelete?: (doc: DocumentItem) => void;
  /** 导出回调 */
  onExport?: (doc: DocumentItem) => void;
  /** 查看回调 */
  onView?: (doc: DocumentItem) => void;
  /** 按钮尺寸 */
  size?: 'sm' | 'md' | 'lg';
  /** 布局方向 */
  direction?: 'horizontal' | 'vertical';
  /** 是否显示标签 */
  showLabels?: boolean;
  /** 额外样式类 */
  className?: string;
}

/**
 * 文档操作组件
 */
export function DocumentActions({
  document,
  onEdit,
  onDelete,
  onExport,
  onView,
  size = 'md',
  direction = 'horizontal',
  showLabels = false,
  className = '',
}: DocumentActionsProps): React.ReactElement {
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);

  // 尺寸配置
  const sizeConfig = {
    sm: { button: 'p-1.5', icon: 'w-4 h-4', text: 'text-xs' },
    md: { button: 'p-2', icon: 'w-5 h-5', text: 'text-sm' },
    lg: { button: 'p-2.5', icon: 'w-6 h-6', text: 'text-base' },
  };

  // 布局配置
  const layoutConfig = {
    horizontal: 'flex items-center gap-1',
    vertical: 'flex flex-col gap-2',
  };

  const { button, icon, text } = sizeConfig[size];

  // 处理查看
  const handleView = () => {
    onView?.(document);
  };

  // 处理编辑
  const handleEdit = () => {
    onEdit?.(document);
  };

  // 处理导出
  const handleExport = () => {
    onExport?.(document);
  };

  // 处理删除确认
  const handleDeleteClick = () => {
    setShowDeleteConfirm(true);
  };

  // 确认删除
  const handleConfirmDelete = () => {
    onDelete?.(document);
    setShowDeleteConfirm(false);
  };

  // 取消删除
  const handleCancelDelete = () => {
    setShowDeleteConfirm(false);
  };

  // 渲染按钮
  const renderButton = (
    action: () => void,
    iconSvg: React.ReactNode,
    label: string,
    colorClass: string = 'text-gray-600 hover:text-gray-900 hover:bg-gray-100'
  ) => (
    <button
      onClick={action}
      className={`
        ${button} rounded-lg transition-colors flex items-center gap-1.5
        ${colorClass}
      `}
      title={label}
    >
      {iconSvg}
      {showLabels && <span className={text}>{label}</span>}
    </button>
  );

  return (
    <div className={`${layoutConfig[direction]} ${className}`}>
      {/* 查看按钮 */}
      {onView && renderButton(
        handleView,
        <svg className={icon} fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
        </svg>,
        '查看',
        'text-gray-600 hover:text-blue-600 hover:bg-blue-50'
      )}

      {/* 编辑按钮 */}
      {onEdit && renderButton(
        handleEdit,
        <svg className={icon} fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
        </svg>,
        '编辑',
        'text-gray-600 hover:text-indigo-600 hover:bg-indigo-50'
      )}

      {/* 导出按钮 */}
      {onExport && renderButton(
        handleExport,
        <svg className={icon} fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
        </svg>,
        '导出',
        'text-gray-600 hover:text-green-600 hover:bg-green-50'
      )}

      {/* 删除按钮 */}
      {onDelete && !showDeleteConfirm && renderButton(
        handleDeleteClick,
        <svg className={icon} fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
        </svg>,
        '删除',
        'text-gray-600 hover:text-red-600 hover:bg-red-50'
      )}

      {/* 删除确认 */}
      {showDeleteConfirm && (
        <div className={`flex items-center gap-2 ${direction === 'vertical' ? 'flex-col' : ''}`}>
          <span className="text-xs text-red-600 whitespace-nowrap">确认删除?</span>
          <div className="flex items-center gap-1">
            <button
              onClick={handleConfirmDelete}
              className={`${button} rounded-lg bg-red-600 text-white hover:bg-red-700 transition-colors`}
              title="确认"
            >
              <svg className={icon} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
              </svg>
            </button>
            <button
              onClick={handleCancelDelete}
              className={`${button} rounded-lg bg-gray-200 text-gray-600 hover:bg-gray-300 transition-colors`}
              title="取消"
            >
              <svg className={icon} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

/**
 * 文档批量操作组件
 */
export interface DocumentBatchActionsProps {
  /** 选中的文档ID列表 */
  selectedIds: number[];
  /** 全选状态 */
  isAllSelected?: boolean;
  /** 全选切换回调 */
  onSelectAll?: () => void;
  /** 批量删除回调 */
  onBatchDelete?: () => void;
  /** 批量导出回调 */
  onBatchExport?: () => void;
  /** 取消选择回调 */
  onClearSelection?: () => void;
  /** 额外样式类 */
  className?: string;
}

export function DocumentBatchActions({
  selectedIds,
  isAllSelected = false,
  onSelectAll,
  onBatchDelete,
  onBatchExport,
  onClearSelection,
  className = '',
}: DocumentBatchActionsProps): React.ReactElement | null {
  if (selectedIds.length === 0) {
    return null;
  }

  return (
    <div className={`bg-blue-50 border border-blue-200 rounded-lg p-3 flex items-center justify-between ${className}`}>
      <div className="flex items-center gap-3">
        {onSelectAll && (
          <button
            onClick={onSelectAll}
            className="text-sm text-blue-600 hover:text-blue-700 font-medium"
          >
            {isAllSelected ? '取消全选' : '全选'}
          </button>
        )}
        <span className="text-sm text-blue-800">
          已选择 <strong>{selectedIds.length}</strong> 个文档
        </span>
      </div>

      <div className="flex items-center gap-2">
        {onBatchExport && (
          <button
            onClick={onBatchExport}
            className="px-3 py-1.5 text-sm text-blue-700 bg-white border border-blue-300 rounded-lg hover:bg-blue-50 transition-colors flex items-center gap-1.5"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
            </svg>
            批量导出
          </button>
        )}

        {onBatchDelete && (
          <button
            onClick={onBatchDelete}
            className="px-3 py-1.5 text-sm text-red-700 bg-white border border-red-300 rounded-lg hover:bg-red-50 transition-colors flex items-center gap-1.5"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
            </svg>
            批量删除
          </button>
        )}

        {onClearSelection && (
          <button
            onClick={onClearSelection}
            className="p-1.5 text-gray-500 hover:text-gray-700 hover:bg-gray-200 rounded-lg transition-colors"
            title="取消选择"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        )}
      </div>
    </div>
  );
}