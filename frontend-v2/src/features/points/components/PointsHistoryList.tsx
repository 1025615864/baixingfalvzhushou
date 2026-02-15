/**
 * PointsHistoryList - 积分变动历史列表组件
 *
 * 展示积分获取/消耗历史记录列表，支持分页加载
 */

import { useState } from 'react';

import { usePointsHistory } from '../hooks/usePoints';
import { Pagination } from '../../../components/ui/Pagination';
import { ListItemSkeleton } from '../../../components/ui/Skeleton';
import { EmptyState, EmptyError } from '../../../components/ui/EmptyState';
import type { PointsTransaction } from '../types';

/**
 * 积分历史项类型
 * 扩展 PointsTransaction，添加 balance 字段用于显示变动后余额
 */
export interface PointsHistoryItem {
  /** 记录ID */
  id: string;
  /** 动作类型 */
  action: string;
  /** 积分变动值（正数为获取，负数为消耗） */
  points: number;
  /** 变动描述 */
  description?: string;
  /** 变动时间 */
  createdAt: string;
  /** 变动后余额 */
  balance: number;
}

interface PointsHistoryListProps {
  /** 自定义类名 */
  className?: string;
  /** 是否使用骨架屏加载 */
  useSkeleton?: boolean;
  /** 初始每页条数 */
  defaultPageSize?: number;
}

/**
 * 积分动作显示文本映射
 */
const actionLabelMap: Record<string, string> = {
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

/**
 * 积分动作图标颜色映射（支持暗色模式）
 */
const actionColorMap: Record<string, string> = {
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

/**
 * 获取动作显示文本
 */
function getActionLabel(action: string): string {
  return actionLabelMap[action] || action;
}

/**
 * 获取动作图标颜色
 */
function getActionColor(action: string): string {
  return actionColorMap[action] || 'text-gray-500 bg-gray-50 dark:bg-gray-800';
}

/**
 * 格式化日期时间
 */
function formatDateTime(dateString: string): string {
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
 * 积分变动历史列表组件
 */
export function PointsHistoryList({
  className = '',
  useSkeleton = true,
  defaultPageSize = 10,
}: PointsHistoryListProps): JSX.Element {
  // 分页状态
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(defaultPageSize);

  // 查询参数
  const queryParams = {
    limit: pageSize,
    offset: (page - 1) * pageSize,
  };

  // 获取数据
  const { data, isLoading, error, refetch } = usePointsHistory(queryParams);

  // 处理分页变化
  const handlePageChange = (newPage: number, newPageSize: number): void => {
    setPage(newPage);
    setPageSize(newPageSize);
  };

  // 骨架屏加载状态
  if (isLoading && useSkeleton) {
    return (
      <div className={`space-y-3 ${className}`}>
        {/* 列表骨架 */}
        {Array.from({ length: pageSize }).map((_, index) => (
          <ListItemSkeleton
            key={index}
            avatar={false}
            lines={2}
            className="bg-white rounded-lg border dark:bg-gray-800 dark:border-gray-700"
          />
        ))}
      </div>
    );
  }

  // 错误状态
  if (error) {
    return (
      <div className={className}>
        <EmptyError
          title="加载失败"
          description="无法获取积分历史记录，请稍后重试"
          onRetry={() => { void refetch(); }}
        />
      </div>
    );
  }

  const history: PointsHistoryItem[] = (data?.history ?? []).map((item: PointsTransaction) => ({
    id: item.id,
    action: item.action,
    points: item.points,
    description: item.description,
    createdAt: item.createdAt,
    balance: item.balanceAfter,
  }));

  const total = data?.total ?? 0;

  // 空状态
  if (history.length === 0) {
    return (
      <div className={className}>
        <EmptyState
          icon="document"
          title="暂无积分记录"
          description="完成积分任务后将在这里显示您的积分变动记录"
          size="md"
        />
      </div>
    );
  }

  return (
    <div className={className}>
      {/* 数据列表 */}
      <div className="space-y-2 mb-4">
        {history.map((item: PointsHistoryItem) => (
          <div
            key={item.id}
            className="flex items-center justify-between p-4 bg-white rounded-lg border hover:shadow-sm transition-shadow dark:bg-gray-800 dark:border-gray-700"
          >
            {/* 左侧：类型和描述 */}
            <div className="flex items-center gap-3 flex-1 min-w-0">
              {/* 动作图标 */}
              <div className={`w-10 h-10 rounded-full flex items-center justify-center flex-shrink-0 ${getActionColor(item.action)}`}>
                <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                  {item.points >= 0 ? (
                    <path
                      fillRule="evenodd"
                      d="M10 18a8 8 0 100-16 8 8 0 000 16zm1-11a1 1 0 10-2 0v2H7a1 1 0 100 2h2v2a1 1 0 102 0v-2h2a1 1 0 100-2h-2V7z"
                      clipRule="evenodd"
                    />
                  ) : (
                    <path
                      fillRule="evenodd"
                      d="M10 18a8 8 0 100-16 8 8 0 000 16zM7 9a1 1 0 000 2h6a1 1 0 100-2H7z"
                      clipRule="evenodd"
                    />
                  )}
                </svg>
              </div>

              {/* 类型和描述 */}
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 flex-wrap">
                  <span className="font-medium text-gray-900 dark:text-gray-100">
                    {getActionLabel(item.action)}
                  </span>
                  {item.description && (
                    <span className="text-sm text-gray-500 dark:text-gray-400 truncate max-w-[200px]">
                      {item.description}
                    </span>
                  )}
                </div>
                <div className="text-sm text-gray-400 dark:text-gray-500 mt-0.5">
                  {formatDateTime(item.createdAt)}
                </div>
              </div>
            </div>

            {/* 右侧：积分变动和余额 */}
            <div className="flex items-center gap-4 text-right flex-shrink-0">
              {/* 积分变动 */}
              <span className={`text-lg font-bold ${item.points >= 0 ? 'text-green-500' : 'text-red-500'}`}>
                {item.points >= 0 ? '+' : ''}{item.points}
              </span>
              {/* 变动后余额 */}
              <span className="text-sm text-gray-400 dark:text-gray-500 min-w-[60px]">
                余额: {item.balance}
              </span>
            </div>
          </div>
        ))}
      </div>

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

export default PointsHistoryList;