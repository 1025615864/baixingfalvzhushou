/**
 * StatCard - 统计卡片组件
 */

import type { StatCardData } from '../types';

interface StatCardProps {
  data: StatCardData;
  className?: string;
  loading?: boolean;
}

/**
 * 用户图标
 */
function UsersIcon({ className = 'h-6 w-6' }: { className?: string }): JSX.Element {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth={2}
        d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z"
      />
    </svg>
  );
}

/**
 * 活动图标
 */
function ActivityIcon({ className = 'h-6 w-6' }: { className?: string }): JSX.Element {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth={2}
        d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"
      />
    </svg>
  );
}

/**
 * 美元图标
 */
function DollarIcon({ className = 'h-6 w-6' }: { className?: string }): JSX.Element {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth={2}
        d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
      />
    </svg>
  );
}

/**
 * 时钟图标
 */
function ClockIcon({ className = 'h-6 w-6' }: { className?: string }): JSX.Element {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth={2}
        d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"
      />
    </svg>
  );
}

/**
 * 上升趋势图标
 */
function TrendUpIcon({ className = 'h-4 w-4' }: { className?: string }): JSX.Element {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth={2}
        d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6"
      />
    </svg>
  );
}

/**
 * 下降趋势图标
 */
function TrendDownIcon({ className = 'h-4 w-4' }: { className?: string }): JSX.Element {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth={2}
        d="M13 17h8m0 0V9m0 8l-8-8-4 4-6-6"
      />
    </svg>
  );
}

/**
 * 获取图标组件
 */
function getIcon(iconName: string): JSX.Element {
  const iconClass = 'h-6 w-6';

  switch (iconName) {
    case 'Users':
      return <UsersIcon className={iconClass} />;
    case 'Activity':
      return <ActivityIcon className={iconClass} />;
    case 'DollarSign':
      return <DollarIcon className={iconClass} />;
    case 'Clock':
      return <ClockIcon className={iconClass} />;
    default:
      return <ActivityIcon className={iconClass} />;
  }
}

/**
 * 格式化数值
 */
function formatValue(value: number, unit?: string): string {
  if (value >= 1000000) {
    return `${(value / 1000000).toFixed(1)}M${unit || ''}`;
  }
  if (value >= 1000) {
    return `${(value / 1000).toFixed(1)}K${unit || ''}`;
  }
  return `${value}${unit || ''}`;
}

export function StatCard({ data, className = '', loading = false }: StatCardProps): JSX.Element {
  if (loading) {
    return (
      <div className={`rounded-lg bg-white p-6 shadow-sm ${className}`}>
        <div className="animate-pulse">
          <div className="flex items-center justify-between">
            <div className="h-4 w-24 rounded bg-gray-200"></div>
            <div className="h-10 w-10 rounded-full bg-gray-200"></div>
          </div>
          <div className="mt-4 h-8 w-32 rounded bg-gray-200"></div>
          <div className="mt-2 h-4 w-20 rounded bg-gray-200"></div>
        </div>
      </div>
    );
  }

  const { title, value, change, changeType, unit, icon } = data;

  return (
    <div
      className={`rounded-lg bg-white p-6 shadow-sm transition-shadow hover:shadow-md ${className}`}
    >
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-medium text-gray-500">{title}</h3>
        <div className="rounded-full bg-blue-50 p-2 text-blue-600">{getIcon(icon || 'Activity')}</div>
      </div>

      <div className="mt-4">
        <p className="text-2xl font-bold text-gray-900">{formatValue(value, unit)}</p>

        {change !== undefined && (
          <div className="mt-2 flex items-center">
            {changeType === 'increase' ? (
              <TrendUpIcon className="mr-1 h-4 w-4 text-green-500" />
            ) : (
              <TrendDownIcon className="mr-1 h-4 w-4 text-red-500" />
            )}
            <span
              className={`text-sm font-medium ${
                changeType === 'increase' ? 'text-green-600' : 'text-red-600'
              }`}
            >
              {change > 0 ? '+' : ''}
              {change}
              {typeof change === 'number' && change <= 100 && '%'}
            </span>
            <span className="ml-2 text-sm text-gray-400">较上期</span>
          </div>
        )}
      </div>
    </div>
  );
}

/**
 * 统计卡片骨架屏
 */
export function StatCardSkeleton(): JSX.Element {
  return (
    <div className="rounded-lg bg-white p-6 shadow-sm">
      <div className="animate-pulse">
        <div className="flex items-center justify-between">
          <div className="h-4 w-24 rounded bg-gray-200"></div>
          <div className="h-10 w-10 rounded-full bg-gray-200"></div>
        </div>
        <div className="mt-4 h-8 w-32 rounded bg-gray-200"></div>
        <div className="mt-2 h-4 w-20 rounded bg-gray-200"></div>
      </div>
    </div>
  );
}

/**
 * 统计卡片列表
 */
interface StatCardListProps {
  data: StatCardData[];
  loading?: boolean;
  className?: string;
}

export function StatCardList({ data, loading = false, className = '' }: StatCardListProps): JSX.Element {
  if (loading) {
    return (
      <div className={`grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-4 ${className}`}>
        {[1, 2, 3, 4].map((index) => (
          <StatCardSkeleton key={index} />
        ))}
      </div>
    );
  }

  return (
    <div className={`grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-4 ${className}`}>
      {data.map((item, index) => (
        <StatCard key={`${item.title}-${index}`} data={item} />
      ))}
    </div>
  );
}