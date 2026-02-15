/**
 * AnalyticsDashboardPage - 数据分析仪表板页面
 */

import { useState, useMemo } from 'react';
import { Link } from 'react-router-dom';

import { StatCardList } from '../components/StatCard';
import { FunnelChart } from '../components/FunnelChart';
import { TrendChart, BarChart } from '../components/TrendChart';
import { DataTable } from '../components/DataTable';
import { useAnalyticsOverview, useConversionFunnel, useRevenue, useUserBehavior } from '../hooks/useAnalytics';
import { useToast } from '../../../components/ui/useToast';
import type { FunnelChartDataItem, TrendDataPoint, DataTableColumn, StatCardData } from '../types';

/**
 * 日期范围选择器
 */
function DateRangeSelector({
  value,
  onChange,
}: {
  value: string;
  onChange: (value: string) => void;
}): JSX.Element {
  const options = [
    { label: '最近7天', value: '7d' },
    { label: '最近30天', value: '30d' },
    { label: '最近90天', value: '90d' },
  ];

  return (
    <div className="flex gap-2">
      {options.map((opt) => (
        <button
          key={opt.value}
          onClick={() => onChange(opt.value)}
          className={`rounded-md px-3 py-1.5 text-sm font-medium transition-colors ${
            value === opt.value
              ? 'bg-blue-600 text-white'
              : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
          }`}
        >
          {opt.label}
        </button>
      ))}
    </div>
  );
}

/**
 * 数据导出按钮
 */
function ExportButton({ onClick }: { onClick?: () => void }): JSX.Element {
  return (
    <button
      onClick={onClick}
      className="inline-flex items-center gap-2 rounded-md border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50"
    >
      <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth={2}
          d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"
        />
      </svg>
      导出数据
    </button>
  );
}

/**
 * 刷新按钮
 */
function RefreshButton({
  onClick,
  isLoading
}: {
  onClick: () => void;
  isLoading: boolean;
}): JSX.Element {
  return (
    <button
      onClick={onClick}
      disabled={isLoading}
      className="inline-flex items-center gap-2 rounded-md border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-50"
    >
      <svg
        className={`h-4 w-4 ${isLoading ? 'animate-spin' : ''}`}
        fill="none"
        viewBox="0 0 24 24"
        stroke="currentColor"
      >
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth={2}
          d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
        />
      </svg>
      {isLoading ? '刷新中...' : '刷新'}
    </button>
  );
}

/**
 * 实时数据指示器
 */
function RealtimeIndicator(): JSX.Element {
  return (
    <div className="flex items-center gap-2 text-sm text-gray-500">
      <span className="relative flex h-3 w-3">
        <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75"></span>
        <span className="relative inline-flex rounded-full h-3 w-3 bg-green-500"></span>
      </span>
      <span>实时数据</span>
    </div>
  );
}

/**
 * 查看更多链接
 */
function ViewMoreLink({ to, label }: { to: string; label: string }): JSX.Element {
  return (
    <Link
      to={to}
      className="inline-flex items-center gap-1 text-sm text-blue-600 hover:text-blue-700 font-medium"
    >
      {label}
      <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
      </svg>
    </Link>
  );
}

export function AnalyticsDashboardPage(): JSX.Element {
  const [dateRange, setDateRange] = useState('30d');
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [lastUpdated, setLastUpdated] = useState(new Date());
  const toast = useToast();
  
  // 计算日期范围
  const { startDate, endDate } = useMemo(() => {
    const end = new Date();
    const days = parseInt(dateRange);
    const start = new Date(end.getTime() - days * 24 * 60 * 60 * 1000);
    return {
      startDate: start.toISOString().split('T')[0],
      endDate: end.toISOString().split('T')[0],
    };
  }, [dateRange]);

  // 获取数据
  const {
    data: overview,
    isLoading: overviewLoading,
    refetch: refetchOverview
  } = useAnalyticsOverview();
  const {
    data: funnelData,
    isLoading: funnelLoading,
    refetch: refetchFunnel
  } = useConversionFunnel(startDate, endDate);
  const {
    data: revenueData,
    isLoading: revenueLoading,
    refetch: refetchRevenue
  } = useRevenue(startDate, endDate);
  const {
    data: behaviorData,
    isLoading: behaviorLoading,
    refetch: refetchBehavior
  } = useUserBehavior();

  // 刷新所有数据
  const handleRefresh = async (): Promise<void> => {
    setIsRefreshing(true);
    try {
      await Promise.all([
        refetchOverview(),
        refetchFunnel(),
        refetchRevenue(),
        refetchBehavior(),
      ]);
      setLastUpdated(new Date());
      toast.success('数据已刷新');
    } catch {
      toast.error('刷新失败，请重试');
    } finally {
      setIsRefreshing(false);
    }
  };

  // 导出数据
  const handleExport = (): void => {
    // 导出功能占位
    toast.info('导出功能开发中，敬请期待');
  };

  // 生成统计卡片数据
  const statCardsData: StatCardData[] = useMemo(() => {
    if (!overview) return [];
    
    return [
      {
        title: '总用户数',
        value: overview.users.totalUsers,
        change: Math.round((overview.users.newUsersToday / (overview.users.totalUsers || 1)) * 1000) / 10,
        changeType: 'increase',
        unit: '人',
        icon: 'Users',
      },
      {
        title: '今日活跃用户',
        value: overview.users.activeUsersToday,
        change: Math.round(
          ((overview.users.activeUsersToday - overview.users.activeUsersYesterday) /
            (overview.users.activeUsersYesterday || 1)) *
            100
        ),
        changeType: overview.users.activeUsersToday >= overview.users.activeUsersYesterday ? 'increase' : 'decrease',
        unit: '人',
        icon: 'Activity',
      },
      {
        title: '今日收入',
        value: overview.revenue.today,
        change: Math.round(
          ((overview.revenue.today - overview.revenue.yesterday) / (overview.revenue.yesterday || 1)) * 100
        ),
        changeType: overview.revenue.today >= overview.revenue.yesterday ? 'increase' : 'decrease',
        unit: '元',
        icon: 'DollarSign',
      },
      {
        title: '平均会话时长',
        value: Math.round(overview.engagement.avgSessionDuration / 60),
        change: 5,
        changeType: 'increase',
        unit: '分钟',
        icon: 'Clock',
      },
    ];
  }, [overview]);

  // 格式化漏斗图数据
  const funnelChartData: FunnelChartDataItem[] = useMemo(() => {
    if (!funnelData?.steps) return [];
    
    return funnelData.steps.map((step, index) => ({
      name: step.name,
      value: step.count,
      conversionRate: step.conversionRate,
      dropRate: step.dropRate,
      color: `hsl(${210 + index * 25}, 70%, ${55 + index * 3}%)`,
    }));
  }, [funnelData]);

  // 格式化收入趋势数据
  const revenueTrendData: TrendDataPoint[] = useMemo(() => {
    if (!revenueData?.trend) return [];
    
    return revenueData.trend.map((item) => ({
      date: item.date.slice(5), // 只显示 MM-DD
      value: item.revenue,
      label: item.date,
    }));
  }, [revenueData]);

  // 格式化功能使用数据
  const featureUsageData: TrendDataPoint[] = useMemo(() => {
    if (!behaviorData?.featureUsage) return [];
    
    return behaviorData.featureUsage.map((item) => ({
      date: item.feature,
      value: item.usageCount,
      label: item.feature,
    }));
  }, [behaviorData]);

  // 活跃度趋势数据
  const activityTrendData: TrendDataPoint[] = useMemo(() => {
    if (!behaviorData?.activityTrend) return [];
    
    return behaviorData.activityTrend.map((item) => ({
      date: item.date.slice(5),
      value: item.activeUsers,
      label: item.date,
    }));
  }, [behaviorData]);

  // 表格数据
  const tableColumns: DataTableColumn[] = [
    { key: 'source', title: '收入来源', dataIndex: 'name', align: 'left' },
    { 
      key: 'value', 
      title: '金额', 
      dataIndex: 'value',
      align: 'right',
      render: (record) => `¥${(record.value as number).toLocaleString()}`,
    },
    { 
      key: 'percentage', 
      title: '占比', 
      dataIndex: 'percentage',
      align: 'right',
      render: (record) => `${(record.percentage as number).toFixed(1)}%`,
    },
  ];

  const revenueSourceData = useMemo(() => {
    return (revenueData?.sources || []).map((source, index) => ({
      key: index,
      name: source.name,
      value: source.value,
      percentage: source.percentage,
    }));
  }, [revenueData]);

  return (
    <div className="min-h-screen bg-gray-50 pb-12">
      {/* 页面头部 */}
      <div className="border-b border-gray-200 bg-white">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <div className="flex flex-col gap-4 py-6 sm:flex-row sm:items-center sm:justify-between">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">数据分析中心</h1>
              <p className="mt-1 text-sm text-gray-500">查看平台运营数据、用户行为和收入统计</p>
            </div>
            <div className="flex items-center gap-4 flex-wrap">
              <RealtimeIndicator />
              <DateRangeSelector value={dateRange} onChange={setDateRange} />
              <RefreshButton onClick={() => void handleRefresh()} isLoading={isRefreshing} />
              <ExportButton onClick={handleExport} />
            </div>
          </div>
        </div>
      </div>

      {/* 页面内容 */}
      <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
        {/* 统计卡片 */}
        <section className="mb-8">
          <StatCardList data={statCardsData} loading={overviewLoading} />
        </section>

        {/* 主要图表区域 */}
        <div className="mb-8 grid grid-cols-1 gap-8 lg:grid-cols-2">
          {/* 转化漏斗 */}
          <div>
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold text-gray-900">用户转化漏斗</h2>
              <ViewMoreLink to="/analytics/funnel" label="详细分析" />
            </div>
            <FunnelChart
              data={funnelChartData}
              title=""
              loading={funnelLoading}
            />
          </div>

          {/* 收入趋势 */}
          <div>
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold text-gray-900">收入趋势</h2>
              <ViewMoreLink to="/analytics/revenue" label="查看详情" />
            </div>
            <TrendChart
              data={revenueTrendData}
              title=""
              loading={revenueLoading}
              color="#10b981"
              unit="元"
            />
          </div>
        </div>

        {/* 次要图表区域 */}
        <div className="mb-8 grid grid-cols-1 gap-8 lg:grid-cols-3">
          {/* 活跃度趋势 */}
          <div className="lg:col-span-2">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold text-gray-900">用户活跃度趋势</h2>
              <ViewMoreLink to="/analytics/behavior" label="行为分析" />
            </div>
            <TrendChart
              data={activityTrendData}
              title=""
              loading={behaviorLoading}
              color="#3b82f6"
              unit="人"
            />
          </div>

          {/* 功能使用分布 */}
          <div>
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold text-gray-900">功能使用分布</h2>
            </div>
            <BarChart
              data={featureUsageData}
              title=""
              loading={behaviorLoading}
              height={300}
            />
          </div>
        </div>

        {/* 数据表格区域 */}
        <div className="grid grid-cols-1 gap-8 lg:grid-cols-2">
          {/* 收入来源分布 */}
          <DataTable
            data={revenueSourceData}
            columns={tableColumns}
            title="收入来源分布"
            loading={revenueLoading}
            rowKey="key"
            bordered
          />

          {/* 用户行为统计 */}
          <div className="rounded-lg bg-white p-6 shadow-sm">
            <h3 className="mb-4 text-lg font-semibold text-gray-900">用户行为概览</h3>
            {behaviorLoading ? (
              <div className="animate-pulse space-y-4">
                <div className="h-4 rounded bg-gray-200"></div>
                <div className="h-4 rounded bg-gray-200"></div>
                <div className="h-4 rounded bg-gray-200"></div>
              </div>
            ) : behaviorData ? (
              <div className="space-y-4">
                <div className="flex items-center justify-between border-b border-gray-100 pb-3">
                  <span className="text-sm text-gray-600">总会话数</span>
                  <span className="text-lg font-semibold text-gray-900">
                    {behaviorData.totalSessions.toLocaleString()}
                  </span>
                </div>
                <div className="flex items-center justify-between border-b border-gray-100 pb-3">
                  <span className="text-sm text-gray-600">平均会话时长</span>
                  <span className="text-lg font-semibold text-gray-900">
                    {Math.round(behaviorData.averageSessionDuration / 60)} 分钟
                  </span>
                </div>
                <div className="flex items-center justify-between border-b border-gray-100 pb-3">
                  <span className="text-sm text-gray-600">活跃用户（最新）</span>
                  <span className="text-lg font-semibold text-gray-900">
                    {behaviorData.activityTrend[behaviorData.activityTrend.length - 1]?.activeUsers.toLocaleString() || '-'}
                  </span>
                </div>
                <div className="flex items-center justify-between pb-3">
                  <span className="text-sm text-gray-600">新用户（最新）</span>
                  <span className="text-lg font-semibold text-gray-900">
                    {behaviorData.activityTrend[behaviorData.activityTrend.length - 1]?.newUsers.toLocaleString() || '-'}
                  </span>
                </div>
              </div>
            ) : (
              <div className="text-center text-gray-500">暂无数据</div>
            )}
          </div>
        </div>

        {/* 底部刷新提示 */}
        <div className="mt-8 text-center text-sm text-gray-400">
          数据每 5 分钟自动刷新一次 · 上次更新: {lastUpdated.toLocaleString('zh-CN')}
        </div>
      </div>
    </div>
  );
}