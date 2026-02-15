/**
 * PointsHistory - 积分历史列表组件
 *
 * 支持类型筛选和分页功能
 */

import { useState } from 'react';

import { usePointsHistory } from '../hooks/usePoints';
import { Pagination } from '../../../components/ui/Pagination';
import { FilterDropdown } from '../../../components/ui/FilterDropdown';
import { DateRangePicker, type DateRange } from '../../../components/ui/DateRangePicker';
import { Skeleton, ListItemSkeleton } from '../../../components/ui/Skeleton';
import { EmptyState, EmptyError } from '../../../components/ui/EmptyState';
import type { PointsTransaction } from '../types';

interface PointsHistoryProps {
  className?: string;
  /** 是否使用骨架屏加载 */
  useSkeleton?: boolean;
  /** 初始每页条数 */
  defaultPageSize?: number;
}

/**
 * 积分动作选项
 */
const actionOptions = [
  { value: 'sign_in', label: '每日签到' },
  { value: 'post_create', label: '发布帖子' },
  { value: 'comment_create', label: '发表评论' },
  { value: 'like', label: '点赞' },
  { value: 'share', label: '分享' },
  { value: 'consultation_complete', label: '完成咨询' },
  { value: 'document_upload', label: '上传文档' },
  { value: 'profile_complete', label: '完善资料' },
  { value: 'invite_friend', label: '邀请好友' },
  { value: 'exchange_product', label: '兑换商品' },
  { value: 'bonus', label: '系统奖励' },
];

/**
 * 格式化日期
 */
function formatDate(dateString: string): string {
  const date = new Date(dateString);
  return date.toLocaleDateString('zh-CN', {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
}

/**
 * 获取动作显示文本
 */
function getActionLabel(action: string): string {
  const actionMap: Record<string, string> = {
    sign_in: '每日签到',
    post_create: '发布帖子',
    comment_create: '发表评论',
    like: '点赞',
    share: '分享',
    consultation_complete: '完成咨询',
    document_upload: '上传文档',
    profile_complete: '完善资料',
    invite_friend: '邀请好友',
    exchange_product: '兑换商品',
    bonus: '系统奖励',
  };
  return actionMap[action] || action;
}

/**
 * 获取动作图标颜色
 */
function getActionColor(action: string): string {
  const colorMap: Record<string, string> = {
    sign_in: 'text-yellow-500 bg-yellow-50 dark:bg-yellow-900/20',
    post_create: 'text-blue-500 bg-blue-50 dark:bg-blue-900/20',
    comment_create: 'text-green-500 bg-green-50 dark:bg-green-900/20',
    like: 'text-pink-500 bg-pink-50 dark:bg-pink-900/20',
    share: 'text-purple-500 bg-purple-50 dark:bg-purple-900/20',
    consultation_complete: 'text-indigo-500 bg-indigo-50 dark:bg-indigo-900/20',
    document_upload: 'text-cyan-500 bg-cyan-50 dark:bg-cyan-900/20',
    profile_complete: 'text-teal-500 bg-teal-50 dark:bg-teal-900/20',
    invite_friend: 'text-orange-500 bg-orange-50 dark:bg-orange-900/20',
    exchange_product: 'text-red-500 bg-red-50 dark:bg-red-900/20',
    bonus: 'text-emerald-500 bg-emerald-50 dark:bg-emerald-900/20',
  };
  return colorMap[action] || 'text-gray-500 bg-gray-50 dark:bg-gray-800';
}

/**
 * 积分历史列表组件
 */
export function PointsHistory({
  className = '',
  useSkeleton = true,
  defaultPageSize = 10,
}: PointsHistoryProps): JSX.Element {
  // 分页状态
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(defaultPageSize);

  // 筛选状态
  const [selectedActions, setSelectedActions] = useState<string[]>([]);
  const [dateRange, setDateRange] = useState<DateRange>({ startDate: null, endDate: null });

  // 查询参数
  const queryParams = {
    limit: pageSize,
    offset: (page - 1) * pageSize,
    actionTypes: selectedActions.length > 0 ? selectedActions : undefined,
    startDate: dateRange.startDate?.toISOString().split('T')[0],
    endDate: dateRange.endDate?.toISOString().split('T')[0],
  };

  // 获取数据
  const { data, isLoading, error, refetch } = usePointsHistory(queryParams);

  // 处理分页变化
  const handlePageChange = (newPage: number, newPageSize: number): void => {
    setPage(newPage);
    setPageSize(newPageSize);
  };

  // 清除筛选
  const handleClearFilters = (): void => {
    setSelectedActions([]);
    setDateRange({ startDate: null, endDate: null });
    setPage(1);
  };

  // 是否有筛选条件
  const hasFilters = selectedActions.length > 0 || dateRange.startDate !== null;

  if (isLoading && useSkeleton) {
    return (
      <div className={`space-y-3 ${className}`}>
        {/* 筛选骨架 */}
        <div className="flex flex-wrap gap-3 mb-4">
          <Skeleton width={150} height={36} rounded="lg" />
          <Skeleton width={200} height={36} rounded="lg" />
        </div>
        {/* 列表骨架 */}
        {Array.from({ length: 5 }).map((_, index) => (
          <ListItemSkeleton
            key={index}
            avatar={false}
            lines={1}
            className="bg-white rounded-lg border dark:bg-gray-800 dark:border-gray-700"
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
          description="无法获取积分历史记录"
          onRetry={() => { void refetch(); }}
        />
      </div>
    );
  }

  const history = data?.history ?? [];
  const total = data?.total ?? 0;

  return (
    <div className={className}>
      {/* 筛选栏 */}
      <div className="flex flex-wrap items-center gap-3 mb-4">
        <FilterDropdown
          label="类型"
          placeholder="全部类型"
          multiple
          searchable
          options={actionOptions}
          value={selectedActions}
          onChange={(value) => {
            setSelectedActions(value);
            setPage(1);
          }}
        />

        <DateRangePicker
          value={dateRange}
          onChange={(range) => {
            setDateRange(range);
            setPage(1);
          }}
          placeholder="选择日期范围"
          showPresets
        />

        {/* 清除筛选按钮 */}
        {hasFilters && (
          <button
            onClick={handleClearFilters}
            className="px-3 py-2 text-sm font-medium text-gray-600 hover:text-gray-800 hover:bg-gray-100 rounded-lg transition-colors dark:text-gray-400 dark:hover:text-gray-200 dark:hover:bg-gray-700"
          >
            清除筛选
          </button>
        )}
      </div>

      {/* 数据列表 */}
      {history.length === 0 ? (
        <EmptyState
          icon="document"
          title="暂无积分记录"
          description={hasFilters ? '没有找到符合条件的记录，尝试调整筛选条件' : '完成积分任务后将在这里显示'}
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
          {history.map((transaction: PointsTransaction) => (
            <div
              key={transaction.id}
              className="flex items-center justify-between p-4 bg-white rounded-lg border hover:shadow-sm transition-shadow dark:bg-gray-800 dark:border-gray-700"
            >
              <div className="flex items-center gap-3 flex-1 min-w-0">
                {/* 动作图标 */}
                <div className={`w-10 h-10 rounded-full flex items-center justify-center ${getActionColor(transaction.action)}`}>
                  <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                    {transaction.points >= 0 ? (
                      <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm1-11a1 1 0 10-2 0v2H7a1 1 0 100 2h2v2a1 1 0 102 0v-2h2a1 1 0 100-2h-2V7z" clipRule="evenodd" />
                    ) : (
                      <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM7 9a1 1 0 000 2h6a1 1 0 100-2H7z" clipRule="evenodd" />
                    )}
                  </svg>
                </div>

                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 flex-wrap">
                    <span className="font-medium text-gray-900 dark:text-gray-100">
                      {getActionLabel(transaction.action)}
                    </span>
                    {transaction.description && (
                      <span className="text-sm text-gray-500 dark:text-gray-400 truncate max-w-[200px]">
                        {transaction.description}
                      </span>
                    )}
                  </div>
                  <div className="text-sm text-gray-400 dark:text-gray-500 mt-0.5">
                    {formatDate(transaction.createdAt)}
                  </div>
                </div>
              </div>

              <div className="flex items-center gap-4 text-right">
                <span className={`text-lg font-bold ${transaction.points >= 0 ? 'text-green-500' : 'text-red-500'}`}>
                  {transaction.points >= 0 ? '+' : ''}{transaction.points}
                </span>
                <span className="text-sm text-gray-400 dark:text-gray-500 min-w-[60px]">
                  余: {transaction.balanceAfter}
                </span>
              </div>
            </div>
          ))}
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

export default PointsHistory;