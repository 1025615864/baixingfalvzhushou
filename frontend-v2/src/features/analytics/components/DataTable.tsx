/**
 * DataTable - 数据表格组件
 */

import { useState, useMemo } from 'react';

import type { DataTableColumn, DataTablePagination } from '../types';

interface DataTableProps<T extends Record<string, unknown>> {
  data: T[];
  columns: DataTableColumn<T>[];
  loading?: boolean;
  title?: string;
  className?: string;
  pagination?: DataTablePagination;
  rowKey?: keyof T | ((record: T) => string);
  onRowClick?: (record: T, index: number) => void;
  emptyText?: string;
  striped?: boolean;
  bordered?: boolean;
  size?: 'small' | 'middle' | 'large';
}

/**
 * 获取行唯一标识
 */
function getRowKey<T extends Record<string, unknown>>(
  record: T,
  index: number,
  rowKey?: keyof T | ((record: T) => string)
): string {
  if (typeof rowKey === 'function') {
    return rowKey(record);
  }
  if (rowKey) {
    const key = record[rowKey];
    return String(key ?? index);
  }
  return String(index);
}

/**
 * 获取嵌套字段值
 */
function getNestedValue<T extends Record<string, unknown>>(
  record: T,
  dataIndex?: string
): unknown {
  if (!dataIndex) return undefined;
  
  const keys = dataIndex.split('.');
  let value: unknown = record;
  
  for (const key of keys) {
    if (value && typeof value === 'object') {
      value = (value as Record<string, unknown>)[key];
    } else {
      return undefined;
    }
  }
  
  return value;
}

export function DataTable<T extends Record<string, unknown>>({
  data,
  columns,
  loading = false,
  title,
  className = '',
  pagination,
  rowKey,
  onRowClick,
  emptyText = '暂无数据',
  striped = true,
  bordered = false,
  size = 'middle',
}: DataTableProps<T>): JSX.Element {
  const [sortConfig, setSortConfig] = useState<{
    key: string;
    direction: 'asc' | 'desc';
  } | null>(null);

  // 处理排序
  const sortedData = useMemo(() => {
    if (!sortConfig) return data;

    return [...data].sort((a, b) => {
      const column = columns.find((col) => col.key === sortConfig.key);
      if (!column?.sorter) return 0;

      return sortConfig.direction === 'asc'
        ? column.sorter(a, b)
        : column.sorter(b, a);
    });
  }, [data, sortConfig, columns]);

  // 处理分页
  const paginatedData = useMemo(() => {
    if (!pagination) return sortedData;

    const start = (pagination.current - 1) * pagination.pageSize;
    const end = start + pagination.pageSize;
    return sortedData.slice(start, end);
  }, [sortedData, pagination]);

  // 尺寸样式
  const sizeClasses = {
    small: 'text-xs py-2 px-3',
    middle: 'text-sm py-3 px-4',
    large: 'text-base py-4 px-5',
  };

  const headerSizeClasses = {
    small: 'text-xs py-2 px-3',
    middle: 'text-sm py-3 px-4',
    large: 'text-base py-4 px-5',
  };

  // 处理表头点击排序
  const handleSort = (column: DataTableColumn<T>): void => {
    if (!column.sorter) return;

    if (sortConfig?.key === column.key) {
      setSortConfig({
        key: column.key,
        direction: sortConfig.direction === 'asc' ? 'desc' : 'asc',
      });
    } else {
      setSortConfig({
        key: column.key,
        direction: 'asc',
      });
    }
  };

  // 渲染排序图标
  const renderSortIcon = (column: DataTableColumn<T>): JSX.Element | null => {
    if (!column.sorter) return null;

    const isActive = sortConfig?.key === column.key;
    const direction = isActive ? sortConfig.direction : null;

    return (
      <span className="ml-1 inline-flex flex-col">
        <svg
          className={`h-3 w-3 ${direction === 'asc' ? 'text-blue-600' : 'text-gray-300'}`}
          fill="currentColor"
          viewBox="0 0 20 20"
        >
          <path
            fillRule="evenodd"
            d="M14.707 12.707a1 1 0 01-1.414 0L10 9.414l-3.293 3.293a1 1 0 01-1.414-1.414l4-4a1 1 0 011.414 0l4 4a1 1 0 010 1.414z"
            clipRule="evenodd"
          />
        </svg>
        <svg
          className={`h-3 w-3 ${direction === 'desc' ? 'text-blue-600' : 'text-gray-300'}`}
          fill="currentColor"
          viewBox="0 0 20 20"
        >
          <path
            fillRule="evenodd"
            d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 011.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z"
            clipRule="evenodd"
          />
        </svg>
      </span>
    );
  };

  if (loading) {
    return (
      <div className={`rounded-lg bg-white shadow-sm ${className}`}>
        {title && (
          <div className="border-b border-gray-200 px-6 py-4">
            <h3 className="text-lg font-semibold text-gray-900">{title}</h3>
          </div>
        )}
        <div className="animate-pulse p-6">
          <div className="space-y-3">
            <div className="h-10 rounded bg-gray-200"></div>
            {[1, 2, 3, 4, 5].map((i) => (
              <div key={i} className="h-12 rounded bg-gray-100"></div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className={`rounded-lg bg-white shadow-sm ${className}`}>
      {title && (
        <div className="border-b border-gray-200 px-6 py-4">
          <h3 className="text-lg font-semibold text-gray-900">{title}</h3>
        </div>
      )}

      <div className={`overflow-x-auto ${bordered ? 'border border-gray-200' : ''}`}>
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              {columns.map((column) => (
                <th
                  key={column.key}
                  scope="col"
                  className={`text-left font-medium text-gray-500 ${headerSizeClasses[size]} ${
                    column.align === 'center'
                      ? 'text-center'
                      : column.align === 'right'
                      ? 'text-right'
                      : 'text-left'
                  } ${column.sorter ? 'cursor-pointer hover:bg-gray-100' : ''}`}
                  style={{ width: column.width }}
                  onClick={() => handleSort(column)}
                >
                  <div
                    className={`flex items-center ${
                      column.align === 'center'
                        ? 'justify-center'
                        : column.align === 'right'
                        ? 'justify-end'
                        : 'justify-start'
                    }`}
                  >
                    {column.title}
                    {renderSortIcon(column)}
                  </div>
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-200 bg-white">
            {paginatedData.length === 0 ? (
              <tr>
                <td
                  colSpan={columns.length}
                  className="py-12 text-center text-gray-500"
                >
                  {emptyText}
                </td>
              </tr>
            ) : (
              paginatedData.map((record, index) => (
                <tr
                  key={getRowKey(record, index, rowKey)}
                  className={`${
                    striped && index % 2 === 1 ? 'bg-gray-50' : 'bg-white'
                  } ${onRowClick ? 'cursor-pointer hover:bg-blue-50' : ''}`}
                  onClick={() => onRowClick?.(record, index)}
                >
                  {columns.map((column) => {
                    const value = column.dataIndex
                      ? getNestedValue(record, column.dataIndex)
                      : undefined;
                    const content = column.render
                      ? column.render(record, index)
                      : String(value ?? '-');

                    return (
                      <td
                        key={column.key}
                        className={`${sizeClasses[size]} ${
                          column.align === 'center'
                            ? 'text-center'
                            : column.align === 'right'
                            ? 'text-right'
                            : 'text-left'
                        } text-gray-900`}
                      >
                        {content}
                      </td>
                    );
                  })}
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* 分页 */}
      {pagination && pagination.total > pagination.pageSize && (
        <div className="flex items-center justify-between border-t border-gray-200 px-6 py-4">
          <div className="text-sm text-gray-500">
            显示第 {(pagination.current - 1) * pagination.pageSize + 1} 到{' '}
            {Math.min(pagination.current * pagination.pageSize, pagination.total)} 条，共{' '}
            {pagination.total} 条
          </div>
          <div className="flex gap-2">
            <button
              className="rounded-md border border-gray-300 px-3 py-1 text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:cursor-not-allowed disabled:opacity-50"
              onClick={() => pagination.onChange?.(pagination.current - 1, pagination.pageSize)}
              disabled={pagination.current <= 1}
            >
              上一页
            </button>
            <span className="flex items-center px-3 text-sm text-gray-500">
              {pagination.current} / {Math.ceil(pagination.total / pagination.pageSize)}
            </span>
            <button
              className="rounded-md border border-gray-300 px-3 py-1 text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:cursor-not-allowed disabled:opacity-50"
              onClick={() => pagination.onChange?.(pagination.current + 1, pagination.pageSize)}
              disabled={pagination.current >= Math.ceil(pagination.total / pagination.pageSize)}
            >
              下一页
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

/**
 * 表格骨架屏
 */
interface TableSkeletonProps {
  columns?: number;
  rows?: number;
  className?: string;
  title?: string;
}

export function TableSkeleton({
  columns = 4,
  rows = 5,
  className = '',
  title,
}: TableSkeletonProps): JSX.Element {
  return (
    <div className={`rounded-lg bg-white shadow-sm ${className}`}>
      {title && (
        <div className="border-b border-gray-200 px-6 py-4">
          <div className="h-6 w-32 rounded bg-gray-200"></div>
        </div>
      )}
      <div className="animate-pulse p-6">
        <div className="space-y-3">
          <div className="flex gap-4">
            {Array.from({ length: columns }).map((_, i) => (
              <div key={i} className="h-10 flex-1 rounded bg-gray-200"></div>
            ))}
          </div>
          {Array.from({ length: rows }).map((_, rowIndex) => (
            <div key={rowIndex} className="flex gap-4">
              {Array.from({ length: columns }).map((_, colIndex) => (
                <div key={colIndex} className="h-12 flex-1 rounded bg-gray-100"></div>
              ))}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

/**
 * 统计数据表格
 */
interface StatTableProps {
  data: Array<{ label: string; value: string | number; change?: number }>;
  title?: string;
  loading?: boolean;
  className?: string;
}

export function StatTable({
  data,
  title,
  loading = false,
  className = '',
}: StatTableProps): JSX.Element {
  if (loading) {
    return <TableSkeleton columns={3} rows={5} className={className} title={title} />;
  }

  return (
    <div className={`rounded-lg bg-white shadow-sm ${className}`}>
      {title && (
        <div className="border-b border-gray-200 px-6 py-4">
          <h3 className="text-lg font-semibold text-gray-900">{title}</h3>
        </div>
      )}
      <div className="divide-y divide-gray-200">
        {data.map((item, index) => (
          <div
            key={index}
            className="flex items-center justify-between px-6 py-4 hover:bg-gray-50"
          >
            <span className="text-sm text-gray-600">{item.label}</span>
            <div className="flex items-center gap-3">
              <span className="text-sm font-semibold text-gray-900">{item.value}</span>
              {item.change !== undefined && (
                <span
                  className={`text-xs ${
                    item.change >= 0 ? 'text-green-600' : 'text-red-600'
                  }`}
                >
                  {item.change >= 0 ? '+' : ''}
                  {item.change}%
                </span>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}