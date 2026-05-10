/**
 * ComplianceReportList - 合规报告列表组件
 *
 * 展示企业合规报告列表，支持筛选、排序、分页和统计功能
 */

import { logger } from '@/shared/lib/logger';
import { useMemo, useState, useCallback } from 'react';

import { StatCard } from '../../analytics/components/StatCard';
import { DataTable } from '../../analytics/components/DataTable';
import { EmptyState } from '../../../components/ui/EmptyState';
import type { StatCardData, DataTableColumn } from '../../analytics/types';

// ==================== 类型定义 ====================

/**
 * 报告类型
 */
export type ReportType = 'gdpr' | 'iso27001' | 'hipaa' | 'soc2' | 'pci' | 'custom';

/**
 * 报告状态
 */
export type ReportStatus = 'pending' | 'generating' | 'completed' | 'failed';

/**
 * 合规报告数据
 */
export interface ComplianceReport extends Record<string, unknown> {
  /** 报告ID */
  id: number;
  /** 报告名称 */
  name: string;
  /** 报告类型 */
  type: ReportType;
  /** 报告状态 */
  status: ReportStatus;
  /** 创建时间 */
  createdAt: string;
  /** 文件URL */
  fileUrl?: string;
  /** 报告描述 */
  description?: string;
  /** 报告周期开始时间 */
  periodStart?: string;
  /** 报告周期结束时间 */
  periodEnd?: string;
  /** 文件大小（字节） */
  fileSize?: number;
}

/**
 * 分页配置
 */
export interface PaginationConfig {
  /** 当前页码 */
  current: number;
  /** 每页条数 */
  pageSize: number;
  /** 总条数 */
  total: number;
}

/**
 * 筛选配置
 */
export interface FilterConfig {
  /** 按类型筛选 */
  type?: ReportType;
  /** 按状态筛选 */
  status?: ReportStatus;
  /** 关键词搜索 */
  keyword?: string;
}

/**
 * 合规报告列表组件属性
 */
export interface ComplianceReportListProps {
  /** 企业账户ID */
  accountId: number;
  /** 报告列表数据 */
  reports?: ComplianceReport[];
  /** 加载状态 */
  isLoading?: boolean;
  /** 错误状态 */
  error?: Error | null;
  /** 分页配置 */
  pagination?: PaginationConfig;
  /** 筛选配置 */
  filter?: FilterConfig;
  /** 点击报告回调 */
  onReportClick?: (report: ComplianceReport) => void;
  /** 生成报告回调 */
  onGenerateReport?: () => void;
  /** 导出报告回调 */
  onExportReport?: (report: ComplianceReport) => void;
  /** 删除报告回调 */
  onDeleteReport?: (report: ComplianceReport) => void;
  /** 筛选变化回调 */
  onFilterChange?: (filter: FilterConfig) => void;
  /** 分页变化回调 */
  onPageChange?: (page: number) => void;
}

// ==================== 常量定义 ====================

/** 报告类型标签映射 */
const REPORT_TYPE_LABELS: Record<ReportType, string> = {
  gdpr: 'GDPR',
  iso27001: 'ISO 27001',
  hipaa: 'HIPAA',
  soc2: 'SOC 2',
  pci: 'PCI DSS',
  custom: '自定义',
};

/** 报告状态标签映射 */
const REPORT_STATUS_LABELS: Record<ReportStatus, string> = {
  pending: '待生成',
  generating: '生成中',
  completed: '已完成',
  failed: '失败',
};

/** 报告状态颜色映射（背景 + 文字） */
const REPORT_STATUS_COLORS: Record<ReportStatus, string> = {
  pending: 'bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-200',
  generating: 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200',
  completed: 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200',
  failed: 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200',
};

/** 报告类型颜色映射 */
const REPORT_TYPE_COLORS: Record<ReportType, string> = {
  gdpr: 'text-purple-600 dark:text-purple-400',
  iso27001: 'text-blue-600 dark:text-blue-400',
  hipaa: 'text-teal-600 dark:text-teal-400',
  soc2: 'text-indigo-600 dark:text-indigo-400',
  pci: 'text-orange-600 dark:text-orange-400',
  custom: 'text-gray-600 dark:text-gray-400',
};

// ==================== 辅助函数 ====================

/**
 * 格式化日期
 * @param dateString - ISO 日期字符串
 * @returns 格式化后的日期字符串
 */
function formatDate(dateString: string): string {
  if (!dateString) return '-';
  const date = new Date(dateString);
  return date.toLocaleDateString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  });
}

/**
 * 格式化文件大小
 * @param bytes - 字节数
 * @returns 格式化后的文件大小字符串
 */
function formatFileSize(bytes?: number): string {
  if (bytes === undefined || bytes === null) return '-';
  if (bytes === 0) return '0 B';

  const units = ['B', 'KB', 'MB', 'GB', 'TB'];
  const k = 1024;
  const i = Math.floor(Math.log(bytes) / Math.log(k));

  return `${(bytes / Math.pow(k, i)).toFixed(1)} ${units[i]}`;
}

// ==================== 子组件 ====================

/**
 * 统计卡片骨架屏
 */
function StatsSkeleton(): JSX.Element {
  return (
    <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
      {[1, 2, 3, 4].map((i) => (
        <div
          key={i}
          className="rounded-lg bg-white p-6 shadow-sm dark:bg-gray-800"
        >
          <div className="animate-pulse">
            <div className="flex items-center justify-between">
              <div className="h-4 w-24 rounded bg-gray-200 dark:bg-gray-700"></div>
              <div className="h-10 w-10 rounded-full bg-gray-200 dark:bg-gray-700"></div>
            </div>
            <div className="mt-4 h-8 w-32 rounded bg-gray-200 dark:bg-gray-700"></div>
            <div className="mt-2 h-4 w-20 rounded bg-gray-200 dark:bg-gray-700"></div>
          </div>
        </div>
      ))}
    </div>
  );
}

/**
 * 表格骨架屏
 */
function TableSkeleton(): JSX.Element {
  return (
    <div className="rounded-lg bg-white shadow-sm dark:bg-gray-800">
      <div className="animate-pulse p-6">
        <div className="mb-4 h-6 w-32 rounded bg-gray-200 dark:bg-gray-700"></div>
        <div className="space-y-3">
          <div className="h-10 rounded bg-gray-200 dark:bg-gray-700"></div>
          {[1, 2, 3, 4, 5].map((i) => (
            <div key={i} className="h-12 rounded bg-gray-100 dark:bg-gray-700"></div>
          ))}
        </div>
      </div>
    </div>
  );
}

/**
 * 筛选栏组件
 */
function FilterBar({
  filter,
  onFilterChange,
  onGenerateReport,
}: {
  filter?: FilterConfig;
  onFilterChange?: (filter: FilterConfig) => void;
  onGenerateReport?: () => void;
}): JSX.Element {
  const [localKeyword, setLocalKeyword] = useState(filter?.keyword || '');

  const handleKeywordChange = (e: React.ChangeEvent<HTMLInputElement>): void => {
    setLocalKeyword(e.target.value);
  };

  const handleKeywordSubmit = (e: React.FormEvent): void => {
    e.preventDefault();
    onFilterChange?.({ ...filter, keyword: localKeyword || undefined });
  };

  const handleTypeChange = (e: React.ChangeEvent<HTMLSelectElement>): void => {
    const type = e.target.value as ReportType | '';
    onFilterChange?.({ ...filter, type: type || undefined });
  };

  const handleStatusChange = (e: React.ChangeEvent<HTMLSelectElement>): void => {
    const status = e.target.value as ReportStatus | '';
    onFilterChange?.({ ...filter, status: status || undefined });
  };

  return (
    <div className="rounded-lg bg-white p-4 shadow-sm dark:bg-gray-800">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        {/* 筛选控件组 */}
        <div className="flex flex-col gap-3 sm:flex-row sm:items-center">
          {/* 类型筛选 */}
          <select
            value={filter?.type || ''}
            onChange={handleTypeChange}
            className="rounded-md border border-gray-300 bg-white px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-700 dark:text-gray-100"
            aria-label="筛选报告类型"
          >
            <option value="">所有类型</option>
            {Object.entries(REPORT_TYPE_LABELS).map(([type, label]) => (
              <option key={type} value={type}>
                {label}
              </option>
            ))}
          </select>

          {/* 状态筛选 */}
          <select
            value={filter?.status || ''}
            onChange={handleStatusChange}
            className="rounded-md border border-gray-300 bg-white px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-700 dark:text-gray-100"
            aria-label="筛选报告状态"
          >
            <option value="">所有状态</option>
            {Object.entries(REPORT_STATUS_LABELS).map(([status, label]) => (
              <option key={status} value={status}>
                {label}
              </option>
            ))}
          </select>

          {/* 关键词搜索 */}
          <form onSubmit={handleKeywordSubmit} className="relative">
            <input
              type="text"
              placeholder="搜索报告名称..."
              value={localKeyword}
              onChange={handleKeywordChange}
              className="w-full rounded-md border border-gray-300 bg-white py-2 pl-3 pr-10 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-700 dark:text-gray-100 sm:w-64"
              aria-label="搜索报告"
            />
            <button
              type="submit"
              className="absolute right-2 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
              aria-label="搜索"
            >
              <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
                />
              </svg>
            </button>
          </form>
        </div>

        {/* 生成报告按钮 */}
        {onGenerateReport && (
          <button
            onClick={onGenerateReport}
            className="inline-flex items-center justify-center rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 dark:bg-blue-700 dark:hover:bg-blue-600"
          >
            <svg className="mr-2 h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
            </svg>
            生成报告
          </button>
        )}
      </div>
    </div>
  );
}

/**
 * 分页组件
 */
function Pagination({
  pagination,
  onPageChange,
}: {
  pagination?: PaginationConfig;
  onPageChange?: (page: number) => void;
}): JSX.Element | null {
  if (!pagination || pagination.total <= pagination.pageSize) return null;

  const totalPages = Math.ceil(pagination.total / pagination.pageSize);
  const current = pagination.current;

  const getPageNumbers = (): (number | string)[] => {
    const pages: (number | string)[] = [];

    if (totalPages <= 7) {
      for (let i = 1; i <= totalPages; i++) pages.push(i);
    } else {
      if (current <= 3) {
        pages.push(1, 2, 3, 4, '...', totalPages);
      } else if (current >= totalPages - 2) {
        pages.push(1, '...', totalPages - 3, totalPages - 2, totalPages - 1, totalPages);
      } else {
        pages.push(1, '...', current - 1, current, current + 1, '...', totalPages);
      }
    }

    return pages;
  };

  return (
    <div className="flex items-center justify-between border-t border-gray-200 bg-white px-4 py-3 dark:border-gray-700 dark:bg-gray-800 sm:px-6">
      <div className="flex flex-1 items-center justify-between sm:hidden">
        <button
          onClick={() => onPageChange?.(current - 1)}
          disabled={current <= 1}
          className="relative inline-flex items-center rounded-md border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-50 dark:border-gray-600 dark:bg-gray-700 dark:text-gray-200 dark:hover:bg-gray-600"
        >
          上一页
        </button>
        <span className="text-sm text-gray-700 dark:text-gray-300">
          {current} / {totalPages}
        </span>
        <button
          onClick={() => onPageChange?.(current + 1)}
          disabled={current >= totalPages}
          className="relative inline-flex items-center rounded-md border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-50 dark:border-gray-600 dark:bg-gray-700 dark:text-gray-200 dark:hover:bg-gray-600"
        >
          下一页
        </button>
      </div>
      <div className="hidden sm:flex sm:flex-1 sm:items-center sm:justify-between">
        <div>
          <p className="text-sm text-gray-700 dark:text-gray-300">
            显示第 <span className="font-medium">{(current - 1) * pagination.pageSize + 1}</span> 到{' '}
            <span className="font-medium">
              {Math.min(current * pagination.pageSize, pagination.total)}
            </span>{' '}
            条，共 <span className="font-medium">{pagination.total}</span> 条
          </p>
        </div>
        <div>
          <nav className="isolate inline-flex -space-x-px rounded-md shadow-sm" aria-label="分页">
            <button
              onClick={() => onPageChange?.(current - 1)}
              disabled={current <= 1}
              className="relative inline-flex items-center rounded-l-md px-2 py-2 text-gray-400 ring-1 ring-inset ring-gray-300 hover:bg-gray-50 focus:z-20 focus:outline-offset-0 disabled:opacity-50 dark:ring-gray-600 dark:hover:bg-gray-700"
            >
              <span className="sr-only">上一页</span>
              <svg className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true">
                <path
                  fillRule="evenodd"
                  d="M12.79 5.23a.75.75 0 01-.02 1.06L8.832 10l3.938 3.71a.75.75 0 11-1.04 1.08l-4.5-4.25a.75.75 0 010-1.08l4.5-4.25a.75.75 0 011.06.02z"
                  clipRule="evenodd"
                />
              </svg>
            </button>
            {getPageNumbers().map((page, index) =>
              page === '...' ? (
                <span
                  key={`ellipsis-${index}`}
                  className="relative inline-flex items-center px-4 py-2 text-sm font-semibold text-gray-700 ring-1 ring-inset ring-gray-300 focus:outline-offset-0 dark:ring-gray-600 dark:text-gray-300"
                >
                  ...
                </span>
              ) : (
                <button
                  key={page}
                  onClick={() => onPageChange?.(page as number)}
                  className={`relative inline-flex items-center px-4 py-2 text-sm font-semibold ${
                    page === current
                      ? 'z-10 bg-blue-600 text-white focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-blue-600'
                      : 'text-gray-900 ring-1 ring-inset ring-gray-300 hover:bg-gray-50 focus:z-20 focus:outline-offset-0 dark:text-gray-300 dark:ring-gray-600 dark:hover:bg-gray-700'
                  }`}
                >
                  {page}
                </button>
              )
            )}
            <button
              onClick={() => onPageChange?.(current + 1)}
              disabled={current >= totalPages}
              className="relative inline-flex items-center rounded-r-md px-2 py-2 text-gray-400 ring-1 ring-inset ring-gray-300 hover:bg-gray-50 focus:z-20 focus:outline-offset-0 disabled:opacity-50 dark:ring-gray-600 dark:hover:bg-gray-700"
            >
              <span className="sr-only">下一页</span>
              <svg className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true">
                <path
                  fillRule="evenodd"
                  d="M7.21 14.77a.75.75 0 01.02-1.06L11.168 10 7.23 6.29a.75.75 0 111.04-1.08l4.5 4.25a.75.75 0 010 1.08l-4.5 4.25a.75.75 0 01-1.06-.02z"
                  clipRule="evenodd"
                />
              </svg>
            </button>
          </nav>
        </div>
      </div>
    </div>
  );
}

// ==================== 主组件 ====================

/**
 * 合规报告列表组件
 *
 * @example
 * ```tsx
 * // 基本使用
 * <ComplianceReportList accountId={123} />
 *
 * // 带数据和回调
 * <ComplianceReportList
 *   accountId={123}
 *   reports={reportsData}
 *   isLoading={false}
 *   pagination={{ current: 1, pageSize: 10, total: 100 }}
 *   onReportClick={(report) => logger.info(report)}
 *   onGenerateReport={() => logger.info('生成报告')}
 * />
 * ```
 */
export function ComplianceReportList({
  accountId,
  reports = [],
  isLoading = false,
  error = null,
  pagination,
  filter,
  onReportClick,
  onGenerateReport,
  onExportReport,
  onDeleteReport,
  onFilterChange,
  onPageChange,
}: ComplianceReportListProps): JSX.Element {
  // 本地筛选状态（用于客户端筛选）
  const [sortConfig, setSortConfig] = useState<{
    key: keyof ComplianceReport;
    direction: 'asc' | 'desc';
  } | null>(null);

  // 计算统计数据
  const stats = useMemo(() => {
    const total = reports.length;
    const completed = reports.filter((r) => r.status === 'completed').length;
    const generating = reports.filter((r) => r.status === 'generating').length;
    const failed = reports.filter((r) => r.status === 'failed').length;

    return { total, completed, generating, failed };
  }, [reports]);

  // 构建统计卡片数据
  const statCardsData: StatCardData[] = useMemo(() => {
    return [
      {
        title: '总报告数',
        value: stats.total,
        icon: 'Activity',
      },
      {
        title: '已完成',
        value: stats.completed,
        change: stats.total > 0 ? (stats.completed / stats.total) * 100 : 0,
        changeType: 'increase',
        icon: 'Users',
      },
      {
        title: '生成中',
        value: stats.generating,
        icon: 'Clock',
      },
      {
        title: '失败',
        value: stats.failed,
        change: stats.failed > 0 ? -stats.failed : 0,
        changeType: 'decrease',
        icon: 'Activity',
      },
    ];
  }, [stats]);

  // 筛选和排序数据
  const filteredAndSortedReports = useMemo(() => {
    let result = [...reports];

    // 客户端筛选（如果提供了 filter）
    if (filter) {
      if (filter.type) {
        result = result.filter((r) => r.type === filter.type);
      }
      if (filter.status) {
        result = result.filter((r) => r.status === filter.status);
      }
      if (filter.keyword) {
        const keyword = filter.keyword.toLowerCase();
        result = result.filter(
          (r) =>
            r.name.toLowerCase().includes(keyword) ||
            r.description?.toLowerCase().includes(keyword)
        );
      }
    }

    // 排序
    if (sortConfig) {
      result.sort((a, b) => {
        const aValue = a[sortConfig.key];
        const bValue = b[sortConfig.key];

        if (aValue === undefined || aValue === null || bValue === undefined || bValue === null) return 0;
        if (aValue < bValue) return sortConfig.direction === 'asc' ? -1 : 1;
        if (aValue > bValue) return sortConfig.direction === 'asc' ? 1 : -1;
        return 0;
      });
    }

    return result;
  }, [reports, filter, sortConfig]);

  // 处理排序（预留）
  const _handleSort = useCallback(
    (key: keyof ComplianceReport) => {
      setSortConfig((current) => {
        if (current?.key === key) {
          return {
            key,
            direction: current.direction === 'asc' ? 'desc' : 'asc',
          };
        }
        return { key, direction: 'asc' };
      });
    },
    [setSortConfig]
  );

  // 表格列定义
  const columns: DataTableColumn<ComplianceReport>[] = useMemo(
    () => [
      {
        key: 'name',
        title: '报告名称',
        dataIndex: 'name',
        render: (record) => (
          <div className="flex flex-col">
            <button
              onClick={() => onReportClick?.(record)}
              className="text-left font-medium text-blue-600 hover:text-blue-800 hover:underline dark:text-blue-400 dark:hover:text-blue-300"
            >
              {record.name}
            </button>
            {record.description && (
              <span className="mt-1 max-w-xs truncate text-xs text-gray-500 dark:text-gray-400">
                {record.description}
              </span>
            )}
          </div>
        ),
        sorter: (a: ComplianceReport, b: ComplianceReport) => a.name.localeCompare(b.name),
      },
      {
        key: 'type',
        title: '类型',
        dataIndex: 'type',
        width: 120,
        render: (record) => (
          <span
            className={`inline-flex items-center text-sm font-medium ${REPORT_TYPE_COLORS[record.type]}`}
          >
            {REPORT_TYPE_LABELS[record.type]}
          </span>
        ),
      },
      {
        key: 'status',
        title: '状态',
        dataIndex: 'status',
        width: 100,
        render: (record) => (
          <span
            className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${REPORT_STATUS_COLORS[record.status]}`}
          >
            {record.status === 'generating' && (
              <svg
                className="mr-1.5 h-2 w-2 animate-spin"
                fill="currentColor"
                viewBox="0 0 24 24"
              >
                <circle
                  className="opacity-25"
                  cx="12"
                  cy="12"
                  r="10"
                  stroke="currentColor"
                  strokeWidth="4"
                  fill="none"
                />
                <path
                  className="opacity-75"
                  fill="currentColor"
                  d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                />
              </svg>
            )}
            {REPORT_STATUS_LABELS[record.status]}
          </span>
        ),
      },
      {
        key: 'fileSize',
        title: '文件大小',
        dataIndex: 'fileSize',
        width: 100,
        render: (record) => (
          <span className="text-sm text-gray-600 dark:text-gray-400">
            {formatFileSize(record.fileSize)}
          </span>
        ),
      },
      {
        key: 'createdAt',
        title: '创建时间',
        dataIndex: 'createdAt',
        width: 150,
        render: (record) => (
          <span className="text-sm text-gray-500 dark:text-gray-400">
            {formatDate(record.createdAt)}
          </span>
        ),
        sorter: (a: ComplianceReport, b: ComplianceReport) =>
          new Date(a.createdAt).getTime() - new Date(b.createdAt).getTime(),
      },
      {
        key: 'actions',
        title: '操作',
        width: 120,
        align: 'center',
        render: (record) => (
          <div className="flex items-center justify-center space-x-2">
            {record.status === 'completed' && onExportReport && (
              <button
                onClick={() => onExportReport(record)}
                className="rounded p-1 text-blue-600 hover:bg-blue-50 dark:text-blue-400 dark:hover:bg-blue-900/30"
                title="导出报告"
                aria-label="导出报告"
              >
                <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"
                  />
                </svg>
              </button>
            )}
            {onDeleteReport && (
              <button
                onClick={() => onDeleteReport(record)}
                className="rounded p-1 text-red-600 hover:bg-red-50 dark:text-red-400 dark:hover:bg-red-900/30"
                title="删除报告"
                aria-label="删除报告"
              >
                <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"
                  />
                </svg>
              </button>
            )}
          </div>
        ),
      },
    ],
    [onReportClick, onExportReport, onDeleteReport]
  );

  // 错误状态
  if (error) {
    return (
      <div className="space-y-6">
        <div>
          <h2 className="text-xl font-semibold text-gray-900 dark:text-gray-100">合规报告</h2>
          <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">管理和查看企业合规报告</p>
        </div>
        <EmptyState
          icon="error"
          title="加载失败"
          description={error.message || '无法加载合规报告数据，请稍后重试'}
        />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* 标题区域 */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h2 className="text-xl font-semibold text-gray-900 dark:text-gray-100">合规报告</h2>
          <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
            管理和查看企业合规报告
            {accountId && (
              <span className="ml-2 text-xs text-gray-400">(企业ID: {accountId})</span>
            )}
          </p>
        </div>
      </div>

      {/* 统计卡片区域 */}
      {isLoading ? (
        <StatsSkeleton />
      ) : (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {statCardsData.map((stat, index) => (
            <StatCard key={`${stat.title}-${index}`} data={stat} />
          ))}
        </div>
      )}

      {/* 筛选栏 */}
      <FilterBar
        filter={filter}
        onFilterChange={onFilterChange}
        onGenerateReport={onGenerateReport}
      />

      {/* 报告列表表格 */}
      {isLoading ? (
        <TableSkeleton />
      ) : filteredAndSortedReports.length > 0 ? (
        <div className="rounded-lg bg-white shadow-sm dark:bg-gray-800">
          <DataTable<ComplianceReport>
            data={filteredAndSortedReports}
            columns={columns}
            title="报告列表"
            rowKey="id"
            striped={true}
            size="middle"
          />
          <Pagination pagination={pagination} onPageChange={onPageChange} />
        </div>
      ) : (
        <div className="rounded-lg bg-white p-6 shadow-sm dark:bg-gray-800">
          <EmptyState
            icon="document"
            title={filter?.keyword ? '未找到匹配的报告' : '暂无报告'}
            description={
              filter?.keyword
                ? '请尝试其他关键词或清除筛选条件'
                : '还没有生成任何合规报告，点击"生成报告"按钮创建第一个报告'
            }
            action={
              onGenerateReport &&
              !filter?.keyword && (
                <button
                  onClick={onGenerateReport}
                  className="mt-4 inline-flex items-center rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 dark:bg-blue-700 dark:hover:bg-blue-600"
                >
                  <svg
                    className="mr-2 h-4 w-4"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M12 4v16m8-8H4"
                    />
                  </svg>
                  生成报告
                </button>
              )
            }
          />
        </div>
      )}
    </div>
  );
}

export default ComplianceReportList;