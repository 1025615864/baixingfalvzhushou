/**
 * Pagination - 通用分页组件
 *
 * 支持页码导航、每页条数选择等功能
 */

import React, { useState, useCallback } from 'react';

export interface PaginationProps {
  /** 当前页码 */
  currentPage?: number;
  /** 总页数 */
  totalPages?: number;
  /** 总条目数 */
  total?: number;
  /** 每页条数 */
  pageSize?: number;
  /** 初始页码（受控模式下无效） */
  initialPage?: number;
  /** 初始每页条数（受控模式下无效） */
  initialPageSize?: number;
  /** 页码变化回调 */
  onPageChange?: (page: number) => void;
  /** 页码和每页条数变化回调 */
  onChange?: (page: number, pageSize: number) => void;
  /** 自定义类名 */
  className?: string;
  /** 是否显示每页条数选择 */
  showPageSize?: boolean;
  /** 每页条数选项 */
  pageSizeOptions?: number[];
  /** 是否显示快速跳转 */
  showQuickJumper?: boolean;
  /** 是否显示总条目数 */
  showTotal?: boolean;
  /** 是否简洁模式 */
  simple?: boolean;
  /** 测试ID */
  'data-testid'?: string;
}

/**
 * 分页按钮组件属性
 */
interface PageButtonProps {
  page: number;
  isActive?: boolean;
  isDisabled?: boolean;
  onClick: () => void;
  title?: string;
}

/**
 * 分页按钮
 */
function PageButton({
  page,
  isActive = false,
  isDisabled = false,
  onClick,
  title,
}: PageButtonProps): JSX.Element {
  return (
    <button
      onClick={onClick}
      disabled={isDisabled}
      title={title}
      className={`
        min-w-[32px] h-8 px-2 rounded text-sm font-medium transition-colors
        ${isActive
          ? 'bg-primary-600 text-white'
          : 'bg-white text-gray-700 hover:bg-gray-50 border border-gray-300'
        }
        ${isDisabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}
      `}
    >
      {page}
    </button>
  );
}

/**
 * 分页组件
 */
export function Pagination({
  currentPage,
  totalPages,
  total = 0,
  pageSize: controlledPageSize,
  initialPage = 1,
  initialPageSize = 20,
  onPageChange,
  onChange,
  className = '',
  showPageSize = false,
  pageSizeOptions = [10, 20, 50, 100],
  showQuickJumper = false,
  showTotal = true,
  simple = false,
  'data-testid': dataTestId,
}: PaginationProps): JSX.Element | null {
  // 内部状态（非受控模式）
  const [internalPage, setInternalPage] = useState(initialPage);
  const [internalPageSize, setInternalPageSize] = useState(initialPageSize);
  const [jumpPage, setJumpPage] = useState('');

  // 计算实际使用的值
  const actualPageSize = controlledPageSize ?? internalPageSize;
  const actualTotalPages = totalPages ?? Math.max(1, Math.ceil(total / actualPageSize));
  const actualCurrentPage = currentPage ?? internalPage;

  // 处理页码变化
  const handlePageChange = useCallback((page: number) => {
    if (page < 1 || page > actualTotalPages || page === actualCurrentPage) return;

    if (currentPage === undefined) {
      setInternalPage(page);
    }
    onPageChange?.(page);
    onChange?.(page, actualPageSize);
  }, [actualCurrentPage, actualPageSize, actualTotalPages, currentPage, onPageChange, onChange]);

  // 处理每页条数变化
  const handlePageSizeChange = useCallback((newPageSize: number) => {
    if (controlledPageSize === undefined) {
      setInternalPageSize(newPageSize);
    }
    // 调整当前页码以适应新的每页条数
    const newTotalPages = Math.max(1, Math.ceil(total / newPageSize));
    const newPage = Math.min(actualCurrentPage, newTotalPages);
    if (currentPage === undefined) {
      setInternalPage(newPage);
    }
    onChange?.(newPage, newPageSize);
  }, [actualCurrentPage, controlledPageSize, currentPage, onChange, total]);

  // 生成页码数组
  const getPageNumbers = useCallback(() => {
    const pages: (number | string)[] = [];
    const maxVisible = 5;

    if (actualTotalPages <= maxVisible) {
      for (let i = 1; i <= actualTotalPages; i++) {
        pages.push(i);
      }
    } else {
      // 始终显示第一页
      pages.push(1);

      if (actualCurrentPage > 3) {
        pages.push('...');
      }

      // 显示当前页附近的页码
      const start = Math.max(2, actualCurrentPage - 1);
      const end = Math.min(actualTotalPages - 1, actualCurrentPage + 1);

      for (let i = start; i <= end; i++) {
        if (!pages.includes(i)) {
          pages.push(i);
        }
      }

      if (actualCurrentPage < actualTotalPages - 2) {
        pages.push('...');
      }

      // 始终显示最后一页
      if (!pages.includes(actualTotalPages)) {
        pages.push(actualTotalPages);
      }
    }

    return pages;
  }, [actualCurrentPage, actualTotalPages]);

  // 处理快速跳转
  const handleJump = useCallback(() => {
    const page = parseInt(jumpPage, 10);
    if (!isNaN(page) && page >= 1 && page <= actualTotalPages) {
      handlePageChange(page);
      setJumpPage('');
    }
  }, [jumpPage, actualTotalPages, handlePageChange]);

  // 当 total 为 0 或负数时不渲染
  if (total <= 0) {
    return null;
  }

  return (
    <div className={`flex items-center justify-center gap-2 ${className}`} data-testid={dataTestId}>
      {showTotal && !simple && (
        <span className="text-sm text-gray-500 mr-4">
          共 {total} 条
        </span>
      )}

      {!simple && (
        <>
          {/* 首页按钮 */}
          <button
            onClick={() => handlePageChange(1)}
            disabled={actualCurrentPage === 1}
            title="首页"
            className="px-3 h-8 rounded text-sm font-medium bg-white text-gray-700 hover:bg-gray-50 border border-gray-300 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            |&lt;
          </button>

          <button
            onClick={() => handlePageChange(actualCurrentPage - 1)}
            disabled={actualCurrentPage === 1}
            title="上一页"
            className="px-3 h-8 rounded text-sm font-medium bg-white text-gray-700 hover:bg-gray-50 border border-gray-300 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            上一页
          </button>

          <div className="flex items-center gap-1">
            {getPageNumbers().map((page, index) => (
              <React.Fragment key={index}>
                {page === '...' ? (
                  <span className="px-2 text-gray-400">...</span>
                ) : (
                  <PageButton
                    page={page as number}
                    isActive={actualCurrentPage === page}
                    onClick={() => handlePageChange(page as number)}
                  />
                )}
              </React.Fragment>
            ))}
          </div>

          <button
            onClick={() => handlePageChange(actualCurrentPage + 1)}
            disabled={actualCurrentPage === actualTotalPages}
            title="下一页"
            className="px-3 h-8 rounded text-sm font-medium bg-white text-gray-700 hover:bg-gray-50 border border-gray-300 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            下一页
          </button>

          {/* 末页按钮 */}
          <button
            onClick={() => handlePageChange(actualTotalPages)}
            disabled={actualCurrentPage === actualTotalPages}
            title="末页"
            className="px-3 h-8 rounded text-sm font-medium bg-white text-gray-700 hover:bg-gray-50 border border-gray-300 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            &gt;|
          </button>
        </>
      )}

      {simple && (
        <>
          <button
            onClick={() => handlePageChange(actualCurrentPage - 1)}
            disabled={actualCurrentPage === 1}
            title="上一页"
            className="px-3 h-8 rounded text-sm font-medium bg-white text-gray-700 hover:bg-gray-50 border border-gray-300 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            上一页
          </button>
          <span className="text-sm text-gray-600">
            {actualCurrentPage} / {actualTotalPages}
          </span>
          <button
            onClick={() => handlePageChange(actualCurrentPage + 1)}
            disabled={actualCurrentPage === actualTotalPages}
            title="下一页"
            className="px-3 h-8 rounded text-sm font-medium bg-white text-gray-700 hover:bg-gray-50 border border-gray-300 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            下一页
          </button>
        </>
      )}

      {/* 每页条数选择 */}
      {showPageSize && (
        <select
          value={actualPageSize}
          onChange={(e) => handlePageSizeChange(Number(e.target.value))}
          className="ml-4 h-8 px-2 rounded text-sm border border-gray-300 bg-white"
        >
          {pageSizeOptions.map((size) => (
            <option key={size} value={size}>
              {size} 条/页
            </option>
          ))}
        </select>
      )}

      {/* 快速跳转 */}
      {showQuickJumper && (
        <div className="flex items-center gap-2 ml-4">
          <span className="text-sm text-gray-500">跳至</span>
          <input
            type="number"
            min={1}
            max={actualTotalPages}
            value={jumpPage}
            onChange={(e) => setJumpPage(e.target.value)}
            placeholder="页码"
            className="w-16 h-8 px-2 rounded text-sm border border-gray-300 text-center"
            onKeyDown={(e) => {
              if (e.key === 'Enter') {
                handleJump();
              }
            }}
          />
          <span className="text-sm text-gray-500">页</span>
          <button
            onClick={handleJump}
            className="px-3 h-8 rounded text-sm font-medium bg-primary-600 text-white hover:bg-primary-700 transition-colors"
          >
            跳转
          </button>
        </div>
      )}
    </div>
  );
}

export default Pagination;
