/**
 * FunnelChart - 漏斗图组件
 */

import type { FunnelChartDataItem } from '../types';

interface FunnelChartProps {
  data: FunnelChartDataItem[];
  title?: string;
  loading?: boolean;
  className?: string;
  showLegend?: boolean;
  showRates?: boolean;
}

/**
 * 默认颜色配置
 */
const DEFAULT_COLORS = [
  '#3b82f6', // blue-500
  '#6366f1', // indigo-500
  '#8b5cf6', // violet-500
  '#a855f7', // purple-500
  '#d946ef', // fuchsia-500
  '#ec4899', // pink-500
  '#f43f5e', // rose-500
  '#f97316', // orange-500
];

export function FunnelChart({
  data,
  title,
  loading = false,
  className = '',
  showLegend = true,
  showRates = true,
}: FunnelChartProps): JSX.Element {
  if (loading) {
    return (
      <div className={`rounded-lg bg-white p-6 shadow-sm ${className}`}>
        {title && <h3 className="mb-4 text-lg font-semibold text-gray-900">{title}</h3>}
        <div className="animate-pulse space-y-3">
          {[1, 2, 3, 4].map((i) => (
            <div
              key={i}
              className="h-12 rounded-lg bg-gray-200"
              style={{ width: `${100 - i * 15}%`, marginLeft: 'auto', marginRight: 'auto' }}
            />
          ))}
        </div>
      </div>
    );
  }

  if (data.length === 0) {
    return (
      <div className={`rounded-lg bg-white p-6 shadow-sm ${className}`}>
        {title && <h3 className="mb-4 text-lg font-semibold text-gray-900">{title}</h3>}
        <div className="flex h-64 items-center justify-center text-gray-500">暂无数据</div>
      </div>
    );
  }

  const maxValue = Math.max(...data.map((d) => d.value));

  return (
    <div className={`rounded-lg bg-white p-6 shadow-sm ${className}`}>
      {title && <h3 className="mb-4 text-lg font-semibold text-gray-900">{title}</h3>}

      <div className="space-y-3">
        {data.map((item, index) => {
          const widthPercent = (item.value / maxValue) * 100;
          const color = item.color || DEFAULT_COLORS[index % DEFAULT_COLORS.length];

          return (
            <div key={item.name} className="flex flex-col gap-1">
              <div className="flex items-center justify-between text-sm">
                <span className="font-medium text-gray-700">{item.name}</span>
                <div className="flex items-center gap-2">
                  <span className="font-semibold text-gray-900">{item.value.toLocaleString()}</span>
                  {showRates && index > 0 && (
                    <span className="text-xs text-green-600">{item.conversionRate.toFixed(1)}%</span>
                  )}
                </div>
              </div>
              <div className="h-10 w-full rounded-lg bg-gray-100">
                <div
                  className="flex h-full items-center rounded-lg px-3 transition-all duration-500"
                  style={{
                    width: `${Math.max(widthPercent, 20)}%`,
                    backgroundColor: color,
                  }}
                >
                  <span className="truncate text-sm font-medium text-white">
                    {widthPercent > 40 ? item.name : ''}
                  </span>
                </div>
              </div>
              {showRates && item.dropRate > 0 && (
                <div className="text-xs text-gray-400">
                  流失率: <span className="text-red-500">{item.dropRate.toFixed(1)}%</span>
                </div>
              )}
            </div>
          );
        })}
      </div>

      {showLegend && (
        <div className="mt-6 grid grid-cols-2 gap-3 border-t border-gray-100 pt-4 sm:grid-cols-4">
          {data.map((item, index) => (
            <div key={`legend-${item.name}`} className="flex items-center gap-2">
              <div
                className="h-3 w-3 rounded-full"
                style={{ backgroundColor: item.color || DEFAULT_COLORS[index % DEFAULT_COLORS.length] }}
              />
              <span className="truncate text-xs text-gray-600">{item.name}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

/**
 * 紧凑版漏斗图
 */
interface CompactFunnelChartProps {
  data: FunnelChartDataItem[];
  title?: string;
  loading?: boolean;
  className?: string;
}

export function CompactFunnelChart({
  data,
  title,
  loading = false,
  className = '',
}: CompactFunnelChartProps): JSX.Element {
  if (loading) {
    return (
      <div className={`rounded-lg bg-white p-4 shadow-sm ${className}`}>
        {title && <h3 className="mb-2 text-base font-semibold text-gray-900">{title}</h3>}
        <div className="animate-pulse flex flex-col items-center justify-center py-8">
          <div className="h-16 w-32 bg-gray-200 rounded-t-lg" />
          <div className="h-16 w-48 bg-gray-200 mt-1" />
          <div className="h-16 w-64 bg-gray-200 mt-1 rounded-b-lg" />
        </div>
      </div>
    );
  }

  if (data.length === 0) {
    return (
      <div className={`rounded-lg bg-white p-4 shadow-sm ${className}`}>
        {title && <h3 className="mb-2 text-base font-semibold text-gray-900">{title}</h3>}
        <div className="flex h-32 items-center justify-center text-gray-500 text-sm">暂无数据</div>
      </div>
    );
  }

  const maxValue = Math.max(...data.map((d) => d.value));

  return (
    <div className={`rounded-lg bg-white p-4 shadow-sm ${className}`}>
      {title && <h3 className="mb-3 text-base font-semibold text-gray-900">{title}</h3>}

      <div className="flex flex-col items-center gap-2">
        {data.map((item, index) => {
          const widthPercent = (item.value / maxValue) * 100;
          const color = item.color || DEFAULT_COLORS[index % DEFAULT_COLORS.length];

          return (
            <div
              key={item.name}
              className="relative flex items-center justify-center rounded-lg py-2 px-4 text-center text-white transition-all duration-500"
              style={{
                width: `${Math.max(widthPercent, 30)}%`,
                backgroundColor: color,
              }}
            >
              <div className="flex flex-col">
                <span className="text-xs font-medium truncate">{item.name}</span>
                <span className="text-sm font-bold">{item.value.toLocaleString()}</span>
              </div>
              {index > 0 && (
                <div className="absolute -right-8 top-1/2 -translate-y-1/2 text-xs text-gray-500">
                  {item.conversionRate.toFixed(0)}%
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}