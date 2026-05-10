/**
 * PromotionStatsModal - 推广统计详情弹窗组件
 * 
 * 展示详细的推广统计数据和趋势图表
 */

import { useState } from 'react';

import type { PromotionStats } from '../types';

interface PromotionStatsModalProps {
  /** 是否显示 */
  isOpen: boolean;
  /** 统计数据 */
  stats: PromotionStats | null;
  /** 关闭回调 */
  onClose: () => void;
  /** 自定义类名 */
  className?: string;
}

/**
 * 格式化日期
 */
function formatDate(dateString: string): string {
  const date = new Date(dateString);
  return date.toLocaleDateString('zh-CN', {
    month: 'short',
    day: 'numeric',
  });
}

/**
 * 推广统计详情弹窗组件
 * 
 * @example
 * ```tsx
 * const [showModal, setShowModal] = useState(false);
 * 
 * <PromotionStatsModal
 *   isOpen={showModal}
 *   stats={promotionStats}
 *   onClose={() => setShowModal(false)}
 * />
 * ```
 */
export function PromotionStatsModal({
  isOpen,
  stats,
  onClose,
  className = '',
}: PromotionStatsModalProps): JSX.Element | null {
  const [activeTab, setActiveTab] = useState<'overview' | 'trend' | 'detail'>('overview');

  if (!isOpen || !stats) return null;

  // 找出最大值用于图表缩放
  const trend = stats.trend ?? [];
  const maxClicks = Math.max(...trend.map((t) => t.clicks), 1);
  const maxConversions = Math.max(...trend.map((t) => t.conversions), 1);

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      {/* 遮罩层 */}
      <div
        className="absolute inset-0 bg-black/50 backdrop-blur-sm"
        onClick={onClose}
      />

      {/* 弹窗内容 */}
      <div
        className={`
          relative w-full max-w-4xl max-h-[90vh] bg-white dark:bg-gray-800 rounded-2xl shadow-2xl
          flex flex-col overflow-hidden
          ${className}
        `}
      >
        {/* 头部 */}
        <div className="flex items-center justify-between p-6 border-b border-gray-100 dark:border-gray-700">
          <div>
            <h3 className="text-xl font-semibold text-gray-900 dark:text-gray-100">
              推广统计详情
            </h3>
            <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
              {stats.startDate ? formatDate(stats.startDate) : '未知日期'} - {stats.endDate ? formatDate(stats.endDate) : '未知日期'}
            </p>
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 transition-colors"
            aria-label="关闭"
          >
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* 标签页切换 */}
        <div className="flex border-b border-gray-100 dark:border-gray-700">
          {[
            { id: 'overview', label: '概览' },
            { id: 'trend', label: '趋势' },
            { id: 'detail', label: '详细数据' },
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as typeof activeTab)}
              className={`
                flex-1 px-4 py-3 text-sm font-medium transition-colors
                ${activeTab === tab.id
                  ? 'text-blue-600 border-b-2 border-blue-600 bg-blue-50/50'
                  : 'text-gray-500 hover:text-gray-700 hover:bg-gray-50'
                }
              `}
            >
              {tab.label}
            </button>
          ))}
        </div>

        {/* 内容区域 */}
        <div className="flex-1 overflow-y-auto p-6">
          {/* 概览标签 */}
          {activeTab === 'overview' && (
            <div className="space-y-6">
              {/* 核心指标 */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div className="p-4 bg-blue-50 dark:bg-blue-900/20 rounded-xl">
                  <div className="text-sm text-blue-600 dark:text-blue-400 mb-1">总点击</div>
                  <div className="text-2xl font-bold text-gray-900 dark:text-gray-100">
                    {(stats.totalInvited ?? 0).toLocaleString()}
                  </div>
                </div>
                <div className="p-4 bg-green-50 dark:bg-green-900/20 rounded-xl">
                  <div className="text-sm text-green-600 dark:text-green-400 mb-1">总转化</div>
                  <div className="text-2xl font-bold text-gray-900 dark:text-gray-100">
                    {(stats.totalRegistered ?? 0).toLocaleString()}
                  </div>
                </div>
                <div className="p-4 bg-purple-50 dark:bg-purple-900/20 rounded-xl">
                  <div className="text-sm text-purple-600 dark:text-purple-400 mb-1">转化率</div>
                  <div className="text-2xl font-bold text-gray-900 dark:text-gray-100">
                    {(stats.conversionRate * 100).toFixed(2)}%
                  </div>
                </div>
                <div className="p-4 bg-yellow-50 dark:bg-yellow-900/20 rounded-xl">
                  <div className="text-sm text-yellow-600 dark:text-yellow-400 mb-1">总佣金</div>
                  <div className="text-2xl font-bold text-gray-900 dark:text-gray-100">
                    ¥{stats.totalCommission.toFixed(2)}
                  </div>
                </div>
              </div>

              {/* 佣金状态 */}
              <div className="grid grid-cols-3 gap-4">
                <div className="p-4 bg-orange-50 dark:bg-orange-900/20 rounded-xl text-center">
                  <div className="text-2xl font-bold text-orange-600">
                    ¥{stats.pendingCommission.toFixed(2)}
                  </div>
                  <div className="text-sm text-gray-500 dark:text-gray-400 mt-1">待确认佣金</div>
                </div>
                <div className="p-4 bg-blue-50 dark:bg-blue-900/20 rounded-xl text-center">
                  <div className="text-2xl font-bold text-blue-600">
                    ¥{stats.paidCommission.toFixed(2)}
                  </div>
                  <div className="text-sm text-gray-500 dark:text-gray-400 mt-1">已结算佣金</div>
                </div>
                <div className="p-4 bg-green-50 dark:bg-green-900/20 rounded-xl text-center">
                  <div className="text-2xl font-bold text-green-600">
                    ¥{(stats.totalCommission - stats.pendingCommission - stats.paidCommission).toFixed(2)}
                  </div>
                  <div className="text-sm text-gray-500 dark:text-gray-400 mt-1">可提现佣金</div>
                </div>
              </div>

              {/* 趋势预览 */}
              <div>
                <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-4">点击趋势</h4>
                <div className="h-32 flex items-end gap-2">
                  {trend.map((item) => (
                    <div
                      key={item.date}
                      className="flex-1 bg-blue-200 dark:bg-blue-800 rounded-t"
                      style={{
                        height: `${(item.clicks / maxClicks) * 100}%`,
                        minHeight: '4px',
                      }}
                      title={`${formatDate(item.date)}: ${item.clicks} 点击`}
                    />
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* 趋势标签 */}
          {activeTab === 'trend' && (
            <div className="space-y-6">
              {/* 点击趋势图 */}
              <div>
                <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-4">每日点击量</h4>
                <div className="h-48 flex items-end gap-1 bg-gray-50 dark:bg-gray-700/30 rounded-lg p-4">
                  {trend.map((item) => (
                    <div key={`click-${item.date}`} className="flex-1 flex flex-col items-center gap-1">
                      <div
                        className="w-full bg-blue-500 rounded-t transition-all hover:bg-blue-600"
                        style={{ height: `${(item.clicks / maxClicks) * 160}px` }}
                        title={`${formatDate(item.date)}: ${item.clicks} 点击`}
                      />
                      <span className="text-xs text-gray-400">{formatDate(item.date)}</span>
                    </div>
                  ))}
                </div>
              </div>

              {/* 转化趋势图 */}
              <div>
                <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-4">每日转化量</h4>
                <div className="h-48 flex items-end gap-1 bg-gray-50 dark:bg-gray-700/30 rounded-lg p-4">
                  {trend.map((item) => (
                    <div key={`conv-${item.date}`} className="flex-1 flex flex-col items-center gap-1">
                      <div
                        className="w-full bg-green-500 rounded-t transition-all hover:bg-green-600"
                        style={{ height: `${(item.conversions / maxConversions) * 160}px` }}
                        title={`${formatDate(item.date)}: ${item.conversions} 转化`}
                      />
                      <span className="text-xs text-gray-400">{formatDate(item.date)}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* 详细数据标签 */}
          {activeTab === 'detail' && (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-gray-200 dark:border-gray-700">
                    <th className="text-left py-3 px-4 font-medium text-gray-700 dark:text-gray-300">日期</th>
                    <th className="text-right py-3 px-4 font-medium text-gray-700 dark:text-gray-300">点击</th>
                    <th className="text-right py-3 px-4 font-medium text-gray-700 dark:text-gray-300">转化</th>
                    <th className="text-right py-3 px-4 font-medium text-gray-700 dark:text-gray-300">佣金</th>
                    <th className="text-right py-3 px-4 font-medium text-gray-700 dark:text-gray-300">转化率</th>
                  </tr>
                </thead>
                <tbody>
                  {trend.map((item) => {
                    const rate = item.clicks > 0 ? (item.conversions / item.clicks) * 100 : 0;
                    return (
                      <tr
                        key={item.date}
                        className="border-b border-gray-100 dark:border-gray-800 hover:bg-gray-50 dark:hover:bg-gray-700/30"
                      >
                        <td className="py-3 px-4 text-gray-900 dark:text-gray-100">
                          {formatDate(item.date)}
                        </td>
                        <td className="py-3 px-4 text-right text-gray-700 dark:text-gray-300">
                          {item.clicks.toLocaleString()}
                        </td>
                        <td className="py-3 px-4 text-right text-gray-700 dark:text-gray-300">
                          {item.conversions.toLocaleString()}
                        </td>
                        <td className="py-3 px-4 text-right text-green-600">
                          ¥{item.commission.toFixed(2)}
                        </td>
                        <td className="py-3 px-4 text-right text-gray-700 dark:text-gray-300">
                          {rate.toFixed(2)}%
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
        </div>

        {/* 底部按钮 */}
        <div className="flex justify-end gap-3 p-6 border-t border-gray-100 dark:border-gray-700">
          <button
            onClick={onClose}
            className="px-6 py-2 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 transition-colors"
          >
            关闭
          </button>
        </div>
      </div>
    </div>
  );
}

export default PromotionStatsModal;