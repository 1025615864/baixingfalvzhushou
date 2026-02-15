/**
 * MetricCard 组件 - 指标卡片
 * 用于展示系统监控的各项指标数据
 */

import type { MetricCardProps } from '../types';

interface MetricCardComponentProps extends MetricCardProps {
  className?: string;
}

/**
 * 图标组件
 */
const Icons = {
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
  Database: ({ className }: { className?: string }) => (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <ellipse cx="12" cy="5" rx="9" ry="3" />
      <path d="M3 5V19A9 3 0 0 0 21 19V5" />
      <path d="M3 12A9 3 0 0 0 21 12" />
    </svg>
  ),
  HardDrive: ({ className }: { className?: string }) => (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M2 12h20" />
      <path d="M20 12v6a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2v-6" />
      <circle cx="12" cy="7" r="3" />
    </svg>
  ),
  MemoryStick: ({ className }: { className?: string }) => (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M6 19v2M10 19v2M14 19v2M18 19v2" />
      <path d="M8 11h8M8 15h8" />
      <rect x="4" y="4" width="16" height="16" rx="2" />
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
  TrendingDown: ({ className }: { className?: string }) => (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <polyline points="23 18 13.5 8.5 8.5 13.5 1 6" />
      <polyline points="17 18 23 18 23 12" />
    </svg>
  ),
  TrendingUp: ({ className }: { className?: string }) => (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <polyline points="23 6 13.5 15.5 8.5 10.5 1 18" />
      <polyline points="17 6 23 6 23 12" />
    </svg>
  ),
  Users: ({ className }: { className?: string }) => (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2" />
      <circle cx="9" cy="7" r="4" />
      <path d="M23 21v-2a4 4 0 0 0-3-3.87" />
      <path d="M16 3.13a4 4 0 0 1 0 7.75" />
    </svg>
  ),
  Zap: ({ className }: { className?: string }) => (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2" />
    </svg>
  ),
};

/**
 * 获取图标组件
 */
function getIcon(iconName: string | undefined): React.ReactNode {
  const iconClass = 'h-6 w-6';
  switch (iconName) {
    case 'Cpu':
      return <Icons.Cpu className={iconClass} />;
    case 'MemoryStick':
      return <Icons.MemoryStick className={iconClass} />;
    case 'HardDrive':
      return <Icons.HardDrive className={iconClass} />;
    case 'Server':
      return <Icons.Server className={iconClass} />;
    case 'Database':
      return <Icons.Database className={iconClass} />;
    case 'Users':
      return <Icons.Users className={iconClass} />;
    case 'Zap':
      return <Icons.Zap className={iconClass} />;
    case 'Activity':
    default:
      return <Icons.Activity className={iconClass} />;
  }
}

/**
 * 获取颜色样式
 */
function getColorStyles(color: string | undefined): string {
  switch (color) {
    case 'green':
      return 'bg-green-50 border-green-200 text-green-700';
    case 'yellow':
      return 'bg-yellow-50 border-yellow-200 text-yellow-700';
    case 'red':
      return 'bg-red-50 border-red-200 text-red-700';
    case 'purple':
      return 'bg-purple-50 border-purple-200 text-purple-700';
    case 'blue':
    default:
      return 'bg-blue-50 border-blue-200 text-blue-700';
  }
}

/**
 * 获取图标背景样式
 */
function getIconBgStyles(color: string | undefined): string {
  switch (color) {
    case 'green':
      return 'bg-green-100 text-green-600';
    case 'yellow':
      return 'bg-yellow-100 text-yellow-600';
    case 'red':
      return 'bg-red-100 text-red-600';
    case 'purple':
      return 'bg-purple-100 text-purple-600';
    case 'blue':
    default:
      return 'bg-blue-100 text-blue-600';
  }
}

/**
 * 格式化数值
 */
function formatValue(value: number | string, unit?: string): string {
  if (typeof value === 'string') {
    return value;
  }

  // 大数字格式化
  if (value >= 1000000) {
    return `${(value / 1000000).toFixed(1)}M${unit ? ` ${unit}` : ''}`;
  }
  if (value >= 1000) {
    return `${(value / 1000).toFixed(1)}K${unit ? ` ${unit}` : ''}`;
  }

  // 小数格式化
  if (value < 10 && value % 1 !== 0) {
    return `${value.toFixed(2)}${unit ? ` ${unit}` : ''}`;
  }

  return `${Math.round(value)}${unit ? ` ${unit}` : ''}`;
}

/**
 * 指标卡片组件
 */
export function MetricCard({
  title,
  value,
  unit,
  change,
  changeType = 'neutral',
  icon,
  color = 'blue',
  loading = false,
  className = '',
}: MetricCardComponentProps): JSX.Element {
  if (loading) {
    return (
      <div
        className={`rounded-lg border bg-white p-6 shadow-sm animate-pulse ${className}`}
      >
        <div className="flex items-center justify-between">
          <div className="space-y-2">
            <div className="h-4 w-24 rounded bg-gray-200" />
            <div className="h-8 w-32 rounded bg-gray-200" />
          </div>
          <div className="h-12 w-12 rounded-full bg-gray-200" />
        </div>
      </div>
    );
  }

  const cardStyles = getColorStyles(color);
  const iconBgStyles = getIconBgStyles(color);

  return (
    <div
      className={`rounded-lg border p-6 shadow-sm transition-all hover:shadow-md ${cardStyles} ${className}`}
    >
      <div className="flex items-start justify-between">
        <div className="space-y-2">
          <p className="text-sm font-medium opacity-80">{title}</p>
          <p className="text-2xl font-bold tracking-tight">
            {formatValue(value, unit)}
          </p>
          {change !== undefined && (
            <div className="flex items-center gap-1 text-sm">
              {changeType === 'increase' ? (
                <Icons.TrendingUp className="h-4 w-4 text-green-600" />
              ) : changeType === 'decrease' ? (
                <Icons.TrendingDown className="h-4 w-4 text-red-600" />
              ) : null}
              <span
                className={
                  changeType === 'increase'
                    ? 'text-green-600'
                    : changeType === 'decrease'
                      ? 'text-red-600'
                      : 'text-gray-600'
                }
              >
                {change > 0 ? '+' : ''}
                {change}
                {unit ? ` ${unit}` : '%'}
              </span>
            </div>
          )}
        </div>
        <div className={`rounded-full p-3 ${iconBgStyles}`}>{getIcon(icon)}</div>
      </div>
    </div>
  );
}

/**
 * 系统状态卡片组件
 */
export function StatusCard({
  title,
  status,
  message,
  responseTime,
  loading = false,
  className = '',
}: {
  title: string;
  status: 'healthy' | 'unhealthy' | 'degraded';
  message?: string;
  responseTime?: number;
  loading?: boolean;
  className?: string;
}): JSX.Element {
  if (loading) {
    return (
      <div className={`rounded-lg border bg-gray-50 p-4 shadow-sm animate-pulse ${className}`}>
        <div className="flex items-center justify-between">
          <div className="space-y-2">
            <div className="h-4 w-20 rounded bg-gray-200" />
            <div className="h-3 w-32 rounded bg-gray-200" />
          </div>
          <div className="h-3 w-3 rounded-full bg-gray-200" />
        </div>
      </div>
    );
  }
  const getStatusColor = (): string => {
    switch (status) {
      case 'healthy':
        return 'bg-green-50 border-green-200 text-green-800';
      case 'unhealthy':
        return 'bg-red-50 border-red-200 text-red-800';
      case 'degraded':
        return 'bg-yellow-50 border-yellow-200 text-yellow-800';
      default:
        return 'bg-gray-50 border-gray-200 text-gray-800';
    }
  };

  const getStatusDot = (): string => {
    switch (status) {
      case 'healthy':
        return 'bg-green-500';
      case 'unhealthy':
        return 'bg-red-500';
      case 'degraded':
        return 'bg-yellow-500';
      default:
        return 'bg-gray-500';
    }
  };

  return (
    <div
      className={`rounded-lg border p-4 shadow-sm ${getStatusColor()} ${className}`}
    >
      <div className="flex items-center justify-between">
        <div>
          <h4 className="font-medium">{title}</h4>
          {message && <p className="mt-1 text-sm opacity-80">{message}</p>}
        </div>
        <div className="flex items-center gap-2">
          {responseTime !== undefined && (
            <span className="text-sm opacity-70">{responseTime}ms</span>
          )}
          <span className={`h-3 w-3 rounded-full ${getStatusDot()}`} />
        </div>
      </div>
    </div>
  );
}

/**
 * 资源使用卡片组件
 */
export function ResourceCard({
  title,
  used,
  total,
  unit,
  percentage,
  color = 'blue',
  className = '',
}: {
  title: string;
  used: number;
  total: number;
  unit: string;
  percentage: number;
  color?: 'blue' | 'green' | 'yellow' | 'red';
  className?: string;
}): JSX.Element {
  const getProgressColor = (): string => {
    if (percentage >= 90) return 'bg-red-500';
    if (percentage >= 70) return 'bg-yellow-500';
    return 'bg-green-500';
  };

  const getCardColor = (): string => {
    switch (color) {
      case 'green':
        return 'border-green-200';
      case 'yellow':
        return 'border-yellow-200';
      case 'red':
        return 'border-red-200';
      case 'blue':
      default:
        return 'border-blue-200';
    }
  };

  return (
    <div
      className={`rounded-lg border bg-white p-4 shadow-sm ${getCardColor()} ${className}`}
    >
      <div className="flex items-center justify-between">
        <h4 className="font-medium text-gray-700">{title}</h4>
        <span className="text-sm text-gray-500">
          {used.toFixed(1)} / {total.toFixed(1)} {unit}
        </span>
      </div>
      <div className="mt-3">
        <div className="flex items-center justify-between text-sm">
          <span className="text-gray-600">使用率</span>
          <span
            className={`font-medium ${
              percentage >= 90
                ? 'text-red-600'
                : percentage >= 70
                  ? 'text-yellow-600'
                  : 'text-green-600'
            }`}
          >
            {percentage.toFixed(1)}%
          </span>
        </div>
        <div className="mt-2 h-2 w-full rounded-full bg-gray-200">
          <div
            className={`h-2 rounded-full transition-all duration-500 ${getProgressColor()}`}
            style={{ width: `${Math.min(100, percentage)}%` }}
          />
        </div>
      </div>
    </div>
  );
}