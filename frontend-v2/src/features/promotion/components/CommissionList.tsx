/**
 * CommissionList - 佣金记录列表组件
 *
 * 支持状态筛选和分页功能
 */

import { useState } from 'react';

import { useCommissionRecords } from '../hooks/usePromotion';
import { Pagination } from '../../../components/ui/Pagination';
import { FilterDropdown } from '../../../components/ui/FilterDropdown';
import { DateRangePicker, type DateRange } from '../../../components/ui/DateRangePicker';
import { ListItemSkeleton } from '../../../components/ui/Skeleton';
import { EmptyState, EmptyError } from '../../../components/ui/EmptyState';
import type { CommissionRecord } from '../types';

interface CommissionListProps {
  className?: string;
  /** 是否使用骨架屏加载 */
  useSkeleton?: boolean;
  /** 初始每页条数 */
  defaultPageSize?: number;
}

/**
 * 佣金状态选项
 */
const statusOptions = [
  { value: 'pending', label: '待确认', color: 'text-orange-500' },
  { value: 'confirmed', label: '已确认', color: 'text-blue-500' },
  { value: 'paid', label: '已结算', color: 'text-green-500' },
  { value: 'cancelled', label: '已取消', color: 'text-gray-500' },
];

/**
 * 排序选项
 */
const sortOptions = [
  { value: 'newest', label: '最新优先' },
  { value: 'oldest', label: '最早优先' },
  { value: 'amount_desc', label: '金额从高到低' },
  { value: 'amount_asc', label: '金额从低到高' },
];

/**
 * 格式化日期
 */
function formatDate(dateString: string): string {
  const date = new Date(dateString);
  return date.toLocaleDateString('zh-CN', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
}

/**
 * 获取状态显示文本
 */
function getStatusLabel(status: string): { text: string; color: string } {
  const statusMap: Record<string, { text: string; color: string }> = {
    pending: { text: '待确认', color: 'text-orange-500 bg-orange-50 dark:bg-orange-900/20' },
    confirmed: { text: '已确认', color: 'text-blue-500 bg-blue-50 dark:bg-blue-900/20' },
    paid: { text: '已结算', color: 'text-green-500 bg-green-50 dark:bg-green-900/20' },
    cancelled: { text: '已取消', color: 'text-gray-500 bg-gray-50 dark:bg-gray-800' },
  };
  return statusMap[status] || { text: status, color: 'text-gray-500 bg-gray-50 dark:bg-gray-800' };
}

/**
 * 佣金记录列表组件
 */
export function CommissionList({
  className = '',
  useSkeleton = true,
  defaultPageSize = 10,
}: CommissionListProps): JSX.Element {
  // 分页状态
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(defaultPageSize);

  // 筛选状态
  const [selectedStatuses, setSelectedStatuses] = useState<string[]>([]);
  const [dateRange, setDateRange] = useState<DateRange>({ startDate: null, endDate: null });
  const [sortBy, setSortBy] = useState<string>('newest');

  // 查询参数
  const queryParams = {
    limit: pageSize,
    offset: (page - 1) * pageSize,
    status: selectedStatuses.length === 1 ? (selectedStatuses[0] as 'pending' | 'confirmed' | 'paid' | 'cancelled') : undefined,
    startDate: dateRange.startDate?.toISOString().split('T')[0],
    endDate: dateRange.endDate?.toISOString().split('T')[0],
  };

  // 获取数据
  const { data, isLoading, error, refetch } = useCommissionRecords(queryParams);

  // 处理分页变化
  const handlePageChange = (newPage: number, newPageSize: number): void => {
    setPage(newPage);
    setPageSize(newPageSize);
  };

  // 清除筛选
  const handleClearFilters = (): void => {
    setSelectedStatuses([]);
    setDateRange({ startDate: null, endDate: null });
    setSortBy('newest');
    setPage(1);
  };

  // 是否有筛选条件
  const hasFilters = selectedStatuses.length > 0 || dateRange.startDate !== null || sortBy !== 'newest';

  // 排序记录
  const sortRecords = (records: CommissionRecord[]): CommissionRecord[] => {
    return [...records].sort((a, b) => {
      switch (sortBy) {
        case 'newest':
          return new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime();
        case 'oldest':
          return new Date(a.createdAt).getTime() - new Date(b.createdAt).getTime();
        case 'amount_desc':
          return b.commissionAmount - a.commissionAmount;
        case 'amount_asc':
          return a.commissionAmount - b.commissionAmount;
        default:
          return 0;
      }
    });
  };

  if (isLoading && useSkeleton) {
    return (
      <div className={`space-y-3 ${className}`}>
        {/* 筛选骨架 */}
        <div className="flex flex-wrap gap-3 mb-4">
          <div className="w-32 h-9 bg-gray-200 rounded-lg animate-pulse" />
          <div className="w-40 h-9 bg-gray-200 rounded-lg animate-pulse" />
        </div>
        {/* 列表骨架 */}
        {Array.from({ length: 5 }).map((_, index) => (
          <ListItemSkeleton
            key={index}
            avatar={false}
            lines={2}
            className="bg-white dark:bg-gray-800 rounded-lg border dark:border-gray-700"
          />
        ))}
      </div>
    );
  }

  if (error) {
    return (
      <div className={`${className}`}>
        <EmptyError
          title="加载失败"
          description="无法获取佣金记录"
          onRetry={() => { void refetch(); }}
        />
      </div>
    );
  }

  const records = sortRecords(data?.records ?? []);
  const total = data?.total ?? 0;

  return (
    <div className={className}>
      {/* 筛选栏 */}
      <div className="flex flex-wrap items-center gap-3 mb-4">
        {/* 状态筛选 */}
        <FilterDropdown
          label="状态"
          placeholder="全部状态"
          multiple
          options={statusOptions.map(({ value, label }) => ({ value, label }))}
          value={selectedStatuses}
          onChange={(value) => {
            setSelectedStatuses(value);
            setPage(1);
          }}
        />

        {/* 日期范围 */}
        <DateRangePicker
          value={dateRange}
          onChange={(range) => {
            setDateRange(range);
            setPage(1);
          }}
          placeholder="选择日期范围"
          showPresets
        />

        {/* 排序 */}
        <FilterDropdown
          label="排序"
          placeholder="最新优先"
          options={sortOptions}
          value={sortBy ? [sortBy] : []}
          onChange={(value) => {
            setSortBy(value[0] || 'newest');
            setPage(1);
          }}
        />

        {/* 清除筛选 */}
        {hasFilters && (
          <button
            onClick={handleClearFilters}
            className="px-3 py-2 text-sm font-medium text-gray-600 hover:text-gray-800 hover:bg-gray-100 rounded-lg transition-colors dark:text-gray-400 dark:hover:text-gray-200 dark:hover:bg-gray-700"
          >
            清除筛选
          </button>
        )}
      </div>

      {/* 统计摘要 */}
      <div className="flex flex-wrap gap-4 mb-4 text-sm text-gray-500 dark:text-gray-400">
        <span>
          共 <strong className="text-gray-900 dark:text-gray-100">{total}</strong> 条记录
        </span>
        {selectedStatuses.length > 0 && (
          <span>
            已筛选: {selectedStatuses.map(s => statusOptions.find(o => o.value === s)?.label).join(', ')}
          </span>
        )}
      </div>

      {/* 数据列表 */}
      {records.length === 0 ? (
        <EmptyState
          icon="box"
          title="暂无佣金记录"
          description={hasFilters ? '没有找到符合条件的记录，尝试调整筛选条件' : '推广成功后佣金将在这里显示'}
          size="md"
          action={
            hasFilters && (
              <button
                onClick={handleClearFilters}
                className="px-4 py-2 text-sm font-medium text-blue-600 hover:text-blue-700"
              >
                清除筛选
              </button>
            )
          }
        />
      ) : (
        <div className="space-y-2 mb-4">
          {records.map((record: CommissionRecord) => {
            const statusInfo = getStatusLabel(record.status);
            return (
              <div
                key={record.id}
                className="flex items-center justify-between p-4 bg-white dark:bg-gray-800 rounded-lg border dark:border-gray-700 hover:shadow-sm transition-shadow"
              >
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 flex-wrap">
                    <span className="font-medium text-gray-900 dark:text-gray-100">
                      订单佣金
                    </span>
                    <span className={`px-2 py-0.5 text-xs rounded-full ${statusInfo.color}`}>
                      {statusInfo.text}
                    </span>
                  </div>
                  <div className="text-sm text-gray-400 dark:text-gray-500 mt-1">
                    {formatDate(record.createdAt)}
                    {record.sourceUserName && (
                      <span className="ml-2">来自: {record.sourceUserName}</span>
                    )}
                  </div>
                  {record.description && (
                    <div className="text-sm text-gray-500 dark:text-gray-400 mt-1">{record.description}</div>
                  )}
                </div>

                <div className="flex flex-col items-end gap-1 ml-4">
                  <span className="text-lg font-bold text-green-600 dark:text-green-400">
                    +¥{record.commissionAmount.toFixed(2)}
                  </span>
                  <span className="text-xs text-gray-400 dark:text-gray-500">
                    订单金额: ¥{record.orderAmount.toFixed(2)}
                  </span>
                  <span className="text-xs text-gray-400 dark:text-gray-500">
                    佣金率: {(record.commissionRate * 100).toFixed(1)}%
                  </span>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* 分页 */}
      {total > 0 && (
        <Pagination
          currentPage={page}
          totalPages={Math.ceil(total / pageSize)}
          total={total}
          onChange={handlePageChange}
          showTotal
        />
      )}
    </div>
  );
}

export default CommissionList;