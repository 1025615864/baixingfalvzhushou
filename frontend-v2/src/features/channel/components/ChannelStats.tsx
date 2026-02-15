/**
 * ChannelStats 组件 - 渠道统计
 */

import type { ReactNode } from 'react';

import type { ChannelAnalytics, ChannelStatsSummary } from '../types';

interface ChannelStatsProps {
  summary?: ChannelStatsSummary;
  analytics?: ChannelAnalytics[];
  selectedChannelId?: string;
  isLoading?: boolean;
}

interface StatCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  trend?: 'up' | 'down' | 'neutral';
  trendValue?: string;
  icon?: ReactNode;
  color?: 'blue' | 'green' | 'yellow' | 'red' | 'purple';
}

function StatCard({
  title,
  value,
  subtitle,
  trend,
  trendValue,
  icon,
  color = 'blue',
}: StatCardProps): JSX.Element {
  const colorMap = {
    blue: 'bg-blue-50 border-blue-200',
    green: 'bg-green-50 border-green-200',
    yellow: 'bg-yellow-50 border-yellow-200',
    red: 'bg-red-50 border-red-200',
    purple: 'bg-purple-50 border-purple-200',
  };

  const trendColor = trend === 'up' ? 'text-green-600' : trend === 'down' ? 'text-red-600' : 'text-gray-500';

  return (
    <div className={`p-6 rounded-lg border ${colorMap[color]}`}>
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm font-medium text-gray-600">{title}</p>
          <p className="mt-2 text-3xl font-bold text-gray-900">{value}</p>
          {subtitle && <p className="mt-1 text-sm text-gray-500">{subtitle}</p>}
          {trend && trendValue && (
            <p className={`mt-1 text-sm font-medium ${trendColor}`}>
              {trend === 'up' ? '↑' : trend === 'down' ? '↓' : '→'} {trendValue}
            </p>
          )}
        </div>
        {icon && (
          <div className="p-3 bg-white rounded-full shadow-sm">
            {icon}
          </div>
        )}
      </div>
    </div>
  );
}

interface FunnelChartProps {
  funnel: ChannelAnalytics['funnel'];
  channelName: string;
}

function FunnelChart({ funnel, channelName }: FunnelChartProps): JSX.Element {
  const steps = [
    { label: '访问', value: funnel.visits, percentage: 100 },
    { label: '注册', value: funnel.registers, percentage: funnel.registersPercentage },
    { label: '激活', value: funnel.activations, percentage: funnel.activationsPercentage },
    { label: '付费', value: funnel.payments, percentage: funnel.paymentsPercentage },
  ];

  const maxWidth = 100;

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <h3 className="text-lg font-medium text-gray-900 mb-6">{channelName} - 转化漏斗</h3>
      <div className="space-y-4">
        {steps.map((step, index) => {
          const width = index === 0 ? maxWidth : (step.percentage / 100) * maxWidth;
          const colors = ['bg-blue-500', 'bg-green-500', 'bg-yellow-500', 'bg-red-500'];

          return (
            <div key={step.label} className="relative">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-medium text-gray-700">{step.label}</span>
                <span className="text-sm text-gray-500">
                  {step.value.toLocaleString()} ({step.percentage.toFixed(1)}%)
                </span>
              </div>
              <div className="h-8 bg-gray-100 rounded-full overflow-hidden">
                <div
                  className={`h-full ${colors[index]} transition-all duration-500 flex items-center justify-end pr-3`}
                  style={{ width: `${Math.max(width, 5)}%` }}
                >
                  {width > 20 && (
                    <span className="text-white text-xs font-medium">{step.percentage.toFixed(0)}%</span>
                  )}
                </div>
              </div>
              {index < steps.length - 1 && (
                <div className="flex justify-center py-2">
                  <svg className="w-6 h-6 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 14l-7 7m0 0l-7-7m7 7V3" />
                  </svg>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}

interface MetricsGridProps {
  metrics: ChannelAnalytics['metrics'];
  channelName: string;
}

function MetricsGrid({ metrics, channelName }: MetricsGridProps): JSX.Element {
  const formatCurrency = (value: number): string => {
    return `¥${value.toLocaleString()}`;
  };

  const formatPercent = (value: number): string => {
    return `${value.toFixed(2)}%`;
  };

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <h3 className="text-lg font-medium text-gray-900 mb-6">{channelName} - 关键指标</h3>
      <div className="grid grid-cols-2 gap-6">
        <div className="p-4 bg-blue-50 rounded-lg">
          <p className="text-sm text-gray-600">总访问量</p>
          <p className="mt-1 text-2xl font-bold text-blue-900">{metrics.visitCount.toLocaleString()}</p>
        </div>
        <div className="p-4 bg-green-50 rounded-lg">
          <p className="text-sm text-gray-600">注册用户数</p>
          <p className="mt-1 text-2xl font-bold text-green-900">{metrics.registerCount.toLocaleString()}</p>
        </div>
        <div className="p-4 bg-yellow-50 rounded-lg">
          <p className="text-sm text-gray-600">激活用户数</p>
          <p className="mt-1 text-2xl font-bold text-yellow-900">{metrics.activationCount.toLocaleString()}</p>
        </div>
        <div className="p-4 bg-red-50 rounded-lg">
          <p className="text-sm text-gray-600">付费用户数</p>
          <p className="mt-1 text-2xl font-bold text-red-900">{metrics.paymentCount.toLocaleString()}</p>
        </div>
        <div className="p-4 bg-purple-50 rounded-lg col-span-2">
          <p className="text-sm text-gray-600">总收入</p>
          <p className="mt-1 text-2xl font-bold text-purple-900">{formatCurrency(metrics.totalRevenue)}</p>
        </div>
        <div className="p-4 bg-gray-50 rounded-lg">
          <p className="text-sm text-gray-600">平均订单金额</p>
          <p className="mt-1 text-2xl font-bold text-gray-900">{formatCurrency(metrics.avgOrderValue)}</p>
        </div>
        <div className="p-4 bg-gray-50 rounded-lg">
          <p className="text-sm text-gray-600">转化率</p>
          <p className="mt-1 text-2xl font-bold text-gray-900">{formatPercent(metrics.conversionRate)}</p>
        </div>
        <div className="p-4 bg-gray-50 rounded-lg">
          <p className="text-sm text-gray-600">激活率</p>
          <p className="mt-1 text-2xl font-bold text-gray-900">{formatPercent(metrics.activationRate)}</p>
        </div>
        <div className="p-4 bg-gray-50 rounded-lg">
          <p className="text-sm text-gray-600">付费率</p>
          <p className="mt-1 text-2xl font-bold text-gray-900">{formatPercent(metrics.paymentRate)}</p>
        </div>
      </div>
    </div>
  );
}

export function ChannelStats({
  summary,
  analytics,
  selectedChannelId,
  isLoading = false,
}: ChannelStatsProps): JSX.Element {
  if (isLoading) {
    return (
      <div className="space-y-6">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="h-32 bg-gray-200 rounded-lg animate-pulse"></div>
          ))}
        </div>
        <div className="h-96 bg-gray-200 rounded-lg animate-pulse"></div>
      </div>
    );
  }

  if (!summary) {
    return (
      <div className="text-center py-12">
        <p className="text-gray-500">暂无统计数据</p>
      </div>
    );
  }

  const selectedAnalytics = selectedChannelId
    ? analytics?.find(a => a.channelId === selectedChannelId)
    : analytics?.[0];

  return (
    <div className="space-y-6">
      {/* 汇总统计卡片 */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatCard
          title="总渠道数"
          value={summary.totalChannels}
          subtitle={`${summary.activeChannels} 个活跃渠道`}
          color="blue"
          icon={
            <svg className="w-6 h-6 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
            </svg>
          }
        />
        <StatCard
          title="总访问量"
          value={summary.totalVisits.toLocaleString()}
          color="green"
          icon={
            <svg className="w-6 h-6 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
            </svg>
          }
        />
        <StatCard
          title="注册用户"
          value={summary.totalRegisters.toLocaleString()}
          color="yellow"
          icon={
            <svg className="w-6 h-6 text-yellow-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M18 9v3m0 0v3m0-3h3m-3 0h-3m-2-5a4 4 0 11-8 0 4 4 0 018 0zM3 20a6 6 0 0112 0v1H3v-1z" />
            </svg>
          }
        />
        <StatCard
          title="总收入"
          value={`¥${summary.totalRevenue.toLocaleString()}`}
          subtitle={`${summary.totalPayments} 笔订单`}
          color="purple"
          icon={
            <svg className="w-6 h-6 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          }
        />
      </div>

      {/* 详细分析 */}
      {selectedAnalytics && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <FunnelChart
            funnel={selectedAnalytics.funnel}
            channelName={selectedAnalytics.channelName}
          />
          <MetricsGrid
            metrics={selectedAnalytics.metrics}
            channelName={selectedAnalytics.channelName}
          />
        </div>
      )}

      {/* 渠道对比表格 */}
      {analytics && analytics.length > 1 && !selectedChannelId && (
        <div className="bg-white rounded-lg shadow overflow-hidden">
          <div className="px-6 py-4 border-b border-gray-200">
            <h3 className="text-lg font-medium text-gray-900">渠道对比</h3>
          </div>
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  渠道名称
                </th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                  访问量
                </th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                  注册数
                </th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                  付费数
                </th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                  收入
                </th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                  转化率
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {analytics.map((item) => (
                <tr key={item.channelId} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                    {item.channelName}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 text-right">
                    {item.metrics.visitCount.toLocaleString()}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 text-right">
                    {item.metrics.registerCount.toLocaleString()}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 text-right">
                    {item.metrics.paymentCount.toLocaleString()}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 text-right">
                    ¥{item.metrics.totalRevenue.toLocaleString()}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 text-right">
                    {item.metrics.conversionRate.toFixed(2)}%
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}