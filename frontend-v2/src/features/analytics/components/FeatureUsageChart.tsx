/**
 * FeatureUsageChart - 功能使用图表组件
 */

import type { FeatureUsage } from '../types';

interface FeatureUsageChartProps {
  data: FeatureUsage[];
  title?: string;
  loading?: boolean;
  className?: string;
  height?: number;
  maxItems?: number;
}

/**
 * 颜色映射
 */
const COLORS = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899', '#06b6d4', '#84cc16'];

/**
 * 功能使用图表组件
 */
export function FeatureUsageChart({
  data,
  title = '功能使用情况',
  loading = false,
  className = '',
  height = 400,
  maxItems = 8,
}: FeatureUsageChartProps): JSX.Element {
  // 限制显示数量，并排序
  const sortedData = [...data]
    .sort((a, b) => b.usageCount - a.usageCount)
    .slice(0, maxItems);

  if (loading) {
    return (
      <div className={`rounded-lg bg-white p-6 shadow-sm ${className}`}>
        <h3 className="mb-4 text-lg font-semibold text-gray-900">{title}</h3>
        <div className="animate-pulse" style={{ height: `${height}px` }}>
          <div className="h-full w-full rounded-lg bg-gray-200"></div>
        </div>
      </div>
    );
  }

  if (sortedData.length === 0) {
    return (
      <div className={`rounded-lg bg-white p-6 shadow-sm ${className}`}>
        <h3 className="mb-4 text-lg font-semibold text-gray-900">{title}</h3>
        <div
          className="flex items-center justify-center text-gray-500"
          style={{ height: `${height}px` }}
        >
          暂无数据
        </div>
      </div>
    );
  }

  const maxUsage = Math.max(...sortedData.map((d) => d.usageCount), 1);
  const totalUsage = sortedData.reduce((sum, d) => sum + d.usageCount, 0);

  return (
    <div className={`rounded-lg bg-white p-6 shadow-sm ${className}`}>
      <div className="mb-6">
        <h3 className="text-lg font-semibold text-gray-900">{title}</h3>
        <p className="text-sm text-gray-500">总使用次数: {totalUsage.toLocaleString()}</p>
      </div>

      <div className="space-y-4" style={{ minHeight: `${height - 80}px` }}>
        {sortedData.map((item, index) => {
          const percentage = (item.usageCount / maxUsage) * 100;
          const color = item.color || COLORS[index % COLORS.length];

          return (
            <div key={item.feature} className="space-y-2">
              <div className="flex items-center justify-between text-sm">
                <div className="flex items-center gap-2">
                  <span
                    className="h-3 w-3 rounded-full"
                    style={{ backgroundColor: color }}
                  ></span>
                  <span className="font-medium text-gray-900">{item.feature}</span>
                </div>
                <div className="flex items-center gap-2 text-gray-500">
                  <span>{item.usageCount.toLocaleString()} 次</span>
                  <span className="text-xs">({item.percentage}%)</span>
                </div>
              </div>
              <div className="h-2 w-full overflow-hidden rounded-full bg-gray-100">
                <div
                  className="h-full rounded-full transition-all duration-500 ease-out"
                  style={{
                    width: `${percentage}%`,
                    backgroundColor: color,
                  }}
                ></div>
              </div>
            </div>
          );
        })}
      </div>

      {/* 图例 */}
      <div className="mt-4 grid grid-cols-2 gap-2 text-xs">
        {sortedData.slice(0, 6).map((item, index) => (
          <div key={item.feature} className="flex items-center gap-2">
            <span
              className="h-2 w-2 rounded-full"
              style={{ backgroundColor: item.color || COLORS[index % COLORS.length] }}
            ></span>
            <span className="truncate text-gray-600">{item.feature}</span>
          </div>
        ))}
      </div>
    </div>
  );
}