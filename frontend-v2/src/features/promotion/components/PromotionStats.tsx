/**
 * PromotionStats - 推广统计组件
 */

import { usePromotionStats } from '../hooks/usePromotion';
import { TrendChart } from '../../analytics/components/TrendChart';
import type { StatsTrendItem, GetPromotionStatsRequest } from '../types';

interface PromotionStatsProps {
  className?: string;
  period?: GetPromotionStatsRequest['period'];
}

/**
 * 格式化趋势数据为图表数据
 */
function formatTrendData(trend: StatsTrendItem[]): Array<{ date: string; value: number; label?: string }> {
  return trend.map((item) => ({
    date: item.date,
    value: item.clicks,
    label: item.date,
  }));
}

/**
 * 推广统计组件
 */
export function PromotionStats({ className = '', period = 'month' }: PromotionStatsProps): JSX.Element {
  const { data: stats, isLoading, error } = usePromotionStats({ period });

  if (isLoading) {
    return (
      <div className={`bg-white rounded-xl shadow-sm p-6 ${className}`}>
        <div className="animate-pulse space-y-4">
          <div className="h-4 bg-gray-200 rounded w-1/3" />
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {[1, 2, 3, 4].map((i) => (
              <div key={i} className="h-20 bg-gray-200 rounded" />
            ))}
          </div>
          <div className="h-64 bg-gray-200 rounded" />
        </div>
      </div>
    );
  }

  if (error || !stats) {
    return (
      <div className={`bg-white rounded-xl shadow-sm p-6 ${className}`}>
        <div className="text-center text-red-500">
          <p>获取推广统计失败</p>
          <button
            onClick={() => window.location.reload()}
            className="mt-4 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
          >
            刷新重试
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className={`bg-white rounded-xl shadow-sm p-6 ${className}`}>
      <h3 className="text-lg font-semibold text-gray-900 mb-6">推广统计</h3>

      {/* 统计卡片 */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
        <div className="p-4 bg-blue-50 rounded-lg">
          <p className="text-sm text-gray-500">总邀请</p>
          <p className="text-2xl font-bold text-blue-600">{stats.totalInvited.toLocaleString()}</p>
        </div>
        <div className="p-4 bg-green-50 rounded-lg">
          <p className="text-sm text-gray-500">总注册</p>
          <p className="text-2xl font-bold text-green-600">{stats.totalRegistered.toLocaleString()}</p>
        </div>
        <div className="p-4 bg-purple-50 rounded-lg">
          <p className="text-sm text-gray-500">转化率</p>
          <p className="text-2xl font-bold text-purple-600">{stats.conversionRate.toFixed(2)}%</p>
        </div>
        <div className="p-4 bg-orange-50 rounded-lg">
          <p className="text-sm text-gray-500">总佣金</p>
          <p className="text-2xl font-bold text-orange-600">¥{stats.totalCommission.toFixed(2)}</p>
        </div>
      </div>

      {/* 佣金统计 */}
      <div className="grid grid-cols-2 gap-4 mb-6">
        <div className="p-4 bg-yellow-50 rounded-lg border border-yellow-100">
          <p className="text-sm text-yellow-700">待结算佣金</p>
          <p className="text-xl font-bold text-yellow-800">¥{stats.pendingCommission.toFixed(2)}</p>
        </div>
        <div className="p-4 bg-teal-50 rounded-lg border border-teal-100">
          <p className="text-sm text-teal-700">已结算佣金</p>
          <p className="text-xl font-bold text-teal-800">¥{stats.paidCommission.toFixed(2)}</p>
        </div>
      </div>

      {/* 趋势图表 */}
      {(stats.trend?.length ?? 0) > 0 && (
        <TrendChart
          data={formatTrendData(stats.trend ?? [])}
          title="点击趋势"
          height={250}
          showArea={true}
          color="#3b82f6"
          className="mt-4"
        />
      )}

      {/* 时间范围 */}
      {stats.startDate && stats.endDate && (
        <div className="mt-4 text-sm text-gray-400 text-center">
          统计周期：{new Date(stats.startDate).toLocaleDateString('zh-CN')} 至{' '}
          {new Date(stats.endDate).toLocaleDateString('zh-CN')}
        </div>
      )}
    </div>
  );
}
