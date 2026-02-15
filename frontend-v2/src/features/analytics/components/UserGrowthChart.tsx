/**
 * UserGrowthChart - 用户增长图表组件
 */

import type { UserGrowthPoint } from '../types';

interface UserGrowthChartProps {
  data: UserGrowthPoint[];
  title?: string;
  loading?: boolean;
  className?: string;
  height?: number;
}

/**
 * 计算 SVG 路径
 */
function calculatePath(data: UserGrowthPoint[], width: number, height: number): string {
  if (data.length === 0) return '';

  const maxValue = Math.max(...data.map((d) => d.totalUsers), 1);
  const minValue = Math.min(...data.map((d) => d.totalUsers), 0);
  const valueRange = maxValue - minValue || 1;

  const padding = 30;
  const chartWidth = width - padding * 2;
  const chartHeight = height - padding * 2;

  return data
    .map((point, index) => {
      const x = padding + (index / (data.length - 1 || 1)) * chartWidth;
      const y = padding + chartHeight - ((point.totalUsers - minValue) / valueRange) * chartHeight;
      return `${index === 0 ? 'M' : 'L'} ${x} ${y}`;
    })
    .join(' ');
}

/**
 * 计算柱状图路径
 */
function calculateBars(data: UserGrowthPoint[], width: number, height: number): Array<{ x: number; y: number; height: number; value: number }> {
  if (data.length === 0) return [];

  const maxValue = Math.max(...data.map((d) => d.newUsers), 1);
  const padding = 30;
  const chartWidth = width - padding * 2;
  const chartHeight = height - padding * 2;
  const barWidth = chartWidth / data.length * 0.6;

  return data.map((point, index) => {
    const x = padding + (index / (data.length - 1 || 1)) * chartWidth - barWidth / 2;
    const barHeight = (point.newUsers / maxValue) * chartHeight * 0.5;
    const y = padding + chartHeight - barHeight;
    return { x, y, height: barHeight, value: point.newUsers };
  });
}

/**
 * 用户增长图表组件
 */
export function UserGrowthChart({
  data,
  title = '用户增长趋势',
  loading = false,
  className = '',
  height = 350,
}: UserGrowthChartProps): JSX.Element {
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

  if (data.length === 0) {
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

  const svgWidth = 800;
  const svgHeight = height;
  const bars = calculateBars(data, svgWidth, svgHeight);

  // 计算统计数据
  const totalNewUsers = data.reduce((sum, d) => sum + d.newUsers, 0);
  const avgNewUsers = Math.round(totalNewUsers / data.length);
  const latestTotal = data[data.length - 1]?.totalUsers || 0;
  const previousTotal = data[data.length - 2]?.totalUsers || latestTotal;
  const growthRate = previousTotal > 0 ? ((latestTotal - previousTotal) / previousTotal) * 100 : 0;

  return (
    <div className={`rounded-lg bg-white p-6 shadow-sm ${className}`}>
      <div className="mb-4 flex items-center justify-between">
        <h3 className="text-lg font-semibold text-gray-900">{title}</h3>
        <div className="flex items-center gap-4 text-sm">
          <span className="flex items-center gap-1">
            <span className="h-3 w-3 rounded-full bg-blue-500"></span>
            总用户数
          </span>
          <span className="flex items-center gap-1">
            <span className="h-3 w-3 rounded bg-green-400"></span>
            新增用户
          </span>
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
              y1={(svgHeight / 4) * i + 30}
              x2={svgWidth}
              y2={(svgHeight / 4) * i + 30}
              stroke="#f3f4f6"
              strokeWidth="1"
            />
          ))}

          {/* 总用户数折线 */}
          <path
            d={calculatePath(data, svgWidth, svgHeight)}
            fill="none"
            stroke="#3b82f6"
            strokeWidth="3"
            strokeLinecap="round"
            strokeLinejoin="round"
          />

          {/* 新增用户柱状图 */}
          {bars.map((bar, index) => (
            <rect
              key={index}
              x={bar.x}
              y={bar.y}
              width={(svgWidth - 60) / data.length * 0.5}
              height={bar.height}
              fill="#4ade80"
              rx="2"
            >
              <title>{`新增: ${bar.value}`}</title>
            </rect>
          ))}

          {/* 数据点 */}
          {data.map((point, index) => {
            const maxVal = Math.max(...data.map((d) => d.totalUsers), 1);
            const minVal = Math.min(...data.map((d) => d.totalUsers), 0);
            const range = maxVal - minVal || 1;
            const padding = 30;
            const chartWidth = svgWidth - padding * 2;
            const chartHeight = svgHeight - padding * 2;
            const x = padding + (index / (data.length - 1 || 1)) * chartWidth;
            const y = padding + chartHeight - ((point.totalUsers - minVal) / range) * chartHeight;

            return (
              <g key={index}>
                <circle cx={x} cy={y} r="5" fill="white" stroke="#3b82f6" strokeWidth="2" />
                <title>{`${point.date}: 总用户 ${point.totalUsers}, 新增 ${point.newUsers}`}</title>
              </g>
            );
          })}
        </svg>
      </div>

      {/* X轴标签 */}
      <div className="mt-2 flex justify-between text-xs text-gray-400">
        {data.length > 0 && <span>{data[0].date}</span>}
        {data.length > 1 && (
          <span>{data[Math.floor(data.length / 2)].date}</span>
        )}
        {data.length > 2 && <span>{data[data.length - 1].date}</span>}
      </div>

      {/* 统计信息 */}
      <div className="mt-6 grid grid-cols-4 gap-4 border-t border-gray-100 pt-4">
        <div className="text-center">
          <p className="text-xs text-gray-500">总用户数</p>
          <p className="text-lg font-semibold text-gray-900">{latestTotal.toLocaleString()}</p>
        </div>
        <div className="text-center">
          <p className="text-xs text-gray-500">本期新增</p>
          <p className="text-lg font-semibold text-green-600">{totalNewUsers.toLocaleString()}</p>
        </div>
        <div className="text-center">
          <p className="text-xs text-gray-500">日均新增</p>
          <p className="text-lg font-semibold text-gray-900">{avgNewUsers.toLocaleString()}</p>
        </div>
        <div className="text-center">
          <p className="text-xs text-gray-500">增长率</p>
          <p className={`text-lg font-semibold ${growthRate >= 0 ? 'text-green-600' : 'text-red-600'}`}>
            {growthRate >= 0 ? '+' : ''}
            {growthRate.toFixed(1)}%
          </p>
        </div>
      </div>
    </div>
  );
}