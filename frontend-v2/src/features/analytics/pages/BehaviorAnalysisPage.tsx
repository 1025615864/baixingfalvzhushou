/**
 * BehaviorAnalysisPage - 行为分析详情页
 * 
 * 展示详细的用户行为数据，包括活跃度、功能使用、用户路径等
 */

import { useState, useMemo } from 'react';
import { Link } from 'react-router-dom';

import { TrendChart, BarChart } from '../components/TrendChart';
import { DataTable } from '../components/DataTable';
import { useUserBehavior, useActionStatistics } from '../hooks/useAnalytics';
import type { TrendDataPoint, DataTableColumn } from '../types';

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
 * 行为统计卡片
 */
function BehaviorStatCard({
  title,
  value,
  change,
  changeType,
  icon,
}: {
  title: string;
  value: string | number;
  change?: number;
  changeType?: 'increase' | 'decrease';
  icon: string;
}): JSX.Element {
  return (
    <div className="bg-white rounded-xl shadow-sm p-6 border border-gray-100">
      <div className="flex items-start justify-between">
        <div>
          <p className="text-gray-500 text-sm mb-1">{title}</p>
          <p className="text-2xl font-bold text-gray-900">{value}</p>
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
 * 用户路径分析
 */
function UserPathAnalysis(): JSX.Element {
  const paths = [
    { path: '首页 → 浏览 → 购买', users: 1234, conversion: 0.15 },
    { path: '首页 → 搜索 → 浏览 → 购买', users: 892, conversion: 0.12 },
    { path: '首页 → 推荐 → 购买', users: 756, conversion: 0.18 },
    { path: '直接访问 → 购买', users: 543, conversion: 0.25 },
    { path: '分享链接 → 浏览 → 注册', users: 432, conversion: 0.08 },
  ];

  return (
    <div className="bg-white rounded-xl shadow-sm p-6">
      <h3 className="text-lg font-semibold text-gray-900 mb-4">用户路径分析</h3>
      <div className="space-y-4">
        {paths.map((item, index) => (
          <div key={index} className="flex items-center gap-4">
            <div className="w-8 h-8 bg-blue-100 text-blue-600 rounded-full flex items-center justify-center text-sm font-bold">
              {index + 1}
            </div>
            <div className="flex-1">
              <div className="flex items-center gap-2 flex-wrap">
                {item.path.split(' → ').map((step, i, arr) => (
                  <span key={i} className="flex items-center gap-2">
                    <span className="px-2 py-1 bg-gray-100 rounded text-sm">{step}</span>
                    {i < arr.length - 1 && (
                      <svg className="w-4 h-4 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                      </svg>
                    )}
                  </span>
                ))}
              </div>
            </div>
            <div className="text-right">
              <p className="font-semibold text-gray-900">{item.users.toLocaleString()}人</p>
              <p className="text-sm text-green-600">{(item.conversion * 100).toFixed(1)}%</p>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

/**
 * 活跃时间段分析
 */
function ActiveTimeAnalysis(): JSX.Element {
  const timeSlots = [
    { hour: '00:00', users: 120 },
    { hour: '04:00', users: 80 },
    { hour: '08:00', users: 450 },
    { hour: '12:00', users: 890 },
    { hour: '16:00', users: 720 },
    { hour: '20:00', users: 950 },
    { hour: '23:59', users: 380 },
  ];

  const maxUsers = Math.max(...timeSlots.map(t => t.users));

  return (
    <div className="bg-white rounded-xl shadow-sm p-6">
      <h3 className="text-lg font-semibold text-gray-900 mb-4">活跃时间段分布</h3>
      <div className="space-y-3">
        {timeSlots.map((slot) => (
          <div key={slot.hour} className="flex items-center gap-3">
            <span className="w-12 text-sm text-gray-500">{slot.hour}</span>
            <div className="flex-1 h-8 bg-gray-100 rounded-full overflow-hidden">
              <div
                className="h-full bg-gradient-to-r from-blue-400 to-blue-600 rounded-full transition-all"
                style={{ width: `${(slot.users / maxUsers) * 100}%` }}
              />
            </div>
            <span className="w-16 text-right text-sm text-gray-600">{slot.users}人</span>
          </div>
        ))}
      </div>
    </div>
  );
}

/**
 * 行为分析页面
 */
export function BehaviorAnalysisPage(): JSX.Element {
  const [startDate, setStartDate] = useState(() => {
    const date = new Date();
    date.setDate(date.getDate() - 30);
    return date.toISOString().split('T')[0];
  });
  const [endDate, setEndDate] = useState(() => new Date().toISOString().split('T')[0]);

  const { data: behaviorData, isLoading: behaviorLoading } = useUserBehavior();
  const { data: actionStats, isLoading: statsLoading } = useActionStatistics(startDate, endDate);

  // 格式化活跃度趋势数据
  const activityTrendData: TrendDataPoint[] = useMemo(() => {
    if (!behaviorData?.activityTrend) return [];
    
    return behaviorData.activityTrend.map((item) => ({
      date: item.date.slice(5),
      value: item.activeUsers,
      label: item.date,
    }));
  }, [behaviorData]);

  // 格式化功能使用数据
  const featureUsageData: TrendDataPoint[] = useMemo(() => {
    if (!behaviorData?.featureUsage) return [];
    
    return behaviorData.featureUsage.map((item) => ({
      date: item.feature,
      value: item.usageCount,
      label: item.feature,
    }));
  }, [behaviorData]);

  // 行为统计表格数据
  const actionColumns: DataTableColumn[] = [
    { key: 'action', title: '行为类型', dataIndex: 'action', align: 'left' },
    { 
      key: 'count', 
      title: '次数', 
      dataIndex: 'count',
      align: 'right',
      render: (record) => (record.count as number).toLocaleString(),
    },
    { 
      key: 'percentage', 
      title: '占比', 
      dataIndex: 'percentage',
      align: 'right',
      render: (record) => `${(record.percentage as number).toFixed(1)}%`,
    },
  ];

  const actionTableData = useMemo(() => {
    if (!actionStats?.items) return [];
    const total = actionStats.items.reduce((sum, item) => sum + item.count, 0);
    return actionStats.items.map((item, index) => ({
      key: index,
      action: item.action,
      count: item.count,
      percentage: total > 0 ? (item.count / total) * 100 : 0,
    }));
  }, [actionStats]);

  // 计算统计数据
  const stats = useMemo(() => {
    if (!behaviorData) return null;
    return {
      totalSessions: behaviorData.totalSessions,
      avgSessionDuration: Math.round(behaviorData.averageSessionDuration / 60),
      activeUsers: behaviorData.activityTrend[behaviorData.activityTrend.length - 1]?.activeUsers || 0,
      newUsers: behaviorData.activityTrend[behaviorData.activityTrend.length - 1]?.newUsers || 0,
    };
  }, [behaviorData]);

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-7xl mx-auto px-4">
        {/* 页面标题 */}
        <div className="mb-6 flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">行为分析</h1>
            <p className="text-gray-500 mt-1">深入了解用户行为模式和偏好</p>
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
          <DateRangeSelector
            startDate={startDate}
            endDate={endDate}
            onStartDateChange={setStartDate}
            onEndDateChange={setEndDate}
          />
        </div>

        {/* 核心统计卡片 */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
          <BehaviorStatCard
            title="总会话数"
            value={stats?.totalSessions.toLocaleString() || '-'}
            icon="💬"
          />
          <BehaviorStatCard
            title="平均会话时长"
            value={`${stats?.avgSessionDuration || '-'} 分钟`}
            change={5}
            changeType="increase"
            icon="⏱️"
          />
          <BehaviorStatCard
            title="活跃用户"
            value={stats?.activeUsers.toLocaleString() || '-'}
            change={12}
            changeType="increase"
            icon="👥"
          />
          <BehaviorStatCard
            title="新用户"
            value={stats?.newUsers.toLocaleString() || '-'}
            change={8}
            changeType="increase"
            icon="✨"
          />
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* 左侧主要图表 */}
          <div className="lg:col-span-2 space-y-6">
            {/* 活跃度趋势 */}
            <div className="bg-white rounded-xl shadow-sm p-6">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">用户活跃度趋势</h2>
              <TrendChart
                data={activityTrendData}
                title=""
                loading={behaviorLoading}
                color="#3b82f6"
                unit="人"
              />
            </div>

            {/* 行为统计表格 */}
            <div className="bg-white rounded-xl shadow-sm p-6">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">行为统计</h2>
              <DataTable
                data={actionTableData}
                columns={actionColumns}
                title=""
                loading={statsLoading}
                rowKey="key"
                bordered
              />
            </div>

            {/* 用户路径分析 */}
            <UserPathAnalysis />
          </div>

          {/* 右侧辅助信息 */}
          <div className="space-y-6">
            {/* 功能使用分布 */}
            <div className="bg-white rounded-xl shadow-sm p-6">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">功能使用分布</h2>
              <BarChart
                data={featureUsageData}
                title=""
                loading={behaviorLoading}
              />
            </div>

            {/* 活跃时间段 */}
            <ActiveTimeAnalysis />

            {/* 用户画像卡片 */}
            <div className="bg-gradient-to-br from-purple-500 to-pink-500 rounded-xl shadow-lg p-6 text-white">
              <h3 className="text-lg font-semibold mb-3">用户画像洞察</h3>
              <ul className="space-y-2 text-white/90 text-sm">
                <li>• 主要活跃时间：晚上 8-10点</li>
                <li>• 平均使用时长：15分钟</li>
                <li>• 最常使用功能：法律咨询</li>
                <li>• 用户留存率：65%</li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}