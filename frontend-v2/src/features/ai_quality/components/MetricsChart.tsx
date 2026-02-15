/**
 * MetricsChart - 指标图表组件
 */

import { useMemo } from 'react';
import {
  Area,
  Bar,
  BarChart,
  Cell,
  CartesianGrid,
  ComposedChart,
  Legend,
  Line,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';

import type { AIMetrics, QualityTrendData } from '../types';

interface MetricsChartProps {
  metrics: AIMetrics | undefined;
  trendData: QualityTrendData | undefined;
  loading?: boolean;
}

const COLORS = ['#10B981', '#3B82F6', '#F59E0B', '#EF4444', '#8B5CF6', '#EC4899', '#14B8A6', '#F97316'];

/**
 * 指标图表组件
 */
export function MetricsChart({ metrics, trendData, loading = false }: MetricsChartProps): JSX.Element {
  // 响应时间分布数据
  const responseTimeData = useMemo(() => {
    if (!metrics?.response_time) return [];
    return [
      { name: '最小', value: metrics.response_time.min_ms, fill: '#10B981' },
      { name: 'P50', value: metrics.response_time.p50_ms, fill: '#3B82F6' },
      { name: '平均', value: metrics.response_time.avg_ms, fill: '#F59E0B' },
      { name: 'P95', value: metrics.response_time.p95_ms, fill: '#EF4444' },
      { name: 'P99', value: metrics.response_time.p99_ms, fill: '#8B5CF6' },
      { name: '最大', value: metrics.response_time.max_ms, fill: '#EC4899' },
    ];
  }, [metrics?.response_time]);

  // 错误分布数据
  const errorDistributionData = useMemo(() => {
    if (!metrics?.error_distribution) return [];
    const data = [
      { name: '超时', value: metrics.error_distribution.timeout, key: 'timeout' },
      { name: '限流', value: metrics.error_distribution.rate_limit, key: 'rate_limit' },
      { name: 'Token超限', value: metrics.error_distribution.token_exceeded, key: 'token_exceeded' },
      { name: '上下文超长', value: metrics.error_distribution.context_length, key: 'context_length' },
      { name: '服务不可用', value: metrics.error_distribution.service_unavailable, key: 'service_unavailable' },
      { name: '未知错误', value: metrics.error_distribution.unknown, key: 'unknown' },
    ].filter(item => item.value > 0);
    return data;
  }, [metrics?.error_distribution]);

  // 工具使用数据
  const toolUsageData = useMemo(() => {
    if (!metrics?.tool_usage) return [];
    return Object.entries(metrics.tool_usage)
      .map(([name, value]) => ({ name, value }))
      .sort((a, b) => b.value - a.value)
      .slice(0, 8);
  }, [metrics?.tool_usage]);

  // 趋势数据
  const trendChartData = useMemo(() => {
    if (!trendData) return [];
    return trendData.dates.map((date, index) => ({
      date: date.slice(5), // 去掉年份
      successRate: (trendData.success_rate[index] * 100).toFixed(1),
      qualityScore: trendData.avg_quality_score[index].toFixed(1),
      responseTime: trendData.response_time_p95[index].toFixed(0),
      satisfaction: (trendData.satisfaction_rate[index] * 100).toFixed(1),
    }));
  }, [trendData]);

  // 质量分布数据
  const qualityDistributionData = useMemo(() => {
    // 使用固定的质量评分分布字段
    const distribution = {
      excellent: metrics?.quality_score?.excellent || 0,
      good: metrics?.quality_score?.good || 0,
      average: metrics?.quality_score?.average || 0,
      poor: metrics?.quality_score?.poor || 0,
    };
    
    if (Object.values(distribution).every(v => v === 0)) return [];
    
    return Object.entries(distribution).map(([name, value]) => ({
      name: name === 'excellent' ? '优秀' : name === 'good' ? '良好' : name === 'average' ? '一般' : '较差',
      value,
    }));
  }, [metrics?.quality_score]);

  if (loading || !metrics) {
    return (
      <div className="space-y-6">
        <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
          <div className="h-80 rounded-lg bg-white p-6 shadow-sm">
            <div className="h-full animate-pulse rounded bg-gray-200"></div>
          </div>
          <div className="h-80 rounded-lg bg-white p-6 shadow-sm">
            <div className="h-full animate-pulse rounded bg-gray-200"></div>
          </div>
        </div>
        <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
          <div className="h-80 rounded-lg bg-white p-6 shadow-sm">
            <div className="h-full animate-pulse rounded bg-gray-200"></div>
          </div>
          <div className="h-80 rounded-lg bg-white p-6 shadow-sm">
            <div className="h-full animate-pulse rounded bg-gray-200"></div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* 趋势图表 */}
      {trendChartData.length > 0 && (
        <div className="rounded-lg bg-white p-6 shadow-sm">
          <h3 className="mb-4 text-lg font-medium text-gray-900">质量趋势分析</h3>
          <div className="h-80">
            <ResponsiveContainer width="100%" height="100%">
              <ComposedChart data={trendChartData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" />
                <XAxis dataKey="date" stroke="#6B7280" fontSize={12} />
                <YAxis yAxisId="left" stroke="#6B7280" fontSize={12} domain={[0, 100]} />
                <YAxis yAxisId="right" orientation="right" stroke="#6B7280" fontSize={12} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: 'white',
                    border: '1px solid #E5E7EB',
                    borderRadius: '8px',
                    boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)',
                  }}
                />
                <Legend />
                <Area
                  yAxisId="left"
                  type="monotone"
                  dataKey="successRate"
                  name="成功率 (%)"
                  stroke="#10B981"
                  fill="#10B981"
                  fillOpacity={0.1}
                  strokeWidth={2}
                />
                <Line
                  yAxisId="left"
                  type="monotone"
                  dataKey="qualityScore"
                  name="质量分"
                  stroke="#3B82F6"
                  strokeWidth={2}
                  dot={false}
                />
                <Line
                  yAxisId="left"
                  type="monotone"
                  dataKey="satisfaction"
                  name="满意度 (%)"
                  stroke="#8B5CF6"
                  strokeWidth={2}
                  dot={false}
                />
                <Line
                  yAxisId="right"
                  type="monotone"
                  dataKey="responseTime"
                  name="响应时间 (ms)"
                  stroke="#EF4444"
                  strokeWidth={2}
                  dot={false}
                />
              </ComposedChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        {/* 响应时间分布 */}
        <div className="rounded-lg bg-white p-6 shadow-sm">
          <h3 className="mb-4 text-lg font-medium text-gray-900">响应时间分布</h3>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={responseTimeData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" />
                <XAxis dataKey="name" stroke="#6B7280" fontSize={12} />
                <YAxis stroke="#6B7280" fontSize={12} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: 'white',
                    border: '1px solid #E5E7EB',
                    borderRadius: '8px',
                  }}
                  formatter={(value: number | undefined) => [`${(value ?? 0).toFixed(0)} ms`, '响应时间']}
                />
                <Bar dataKey="value" radius={[4, 4, 0, 0]}>
                  {responseTimeData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.fill} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
          <div className="mt-4 grid grid-cols-3 gap-2 text-center text-sm">
            <div className="rounded bg-gray-50 p-2">
              <p className="text-gray-500">平均</p>
              <p className="font-medium">{metrics.response_time.avg_ms.toFixed(0)}ms</p>
            </div>
            <div className="rounded bg-gray-50 p-2">
              <p className="text-gray-500">P95</p>
              <p className="font-medium">{metrics.response_time.p95_ms.toFixed(0)}ms</p>
            </div>
            <div className="rounded bg-gray-50 p-2">
              <p className="text-gray-500">P99</p>
              <p className="font-medium">{metrics.response_time.p99_ms.toFixed(0)}ms</p>
            </div>
          </div>
        </div>

        {/* 错误分布 */}
        <div className="rounded-lg bg-white p-6 shadow-sm">
          <h3 className="mb-4 text-lg font-medium text-gray-900">错误类型分布</h3>
          <div className="h-64">
            {errorDistributionData.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={errorDistributionData}
                    cx="50%"
                    cy="50%"
                    labelLine={false}
                    label={({ name, percent }) => `${name} ${((percent ?? 0) * 100).toFixed(0)}%`}
                    outerRadius={80}
                    fill="#8884d8"
                    dataKey="value"
                  >
                    {errorDistributionData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip
                    contentStyle={{
                      backgroundColor: 'white',
                      border: '1px solid #E5E7EB',
                      borderRadius: '8px',
                    }}
                  />
                  <Legend />
                </PieChart>
              </ResponsiveContainer>
            ) : (
              <div className="flex h-full items-center justify-center text-gray-500">
                暂无错误数据
              </div>
            )}
          </div>
          <div className="mt-4 text-center">
            <p className="text-sm text-gray-500">
              总错误数: <span className="font-medium text-red-600">{metrics.error_count}</span>
            </p>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        {/* 质量评分分布 */}
        <div className="rounded-lg bg-white p-6 shadow-sm">
          <h3 className="mb-4 text-lg font-medium text-gray-900">质量评分分布</h3>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={qualityDistributionData}
                  cx="50%"
                  cy="50%"
                  innerRadius={60}
                  outerRadius={80}
                  paddingAngle={5}
                  dataKey="value"
                >
                  {qualityDistributionData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip
                  contentStyle={{
                    backgroundColor: 'white',
                    border: '1px solid #E5E7EB',
                    borderRadius: '8px',
                  }}
                />
                <Legend />
              </PieChart>
            </ResponsiveContainer>
          </div>
          <div className="mt-4 text-center">
            <p className="text-sm text-gray-500">
              平均质量分: <span className="font-medium text-blue-600">{metrics.quality_score.avg.toFixed(1)}</span>
            </p>
          </div>
        </div>

        {/* 工具使用统计 */}
        <div className="rounded-lg bg-white p-6 shadow-sm">
          <h3 className="mb-4 text-lg font-medium text-gray-900">工具使用统计</h3>
          <div className="h-64">
            {toolUsageData.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={toolUsageData} layout="vertical">
                  <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" />
                  <XAxis type="number" stroke="#6B7280" fontSize={12} />
                  <YAxis dataKey="name" type="category" width={100} stroke="#6B7280" fontSize={12} />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: 'white',
                      border: '1px solid #E5E7EB',
                      borderRadius: '8px',
                    }}
                  />
                  <Bar dataKey="value" fill="#3B82F6" radius={[0, 4, 4, 0]} />
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <div className="flex h-full items-center justify-center text-gray-500">
                暂无工具使用数据
              </div>
            )}
          </div>
        </div>
      </div>

      {/* 话题分布 */}
      {metrics.topic_distribution && Object.keys(metrics.topic_distribution).length > 0 && (
        <div className="rounded-lg bg-white p-6 shadow-sm">
          <h3 className="mb-4 text-lg font-medium text-gray-900">话题分布</h3>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart
                data={Object.entries(metrics.topic_distribution)
                  .map(([name, value]) => ({ name, value }))
                  .sort((a, b) => b.value - a.value)
                  .slice(0, 10)}
              >
                <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" />
                <XAxis dataKey="name" stroke="#6B7280" fontSize={12} />
                <YAxis stroke="#6B7280" fontSize={12} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: 'white',
                    border: '1px solid #E5E7EB',
                    borderRadius: '8px',
                  }}
                />
                <Bar dataKey="value" fill="#10B981" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}
    </div>
  );
}

/**
 * 实时指标卡片
 */
export function MetricCard({
  title,
  value,
  unit,
  trend,
  threshold,
  status,
}: {
  title: string;
  value: number;
  unit?: string;
  trend?: 'up' | 'down' | 'stable';
  threshold?: number;
  status?: 'good' | 'warning' | 'critical';
}): JSX.Element {
  const statusColors = {
    good: 'bg-green-50 border-green-200',
    warning: 'bg-yellow-50 border-yellow-200',
    critical: 'bg-red-50 border-red-200',
  };

  const valueColors = {
    good: 'text-green-700',
    warning: 'text-yellow-700',
    critical: 'text-red-700',
  };

  const trendIcon = trend === 'up' 
    ? '↑' 
    : trend === 'down' 
    ? '↓' 
    : '→';

  return (
    <div className={`rounded-lg border p-4 ${status ? statusColors[status] : 'bg-white border-gray-200'}`}>
      <p className="text-sm text-gray-500">{title}</p>
      <div className="mt-1 flex items-baseline gap-2">
        <span className={`text-2xl font-bold ${status ? valueColors[status] : 'text-gray-900'}`}>
          {value.toFixed(unit === '%' ? 1 : 0)}
        </span>
        {unit && <span className="text-sm text-gray-500">{unit}</span>}
        {trend && (
          <span className={`text-sm ${trend === 'up' ? 'text-green-500' : trend === 'down' ? 'text-red-500' : 'text-gray-500'}`}>
            {trendIcon}
          </span>
        )}
      </div>
      {threshold !== undefined && (
        <p className="mt-1 text-xs text-gray-400">阈值: {threshold}</p>
      )}
    </div>
  );
}