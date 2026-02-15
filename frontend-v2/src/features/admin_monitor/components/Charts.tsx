/**
 * Charts 组件 - 监控图表
 * 使用纯CSS/SVG实现图表
 */

import { useState, useMemo } from 'react';

import type {
  ResourceUsageData,
  RequestTrendData,
} from '../types';

// ==================== 图标组件 ====================

const Icons = {
  Clock: ({ className }: { className?: string }) => (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="12" cy="12" r="10" />
      <polyline points="12 6 12 12 16 14" />
    </svg>
  ),
  Activity: ({ className }: { className?: string }) => (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M22 12h-4l-3 9L9 3l-3 9H2" />
    </svg>
  ),
  Cpu: ({ className }: { className?: string }) => (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <rect x="4" y="4" width="16" height="16" rx="2" />
      <rect x="9" y="9" width="6" height="6" />
      <path d="M9 1v3M15 1v3M9 20v3M15 20v3M20 9h3M20 14h3M1 9h3M1 14h3" />
    </svg>
  ),
  Server: ({ className }: { className?: string }) => (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <rect x="2" y="2" width="20" height="8" rx="2" ry="2" />
      <rect x="2" y="14" width="20" height="8" rx="2" ry="2" />
      <line x1="6" y1="6" x2="6.01" y2="6" />
      <line x1="6" y1="18" x2="6.01" y2="18" />
    </svg>
  ),
  TrendingUp: ({ className }: { className?: string }) => (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <polyline points="23 6 13.5 15.5 8.5 10.5 1 18" />
      <polyline points="17 6 23 6 23 12" />
    </svg>
  ),
  BarChart: ({ className }: { className?: string }) => (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <line x1="18" y1="20" x2="18" y2="10" />
      <line x1="12" y1="20" x2="12" y2="4" />
      <line x1="6" y1="20" x2="6" y2="14" />
    </svg>
  ),
};

// ==================== 颜色配置 ====================

const COLORS = {
  cpu: '#3b82f6',
  memory: '#10b981',
  disk: '#f59e0b',
  requests: '#3b82f6',
  errors: '#ef4444',
  responseTime: '#8b5cf6',
};

// ==================== 时间范围选择器 ====================

interface TimeRangeSelectorProps {
  value: '1h' | '6h' | '24h' | '7d';
  onChange: (range: '1h' | '6h' | '24h' | '7d') => void;
  className?: string;
}

function TimeRangeSelector({
  value,
  onChange,
  className = '',
}: TimeRangeSelectorProps): JSX.Element {
  const ranges: Array<{ value: '1h' | '6h' | '24h' | '7d'; label: string }> = [
    { value: '1h', label: '1小时' },
    { value: '6h', label: '6小时' },
    { value: '24h', label: '24小时' },
    { value: '7d', label: '7天' },
  ];

  return (
    <div className={`flex items-center gap-1 rounded-lg border bg-white p-1 ${className}`}>
      {ranges.map((range) => (
        <button
          key={range.value}
          onClick={() => onChange(range.value)}
          className={`rounded-md px-3 py-1 text-sm font-medium transition-colors ${
            value === range.value
              ? 'bg-blue-500 text-white'
              : 'text-gray-600 hover:bg-gray-100'
          }`}
        >
          {range.label}
        </button>
      ))}
    </div>
  );
}

// ==================== 资源使用图表 ====================

interface ResourceUsageChartProps {
  data?: ResourceUsageData;
  loading?: boolean;
  className?: string;
}

/**
 * 资源使用图表组件
 */
export function ResourceUsageChart({
  data,
  loading = false,
  className = '',
}: ResourceUsageChartProps): JSX.Element {
  const [selectedMetrics, setSelectedMetrics] = useState<string[]>(['cpu', 'memory']);

  if (loading) {
    return (
      <div className={`rounded-lg border bg-white p-4 shadow-sm ${className}`}>
        <div className="h-64 animate-pulse rounded bg-gray-100" />
      </div>
    );
  }

  if (!data || data.timestamps.length === 0) {
    return (
      <div className={`rounded-lg border bg-white p-4 shadow-sm ${className}`}>
        <h3 className="mb-4 font-semibold text-gray-900">资源使用率</h3>
        <div className="flex h-64 items-center justify-center text-gray-400">
          暂无数据
        </div>
      </div>
    );
  }

  const maxValue = 100;
  const chartData = data.timestamps.map((timestamp, index) => ({
    timestamp,
    cpu: data.cpu[index] ?? 0,
    memory: data.memory[index] ?? 0,
    disk: data.disk[index] ?? 0,
  }));

  return (
    <div className={`rounded-lg border bg-white p-4 shadow-sm ${className}`}>
      <div className="mb-4 flex flex-wrap items-center justify-between gap-2">
        <div className="flex items-center gap-2">
          <Icons.Cpu className="h-5 w-5 text-gray-500" />
          <h3 className="font-semibold text-gray-900">资源使用率</h3>
        </div>
        <div className="flex gap-2">
          {['cpu', 'memory', 'disk'].map((metric) => (
            <button
              key={metric}
              onClick={() => {
                setSelectedMetrics((prev) =>
                  prev.includes(metric)
                    ? prev.filter((m) => m !== metric)
                    : [...prev, metric]
                );
              }}
              className={`flex items-center gap-1 rounded-md px-2 py-1 text-xs font-medium transition-colors ${
                selectedMetrics.includes(metric)
                  ? 'bg-blue-100 text-blue-700'
                  : 'bg-gray-100 text-gray-500'
              }`}
            >
              <span
                className="h-2 w-2 rounded-full"
                style={{
                  backgroundColor:
                    metric === 'cpu'
                      ? COLORS.cpu
                      : metric === 'memory'
                        ? COLORS.memory
                        : COLORS.disk,
                }}
              />
              {metric === 'cpu' ? 'CPU' : metric === 'memory' ? '内存' : '磁盘'}
            </button>
          ))}
        </div>
      </div>

      <div className="h-64">
        {/* 简单的折线图实现 */}
        <div className="relative h-full">
          {/* Y轴标签 */}
          <div className="absolute left-0 top-0 flex h-full flex-col justify-between text-xs text-gray-400">
            <span>100%</span>
            <span>75%</span>
            <span>50%</span>
            <span>25%</span>
            <span>0%</span>
          </div>

          {/* 图表区域 */}
          <div className="ml-10 h-full relative">
            {/* 网格线 */}
            <div className="absolute inset-0 flex flex-col justify-between">
              {[0, 1, 2, 3, 4].map((i) => (
                <div key={i} className="border-b border-gray-200" />
              ))}
            </div>

            {/* 数据线 */}
            <svg className="absolute inset-0 h-full w-full">
              {selectedMetrics.includes('cpu') && (
                <polyline
                  fill="none"
                  stroke={COLORS.cpu}
                  strokeWidth="2"
                  points={chartData
                    .map((d, i) => {
                      const x = (i / (chartData.length - 1)) * 100;
                      const y = 100 - (d.cpu / maxValue) * 100;
                      return `${x},${y}`;
                    })
                    .join(' ')}
                  style={{ transform: 'scaleY(0.95) translateY(2.5%)' }}
                  vectorEffect="non-scaling-stroke"
                />
              )}
              {selectedMetrics.includes('memory') && (
                <polyline
                  fill="none"
                  stroke={COLORS.memory}
                  strokeWidth="2"
                  points={chartData
                    .map((d, i) => {
                      const x = (i / (chartData.length - 1)) * 100;
                      const y = 100 - (d.memory / maxValue) * 100;
                      return `${x},${y}`;
                    })
                    .join(' ')}
                  style={{ transform: 'scaleY(0.95) translateY(2.5%)' }}
                  vectorEffect="non-scaling-stroke"
                />
              )}
              {selectedMetrics.includes('disk') && (
                <polyline
                  fill="none"
                  stroke={COLORS.disk}
                  strokeWidth="2"
                  points={chartData
                    .map((d, i) => {
                      const x = (i / (chartData.length - 1)) * 100;
                      const y = 100 - (d.disk / maxValue) * 100;
                      return `${x},${y}`;
                    })
                    .join(' ')}
                  style={{ transform: 'scaleY(0.95) translateY(2.5%)' }}
                  vectorEffect="non-scaling-stroke"
                />
              )}
            </svg>

            {/* X轴标签 */}
            <div className="absolute bottom-0 left-0 right-0 flex justify-between text-xs text-gray-400 transform translate-y-6">
              {chartData.filter((_, i) => i % 2 === 0).map((d, i) => (
                <span key={i}>{d.timestamp}</span>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

// ==================== 请求趋势图表 ====================

interface RequestTrendChartProps {
  data?: RequestTrendData;
  loading?: boolean;
  className?: string;
}

/**
 * 请求趋势图表组件
 */
export function RequestTrendChart({
  data,
  loading = false,
  className = '',
}: RequestTrendChartProps): JSX.Element {
  if (loading) {
    return (
      <div className={`rounded-lg border bg-white p-4 shadow-sm ${className}`}>
        <div className="h-64 animate-pulse rounded bg-gray-100" />
      </div>
    );
  }

  if (!data || data.timestamps.length === 0) {
    return (
      <div className={`rounded-lg border bg-white p-4 shadow-sm ${className}`}>
        <h3 className="mb-4 font-semibold text-gray-900">请求趋势</h3>
        <div className="flex h-64 items-center justify-center text-gray-400">
          暂无数据
        </div>
      </div>
    );
  }

  const maxRequests = Math.max(...data.requests, 1);
  const chartData = data.timestamps.map((timestamp, index) => ({
    timestamp,
    requests: data.requests[index] ?? 0,
    errors: data.errors[index] ?? 0,
    responseTime: data.avgResponseTime[index] ?? 0,
  }));

  return (
    <div className={`rounded-lg border bg-white p-4 shadow-sm ${className}`}>
      <div className="mb-4 flex items-center gap-2">
        <Icons.Activity className="h-5 w-5 text-gray-500" />
        <h3 className="font-semibold text-gray-900">请求趋势</h3>
      </div>

      <div className="h-64">
        <div className="relative h-full">
          {/* 柱状图 */}
          <div className="absolute left-0 right-0 top-0 bottom-8 flex items-end justify-between gap-1">
            {chartData.map((d, i) => (
              <div key={i} className="flex-1 flex flex-col items-center gap-1">
                {/* 请求柱 */}
                <div
                  className="w-full rounded-t bg-blue-500 transition-all"
                  style={{
                    height: `${(d.requests / maxRequests) * 80}%`,
                    minHeight: d.requests > 0 ? '4px' : '0',
                  }}
                  title={`请求: ${Math.round(d.requests)}`}
                />
                {/* 错误柱（叠加） */}
                <div
                  className="w-full rounded-t bg-red-500 transition-all"
                  style={{
                    height: `${(d.errors / maxRequests) * 80}%`,
                    minHeight: d.errors > 0 ? '4px' : '0',
                  }}
                  title={`错误: ${Math.round(d.errors)}`}
                />
              </div>
            ))}
          </div>

          {/* X轴标签 */}
          <div className="absolute bottom-0 left-0 right-0 flex justify-between text-xs text-gray-400">
            {chartData.filter((_, i) => i % 2 === 0).map((d, i) => (
              <span key={i}>{d.timestamp}</span>
            ))}
          </div>
        </div>
      </div>

      {/* 图例 */}
      <div className="mt-4 flex items-center justify-center gap-6">
        <div className="flex items-center gap-2">
          <div className="h-3 w-3 rounded bg-blue-500" />
          <span className="text-sm text-gray-600">请求数</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="h-3 w-3 rounded bg-red-500" />
          <span className="text-sm text-gray-600">错误数</span>
        </div>
      </div>
    </div>
  );
}

// ==================== API端点性能图表 ====================

interface ApiEndpointChartProps {
  endpoints: Record<string, { count: number; avgTime: number }>;
  loading?: boolean;
  className?: string;
}

/**
 * API端点性能图表组件
 */
export function ApiEndpointChart({
  endpoints,
  loading = false,
  className = '',
}: ApiEndpointChartProps): JSX.Element {
  const chartData = useMemo(() => {
    return Object.entries(endpoints)
      .map(([name, data]) => ({
        name: name.length > 25 ? name.slice(0, 25) + '...' : name,
        fullName: name,
        count: data.count,
        avgTime: Math.round(data.avgTime),
      }))
      .sort((a, b) => b.count - a.count)
      .slice(0, 8);
  }, [endpoints]);

  if (loading) {
    return (
      <div className={`rounded-lg border bg-white p-4 shadow-sm ${className}`}>
        <div className="h-64 animate-pulse rounded bg-gray-100" />
      </div>
    );
  }

  if (chartData.length === 0) {
    return (
      <div className={`rounded-lg border bg-white p-4 shadow-sm ${className}`}>
        <h3 className="mb-4 font-semibold text-gray-900">API端点性能 (Top 8)</h3>
        <div className="flex h-64 items-center justify-center text-gray-400">
          暂无数据
        </div>
      </div>
    );
  }

  const maxCount = Math.max(...chartData.map((d) => d.count), 1);

  return (
    <div className={`rounded-lg border bg-white p-4 shadow-sm ${className}`}>
      <h3 className="mb-4 font-semibold text-gray-900">API端点性能 (Top 8)</h3>
      <div className="h-64 space-y-2">
        {chartData.map((item, index) => (
          <div key={index} className="flex items-center gap-3">
            <div className="w-32 flex-shrink-0 truncate text-xs text-gray-600" title={item.fullName}>
              {item.name}
            </div>
            <div className="flex-1">
              <div className="flex items-center gap-2">
                <div className="flex-1 rounded-full bg-gray-100">
                  <div
                    className="h-4 rounded-full bg-blue-500 transition-all"
                    style={{ width: `${(item.count / maxCount) * 100}%` }}
                  />
                </div>
                <span className="w-12 text-right text-xs text-gray-500">{item.count}</span>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

// ==================== 系统状态分布图表 ====================

interface StatusDistributionChartProps {
  healthy: number;
  unhealthy: number;
  degraded: number;
  loading?: boolean;
  className?: string;
}

/**
 * 系统状态分布图表组件
 */
export function StatusDistributionChart({
  healthy,
  unhealthy,
  degraded,
  loading = false,
  className = '',
}: StatusDistributionChartProps): JSX.Element {
  const total = healthy + unhealthy + degraded;

  if (loading) {
    return (
      <div className={`rounded-lg border bg-white p-4 shadow-sm ${className}`}>
        <div className="h-64 animate-pulse rounded bg-gray-100" />
      </div>
    );
  }

  if (total === 0) {
    return (
      <div className={`rounded-lg border bg-white p-4 shadow-sm ${className}`}>
        <h3 className="mb-4 font-semibold text-gray-900">系统状态分布</h3>
        <div className="flex h-64 items-center justify-center text-gray-400">
          暂无数据
        </div>
      </div>
    );
  }

  const data = [
    { name: '健康', value: healthy, color: '#10b981', percent: (healthy / total) * 100 },
    { name: '降级', value: degraded, color: '#f59e0b', percent: (degraded / total) * 100 },
    { name: '异常', value: unhealthy, color: '#ef4444', percent: (unhealthy / total) * 100 },
  ];

  // 计算环形图
  const circumference = 2 * Math.PI * 40; // 半径40
  let currentOffset = 0;

  return (
    <div className={`rounded-lg border bg-white p-4 shadow-sm ${className}`}>
      <h3 className="mb-4 font-semibold text-gray-900">系统状态分布</h3>
      <div className="flex h-64 items-center justify-center">
        <div className="relative h-40 w-40">
          {/* 环形图 */}
          <svg className="h-full w-full -rotate-90 transform" viewBox="0 0 100 100">
            {/* 背景圆环 */}
            <circle
              cx="50"
              cy="50"
              r="40"
              fill="none"
              stroke="#e5e7eb"
              strokeWidth="12"
            />
            {/* 数据圆环 */}
            {data.map((item, index) => {
              if (item.value === 0) return null;
              const strokeDasharray = (item.value / total) * circumference;
              const offset = currentOffset;
              currentOffset += strokeDasharray;
              return (
                <circle
                  key={index}
                  cx="50"
                  cy="50"
                  r="40"
                  fill="none"
                  stroke={item.color}
                  strokeWidth="12"
                  strokeDasharray={`${strokeDasharray} ${circumference}`}
                  strokeDashoffset={-offset}
                />
              );
            })}
          </svg>
          {/* 中心文字 */}
          <div className="absolute inset-0 flex flex-col items-center justify-center">
            <span className="text-2xl font-bold text-gray-900">{total}</span>
            <span className="text-xs text-gray-500">组件总数</span>
          </div>
        </div>
      </div>

      {/* 图例 */}
      <div className="mt-4 grid grid-cols-3 gap-2">
        {data.map((item, index) => (
          <div key={index} className="text-center">
            <div className="flex items-center justify-center gap-1">
              <span
                className="h-3 w-3 rounded-full"
                style={{ backgroundColor: item.color }}
              />
              <span className="text-sm text-gray-600">{item.name}</span>
            </div>
            <div className="text-lg font-semibold" style={{ color: item.color }}>
              {item.value}
            </div>
            <div className="text-xs text-gray-400">{item.percent.toFixed(1)}%</div>
          </div>
        ))}
      </div>
    </div>
  );
}

// ==================== 监控图表组合组件 ====================

interface MonitorChartsProps {
  resourceData?: ResourceUsageData;
  requestData?: RequestTrendData;
  timeRange?: '1h' | '6h' | '24h' | '7d';
  onTimeRangeChange?: (range: '1h' | '6h' | '24h' | '7d') => void;
  loading?: boolean;
  className?: string;
}

/**
 * 监控图表组合组件
 */
export function MonitorCharts({
  resourceData,
  requestData,
  timeRange = '1h',
  onTimeRangeChange,
  loading = false,
  className = '',
}: MonitorChartsProps): JSX.Element {
  return (
    <div className={`space-y-4 ${className}`}>
      {/* 时间范围选择器 */}
      {onTimeRangeChange && (
        <div className="flex justify-end">
          <TimeRangeSelector value={timeRange} onChange={onTimeRangeChange} />
        </div>
      )}

      {/* 图表网格 */}
      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <ResourceUsageChart data={resourceData} loading={loading} />
        <RequestTrendChart data={requestData} loading={loading} />
      </div>
    </div>
  );
}

// 导出所有图表组件
export {
  TimeRangeSelector,
};