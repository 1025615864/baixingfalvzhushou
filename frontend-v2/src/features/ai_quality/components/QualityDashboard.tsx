/**
 * QualityDashboard - 质量仪表盘组件
 */

import { useMemo } from 'react';
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Line,
  LineChart,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';

import type { DashboardData, QualityTrendData } from '../types';

interface QualityDashboardProps {
  data: DashboardData | undefined;
  trendData: QualityTrendData | undefined;
  loading?: boolean;
}

/**
 * 格式化数字
 */
function formatNumber(value: number, decimals = 0): string {
  if (value >= 1000000) {
    return `${(value / 1000000).toFixed(decimals)}M`;
  }
  if (value >= 1000) {
    return `${(value / 1000).toFixed(decimals)}K`;
  }
  return value.toFixed(decimals);
}

/**
 * 格式化百分比
 */
function formatPercent(value: number): string {
  return `${(value * 100).toFixed(1)}%`;
}

/**
 * 获取趋势颜色
 */
function _getTrendColor(trend: string): string {
  switch (trend) {
    case 'increasing':
      return 'text-green-600';
    case 'decreasing':
      return 'text-red-600';
    default:
      return 'text-gray-600';
  }
}

/**
 * 获取趋势图标
 */
function TrendIcon({ trend }: { trend: string }): JSX.Element {
  if (trend === 'increasing') {
    return (
      <svg className="h-4 w-4 text-green-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
      </svg>
    );
  }
  if (trend === 'decreasing') {
    return (
      <svg className="h-4 w-4 text-red-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 17h8m0 0V9m0 8l-8-8-4 4-6-6" />
      </svg>
    );
  }
  return (
    <svg className="h-4 w-4 text-gray-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 12h14" />
    </svg>
  );
}

const COLORS = ['#10B981', '#3B82F6', '#F59E0B', '#EF4444', '#8B5CF6', '#EC4899'];

/**
 * 统计卡片骨架屏
 */
function StatCardSkeleton(): JSX.Element {
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
 * 统计卡片
 */
interface StatCardProps {
  title: string;
  value: string;
  subtitle?: string;
  trend?: string;
  icon: React.ReactNode;
  color?: string;
}

function StatCard({ title, value, subtitle, trend, icon, color = 'blue' }: StatCardProps): JSX.Element {
  const colorClasses: Record<string, string> = {
    blue: 'bg-blue-50 text-blue-600',
    green: 'bg-green-50 text-green-600',
    yellow: 'bg-yellow-50 text-yellow-600',
    red: 'bg-red-50 text-red-600',
    purple: 'bg-purple-50 text-purple-600',
  };

  return (
    <div className="rounded-lg bg-white p-6 shadow-sm transition-shadow hover:shadow-md">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-medium text-gray-500">{title}</h3>
        <div className={`rounded-full p-2 ${colorClasses[color]}`}>{icon}</div>
      </div>

      <div className="mt-4">
        <p className="text-2xl font-bold text-gray-900">{value}</p>

        {(subtitle || trend) && (
          <div className="mt-2 flex items-center gap-2">
            {trend && <TrendIcon trend={trend} />}
            {subtitle && <span className="text-sm text-gray-500">{subtitle}</span>}
          </div>
        )}
      </div>
    </div>
  );
}

/**
 * 消息图标
 */
function MessageIcon({ className = 'h-6 w-6' }: { className?: string }): JSX.Element {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth={2}
        d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z"
      />
    </svg>
  );
}

/**
 * 成功图标
 */
function SuccessIcon({ className = 'h-6 w-6' }: { className?: string }): JSX.Element {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
    </svg>
  );
}

/**
 * 时钟图标
 */
function ClockIcon({ className = 'h-6 w-6' }: { className?: string }): JSX.Element {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
    </svg>
  );
}

/**
 * 评分图标
 */
function StarIcon({ className = 'h-6 w-6' }: { className?: string }): JSX.Element {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth={2}
        d="M11.049 2.927c.3-.921 1.603-.921 1.902 0l1.519 4.674a1 1 0 00.95.69h4.915c.969 0 1.371 1.24.588 1.81l-3.976 2.888a1 1 0 00-.363 1.118l1.518 4.674c.3.922-.755 1.688-1.538 1.118l-3.976-2.888a1 1 0 00-1.176 0l-3.976 2.888c-.783.57-1.838-.197-1.538-1.118l1.518-4.674a1 1 0 00-.363-1.118l-3.976-2.888c-.784-.57-.38-1.81.588-1.81h4.914a1 1 0 00.951-.69l1.519-4.674z"
      />
    </svg>
  );
}

/**
 * 质量仪表盘组件
 */
export function QualityDashboard({ data, trendData, loading = false }: QualityDashboardProps): JSX.Element {
  const qualityDistribution = useMemo(() => {
    if (!data?.quality_distribution) return [];
    return Object.entries(data.quality_distribution).map(([name, value]) => ({
      name: name === 'excellent' ? '优秀' : name === 'good' ? '良好' : name === 'average' ? '一般' : '较差',
      value,
    }));
  }, [data?.quality_distribution]);

  const topicDistribution = useMemo(() => {
    if (!data?.topic_distribution) return [];
    return Object.entries(data.topic_distribution)
      .map(([name, value]) => ({ name, value }))
      .sort((a, b) => b.value - a.value)
      .slice(0, 6);
  }, [data?.topic_distribution]);

  const trendChartData = useMemo(() => {
    if (!trendData) return [];
    return trendData.dates.map((date, index) => ({
      date,
      successRate: trendData.success_rate[index] * 100,
      qualityScore: trendData.avg_quality_score[index],
      responseTime: trendData.response_time_p95[index],
      satisfaction: trendData.satisfaction_rate[index] * 100,
    }));
  }, [trendData]);

  if (loading || !data) {
    return (
      <div className="space-y-6">
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-4">
          {[1, 2, 3, 4].map((index) => (
            <StatCardSkeleton key={index} />
          ))}
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
      {/* 统计卡片 */}
      <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-4">
        <StatCard
          title="总会话数"
          value={formatNumber(data.summary.total_conversations)}
          subtitle="总对话数量"
          trend={data.trend?.quality_trend}
          icon={<MessageIcon className="h-6 w-6" />}
          color="blue"
        />
        <StatCard
          title="成功率"
          value={formatPercent(data.summary.success_rate)}
          subtitle="对话成功比例"
          trend={data.trend?.satisfaction_trend}
          icon={<SuccessIcon className="h-6 w-6" />}
          color="green"
        />
        <StatCard
          title="平均响应时间"
          value={`${data.summary.avg_response_time_ms.toFixed(0)}ms`}
          subtitle="P95: ${data.response_time.p95_ms.toFixed(0)}ms"
          trend={data.trend?.response_time_trend}
          icon={<ClockIcon className="h-6 w-6" />}
          color="yellow"
        />
        <StatCard
          title="平均质量分"
          value={data.summary.avg_quality_score.toFixed(1)}
          subtitle={`满意度: ${formatPercent(data.summary.satisfaction_rate)}`}
          trend={data.trend?.quality_trend}
          icon={<StarIcon className="h-6 w-6" />}
          color="purple"
        />
      </div>

      {/* 趋势图表 */}
      {trendChartData.length > 0 && (
        <div className="rounded-lg bg-white p-6 shadow-sm">
          <h3 className="mb-4 text-lg font-medium text-gray-900">质量趋势（最近7天）</h3>
          <div className="h-80">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={trendChartData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="date" />
                <YAxis yAxisId="left" />
                <YAxis yAxisId="right" orientation="right" />
                <Tooltip />
                <Line
                  yAxisId="left"
                  type="monotone"
                  dataKey="successRate"
                  name="成功率(%)"
                  stroke="#10B981"
                  strokeWidth={2}
                />
                <Line
                  yAxisId="right"
                  type="monotone"
                  dataKey="qualityScore"
                  name="质量分"
                  stroke="#3B82F6"
                  strokeWidth={2}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}

      {/* 分布图表 */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        {/* 质量分布 */}
        <div className="rounded-lg bg-white p-6 shadow-sm">
          <h3 className="mb-4 text-lg font-medium text-gray-900">质量分布</h3>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={qualityDistribution}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={({ name, percent }) => `${name} ${((percent ?? 0) * 100).toFixed(0)}%`}
                  outerRadius={80}
                  fill="#8884d8"
                  dataKey="value"
                >
                  {qualityDistribution.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* 话题分布 */}
        <div className="rounded-lg bg-white p-6 shadow-sm">
          <h3 className="mb-4 text-lg font-medium text-gray-900">热门话题</h3>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={topicDistribution} layout="vertical">
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis type="number" />
                <YAxis dataKey="name" type="category" width={100} />
                <Tooltip />
                <Bar dataKey="value" fill="#3B82F6" radius={[0, 4, 4, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* 反馈统计 */}
      <div className="rounded-lg bg-white p-6 shadow-sm">
        <h3 className="mb-4 text-lg font-medium text-gray-900">用户反馈</h3>
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
          <div className="flex items-center justify-between rounded-lg bg-green-50 p-4">
            <div>
              <p className="text-sm font-medium text-green-600">正面反馈</p>
              <p className="text-2xl font-bold text-green-700">{data.feedback.positive}</p>
            </div>
            <div className="rounded-full bg-green-100 p-3">
              <svg className="h-6 w-6 text-green-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14 10h4.764a2 2 0 011.789 2.894l-3.5 7A2 2 0 0115.263 21h-4.017c-.163 0-.326-.02-.485-.06L7 20m7-10V5a2 2 0 00-2-2h-.095c-.5 0-.905.405-.905.905 0 .714-.211 1.412-.608 2.006L7 11v9m7-10h-2M7 20H5a2 2 0 01-2-2v-6a2 2 0 012-2h2.5" />
              </svg>
            </div>
          </div>
          <div className="flex items-center justify-between rounded-lg bg-red-50 p-4">
            <div>
              <p className="text-sm font-medium text-red-600">负面反馈</p>
              <p className="text-2xl font-bold text-red-700">{data.feedback.negative}</p>
            </div>
            <div className="rounded-full bg-red-100 p-3">
              <svg className="h-6 w-6 text-red-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 14H5.236a2 2 0 01-1.789-2.894l3.5-7A2 2 0 018.736 3h4.018a2 2 0 01.485.06l3.76.94m-7 10v5a2 2 0 002 2h.095c.5 0 .905-.405.905-.905 0-.714.211-1.412.608-2.006L17 13V4m-7 10h2m5-10h2a2 2 0 012 2v6a2 2 0 01-2 2h-2.5" />
              </svg>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}