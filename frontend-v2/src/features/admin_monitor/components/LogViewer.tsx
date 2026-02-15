/**
 * LogViewer 组件 - 日志查看器
 * 用于查看系统日志信息
 */

import { useState, useMemo, useRef } from 'react';

import type { LogEntry, LogLevel, LogFilters } from '../types';

// ==================== 图标组件 ====================

const Icons = {
  Search: ({ className }: { className?: string }) => (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="11" cy="11" r="8" />
      <path d="m21 21-4.35-4.35" />
    </svg>
  ),
  Filter: ({ className }: { className?: string }) => (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <polygon points="22 3 2 3 10 12.46 10 19 14 21 14 12.46 22 3" />
    </svg>
  ),
  Download: ({ className }: { className?: string }) => (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
      <polyline points="7 10 12 15 17 10" />
      <line x1="12" y1="15" x2="12" y2="3" />
    </svg>
  ),
  RefreshCw: ({ className }: { className?: string }) => (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M21 12a9 9 0 0 0-9-9 9.75 9.75 0 0 0-6.74 2.74L3 8" />
      <path d="M3 3v5h5" />
      <path d="M3 12a9 9 0 0 0 9 9 9.75 9.75 0 0 0 6.74-2.74L21 16" />
      <path d="M16 16h5v5" />
    </svg>
  ),
  ChevronDown: ({ className }: { className?: string }) => (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <polyline points="6 9 12 15 18 9" />
    </svg>
  ),
  FileText: ({ className }: { className?: string }) => (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M14.5 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7.5L14.5 2z" />
      <polyline points="14 2 14 8 20 8" />
    </svg>
  ),
  AlertCircle: ({ className }: { className?: string }) => (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="12" cy="12" r="10" />
      <line x1="12" y1="8" x2="12" y2="12" />
      <line x1="12" y1="16" x2="12.01" y2="16" />
    </svg>
  ),
  Info: ({ className }: { className?: string }) => (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="12" cy="12" r="10" />
      <line x1="12" y1="16" x2="12" y2="12" />
      <line x1="12" y1="8" x2="12.01" y2="8" />
    </svg>
  ),
  AlertTriangle: ({ className }: { className?: string }) => (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z" />
      <line x1="12" y1="9" x2="12" y2="13" />
      <line x1="12" y1="17" x2="12.01" y2="17" />
    </svg>
  ),
  XCircle: ({ className }: { className?: string }) => (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="12" cy="12" r="10" />
      <line x1="15" y1="9" x2="9" y2="15" />
      <line x1="9" y1="9" x2="15" y2="15" />
    </svg>
  ),
  Bug: ({ className }: { className?: string }) => (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="m8 2 1.88 1.88" />
      <path d="M14.12 3.88 16 2" />
      <path d="M9 7.13v-1a3.003 3.003 0 1 1 6 0v1" />
      <path d="M12 20c-3.3 0-6-2.7-6-6v-3a4 4 0 0 1 4-4h4a4 4 0 0 1 4 4v3c0 3.3-2.7 6-6 6" />
      <path d="M12 20v-9" />
      <path d="M6.53 9C4.6 8.8 3 7.1 3 5" />
      <path d="M6 13H2" />
      <path d="M3 21c0-2.1 1.7-3.9 3.8-4" />
      <path d="M20.97 5c0 2.1-1.6 3.8-3.5 4" />
      <path d="M22 13h-4" />
      <path d="M17.2 17c2.1.1 3.8 1.9 3.8 4" />
    </svg>
  ),
};

// ==================== 辅助函数 ====================

/**
 * 获取日志级别样式
 */
function getLevelStyles(level: LogLevel): string {
  switch (level) {
    case 'critical':
      return 'bg-red-100 text-red-700 border-red-200';
    case 'error':
      return 'bg-red-50 text-red-600 border-red-100';
    case 'warning':
      return 'bg-yellow-50 text-yellow-600 border-yellow-100';
    case 'debug':
      return 'bg-gray-50 text-gray-600 border-gray-100';
    case 'info':
    default:
      return 'bg-blue-50 text-blue-600 border-blue-100';
  }
}

/**
 * 获取日志级别图标
 */
function getLevelIcon(level: LogLevel): React.ReactNode {
  switch (level) {
    case 'critical':
      return <Icons.XCircle className="h-4 w-4 text-red-500" />;
    case 'error':
      return <Icons.AlertCircle className="h-4 w-4 text-red-500" />;
    case 'warning':
      return <Icons.AlertTriangle className="h-4 w-4 text-yellow-500" />;
    case 'debug':
      return <Icons.Bug className="h-4 w-4 text-gray-500" />;
    case 'info':
    default:
      return <Icons.Info className="h-4 w-4 text-blue-500" />;
  }
}

/**
 * 格式化时间
 */
function formatTimestamp(timestamp: string): string {
  const date = new Date(timestamp);
  return date.toLocaleString('zh-CN', {
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
  });
}

// ==================== 组件Props ====================

interface LogViewerProps {
  logs: LogEntry[];
  onLoadMore?: () => void;
  onFilterChange?: (filters: LogFilters) => void;
  onRefresh?: () => void;
  hasMore?: boolean;
  loading?: boolean;
  total?: number;
  className?: string;
}

// ==================== 主组件 ====================

/**
 * 日志查看器组件
 */
export function LogViewer({
  logs,
  onLoadMore,
  onFilterChange,
  onRefresh,
  hasMore = false,
  loading = false,
  total = 0,
  className = '',
}: LogViewerProps): JSX.Element {
  const [searchQuery, setSearchQuery] = useState('');
  const [levelFilter, setLevelFilter] = useState<LogLevel | 'all'>('all');
  const [sourceFilter, setSourceFilter] = useState('');
  const [expandedLogId, setExpandedLogId] = useState<string | null>(null);
  const logsEndRef = useRef<HTMLDivElement>(null);

  // 应用过滤
  const filteredLogs = useMemo(() => {
    return logs.filter((log) => {
      if (levelFilter !== 'all' && log.level !== levelFilter) {
        return false;
      }
      if (sourceFilter && !log.source.toLowerCase().includes(sourceFilter.toLowerCase())) {
        return false;
      }
      if (searchQuery && !log.message.toLowerCase().includes(searchQuery.toLowerCase())) {
        return false;
      }
      return true;
    });
  }, [logs, levelFilter, sourceFilter, searchQuery]);

  // 触发过滤更新
  const handleFilterUpdate = () => {
    if (onFilterChange) {
      onFilterChange({
        level: levelFilter === 'all' ? undefined : levelFilter,
        source: sourceFilter || undefined,
        search: searchQuery || undefined,
      });
    }
  };

  // 导出日志
  const handleExport = () => {
    const dataStr = JSON.stringify(filteredLogs, null, 2);
    const dataBlob = new Blob([dataStr], { type: 'application/json' });
    const url = URL.createObjectURL(dataBlob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `logs-${new Date().toISOString().split('T')[0]}.json`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  };

  // 切换日志展开状态
  const toggleExpand = (logId: string) => {
    setExpandedLogId(expandedLogId === logId ? null : logId);
  };

  return (
    <div className={`rounded-lg border bg-white shadow-sm ${className}`}>
      {/* 工具栏 */}
      <div className="border-b p-4">
        <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div className="flex items-center gap-2">
            <Icons.FileText className="h-5 w-5 text-gray-500" />
            <h3 className="text-lg font-semibold text-gray-900">系统日志</h3>
            <span className="rounded-full bg-gray-100 px-2 py-0.5 text-xs text-gray-600">
              {total} 条
            </span>
          </div>
          <div className="flex flex-wrap items-center gap-2">
            <button
              onClick={onRefresh}
              disabled={loading}
              className="flex items-center gap-1 rounded-md border border-gray-300 px-3 py-1.5 text-sm text-gray-700 hover:bg-gray-50 disabled:opacity-50"
            >
              <Icons.RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
              刷新
            </button>
            <button
              onClick={handleExport}
              className="flex items-center gap-1 rounded-md border border-gray-300 px-3 py-1.5 text-sm text-gray-700 hover:bg-gray-50"
            >
              <Icons.Download className="h-4 w-4" />
              导出
            </button>
          </div>
        </div>

        {/* 过滤器 */}
        <div className="mt-4 flex flex-wrap items-center gap-3">
          <div className="relative flex-1 min-w-[200px]">
            <Icons.Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-gray-400" />
            <input
              type="text"
              placeholder="搜索日志内容..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              onBlur={handleFilterUpdate}
              onKeyDown={(e) => e.key === 'Enter' && handleFilterUpdate()}
              className="w-full rounded-md border border-gray-300 pl-9 pr-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
            />
          </div>
          <select
            value={levelFilter}
            onChange={(e) => {
              setLevelFilter(e.target.value as LogLevel | 'all');
              setTimeout(handleFilterUpdate, 0);
            }}
            className="rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
          >
            <option value="all">所有级别</option>
            <option value="critical">严重</option>
            <option value="error">错误</option>
            <option value="warning">警告</option>
            <option value="info">信息</option>
            <option value="debug">调试</option>
          </select>
          <input
            type="text"
            placeholder="来源过滤..."
            value={sourceFilter}
            onChange={(e) => setSourceFilter(e.target.value)}
            onBlur={handleFilterUpdate}
            className="rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
          />
        </div>
      </div>

      {/* 日志列表 */}
      <div className="max-h-[500px] overflow-y-auto">
        {filteredLogs.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-16 text-center">
            <Icons.FileText className="h-12 w-12 text-gray-300 mb-3" />
            <p className="text-gray-500">暂无日志</p>
          </div>
        ) : (
          <div className="divide-y divide-gray-100">
            {filteredLogs.map((log) => (
              <div
                key={log.id}
                className={`p-3 transition-colors hover:bg-gray-50 ${
                  expandedLogId === log.id ? 'bg-gray-50' : ''
                }`}
              >
                <div
                  className="flex cursor-pointer items-start gap-3"
                  onClick={() => toggleExpand(log.id)}
                >
                  <div className="mt-0.5 flex-shrink-0">
                    {getLevelIcon(log.level)}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex flex-wrap items-center gap-2">
                      <span
                        className={`rounded px-1.5 py-0.5 text-xs font-medium ${getLevelStyles(
                          log.level
                        )}`}
                      >
                        {log.level.toUpperCase()}
                      </span>
                      <span className="text-xs text-gray-400">
                        {formatTimestamp(log.timestamp)}
                      </span>
                      <span className="rounded bg-gray-100 px-1.5 py-0.5 text-xs text-gray-600">
                        {log.source}
                      </span>
                    </div>
                    <p className="mt-1 text-sm text-gray-700 line-clamp-2">
                      {log.message}
                    </p>
                  </div>
                  <Icons.ChevronDown
                    className={`h-4 w-4 text-gray-400 transition-transform ${
                      expandedLogId === log.id ? 'rotate-180' : ''
                    }`}
                  />
                </div>

                {/* 展开的详细信息 */}
                {expandedLogId === log.id && log.metadata && (
                  <div className="mt-3 rounded-md bg-gray-100 p-3">
                    <p className="mb-2 text-xs font-medium text-gray-500">详细信息:</p>
                    <pre className="overflow-x-auto text-xs text-gray-700">
                      {JSON.stringify(log.metadata, null, 2)}
                    </pre>
                  </div>
                )}
              </div>
            ))}
            <div ref={logsEndRef} />
          </div>
        )}

        {/* 加载更多 */}
        {hasMore && (
          <div className="border-t p-4 text-center">
            <button
              onClick={onLoadMore}
              disabled={loading}
              className="rounded-md border border-gray-300 px-4 py-2 text-sm text-gray-700 hover:bg-gray-50 disabled:opacity-50"
            >
              {loading ? '加载中...' : '加载更多'}
            </button>
          </div>
        )}
      </div>
    </div>
  );
}

/**
 * 日志统计组件
 */
export function LogStats({
  logs,
  className = '',
}: {
  logs: LogEntry[];
  className?: string;
}): JSX.Element {
  const stats = useMemo(() => {
    const counts: Record<LogLevel, number> = {
      debug: 0,
      info: 0,
      warning: 0,
      error: 0,
      critical: 0,
    };

    logs.forEach((log) => {
      if (counts[log.level] !== undefined) {
        counts[log.level]++;
      }
    });

    return counts;
  }, [logs]);

  const total = logs.length;

  return (
    <div className={`rounded-lg border bg-white p-4 shadow-sm ${className}`}>
      <h4 className="mb-3 font-medium text-gray-900">日志统计</h4>
      <div className="grid grid-cols-5 gap-2">
        <div className="rounded-lg bg-gray-50 p-2 text-center">
          <div className="text-lg font-bold text-gray-700">{total}</div>
          <div className="text-xs text-gray-500">总计</div>
        </div>
        <div className="rounded-lg bg-blue-50 p-2 text-center">
          <div className="text-lg font-bold text-blue-600">{stats.info}</div>
          <div className="text-xs text-blue-500">信息</div>
        </div>
        <div className="rounded-lg bg-yellow-50 p-2 text-center">
          <div className="text-lg font-bold text-yellow-600">{stats.warning}</div>
          <div className="text-xs text-yellow-500">警告</div>
        </div>
        <div className="rounded-lg bg-red-50 p-2 text-center">
          <div className="text-lg font-bold text-red-600">{stats.error}</div>
          <div className="text-xs text-red-500">错误</div>
        </div>
        <div className="rounded-lg bg-red-100 p-2 text-center">
          <div className="text-lg font-bold text-red-700">{stats.critical}</div>
          <div className="text-xs text-red-600">严重</div>
        </div>
      </div>
    </div>
  );
}