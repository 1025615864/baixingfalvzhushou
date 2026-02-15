/**
 * PromotionStatsDetail - 推广统计详情组件
 *
 * 功能：
 * 1. 转化漏斗分析 - 展示曝光→点击→咨询→成交的转化流程
 * 2. 各阶段转化率 - 显示曝光到点击、点击到咨询、咨询到成交、总体转化率
 * 3. 时段趋势分析 - 24小时/7天/30天趋势图切换
 * 4. 渠道对比 - 不同推广渠道的对比分析
 */

import { useState, useMemo } from 'react';

import { FunnelChart, CompactFunnelChart } from '../../analytics/components/FunnelChart';
import { TrendChart } from '../../analytics/components/TrendChart';
import { StatCard } from '../../analytics/components/StatCard';
import type { FunnelChartDataItem } from '../../analytics/types';
import type { StatCardData } from '../../analytics/types';

// ==================== 类型定义 ====================

/** 漏斗阶段 */
interface FunnelStage {
  name: string;
  count: number;
  conversionRate: number; // 相对于上一阶段的转化率
  dropRate: number; // 流失率
}

/** 趋势数据 */
interface TrendData {
  labels: string[];
  exposure: number[];
  clicks: number[];
  inquiries: number[];
  conversions: number[];
}

/** 渠道数据 */
interface ChannelData {
  name: string;
  exposure: number;
  clicks: number;
  conversions: number;
  revenue: number;
}

/** 转化率数据项 */
interface ConversionRateItem {
  title: string;
  rate: number;
  from: string;
  to: string;
  color: string;
}

/** 推广统计详情 */
interface PromotionStatsDetail {
  funnel: {
    stages: FunnelStage[];
    totalConversionRate: number;
  };
  trends: {
    '24h': TrendData;
    '7d': TrendData;
    '30d': TrendData;
  };
  channels: ChannelData[];
  summary: {
    totalExposure: number;
    totalClicks: number;
    totalInquiries: number;
    totalConversions: number;
    totalRevenue: number;
  };
}

/** 组件 Props */
interface PromotionStatsDetailProps {
  stats: PromotionStatsDetail;
  timeRange?: '24h' | '7d' | '30d';
  isLoading?: boolean;
  className?: string;
}

// ==================== 辅助函数 ====================

/**
 * 格式化数字
 */
function formatNumber(value: number): string {
  if (value >= 1000000) {
    return `${(value / 1000000).toFixed(1)}M`;
  }
  if (value >= 1000) {
    return `${(value / 1000).toFixed(1)}K`;
  }
  return value.toLocaleString();
}

/**
 * 格式化金额
 */
function formatCurrency(value: number): string {
  return `¥${value.toLocaleString()}`;
}

/**
 * 计算百分比（保留供将来使用）
 */
 
function _calculatePercentage(numerator: number, denominator: number): string {
  if (denominator === 0) return '0%';
  return `${((numerator / denominator) * 100).toFixed(1)}%`;
}

// ==================== 子组件 ====================

/**
 * 加载状态骨架屏
 */
function SkeletonCard(): JSX.Element {
  return (
    <div className="rounded-xl bg-white p-6 shadow-sm dark:bg-gray-800">
      <div className="animate-pulse space-y-4">
        <div className="h-4 w-1/3 rounded bg-gray-200 dark:bg-gray-700" />
        <div className="h-32 rounded bg-gray-200 dark:bg-gray-700" />
      </div>
    </div>
  );
}

/**
 * 空状态组件
 */
function EmptyState({ message = '暂无数据' }: { message?: string }): JSX.Element {
  return (
    <div className="flex flex-col items-center justify-center rounded-xl bg-white p-8 shadow-sm dark:bg-gray-800">
      <div className="mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-gray-100 dark:bg-gray-700">
        <svg
          className="h-8 w-8 text-gray-400"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"
          />
        </svg>
      </div>
      <p className="text-gray-500 dark:text-gray-400">{message}</p>
    </div>
  );
}

/**
 * 转化率卡片
 */
interface ConversionRateCardProps {
  title: string;
  rate: number;
  from: string;
  to: string;
  color?: string;
}

function ConversionRateCard({
  title,
  rate,
  from,
  to,
  color = 'blue',
}: ConversionRateCardProps): JSX.Element {
  const colorClasses: Record<string, string> = {
    blue: 'from-blue-500 to-blue-600',
    green: 'from-green-500 to-green-600',
    purple: 'from-purple-500 to-purple-600',
    orange: 'from-orange-500 to-orange-600',
  };

  const bgClass = colorClasses[color] || colorClasses.blue;

  return (
    <div className="rounded-xl bg-white p-4 shadow-sm transition-shadow hover:shadow-md dark:bg-gray-800">
      <h4 className="text-sm font-medium text-gray-500 dark:text-gray-400">{title}</h4>
      <div className="mt-2 flex items-end justify-between">
        <span className="text-2xl font-bold text-gray-900 dark:text-white">
          {rate.toFixed(1)}%
        </span>
        <span className="text-xs text-gray-400 dark:text-gray-500">
          {from} → {to}
        </span>
      </div>
      <div className="mt-3 h-2 w-full rounded-full bg-gray-100 dark:bg-gray-700">
        <div
          className={`h-full rounded-full bg-gradient-to-r ${bgClass} transition-all duration-500`}
          style={{ width: `${Math.min(rate, 100)}%` }}
        />
      </div>
    </div>
  );
}

/**
 * 渠道对比表格
 */
interface ChannelComparisonTableProps {
  channels: ChannelData[];
}

function ChannelComparisonTable({ channels }: ChannelComparisonTableProps): JSX.Element {
  if (channels.length === 0) {
    return <EmptyState message="暂无渠道数据" />;
  }

  const sortedChannels = [...channels].sort((a, b) => b.revenue - a.revenue);

  return (
    <div className="overflow-hidden rounded-xl bg-white shadow-sm dark:bg-gray-800">
      <div className="overflow-x-auto">
        <table className="w-full text-left text-sm">
          <thead className="bg-gray-50 dark:bg-gray-700">
            <tr>
              <th className="px-4 py-3 font-medium text-gray-900 dark:text-white">渠道</th>
              <th className="px-4 py-3 font-medium text-gray-900 dark:text-white text-right">曝光</th>
              <th className="px-4 py-3 font-medium text-gray-900 dark:text-white text-right">点击</th>
              <th className="px-4 py-3 font-medium text-gray-900 dark:text-white text-right">转化</th>
              <th className="px-4 py-3 font-medium text-gray-900 dark:text-white text-right">点击率</th>
              <th className="px-4 py-3 font-medium text-gray-900 dark:text-white text-right">转化率</th>
              <th className="px-4 py-3 font-medium text-gray-900 dark:text-white text-right">收益</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100 dark:divide-gray-700">
            {sortedChannels.map((channel, index) => {
              const clickRate = channel.exposure > 0 ? (channel.clicks / channel.exposure) * 100 : 0;
              const conversionRate = channel.clicks > 0 ? (channel.conversions / channel.clicks) * 100 : 0;

              return (
                <tr
                  key={channel.name}
                  className="transition-colors hover:bg-gray-50 dark:hover:bg-gray-700/50"
                >
                  <td className="px-4 py-3">
                    <div className="flex items-center gap-2">
                      <span
                        className={`flex h-6 w-6 items-center justify-center rounded-full text-xs font-medium ${
                          index === 0
                            ? 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900 dark:text-yellow-300'
                            : index === 1
                            ? 'bg-gray-100 text-gray-700 dark:bg-gray-600 dark:text-gray-300'
                            : index === 2
                            ? 'bg-orange-100 text-orange-700 dark:bg-orange-900 dark:text-orange-300'
                            : 'bg-blue-50 text-blue-600 dark:bg-blue-900 dark:text-blue-300'
                        }`}
                      >
                        {index + 1}
                      </span>
                      <span className="font-medium text-gray-900 dark:text-white">
                        {channel.name}
                      </span>
                    </div>
                  </td>
                  <td className="px-4 py-3 text-right text-gray-600 dark:text-gray-300">
                    {formatNumber(channel.exposure)}
                  </td>
                  <td className="px-4 py-3 text-right text-gray-600 dark:text-gray-300">
                    {formatNumber(channel.clicks)}
                  </td>
                  <td className="px-4 py-3 text-right text-gray-600 dark:text-gray-300">
                    {formatNumber(channel.conversions)}
                  </td>
                  <td className="px-4 py-3 text-right">
                    <span className="text-blue-600 dark:text-blue-400">{clickRate.toFixed(1)}%</span>
                  </td>
                  <td className="px-4 py-3 text-right">
                    <span className="text-green-600 dark:text-green-400">{conversionRate.toFixed(1)}%</span>
                  </td>
                  <td className="px-4 py-3 text-right font-medium text-gray-900 dark:text-white">
                    {formatCurrency(channel.revenue)}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}

// ==================== 主组件 ====================

/**
 * 推广统计详情组件
 */
export function PromotionStatsDetail({
  stats,
  timeRange = '7d',
  isLoading = false,
  className = '',
}: PromotionStatsDetailProps): JSX.Element {
  const [activeTimeRange, setActiveTimeRange] = useState<'24h' | '7d' | '30d'>(timeRange);

  // 转换漏斗数据
  const funnelData: FunnelChartDataItem[] = useMemo(() => {
    if (!stats?.funnel?.stages) return [];
    return stats.funnel.stages.map((stage) => ({
      name: stage.name,
      value: stage.count,
      conversionRate: stage.conversionRate,
      dropRate: stage.dropRate,
    }));
  }, [stats?.funnel?.stages]);

  // 趋势数据转换
  const trendChartData = useMemo(() => {
    const trendData = stats?.trends?.[activeTimeRange];
    if (!trendData) return [];

    // 返回转化数据作为趋势图数据
    return trendData.labels.map((label, index) => ({
      date: label,
      value: trendData.conversions[index] || 0,
      label,
    }));
  }, [stats?.trends, activeTimeRange]);

  // 统计卡片数据
  const statCards: StatCardData[] = useMemo(() => {
    if (!stats?.summary) return [];
    return [
      {
        title: '总曝光',
        value: stats.summary.totalExposure,
        icon: 'Activity',
        change: 12.5,
        changeType: 'increase',
      },
      {
        title: '总点击',
        value: stats.summary.totalClicks,
        icon: 'Activity',
        change: 8.3,
        changeType: 'increase',
      },
      {
        title: '总咨询',
        value: stats.summary.totalInquiries,
        icon: 'Users',
        change: -2.1,
        changeType: 'decrease',
      },
      {
        title: '总成交',
        value: stats.summary.totalConversions,
        icon: 'DollarSign',
        change: 15.7,
        changeType: 'increase',
      },
    ];
  }, [stats?.summary]);

  // 各阶段转化率数据
  const conversionRates = useMemo((): ConversionRateItem[] => {
    if (!stats?.funnel?.stages || stats.funnel.stages.length < 2) {
      return [];
    }

    const stages = stats.funnel.stages;
    const rates: ConversionRateItem[] = [];

    // 曝光 → 点击
    if (stages[0] && stages[1]) {
      rates.push({
        title: '曝光→点击',
        rate: stages[1].conversionRate,
        from: '曝光',
        to: '点击',
        color: 'blue',
      });
    }

    // 点击 → 咨询
    if (stages[1] && stages[2]) {
      rates.push({
        title: '点击→咨询',
        rate: stages[2].conversionRate,
        from: '点击',
        to: '咨询',
        color: 'purple',
      });
    }

    // 咨询 → 成交
    if (stages[2] && stages[3]) {
      rates.push({
        title: '咨询→成交',
        rate: stages[3].conversionRate,
        from: '咨询',
        to: '成交',
        color: 'green',
      });
    }

    return rates;
  }, [stats?.funnel?.stages]);

  // 加载状态
  if (isLoading) {
    return (
      <div className={`space-y-6 ${className}`}>
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {[1, 2, 3, 4].map((i) => (
            <SkeletonCard key={i} />
          ))}
        </div>
        <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
          <SkeletonCard />
          <SkeletonCard />
        </div>
      </div>
    );
  }

  // 空状态
  if (!stats) {
    return <EmptyState message="暂无统计数据" />;
  }

  return (
    <div className={`space-y-6 ${className}`}>
      {/* 统计概览卡片 */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {statCards.map((card, index) => (
          <StatCard key={`${card.title}-${index}`} data={card} />
        ))}
      </div>

      {/* 转化漏斗分析 */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        {/* 漏斗图 */}
        <div className="rounded-xl bg-white p-6 shadow-sm dark:bg-gray-800">
          <h3 className="mb-4 text-lg font-semibold text-gray-900 dark:text-white">
            转化漏斗分析
          </h3>
          <CompactFunnelChart
            data={funnelData}
            loading={isLoading}
            className="border-0 shadow-none"
          />
        </div>

        {/* 各阶段转化率 */}
        <div className="rounded-xl bg-white p-6 shadow-sm dark:bg-gray-800">
          <h3 className="mb-4 text-lg font-semibold text-gray-900 dark:text-white">
            各阶段转化率
          </h3>
          <div className="space-y-4">
            {conversionRates.map((rate) => (
              <ConversionRateCard
                key={rate.title}
                title={rate.title}
                rate={rate.rate}
                from={rate.from}
                to={rate.to}
                color={rate.color}
              />
            ))}
            {/* 总体转化率 */}
            <div className="mt-4 rounded-lg bg-gradient-to-r from-blue-500 to-purple-600 p-4 text-white">
              <div className="flex items-center justify-between">
                <span className="font-medium">总体转化率</span>
                <span className="text-2xl font-bold">
                  {stats.funnel.totalConversionRate.toFixed(1)}%
                </span>
              </div>
              <p className="mt-1 text-sm text-blue-100">
                从曝光到最终成交的整体转化效率
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* 时段趋势分析 */}
      <div className="rounded-xl bg-white p-6 shadow-sm dark:bg-gray-800">
        <div className="mb-4 flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
            时段趋势分析
          </h3>
          <div className="flex gap-2">
            {(['24h', '7d', '30d'] as const).map((range) => (
              <button
                key={range}
                onClick={() => setActiveTimeRange(range)}
                className={`rounded-lg px-4 py-2 text-sm font-medium transition-colors ${
                  activeTimeRange === range
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-100 text-gray-600 hover:bg-gray-200 dark:bg-gray-700 dark:text-gray-300 dark:hover:bg-gray-600'
                }`}
              >
                {range === '24h' ? '24小时' : range === '7d' ? '7天' : '30天'}
              </button>
            ))}
          </div>
        </div>
        <TrendChart
          data={trendChartData}
          loading={isLoading}
          height={300}
          color="#3b82f6"
          showArea={true}
          title=""
        />
      </div>

      {/* 渠道对比 */}
      <div className="rounded-xl bg-white p-6 shadow-sm dark:bg-gray-800">
        <h3 className="mb-4 text-lg font-semibold text-gray-900 dark:text-white">
          渠道对比分析
        </h3>
        <ChannelComparisonTable channels={stats.channels || []} />
      </div>

      {/* 详细漏斗图表 */}
      <div className="rounded-xl bg-white p-6 shadow-sm dark:bg-gray-800">
        <h3 className="mb-4 text-lg font-semibold text-gray-900 dark:text-white">
          详细转化漏斗
        </h3>
        <FunnelChart
          data={funnelData}
          loading={isLoading}
          showLegend={true}
          showRates={true}
          title=""
          className="border-0 shadow-none"
        />
      </div>
    </div>
  );
}

export default PromotionStatsDetail;