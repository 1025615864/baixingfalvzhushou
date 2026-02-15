/**
 * RetentionAnalysisPage - 留存分析详情页
 * 
 * 展示用户留存数据和流失分析
 */

import { useState, useMemo } from 'react';
import { Link } from 'react-router-dom';

import { TrendChart } from '../components/TrendChart';
import { DataTable } from '../components/DataTable';
import { useRetention } from '../hooks/useAnalytics';
import type { TrendDataPoint, DataTableColumn, RetentionItem } from '../types';

/**
 * 日期范围选择器
 */
function DateRangeSelector({
  startDate,
  endDate,
  onStartDateChange,
  onEndDateChange,
}: {
  startDate: string;
  endDate: string;
  onStartDateChange: (date: string) => void;
  onEndDateChange: (date: string) => void;
}): JSX.Element {
  return (
    <div className="flex items-center gap-3">
      <input
        type="date"
        value={startDate}
        onChange={(e) => onStartDateChange(e.target.value)}
        className="px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500"
      />
      <span className="text-gray-500">至</span>
      <input
        type="date"
        value={endDate}
        onChange={(e) => onEndDateChange(e.target.value)}
        className="px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500"
      />
    </div>
  );
}

/**
 * 留存统计卡片
 */
function RetentionStatCard({
  title,
  value,
  change,
  changeType,
  subtitle,
  icon,
}: {
  title: string;
  value: string | number;
  change?: number;
  changeType?: 'increase' | 'decrease';
  subtitle?: string;
  icon: string;
}): JSX.Element {
  return (
    <div className="bg-white rounded-xl shadow-sm p-6 border border-gray-100">
      <div className="flex items-start justify-between">
        <div>
          <p className="text-gray-500 text-sm mb-1">{title}</p>
          <p className="text-2xl font-bold text-gray-900">{value}</p>
          {subtitle && (
            <p className="text-sm text-gray-400 mt-1">{subtitle}</p>
          )}
          {change !== undefined && (
            <div className={`flex items-center gap-1 mt-2 text-sm ${
              changeType === 'increase' ? 'text-green-600' : 'text-red-600'
            }`}>
              <svg 
                className="w-4 h-4" 
                fill="none" 
                viewBox="0 0 24 24" 
                stroke="currentColor"
                style={{ transform: changeType === 'decrease' ? 'rotate(180deg)' : undefined }}
              >
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 10l7-7m0 0l7 7m-7-7v18" />
              </svg>
              <span>{Math.abs(change)}%</span>
              <span className="text-gray-400">vs 上期</span>
            </div>
          )}
        </div>
        <div className="text-3xl">{icon}</div>
      </div>
    </div>
  );
}

/**
 * 留存热力图
 */
function RetentionHeatmap({ data }: { data: number[][] }): JSX.Element {
  const days = ['D1', 'D2', 'D3', 'D7', 'D14', 'D30'];
  const weeks = ['本周', '上周', '2周前', '3周前', '4周前'];

  const getColor = (value: number): string => {
    if (value >= 0.7) return 'bg-green-500';
    if (value >= 0.5) return 'bg-green-400';
    if (value >= 0.3) return 'bg-yellow-400';
    if (value >= 0.1) return 'bg-orange-400';
    return 'bg-red-400';
  };

  return (
    <div className="bg-white rounded-xl shadow-sm p-6">
      <h3 className="text-lg font-semibold text-gray-900 mb-4">留存热力图</h3>
      <div className="overflow-x-auto">
        <div className="inline-block min-w-full">
          <div className="grid grid-cols-7 gap-1 mb-2">
            <div className="text-sm text-gray-400">日期</div>
            {days.map((day) => (
              <div key={day} className="text-center text-sm text-gray-500">{day}</div>
            ))}
          </div>
          {weeks.map((week, weekIndex) => (
            <div key={week} className="grid grid-cols-7 gap-1 mb-1">
              <div className="text-sm text-gray-500 py-2">{week}</div>
              {days.map((_, dayIndex) => {
                const value = data[weekIndex]?.[dayIndex] || 0;
                return (
                  <div
                    key={dayIndex}
                    className={`h-10 rounded ${getColor(value)} flex items-center justify-center text-white text-xs font-medium`}
                    title={`${week} - ${days[dayIndex]}: ${(value * 100).toFixed(1)}%`}
                  >
                    {(value * 100).toFixed(0)}%
                  </div>
                );
              })}
            </div>
          ))}
        </div>
      </div>
      <div className="flex items-center justify-between mt-4 text-xs text-gray-500">
        <span>低留存</span>
        <div className="flex gap-1">
          <div className="w-4 h-4 bg-red-400 rounded"></div>
          <div className="w-4 h-4 bg-orange-400 rounded"></div>
          <div className="w-4 h-4 bg-yellow-400 rounded"></div>
          <div className="w-4 h-4 bg-green-400 rounded"></div>
          <div className="w-4 h-4 bg-green-500 rounded"></div>
        </div>
        <span>高留存</span>
      </div>
    </div>
  );
}

/**
 * 流失原因分析
 */
function ChurnReasonAnalysis(): JSX.Element {
  const reasons = [
    { reason: '使用频率低', count: 234, percentage: 35 },
    { reason: '功能不满足需求', count: 156, percentage: 23 },
    { reason: '价格因素', count: 98, percentage: 15 },
    { reason: '竞品吸引', count: 87, percentage: 13 },
    { reason: '体验不佳', count: 65, percentage: 10 },
    { reason: '其他原因', count: 28, percentage: 4 },
  ];

  return (
    <div className="bg-white rounded-xl shadow-sm p-6">
      <h3 className="text-lg font-semibold text-gray-900 mb-4">流失原因分析</h3>
      <div className="space-y-4">
        {reasons.map((item, index) => (
          <div key={index}>
            <div className="flex justify-between text-sm mb-1">
              <span className="text-gray-600">{item.reason}</span>
              <span className="font-medium">{item.count}人 ({item.percentage}%)</span>
            </div>
            <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
              <div
                className="h-full bg-blue-500 rounded-full"
                style={{ width: `${item.percentage}%` }}
              />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

/**
 * 留存分析页面
 */
export function RetentionAnalysisPage(): JSX.Element {
  const [startDate, setStartDate] = useState(() => {
    const date = new Date();
    date.setDate(date.getDate() - 30);
    return date.toISOString().split('T')[0];
  });
  const [endDate, setEndDate] = useState(() => new Date().toISOString().split('T')[0]);

  // 使用 cohortDate 和 retentionDays 调用 hook
  const cohortDate = startDate;
  const { data: retentionData, isLoading: retentionLoading } = useRetention(cohortDate, [1, 7, 30]);

  // 格式化留存趋势数据
  const retentionTrendData: TrendDataPoint[] = useMemo(() => {
    if (!retentionData?.retention) return [];
    
    return retentionData.retention.map((item: RetentionItem) => ({
      date: `D${item.day}`,
      value: item.rate * 100,
      label: `${item.count}人`,
    }));
  }, [retentionData]);

  // 留存表格数据
  const retentionColumns: DataTableColumn[] = [
    { key: 'date', title: '日期', dataIndex: 'date', align: 'left' },
    { 
      key: 'cohortSize', 
      title: '同期群人数', 
      dataIndex: 'cohortSize',
      align: 'right',
      render: (record: Record<string, unknown>) => (record.cohortSize as number).toLocaleString(),
    },
    { 
      key: 'd1', 
      title: '次日留存', 
      dataIndex: 'd1',
      align: 'right',
      render: (record: Record<string, unknown>) => `${((record.d1 as number) * 100).toFixed(1)}%`,
    },
    { 
      key: 'd7', 
      title: '7日留存', 
      dataIndex: 'd7',
      align: 'right',
      render: (record: Record<string, unknown>) => `${((record.d7 as number) * 100).toFixed(1)}%`,
    },
    { 
      key: 'd30', 
      title: '30日留存', 
      dataIndex: 'd30',
      align: 'right',
      render: (record: Record<string, unknown>) => `${((record.d30 as number) * 100).toFixed(1)}%`,
    },
  ];

  const retentionTableData = useMemo(() => {
    if (!retentionData) return [];
    // 获取留存率
    const getRate = (day: number): number => {
      const item = retentionData.retention.find((r: RetentionItem) => r.day === day);
      return item ? item.rate : 0;
    };
    
    return [
      {
        key: 0,
        date: cohortDate,
        cohortSize: retentionData.cohortCount,
        d1: getRate(1),
        d7: getRate(7),
        d30: getRate(30),
      },
    ];
  }, [retentionData, cohortDate]);

  // 热力图数据（模拟）
  const heatmapData = useMemo(() => {
    return [
      [0.45, 0.38, 0.35, 0.32, 0.28, 0.25],
      [0.48, 0.40, 0.37, 0.34, 0.30, 0.27],
      [0.42, 0.35, 0.33, 0.30, 0.26, 0.23],
      [0.50, 0.42, 0.39, 0.36, 0.32, 0.29],
      [0.44, 0.37, 0.34, 0.31, 0.27, 0.24],
    ];
  }, []);

  // 统计数据
  const stats = useMemo(() => {
    if (!retentionData) return null;
    const getRate = (day: number): number => {
      const item = retentionData.retention.find((r: RetentionItem) => r.day === day);
      return item ? item.rate : 0;
    };
    
    return {
      d1Retention: getRate(1),
      d7Retention: getRate(7),
      d30Retention: getRate(30),
      churnRate: 0.15,
      avgLifetime: 45,
    };
  }, [retentionData]);

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-7xl mx-auto px-4">
        {/* 页面标题 */}
        <div className="mb-6 flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">留存分析</h1>
            <p className="text-gray-500 mt-1">分析用户留存情况和生命周期价值</p>
          </div>
          <Link
            to="/analytics"
            className="text-blue-600 hover:text-blue-700 font-medium"
          >
            ← 返回概览
          </Link>
        </div>

        {/* 日期范围选择 */}
        <div className="mb-6 bg-white rounded-xl shadow-sm p-4">
          <div className="flex items-center gap-4">
            <DateRangeSelector
              startDate={startDate}
              endDate={endDate}
              onStartDateChange={setStartDate}
              onEndDateChange={setEndDate}
            />
            <span className="text-sm text-gray-500">
              选择起始日期查看该日期的留存数据
            </span>
          </div>
        </div>

        {/* 核心统计卡片 */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
          <RetentionStatCard
            title="次日留存率"
            value={stats ? `${(stats.d1Retention * 100).toFixed(1)}%` : '-'}
            change={2.5}
            changeType="increase"
            subtitle="新增用户的次日回访比例"
            icon="📅"
          />
          <RetentionStatCard
            title="7日留存率"
            value={stats ? `${(stats.d7Retention * 100).toFixed(1)}%` : '-'}
            change={1.8}
            changeType="increase"
            subtitle="用户在一周内的持续使用"
            icon="📊"
          />
          <RetentionStatCard
            title="30日留存率"
            value={stats ? `${(stats.d30Retention * 100).toFixed(1)}%` : '-'}
            change={0.5}
            changeType="increase"
            subtitle="长期用户保持情况"
            icon="📈"
          />
          <RetentionStatCard
            title="流失率"
            value={stats ? `${(stats.churnRate * 100).toFixed(1)}%` : '-'}
            change={3.2}
            changeType="decrease"
            subtitle="用户停止使用比例"
            icon="⚠️"
          />
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* 左侧主要图表 */}
          <div className="lg:col-span-2 space-y-6">
            {/* 留存趋势图 */}
            <div className="bg-white rounded-xl shadow-sm p-6">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">留存趋势</h2>
              <TrendChart
                data={retentionTrendData}
                title=""
                loading={retentionLoading}
                color="#10b981"
                unit="%"
              />
            </div>

            {/* 留存数据表格 */}
            <div className="bg-white rounded-xl shadow-sm p-6">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">留存详情</h2>
              <DataTable
                data={retentionTableData}
                columns={retentionColumns}
                title=""
                loading={retentionLoading}
                rowKey="key"
                bordered
              />
            </div>
          </div>

          {/* 右侧辅助信息 */}
          <div className="space-y-6">
            {/* 留存热力图 */}
            <RetentionHeatmap data={heatmapData} />

            {/* 流失原因分析 */}
            <ChurnReasonAnalysis />

            {/* 生命周期价值 */}
            <div className="bg-white rounded-xl shadow-sm p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">用户生命周期</h3>
              <div className="text-center">
                <p className="text-4xl font-bold text-blue-600">
                  {stats ? `${stats.avgLifetime.toFixed(1)}` : '-'}
                </p>
                <p className="text-gray-500 mt-1">平均生命周期（天）</p>
              </div>
              <div className="mt-4 space-y-3">
                <div className="flex justify-between text-sm">
                  <span className="text-gray-500">新用户阶段</span>
                  <span className="font-medium">1-7天</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-gray-500">成长期</span>
                  <span className="font-medium">8-30天</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-gray-500">成熟期</span>
                  <span className="font-medium">30天+</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}