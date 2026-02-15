/**
 * AlertList - 告警列表组件
 */

import { useState } from 'react';

import type { QualityAlert, AlertLevel, AlertStatus, AlertType } from '../types';

interface AlertListProps {
  alerts: QualityAlert[];
  total: number;
  page: number;
  pageSize: number;
  summary: {
    critical: number;
    warning: number;
    info: number;
    active: number;
  };
  loading?: boolean;
  onPageChange?: (page: number) => void;
  onAcknowledge?: (alertId: string) => void;
  onResolve?: (alertId: string) => void;
  onFilterChange?: (filters: {
    level?: AlertLevel;
    status?: AlertStatus;
    type?: AlertType;
  }) => void;
}

/**
 * 告警级别标签
 */
function LevelBadge({ level }: { level: AlertLevel }): JSX.Element {
  const styles: Record<AlertLevel, string> = {
    critical: 'bg-red-100 text-red-700 border-red-200',
    warning: 'bg-yellow-100 text-yellow-700 border-yellow-200',
    info: 'bg-blue-100 text-blue-700 border-blue-200',
  };

  const labels: Record<AlertLevel, string> = {
    critical: '严重',
    warning: '警告',
    info: '信息',
  };

  return (
    <span className={`inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-medium ${styles[level]}`}>
      {labels[level]}
    </span>
  );
}

/**
 * 告警状态标签
 */
function StatusBadge({ status }: { status: AlertStatus }): JSX.Element {
  const styles: Record<AlertStatus, string> = {
    active: 'bg-red-50 text-red-600',
    acknowledged: 'bg-yellow-50 text-yellow-600',
    resolved: 'bg-green-50 text-green-600',
  };

  const labels: Record<AlertStatus, string> = {
    active: '活跃',
    acknowledged: '已确认',
    resolved: '已解决',
  };

  return (
    <span className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${styles[status]}`}>
      <span className={`mr-1.5 inline-block h-1.5 w-1.5 rounded-full ${status === 'active' ? 'bg-red-600' : status === 'acknowledged' ? 'bg-yellow-600' : 'bg-green-600'}`}></span>
      {labels[status]}
    </span>
  );
}

/**
 * 告警类型显示名称
 */
function getAlertTypeLabel(type: AlertType): string {
  const labels: Record<AlertType, string> = {
    high_error_rate: '高错误率',
    slow_response: '响应缓慢',
    low_quality: '质量下降',
    low_satisfaction: '满意度下降',
    service_unavailable: '服务不可用',
    token_quota_exceeded: 'Token配额超限',
  };
  return labels[type] || type;
}

/**
 * 告警列表组件
 */
export function AlertList({
  alerts,
  total,
  page,
  pageSize,
  summary,
  loading = false,
  onPageChange,
  onAcknowledge,
  onResolve,
  onFilterChange,
}: AlertListProps): JSX.Element {
  const [selectedLevel, setSelectedLevel] = useState<AlertLevel | undefined>();
  const [selectedStatus, setSelectedStatus] = useState<AlertStatus | undefined>();
  const [selectedType, setSelectedType] = useState<AlertType | undefined>();
  const [resolvingAlert, setResolvingAlert] = useState<string | null>(null);
  const [resolution, setResolution] = useState('');

  const totalPages = Math.ceil(total / pageSize);

  const handleFilterChange = (newFilters: {
    level?: AlertLevel;
    status?: AlertStatus;
    type?: AlertType;
  }): void => {
    onFilterChange?.(newFilters);
  };

  const handleLevelChange = (level: AlertLevel | ''): void => {
    const newLevel = level || undefined;
    setSelectedLevel(newLevel);
    handleFilterChange({ level: newLevel, status: selectedStatus, type: selectedType });
  };

  const handleStatusChange = (status: AlertStatus | ''): void => {
    const newStatus = status || undefined;
    setSelectedStatus(newStatus);
    handleFilterChange({ level: selectedLevel, status: newStatus, type: selectedType });
  };

  const handleTypeChange = (type: AlertType | ''): void => {
    const newType = type || undefined;
    setSelectedType(newType);
    handleFilterChange({ level: selectedLevel, status: selectedStatus, type: newType });
  };

  const handleResolveClick = (alertId: string): void => {
    setResolvingAlert(alertId);
    setResolution('');
  };

  const handleResolveSubmit = (): void => {
    if (resolvingAlert && resolution.trim()) {
      onResolve?.(resolvingAlert);
      setResolvingAlert(null);
      setResolution('');
    }
  };

  if (loading) {
    return (
      <div className="space-y-4">
        <div className="h-20 animate-pulse rounded-lg bg-gray-200"></div>
        <div className="h-64 animate-pulse rounded-lg bg-gray-200"></div>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* 统计概览 */}
      <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
        <div className="rounded-lg border border-red-200 bg-red-50 p-4">
          <p className="text-sm font-medium text-red-600">严重告警</p>
          <p className="text-2xl font-bold text-red-700">{summary.critical}</p>
        </div>
        <div className="rounded-lg border border-yellow-200 bg-yellow-50 p-4">
          <p className="text-sm font-medium text-yellow-600">警告</p>
          <p className="text-2xl font-bold text-yellow-700">{summary.warning}</p>
        </div>
        <div className="rounded-lg border border-blue-200 bg-blue-50 p-4">
          <p className="text-sm font-medium text-blue-600">信息</p>
          <p className="text-2xl font-bold text-blue-700">{summary.info}</p>
        </div>
        <div className="rounded-lg border border-gray-200 bg-gray-50 p-4">
          <p className="text-sm font-medium text-gray-600">活跃告警</p>
          <p className="text-2xl font-bold text-gray-700">{summary.active}</p>
        </div>
      </div>

      {/* 筛选器 */}
      <div className="flex flex-wrap gap-4 rounded-lg border border-gray-200 bg-white p-4">
        <div>
          <label className="mb-1 block text-xs font-medium text-gray-500">告警级别</label>
          <select
            value={selectedLevel || ''}
            onChange={(e) => handleLevelChange(e.target.value as AlertLevel | '')}
            className="rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none"
          >
            <option value="">全部</option>
            <option value="critical">严重</option>
            <option value="warning">警告</option>
            <option value="info">信息</option>
          </select>
        </div>

        <div>
          <label className="mb-1 block text-xs font-medium text-gray-500">状态</label>
          <select
            value={selectedStatus || ''}
            onChange={(e) => handleStatusChange(e.target.value as AlertStatus | '')}
            className="rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none"
          >
            <option value="">全部</option>
            <option value="active">活跃</option>
            <option value="acknowledged">已确认</option>
            <option value="resolved">已解决</option>
          </select>
        </div>

        <div>
          <label className="mb-1 block text-xs font-medium text-gray-500">类型</label>
          <select
            value={selectedType || ''}
            onChange={(e) => handleTypeChange(e.target.value as AlertType | '')}
            className="rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none"
          >
            <option value="">全部</option>
            <option value="high_error_rate">高错误率</option>
            <option value="slow_response">响应缓慢</option>
            <option value="low_quality">质量下降</option>
            <option value="low_satisfaction">满意度下降</option>
            <option value="service_unavailable">服务不可用</option>
            <option value="token_quota_exceeded">Token配额超限</option>
          </select>
        </div>
      </div>

      {/* 告警列表 */}
      <div className="rounded-lg border border-gray-200 bg-white">
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                  级别
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                  状态
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                  类型
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                  标题
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                  指标值
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                  时间
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                  操作
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200 bg-white">
              {alerts.length === 0 ? (
                <tr>
                  <td colSpan={7} className="px-6 py-8 text-center text-gray-500">
                    暂无告警数据
                  </td>
                </tr>
              ) : (
                alerts.map((alert) => (
                  <tr key={alert.id} className="hover:bg-gray-50">
                    <td className="whitespace-nowrap px-6 py-4">
                      <LevelBadge level={alert.level} />
                    </td>
                    <td className="whitespace-nowrap px-6 py-4">
                      <StatusBadge status={alert.status} />
                    </td>
                    <td className="whitespace-nowrap px-6 py-4 text-sm text-gray-900">
                      {getAlertTypeLabel(alert.type)}
                    </td>
                    <td className="px-6 py-4">
                      <div className="max-w-xs">
                        <p className="truncate text-sm font-medium text-gray-900" title={alert.title}>
                          {alert.title}
                        </p>
                        <p className="truncate text-xs text-gray-500" title={alert.description}>
                          {alert.description}
                        </p>
                      </div>
                    </td>
                    <td className="whitespace-nowrap px-6 py-4 text-sm text-gray-900">
                      {alert.metric_value.toFixed(2)}
                      <span className="ml-1 text-xs text-gray-500">/ {alert.threshold}</span>
                    </td>
                    <td className="whitespace-nowrap px-6 py-4 text-sm text-gray-500">
                      {new Date(alert.created_at).toLocaleString()}
                    </td>
                    <td className="whitespace-nowrap px-6 py-4 text-sm">
                      {alert.status === 'active' && (
                        <button
                          onClick={() => onAcknowledge?.(alert.id)}
                          className="mr-2 text-blue-600 hover:text-blue-900"
                        >
                          确认
                        </button>
                      )}
                      {alert.status !== 'resolved' && (
                        <button
                          onClick={() => handleResolveClick(alert.id)}
                          className="text-green-600 hover:text-green-900"
                        >
                          解决
                        </button>
                      )}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        {/* 分页 */}
        {totalPages > 1 && (
          <div className="flex items-center justify-between border-t border-gray-200 px-6 py-4">
            <div className="text-sm text-gray-500">
              显示第 {(page - 1) * pageSize + 1} - {Math.min(page * pageSize, total)} 条，共 {total} 条
            </div>
            <div className="flex gap-2">
              <button
                onClick={() => onPageChange?.(page - 1)}
                disabled={page === 1}
                className="rounded-lg border border-gray-300 px-3 py-1 text-sm disabled:cursor-not-allowed disabled:opacity-50"
              >
                上一页
              </button>
              <span className="px-3 py-1 text-sm">
                {page} / {totalPages}
              </span>
              <button
                onClick={() => onPageChange?.(page + 1)}
                disabled={page === totalPages}
                className="rounded-lg border border-gray-300 px-3 py-1 text-sm disabled:cursor-not-allowed disabled:opacity-50"
              >
                下一页
              </button>
            </div>
          </div>
        )}
      </div>

      {/* 解决告警弹窗 */}
      {resolvingAlert && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50">
          <div className="w-full max-w-md rounded-lg bg-white p-6">
            <h3 className="mb-4 text-lg font-medium text-gray-900">解决告警</h3>
            <textarea
              value={resolution}
              onChange={(e) => setResolution(e.target.value)}
              placeholder="请输入解决方案..."
              rows={4}
              className="mb-4 w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none"
            />
            <div className="flex justify-end gap-2">
              <button
                onClick={() => setResolvingAlert(null)}
                className="rounded-lg border border-gray-300 px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50"
              >
                取消
              </button>
              <button
                onClick={handleResolveSubmit}
                disabled={!resolution.trim()}
                className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-50"
              >
                确认解决
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}