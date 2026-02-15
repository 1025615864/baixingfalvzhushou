/**
 * AlertList 组件 - 告警列表
 * 用于展示系统监控告警信息
 */

import { useState, useMemo } from 'react';

import type { AlertItem, AlertLevel } from '../types';

// ==================== 图标组件 ====================

const Icons = {
  AlertCircle: ({ className }: { className?: string }) => (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="12" cy="12" r="10" />
      <line x1="12" y1="8" x2="12" y2="12" />
      <line x1="12" y1="16" x2="12.01" y2="16" />
    </svg>
  ),
  AlertTriangle: ({ className }: { className?: string }) => (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z" />
      <line x1="12" y1="9" x2="12" y2="13" />
      <line x1="12" y1="17" x2="12.01" y2="17" />
    </svg>
  ),
  Info: ({ className }: { className?: string }) => (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="12" cy="12" r="10" />
      <line x1="12" y1="16" x2="12" y2="12" />
      <line x1="12" y1="8" x2="12.01" y2="8" />
    </svg>
  ),
  XCircle: ({ className }: { className?: string }) => (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="12" cy="12" r="10" />
      <line x1="15" y1="9" x2="9" y2="15" />
      <line x1="9" y1="9" x2="15" y2="15" />
    </svg>
  ),
  CheckCircle: ({ className }: { className?: string }) => (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14" />
      <polyline points="22 4 12 14.01 9 11.01" />
    </svg>
  ),
  Filter: ({ className }: { className?: string }) => (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <polygon points="22 3 2 3 10 12.46 10 19 14 21 14 12.46 22 3" />
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
  Clock: ({ className }: { className?: string }) => (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="12" cy="12" r="10" />
      <polyline points="12 6 12 12 16 14" />
    </svg>
  ),
};

// ==================== 辅助函数 ====================

/**
 * 格式化时间
 */
function formatTime(timestamp: string): string {
  const date = new Date(timestamp);
  const now = new Date();
  const diff = now.getTime() - date.getTime();

  // 小于1分钟
  if (diff < 60 * 1000) {
    return '刚刚';
  }
  // 小于1小时
  if (diff < 60 * 60 * 1000) {
    return `${Math.floor(diff / (60 * 1000))}分钟前`;
  }
  // 小于24小时
  if (diff < 24 * 60 * 60 * 1000) {
    return `${Math.floor(diff / (60 * 60 * 1000))}小时前`;
  }
  // 小于7天
  if (diff < 7 * 24 * 60 * 60 * 1000) {
    return `${Math.floor(diff / (24 * 60 * 60 * 1000))}天前`;
  }

  return date.toLocaleDateString('zh-CN');
}

/**
 * 获取告警级别图标
 */
function getAlertIcon(level: AlertLevel): React.ReactNode {
  switch (level) {
    case 'critical':
      return <Icons.AlertCircle className="h-5 w-5 text-red-500" />;
    case 'error':
      return <Icons.AlertCircle className="h-5 w-5 text-orange-500" />;
    case 'warning':
      return <Icons.AlertTriangle className="h-5 w-5 text-yellow-500" />;
    case 'info':
    default:
      return <Icons.Info className="h-5 w-5 text-blue-500" />;
  }
}

/**
 * 获取告警级别样式
 */
function getAlertLevelStyles(level: AlertLevel): string {
  switch (level) {
    case 'critical':
      return 'border-l-4 border-red-500 bg-red-50';
    case 'error':
      return 'border-l-4 border-orange-500 bg-orange-50';
    case 'warning':
      return 'border-l-4 border-yellow-500 bg-yellow-50';
    case 'info':
    default:
      return 'border-l-4 border-blue-500 bg-blue-50';
  }
}

/**
 * 获取告警级别标签
 */
function getAlertLevelLabel(level: AlertLevel): string {
  switch (level) {
    case 'critical':
      return '严重';
    case 'error':
      return '错误';
    case 'warning':
      return '警告';
    case 'info':
    default:
      return '信息';
  }
}

// ==================== 组件接口 ====================

interface AlertListProps {
  alerts: AlertItem[];
  onResolve?: (alertId: string) => void;
  onDismiss?: (alertId: string) => void;
  loading?: boolean;
  showFilters?: boolean;
  maxHeight?: string;
  className?: string;
}

// ==================== 主组件 ====================

/**
 * 告警列表组件
 */
export function AlertList({
  alerts,
  onResolve,
  onDismiss,
  loading = false,
  showFilters = true,
  maxHeight = '400px',
  className = '',
}: AlertListProps): JSX.Element {
  const [levelFilter, setLevelFilter] = useState<AlertLevel | 'all'>('all');
  const [resolvedFilter, setResolvedFilter] = useState<'all' | 'resolved' | 'unresolved'>('unresolved');

  // 过滤告警
  const filteredAlerts = useMemo(() => {
    return alerts.filter((alert) => {
      // 级别过滤
      if (levelFilter !== 'all' && alert.level !== levelFilter) {
        return false;
      }
      // 解决状态过滤
      if (resolvedFilter === 'resolved' && !alert.resolved) {
        return false;
      }
      if (resolvedFilter === 'unresolved' && alert.resolved) {
        return false;
      }
      return true;
    });
  }, [alerts, levelFilter, resolvedFilter]);

  // 统计数量
  const stats = useMemo(() => {
    const total = alerts.length;
    const critical = alerts.filter((a) => a.level === 'critical' && !a.resolved).length;
    const error = alerts.filter((a) => a.level === 'error' && !a.resolved).length;
    const warning = alerts.filter((a) => a.level === 'warning' && !a.resolved).length;

    return { total, critical, error, warning };
  }, [alerts]);

  if (loading) {
    return (
      <div className={`rounded-lg border bg-white shadow-sm ${className}`}>
        <div className="border-b p-4">
          <div className="h-6 w-32 rounded bg-gray-200 animate-pulse" />
        </div>
        <div className="p-4 space-y-3">
          {[1, 2, 3].map((i) => (
            <div key={i} className="h-20 rounded bg-gray-100 animate-pulse" />
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className={`rounded-lg border bg-white shadow-sm ${className}`}>
      {/* 头部 */}
      <div className="border-b p-4">
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-semibold text-gray-900">系统告警</h3>
          <div className="flex items-center gap-2">
            {stats.critical > 0 && (
              <span className="rounded-full bg-red-100 px-2 py-0.5 text-xs font-medium text-red-700">
                {stats.critical} 严重
              </span>
            )}
            {stats.error > 0 && (
              <span className="rounded-full bg-orange-100 px-2 py-0.5 text-xs font-medium text-orange-700">
                {stats.error} 错误
              </span>
            )}
            {stats.warning > 0 && (
              <span className="rounded-full bg-yellow-100 px-2 py-0.5 text-xs font-medium text-yellow-700">
                {stats.warning} 警告
              </span>
            )}
            <span className="rounded-full bg-gray-100 px-2 py-0.5 text-xs font-medium text-gray-600">
              共 {stats.total}
            </span>
          </div>
        </div>
      </div>

      {/* 过滤器 */}
      {showFilters && (
        <div className="border-b bg-gray-50 p-3">
          <div className="flex flex-wrap items-center gap-3">
            <div className="flex items-center gap-1 text-sm text-gray-500">
              <Icons.Filter className="h-4 w-4" />
              <span>过滤:</span>
            </div>
            <select
              value={levelFilter}
              onChange={(e) => setLevelFilter(e.target.value as AlertLevel | 'all')}
              className="rounded-md border border-gray-300 px-2 py-1 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
            >
              <option value="all">所有级别</option>
              <option value="critical">严重</option>
              <option value="error">错误</option>
              <option value="warning">警告</option>
              <option value="info">信息</option>
            </select>
            <select
              value={resolvedFilter}
              onChange={(e) => setResolvedFilter(e.target.value as typeof resolvedFilter)}
              className="rounded-md border border-gray-300 px-2 py-1 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
            >
              <option value="unresolved">未解决</option>
              <option value="resolved">已解决</option>
              <option value="all">全部</option>
            </select>
          </div>
        </div>
      )}

      {/* 告警列表 */}
      <div
        className="overflow-y-auto p-2"
        style={{ maxHeight }}
      >
        {filteredAlerts.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-12 text-center">
            <Icons.CheckCircle className="h-12 w-12 text-green-500 mb-3" />
            <p className="text-gray-500">暂无符合条件的告警</p>
          </div>
        ) : (
          <div className="space-y-2">
            {filteredAlerts.map((alert, index) => (
              <div
                key={`${alert.ruleName}-${index}`}
                className={`rounded-r-lg p-3 transition-all hover:shadow-sm ${getAlertLevelStyles(alert.level)} ${
                  alert.resolved ? 'opacity-50' : ''
                }`}
              >
                <div className="flex items-start gap-3">
                  <div className="mt-0.5 flex-shrink-0">
                    {getAlertIcon(alert.level)}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <span className="text-sm font-medium text-gray-900">
                        {alert.ruleName}
                      </span>
                      <span
                        className={`rounded px-1.5 py-0.5 text-xs font-medium ${
                          alert.level === 'critical'
                            ? 'bg-red-100 text-red-700'
                            : alert.level === 'error'
                              ? 'bg-orange-100 text-orange-700'
                              : alert.level === 'warning'
                                ? 'bg-yellow-100 text-yellow-700'
                                : 'bg-blue-100 text-blue-700'
                        }`}
                      >
                        {getAlertLevelLabel(alert.level)}
                      </span>
                      {alert.resolved && (
                        <span className="rounded bg-green-100 px-1.5 py-0.5 text-xs font-medium text-green-700">
                          已解决
                        </span>
                      )}
                    </div>
                    <p className="mt-1 text-sm text-gray-600">{alert.message}</p>
                    <div className="mt-2 flex items-center gap-3 text-xs text-gray-400">
                      <span className="flex items-center gap-1">
                        <Icons.Clock className="h-3 w-3" />
                        {formatTime(alert.timestamp)}
                      </span>
                    </div>
                  </div>
                  <div className="flex flex-shrink-0 gap-1">
                    {!alert.resolved && onResolve && (
                      <button
                        onClick={() => onResolve(`${alert.ruleName}-${index}`)}
                        className="rounded p-1 text-gray-400 hover:bg-green-100 hover:text-green-600"
                        title="标记为已解决"
                      >
                        <Icons.CheckCircle className="h-4 w-4" />
                      </button>
                    )}
                    {onDismiss && (
                      <button
                        onClick={() => onDismiss(`${alert.ruleName}-${index}`)}
                        className="rounded p-1 text-gray-400 hover:bg-red-100 hover:text-red-600"
                        title="忽略"
                      >
                        <Icons.XCircle className="h-4 w-4" />
                      </button>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

/**
 * 告警摘要组件
 */
export function AlertSummary({
  alerts,
  onViewAll,
  className = '',
}: {
  alerts: AlertItem[];
  onViewAll?: () => void;
  className?: string;
}): JSX.Element {
  const stats = useMemo(() => {
    const unresolved = alerts.filter((a) => !a.resolved);
    return {
      critical: unresolved.filter((a) => a.level === 'critical').length,
      error: unresolved.filter((a) => a.level === 'error').length,
      warning: unresolved.filter((a) => a.level === 'warning').length,
      info: unresolved.filter((a) => a.level === 'info').length,
      total: unresolved.length,
    };
  }, [alerts]);

  if (stats.total === 0) {
    return (
      <div className={`rounded-lg border border-green-200 bg-green-50 p-4 ${className}`}>
        <div className="flex items-center gap-3">
          <Icons.CheckCircle className="h-5 w-5 text-green-600" />
          <span className="text-green-800">系统运行正常，无未处理告警</span>
        </div>
      </div>
    );
  }

  return (
    <div className={`rounded-lg border bg-white p-4 shadow-sm ${className}`}>
      <div className="flex items-center justify-between">
        <h4 className="font-medium text-gray-900">告警摘要</h4>
        {onViewAll && (
          <button
            onClick={onViewAll}
            className="text-sm text-blue-600 hover:text-blue-700"
          >
            查看全部
          </button>
        )}
      </div>
      <div className="mt-3 grid grid-cols-4 gap-3">
        {stats.critical > 0 && (
          <div className="rounded-lg bg-red-50 p-2 text-center">
            <div className="text-lg font-bold text-red-600">{stats.critical}</div>
            <div className="text-xs text-red-700">严重</div>
          </div>
        )}
        {stats.error > 0 && (
          <div className="rounded-lg bg-orange-50 p-2 text-center">
            <div className="text-lg font-bold text-orange-600">{stats.error}</div>
            <div className="text-xs text-orange-700">错误</div>
          </div>
        )}
        {stats.warning > 0 && (
          <div className="rounded-lg bg-yellow-50 p-2 text-center">
            <div className="text-lg font-bold text-yellow-600">{stats.warning}</div>
            <div className="text-xs text-yellow-700">警告</div>
          </div>
        )}
        {stats.info > 0 && (
          <div className="rounded-lg bg-blue-50 p-2 text-center">
            <div className="text-lg font-bold text-blue-600">{stats.info}</div>
            <div className="text-xs text-blue-700">信息</div>
          </div>
        )}
      </div>
      <div className="mt-3 text-center text-sm text-gray-500">
        共 {stats.total} 个未处理告警
      </div>
    </div>
  );
}