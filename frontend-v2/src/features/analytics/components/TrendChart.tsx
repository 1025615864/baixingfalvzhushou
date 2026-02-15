/**
 * TrendChart - 趋势图表组件
 */

import type { TrendDataPoint } from '../types';

interface TrendChartProps {
  data: TrendDataPoint[];
  title?: string;
  loading?: boolean;
  className?: string;
  height?: number;
  showArea?: boolean;
  color?: string;
  unit?: string;
}

/**
 * 计算 SVG 路径
 */
function calculatePath(data: TrendDataPoint[], width: number, height: number): string {
  if (data.length === 0) return '';

  const maxValue = Math.max(...data.map((d) => d.value), 1);
  const minValue = Math.min(...data.map((d) => d.value), 0);
  const valueRange = maxValue - minValue || 1;

  const padding = 20;
  const chartWidth = width - padding * 2;
  const chartHeight = height - padding * 2;

  return data
    .map((point, index) => {
      const x = padding + (index / (data.length - 1 || 1)) * chartWidth;
      const y = padding + chartHeight - ((point.value - minValue) / valueRange) * chartHeight;
      return `${index === 0 ? 'M' : 'L'} ${x} ${y}`;
    })
    .join(' ');
}

/**
 * 计算区域路径
 */
function calculateAreaPath(data: TrendDataPoint[], width: number, height: number): string {
  if (data.length === 0) return '';

  const maxValue = Math.max(...data.map((d) => d.value), 1);
  const minValue = Math.min(...data.map((d) => d.value), 0);
  const valueRange = maxValue - minValue || 1;

  const padding = 20;
  const chartWidth = width - padding * 2;
  const chartHeight = height - padding * 2;

  const points = data.map((point, index) => {
    const x = padding + (index / (data.length - 1 || 1)) * chartWidth;
    const y = padding + chartHeight - ((point.value - minValue) / valueRange) * chartHeight;
    return `${x},${y}`;
  });

  return `M ${points[0]} ${points.map((p) => `L ${p}`).join(' ')} L ${padding + chartWidth} ${padding + chartHeight} L ${padding} ${padding + chartHeight} Z`;
}

export function TrendChart({
  data,
  title,
  loading = false,
  className = '',
  height = 300,
  showArea = true,
  color = '#3b82f6',
  unit = '',
}: TrendChartProps): JSX.Element {
  if (loading) {
    return (
      <div className={`rounded-lg bg-white p-6 shadow-sm ${className}`}>
        {title && <h3 className="mb-4 text-lg font-semibold text-gray-900">{title}</h3>}
        <div className="animate-pulse" style={{ height: `${height}px` }}>
          <div className="h-full w-full rounded-lg bg-gray-200"></div>
        </div>
      </div>
    );
  }

  if (data.length === 0) {
    return (
      <div className={`rounded-lg bg-white p-6 shadow-sm ${className}`}>
        {title && <h3 className="mb-4 text-lg font-semibold text-gray-900">{title}</h3>}
        <div className="flex items-center justify-center text-gray-500" style={{ height: `${height}px` }}>
          暂无数据
        </div>
      </div>
    );
  }

  const maxValue = Math.max(...data.map((d) => d.value), 1);
  const minValue = Math.min(...data.map((d) => d.value), 0);
  const svgWidth = 800;
  const svgHeight = height;

  return (
    <div className={`rounded-lg bg-white p-6 shadow-sm ${className}`}>
      {title && <h3 className="mb-4 text-lg font-semibold text-gray-900">{title}</h3>}

      <div className="relative" style={{ height: `${height}px` }}>
        <svg
          viewBox={`0 0 ${svgWidth} ${svgHeight}`}
          className="h-full w-full"
          preserveAspectRatio="none"
        >
          {/* 渐变定义 */}
          <defs>
            <linearGradient id="trendGradient" x1="0%" y1="0%" x2="0%" y2="100%">
              <stop offset="0%" stopColor={color} stopOpacity="0.3" />
              <stop offset="100%" stopColor={color} stopOpacity="0" />
            </linearGradient>
          </defs>

          {/* 网格线 */}
          {[0, 1, 2, 3, 4].map((i) => (
            <line
              key={i}
              x1="0"
              y1={(svgHeight / 4) * i}
              x2={svgWidth}
              y2={(svgHeight / 4) * i}
              stroke="#f3f4f6"
              strokeWidth="1"
            />
          ))}

          {/* 区域填充 */}
          {showArea && (
            <path
              d={calculateAreaPath(data, svgWidth, svgHeight)}
              fill="url(#trendGradient)"
              stroke="none"
            />
          )}

          {/* 趋势线 */}
          <path
            d={calculatePath(data, svgWidth, svgHeight)}
            fill="none"
            stroke={color}
            strokeWidth="3"
            strokeLinecap="round"
            strokeLinejoin="round"
          />

          {/* 数据点 */}
          {data.map((point, index) => {
            const maxVal = Math.max(...data.map((d) => d.value), 1);
            const minVal = Math.min(...data.map((d) => d.value), 0);
            const range = maxVal - minVal || 1;
            const padding = 20;
            const chartWidth = svgWidth - padding * 2;
            const chartHeight = svgHeight - padding * 2;
            const x = padding + (index / (data.length - 1 || 1)) * chartWidth;
            const y = padding + chartHeight - ((point.value - minVal) / range) * chartHeight;

            return (
              <g key={index}>
                <circle cx={x} cy={y} r="5" fill="white" stroke={color} strokeWidth="2" />
                <title>{`${point.label || point.date}: ${point.value}${unit}`}</title>
              </g>
            );
          })}
        </svg>

        {/* Y轴标签 */}
        <div className="absolute left-0 top-0 flex h-full flex-col justify-between text-xs text-gray-400">
          <span>{Math.round(maxValue)}{unit}</span>
          <span>{Math.round((maxValue + minValue) / 2)}{unit}</span>
          <span>{Math.round(minValue)}{unit}</span>
        </div>
      </div>

      {/* X轴标签 */}
      <div className="mt-2 flex justify-between text-xs text-gray-400">
        {data.length > 0 && <span>{data[0].label || data[0].date}</span>}
        {data.length > 1 && (
          <span>{data[Math.floor(data.length / 2)].label || data[Math.floor(data.length / 2)].date}</span>
        )}
        {data.length > 2 && <span>{data[data.length - 1].label || data[data.length - 1].date}</span>}
      </div>

      {/* 数据统计 */}
      <div className="mt-4 grid grid-cols-3 gap-4 border-t border-gray-100 pt-4">
        <div className="text-center">
          <p className="text-xs text-gray-500">最高值</p>
          <p className="text-lg font-semibold text-gray-900">
            {maxValue.toLocaleString()}{unit}
          </p>
        </div>
        <div className="text-center">
          <p className="text-xs text-gray-500">平均值</p>
          <p className="text-lg font-semibold text-gray-900">
            {Math.round(data.reduce((sum, d) => sum + d.value, 0) / data.length).toLocaleString()}{unit}
          </p>
        </div>
        <div className="text-center">
          <p className="text-xs text-gray-500">最低值</p>
          <p className="text-lg font-semibold text-gray-900">
            {minValue.toLocaleString()}{unit}
          </p>
        </div>
      </div>
    </div>
  );
}

/**
 * 对比趋势图（显示当前期和上一期对比）
 */
interface ComparisonTrendChartProps {
  currentData: TrendDataPoint[];
  previousData: TrendDataPoint[];
  title?: string;
  loading?: boolean;
  className?: string;
  height?: number;
  currentLabel?: string;
  previousLabel?: string;
}

export function ComparisonTrendChart({
  currentData,
  previousData,
  title,
  loading = false,
  className = '',
  height = 300,
  currentLabel = '本期',
  previousLabel = '上期',
}: ComparisonTrendChartProps): JSX.Element {
  if (loading) {
    return (
      <div className={`rounded-lg bg-white p-6 shadow-sm ${className}`}>
        {title && <h3 className="mb-4 text-lg font-semibold text-gray-900">{title}</h3>}
        <div className="animate-pulse" style={{ height: `${height}px` }}>
          <div className="h-full w-full rounded-lg bg-gray-200"></div>
        </div>
      </div>
    );
  }

  if (currentData.length === 0 && previousData.length === 0) {
    return (
      <div className={`rounded-lg bg-white p-6 shadow-sm ${className}`}>
        {title && <h3 className="mb-4 text-lg font-semibold text-gray-900">{title}</h3>}
        <div className="flex items-center justify-center text-gray-500" style={{ height: `${height}px` }}>
          暂无数据
        </div>
      </div>
    );
  }

  const allValues = [...currentData.map((d) => d.value), ...previousData.map((d) => d.value)];
  const maxValue = Math.max(...allValues, 1);
  const minValue = Math.min(...allValues, 0);
  const svgWidth = 800;
  const svgHeight = height;

  const currentColor = '#3b82f6';
  const previousColor = '#9ca3af';

  return (
    <div className={`rounded-lg bg-white p-6 shadow-sm ${className}`}>
      {title && <h3 className="mb-4 text-lg font-semibold text-gray-900">{title}</h3>}

      {/* 图例 */}
      <div className="mb-4 flex items-center gap-4">
        <div className="flex items-center gap-2">
          <div className="h-3 w-3 rounded-full" style={{ backgroundColor: currentColor }} />
          <span className="text-sm text-gray-600">{currentLabel}</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="h-3 w-3 rounded-full" style={{ backgroundColor: previousColor }} />
          <span className="text-sm text-gray-600">{previousLabel}</span>
        </div>
      </div>

      <div className="relative" style={{ height: `${height}px` }}>
        <svg
          viewBox={`0 0 ${svgWidth} ${svgHeight}`}
          className="h-full w-full"
          preserveAspectRatio="none"
        >
          {/* 网格线 */}
          {[0, 1, 2, 3, 4].map((i) => (
            <line
              key={i}
              x1="0"
              y1={(svgHeight / 4) * i}
              x2={svgWidth}
              y2={(svgHeight / 4) * i}
              stroke="#f3f4f6"
              strokeWidth="1"
            />
          ))}

          {/* 上一期趋势线 */}
          {previousData.length > 0 && (
            <path
              d={calculatePath(previousData, svgWidth, svgHeight)}
              fill="none"
              stroke={previousColor}
              strokeWidth="2"
              strokeDasharray="5,5"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
          )}

          {/* 本期趋势线 */}
          {currentData.length > 0 && (
            <path
              d={calculatePath(currentData, svgWidth, svgHeight)}
              fill="none"
              stroke={currentColor}
              strokeWidth="3"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
          )}
        </svg>

        {/* Y轴标签 */}
        <div className="absolute left-0 top-0 flex h-full flex-col justify-between text-xs text-gray-400">
          <span>{Math.round(maxValue)}</span>
          <span>{Math.round((maxValue + minValue) / 2)}</span>
          <span>{Math.round(minValue)}</span>
        </div>
      </div>
    </div>
  );
}

/**
 * 条形图
 */
interface BarChartProps {
  data: TrendDataPoint[];
  title?: string;
  loading?: boolean;
  className?: string;
  height?: number;
  color?: string;
  unit?: string;
}

export function BarChart({
  data,
  title,
  loading = false,
  className = '',
  height = 300,
  color = '#3b82f6',
  unit = '',
}: BarChartProps): JSX.Element {
  if (loading) {
    return (
      <div className={`rounded-lg bg-white p-6 shadow-sm ${className}`}>
        {title && <h3 className="mb-4 text-lg font-semibold text-gray-900">{title}</h3>}
        <div className="animate-pulse" style={{ height: `${height}px` }}>
          <div className="h-full w-full rounded-lg bg-gray-200"></div>
        </div>
      </div>
    );
  }

  if (data.length === 0) {
    return (
      <div className={`rounded-lg bg-white p-6 shadow-sm ${className}`}>
        {title && <h3 className="mb-4 text-lg font-semibold text-gray-900">{title}</h3>}
        <div className="flex items-center justify-center text-gray-500" style={{ height: `${height}px` }}>
          暂无数据
        </div>
      </div>
    );
  }

  const maxValue = Math.max(...data.map((d) => d.value), 1);

  return (
    <div className={`rounded-lg bg-white p-6 shadow-sm ${className}`}>
      {title && <h3 className="mb-4 text-lg font-semibold text-gray-900">{title}</h3>}

      <div className="flex items-end justify-between gap-2" style={{ height: `${height}px` }}>
        {data.map((item, index) => {
          const heightPercent = (item.value / maxValue) * 100;
          return (
            <div key={index} className="flex flex-1 flex-col items-center gap-1">
              <div className="relative w-full flex-1 rounded-t bg-gray-100">
                <div
                  className="absolute bottom-0 w-full rounded-t transition-all duration-500"
                  style={{
                    height: `${Math.max(heightPercent, 5)}%`,
                    backgroundColor: color,
                  }}
                  title={`${item.label || item.date}: ${item.value}${unit}`}
                />
              </div>
              <span className="text-xs text-gray-500 truncate max-w-full">
                {item.label || item.date}
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
}