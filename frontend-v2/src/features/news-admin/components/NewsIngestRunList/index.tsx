/**
 * News Ingest Run List Component
 * 抓取运行记录列表组件
 */

import { useMemo, useState } from 'react';
import { Calendar, Filter, RefreshCw } from 'lucide-react';

import { Badge } from '@/components/ui/Badge';
import { Button } from '@/components/ui/Button';
import { Card } from '@/components/ui/Card';
import { Pagination } from '@/components/ui/Pagination';

import { useNewsSources } from '../../hooks/useNewsSources';
import { useNewsIngestRuns } from '../../hooks/useNewsIngestRuns';
import type { NewsIngestRun, GetIngestRunsRequest, IngestRunStatus } from '../../types';

const STATUS_OPTIONS: { value: IngestRunStatus | ''; label: string }[] = [
  { value: '', label: '全部' },
  { value: 'running', label: '运行中' },
  { value: 'success', label: '成功' },
  { value: 'failed', label: '失败' },
];

interface StatusBadgeProps {
  status: NewsIngestRun['status'];
}

function StatusBadge({ status }: StatusBadgeProps): JSX.Element {
  const config = useMemo(() => {
    switch (status) {
      case 'success':
        return { label: '成功', variant: 'success' as const };
      case 'running':
        return { label: '运行中', variant: 'warning' as const };
      case 'failed':
        return { label: '失败', variant: 'danger' as const };
      default:
        return { label: status, variant: 'default' as const };
    }
  }, [status]);

  return <Badge variant={config.variant}>{config.label}</Badge>;
}

interface NewsIngestRunListProps {
  initialFilters?: Partial<GetIngestRunsRequest>;
}

export function NewsIngestRunList({ initialFilters }: NewsIngestRunListProps): JSX.Element {
  const [filters, setFilters] = useState<GetIngestRunsRequest>({
    page: 1,
    pageSize: 20,
    ...initialFilters,
  });

  const { data: sources, isLoading: isSourcesLoading } = useNewsSources();
  const { data: runsData, isLoading: isRunsLoading, refetch } = useNewsIngestRuns(filters);

  const handleFilterChange = <K extends keyof GetIngestRunsRequest>(
    key: K,
    value: GetIngestRunsRequest[K]
  ) => {
    setFilters((prev) => ({
      ...prev,
      [key]: value,
      page: 1, // 重置页码
    }));
  };

  const handleClearFilters = () => {
    setFilters({
      page: 1,
      pageSize: 20,
    });
  };

  const hasActiveFilters = filters.sourceId || filters.status || filters.from || filters.to;

  return (
    <div className="space-y-6">
      {/* 过滤器 */}
      <Card>
        <div className="flex flex-wrap gap-4 items-end">
          <div className="flex items-center gap-2">
            <Filter className="h-4 w-4 text-slate-500" />
            <span className="text-slate-700 text-sm">筛选：</span>
          </div>

          <div className="min-w-[220px]">
            <label className="block text-sm font-medium text-slate-700 mb-2">来源</label>
            <select
              value={filters.sourceId || ''}
              onChange={(e) =>
                handleFilterChange(
                  'sourceId',
                  e.target.value ? Number(e.target.value) : undefined
                )
              }
              className="w-full px-3 py-2 rounded-lg border border-slate-200 bg-white text-sm"
              disabled={isSourcesLoading}
            >
              <option value="">全部来源</option>
              {sources?.map((source) => (
                <option key={source.id} value={source.id}>
                  {source.name} {source.isEnabled ? '' : '(停用)'}
                </option>
              ))}
            </select>
          </div>

          <div className="min-w-[160px]">
            <label className="block text-sm font-medium text-slate-700 mb-2">状态</label>
            <select
              value={filters.status || ''}
              onChange={(e) =>
                handleFilterChange(
                  'status',
                  (e.target.value as IngestRunStatus) || undefined
                )
              }
              className="w-full px-3 py-2 rounded-lg border border-slate-200 bg-white text-sm"
            >
              {STATUS_OPTIONS.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </div>

          <div className="min-w-[220px]">
            <label className="block text-sm font-medium text-slate-700 mb-2">
              开始时间
            </label>
            <div className="relative">
              <input
                type="datetime-local"
                value={filters.from || ''}
                onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
                  handleFilterChange('from', e.target.value || undefined)
                }
                className="w-full px-3 py-2 pr-10 rounded-lg border border-slate-200 bg-white text-sm"
              />
              <Calendar className="absolute right-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400 pointer-events-none" />
            </div>
          </div>

          <div className="min-w-[220px]">
            <label className="block text-sm font-medium text-slate-700 mb-2">
              结束时间
            </label>
            <div className="relative">
              <input
                type="datetime-local"
                value={filters.to || ''}
                onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
                  handleFilterChange('to', e.target.value || undefined)
                }
                className="w-full px-3 py-2 pr-10 rounded-lg border border-slate-200 bg-white text-sm"
              />
              <Calendar className="absolute right-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400 pointer-events-none" />
            </div>
          </div>

          {hasActiveFilters && (
            <Button variant="ghost" size="sm" onClick={handleClearFilters}>
              清除筛选
            </Button>
          )}

          <Button
            variant="outline"
            onClick={(): void => {
              void refetch();
            }}
            disabled={isRunsLoading}
          >
            <RefreshCw className={`h-4 w-4 mr-2 ${isRunsLoading ? 'animate-spin' : ''}`} />
            刷新
          </Button>
        </div>
      </Card>

      {/* 数据表格 */}
      <Card>
        {isRunsLoading ? (
          <div className="p-6">
            <div className="space-y-3">
              {Array.from({ length: 6 }).map((_, index) => (
                <div key={index} className="h-16 bg-slate-100 rounded animate-pulse" />
              ))}
            </div>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-slate-200">
                  <th className="text-left py-3 px-4 text-slate-500 text-sm font-medium">时间</th>
                  <th className="text-left py-3 px-4 text-slate-500 text-sm font-medium">来源</th>
                  <th className="text-left py-3 px-4 text-slate-500 text-sm font-medium">状态</th>
                  <th className="text-left py-3 px-4 text-slate-500 text-sm font-medium">统计</th>
                  <th className="text-left py-3 px-4 text-slate-500 text-sm font-medium">错误</th>
                </tr>
              </thead>
              <tbody>
                {runsData?.items.map((run) => (
                  <NewsIngestRunRow key={run.id} run={run} />
                ))}
                {!runsData?.items.length && (
                  <tr>
                    <td colSpan={5} className="py-10 text-center text-slate-500 text-sm">
                      暂无运行记录
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        )}

        {runsData && runsData.total > 0 && (
          <Pagination
            currentPage={filters.page || 1}
            totalPages={Math.ceil(runsData.total / (filters.pageSize || 20))}
            onPageChange={(page: number) => handleFilterChange('page', page)}
          />
        )}
      </Card>
    </div>
  );
}

interface NewsIngestRunRowProps {
  run: NewsIngestRun;
}

function NewsIngestRunRow({ run }: NewsIngestRunRowProps): JSX.Element {
  return (
    <tr className="border-b border-slate-100 hover:bg-slate-50">
      <td className="py-3 px-4 text-sm text-slate-600">
        <div className="space-y-1">
          <p>开始：{formatDateTime(run.startedAt)}</p>
          {run.finishedAt && <p>结束：{formatDateTime(run.finishedAt)}</p>}
        </div>
      </td>
      <td className="py-3 px-4">
        <div className="space-y-1">
          <p className="text-slate-900 text-sm font-medium">
            {run.sourceName || `源#${run.sourceId ?? '-'}`}
          </p>
          {run.feedUrl && <p className="text-xs text-slate-500 break-all">{run.feedUrl}</p>}
        </div>
      </td>
      <td className="py-3 px-4">
        <StatusBadge status={run.status} />
      </td>
      <td className="py-3 px-4">
        <div className="flex flex-wrap gap-2">
          <Badge variant="primary" size="sm">
            获取: {run.fetched}
          </Badge>
          <Badge variant="success" size="sm">
            插入: {run.inserted}
          </Badge>
          <Badge variant="default" size="sm">
            跳过: {run.skipped}
          </Badge>
          <Badge variant={run.errors > 0 ? 'danger' : 'default'} size="sm">
            错误: {run.errors}
          </Badge>
        </div>
      </td>
      <td className="py-3 px-4 text-sm">
        {run.lastError ? (
          <p className="text-red-500 break-words max-w-[400px]">{run.lastError}</p>
        ) : (
          <span className="text-slate-400">-</span>
        )}
      </td>
    </tr>
  );
}

function formatDateTime(value: string | null): string {
  if (!value) return '-';
  return new Date(value).toLocaleString('zh-CN');
}
