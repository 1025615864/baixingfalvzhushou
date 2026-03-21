/**
 * VideoConsultationList - 视频咨询列表组件
 * 展示用户的视频咨询列表，支持状态筛选
 */

import { useState } from 'react';
import { Video, Calendar, Filter, RefreshCw } from 'lucide-react';

import { Button } from '@/components/ui/Button';

import { useVideoConsultations, useCancelVideoConsultation } from '../hooks/useVideoConsultation';
import type { VideoConsultation } from '../types';

import { VideoConsultationCard } from './VideoConsultationCard';


// 状态筛选选项
const STATUS_FILTERS: Array<{ value: string; label: string; variant: 'default' | 'primary' | 'success' | 'warning' | 'danger' }> = [
  { value: '', label: '全部', variant: 'default' },
  { value: 'pending', label: '待确认', variant: 'warning' },
  { value: 'confirmed', label: '已确认', variant: 'primary' },
  { value: 'in_progress', label: '进行中', variant: 'success' },
  { value: 'completed', label: '已完成', variant: 'default' },
  { value: 'cancelled', label: '已取消', variant: 'danger' },
];

const SKELETON_COUNT = 3;

interface VideoConsultationListProps {
  onSelect?: (consultation: VideoConsultation) => void;
  onJoin?: (consultation: VideoConsultation) => void;
  defaultStatus?: string;
  showFilters?: boolean;
  pageSize?: number;
}

export function VideoConsultationList({
  onSelect,
  onJoin,
  defaultStatus = '',
  showFilters = true,
  pageSize = 10,
}: VideoConsultationListProps): JSX.Element {
  const [statusFilter, setStatusFilter] = useState(defaultStatus);
  const [page, setPage] = useState(1);

  const { data, isLoading, isError, refetch, isRefetching } = useVideoConsultations({
    status: statusFilter || undefined,
    page,
    pageSize,
  });

  const cancelMutation = useCancelVideoConsultation();

  const handleCancel = (consultation: VideoConsultation): void => {
    const confirmed = window.confirm('确定要取消此预约吗？取消后可能无法恢复。');
    if (confirmed) {
      cancelMutation.mutate(consultation.id);
    }
  };

  const handleRefresh = (): void => {
    void refetch();
  };

  // 加载骨架屏
  if (isLoading) {
    return (
      <div className="space-y-4">
        {showFilters && (
          <div className="flex items-center gap-2 mb-4">
            <div className="h-8 w-16 bg-gray-200 rounded animate-pulse" />
            <div className="h-8 w-20 bg-gray-200 rounded animate-pulse" />
            <div className="h-8 w-16 bg-gray-200 rounded animate-pulse" />
          </div>
        )}
        {Array.from({ length: SKELETON_COUNT }, (_, index) => (
          <div
            key={index}
            className="bg-white rounded-lg shadow-sm border border-gray-200 p-4 animate-pulse"
          >
            <div className="flex items-start justify-between mb-3">
              <div className="h-6 bg-gray-200 rounded w-2/3" />
              <div className="h-6 w-16 bg-gray-200 rounded-full" />
            </div>
            <div className="space-y-2">
              <div className="h-4 bg-gray-200 rounded w-1/3" />
              <div className="h-4 bg-gray-200 rounded w-1/2" />
              <div className="h-4 bg-gray-200 rounded w-1/4" />
            </div>
          </div>
        ))}
      </div>
    );
  }

  // 错误状态
  if (isError) {
    return (
      <div className="text-center py-12 bg-white rounded-lg border border-gray-200">
        <Video className="w-12 h-12 text-gray-300 mx-auto mb-4" />
        <p className="text-red-600 mb-4">加载视频咨询列表失败</p>
        <Button variant="outline" onClick={handleRefresh}>
          <RefreshCw className="w-4 h-4 mr-2" />
          重新加载
        </Button>
      </div>
    );
  }

  const items = data?.items ?? [];
  const total = data?.total ?? 0;
  const totalPages = Math.ceil(total / pageSize);

  // 空状态
  if (items.length === 0) {
    return (
      <div className="space-y-4">
        {showFilters && (
          <StatusFilterTabs
            filters={STATUS_FILTERS}
            activeFilter={statusFilter}
            onFilterChange={(filter) => {
              setStatusFilter(filter);
              setPage(1);
            }}
          />
        )}
        <div className="text-center py-12 bg-white rounded-lg border border-gray-200">
          <Calendar className="w-12 h-12 text-gray-300 mx-auto mb-4" />
          <p className="text-gray-500 mb-2">暂无视频咨询记录</p>
          <p className="text-sm text-gray-400">
            {statusFilter ? '当前筛选条件下没有记录，试试其他筛选条件' : '预约视频咨询，与律师面对面沟通'}
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* 筛选器 */}
      {showFilters && (
        <div className="flex items-center justify-between">
          <StatusFilterTabs
            filters={STATUS_FILTERS}
            activeFilter={statusFilter}
            onFilterChange={(filter) => {
              setStatusFilter(filter);
              setPage(1);
            }}
          />
          <Button
            variant="ghost"
            size="sm"
            onClick={handleRefresh}
            isLoading={isRefetching}
            leftIcon={<RefreshCw className="w-4 h-4" />}
          >
            刷新
          </Button>
        </div>
      )}

      {/* 列表 */}
      <div className="space-y-4">
        {items.map((consultation) => (
          <VideoConsultationCard
            key={consultation.id}
            consultation={consultation}
            onClick={() => onSelect?.(consultation)}
            onJoin={() => onJoin?.(consultation)}
            onCancel={() => handleCancel(consultation)}
            loading={cancelMutation.isPending}
          />
        ))}
      </div>

      {/* 分页 */}
      {totalPages > 1 && (
        <div className="flex items-center justify-center gap-2 pt-4">
          <Button
            variant="outline"
            size="sm"
            onClick={() => setPage((p) => Math.max(1, p - 1))}
            disabled={page <= 1}
          >
            上一页
          </Button>
          <span className="text-sm text-gray-500">
            第 {page} / {totalPages} 页
          </span>
          <Button
            variant="outline"
            size="sm"
            onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
            disabled={page >= totalPages}
          >
            下一页
          </Button>
        </div>
      )}

      {/* 统计信息 */}
      <div className="text-center text-sm text-gray-400">
        共 {total} 条记录
      </div>
    </div>
  );
}

// 状态筛选标签组件
interface StatusFilterTabsProps {
  filters: Array<{ value: string; label: string; variant: 'default' | 'primary' | 'success' | 'warning' | 'danger' }>;
  activeFilter: string;
  onFilterChange: (value: string) => void;
}

function StatusFilterTabs({ filters, activeFilter, onFilterChange }: StatusFilterTabsProps): JSX.Element {
  return (
    <div className="flex items-center gap-2 overflow-x-auto pb-2">
      <Filter className="w-4 h-4 text-gray-400 flex-shrink-0" />
      {filters.map((filter) => (
        <button
          key={filter.value}
          onClick={() => onFilterChange(filter.value)}
          className={`
            px-3 py-1.5 text-sm font-medium rounded-full whitespace-nowrap transition-all
            ${activeFilter === filter.value
              ? 'bg-primary-600 text-white shadow-sm'
              : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
            }
          `}
        >
          {filter.label}
        </button>
      ))}
    </div>
  );
}