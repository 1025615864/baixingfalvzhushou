/**
 * PromotionPage - 推广中心页面
 */

import { useState } from 'react';

import { PromotionLink } from '../components/PromotionLink';
import { PromotionStats } from '../components/PromotionStats';
import { CommissionList } from '../components/CommissionList';

type TabType = 'overview' | 'commissions' | 'withdrawals';

/**
 * 推广中心页面
 */
export function PromotionPage(): JSX.Element {
  const [activeTab, setActiveTab] = useState<TabType>('overview');
  const [statsPeriod, setStatsPeriod] = useState<'day' | 'week' | 'month' | 'year' | 'all'>('month');

  // 监听统计周期变化
  if (typeof window !== 'undefined') {
    window.addEventListener('promotionPeriodChange', ((e: CustomEvent<'day' | 'week' | 'month' | 'year' | 'all'>) => {
      setStatsPeriod(e.detail);
    }) as EventListener);
  }

  /**
   * 渲染标签页内容
   */
  const renderTabContent = (): JSX.Element => {
    switch (activeTab) {
      case 'overview':
        return (
          <div className="space-y-6">
            {/* 推广统计 */}
            <PromotionStats period={statsPeriod} />

            {/* 最近佣金记录 */}
            <div className="bg-white rounded-xl shadow-sm p-6">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold text-gray-900">最近佣金记录</h3>
                <button
                  onClick={() => setActiveTab('commissions')}
                  className="text-sm text-blue-600 hover:text-blue-700"
                >
                  查看全部 →
                </button>
              </div>
              <CommissionList defaultPageSize={5} />
            </div>
          </div>
        );

      case 'commissions':
        return (
          <div className="space-y-6">
            {/* 佣金列表 */}
            <div className="bg-white rounded-xl shadow-sm p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">佣金记录</h3>
              <CommissionList />
            </div>
          </div>
        );

      case 'withdrawals':
        return (
          <div className="bg-white rounded-xl shadow-sm p-6">
            <div className="text-center py-12">
              <div className="w-16 h-16 mx-auto mb-4 bg-gray-100 rounded-full flex items-center justify-center">
                <svg
                  className="w-8 h-8 text-gray-400"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M17 9V7a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2m2 4h10a2 2 0 002-2v-6a2 2 0 00-2-2H9a2 2 0 00-2 2v6a2 2 0 002 2zm7-5a2 2 0 11-4 0 2 2 0 014 0z"
                  />
                </svg>
              </div>
              <h3 className="text-lg font-medium text-gray-900 mb-2">提现功能开发中</h3>
              <p className="text-gray-500">敬请期待...</p>
            </div>
          </div>
        );

      default:
        return <div />;
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-6xl mx-auto px-4 py-8">
        {/* 页面标题 */}
        <div className="mb-6">
          <h1 className="text-2xl font-bold text-gray-900">推广中心</h1>
          <p className="text-gray-500 mt-1">分享链接，赚取佣金</p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* 左侧：推广链接 */}
          <div className="lg:col-span-1">
            <PromotionLink />
          </div>

          {/* 右侧：标签页内容 */}
          <div className="lg:col-span-2">
            {/* 标签导航 */}
            <div className="bg-white rounded-xl shadow-sm mb-6">
              <div className="flex border-b">
                <button
                  onClick={() => setActiveTab('overview')}
                  className={`flex-1 px-6 py-4 text-sm font-medium text-center border-b-2 transition-colors ${
                    activeTab === 'overview'
                      ? 'text-blue-600 border-blue-600'
                      : 'text-gray-500 border-transparent hover:text-gray-700'
                  }`}
                >
                  概览
                </button>
                <button
                  onClick={() => setActiveTab('commissions')}
                  className={`flex-1 px-6 py-4 text-sm font-medium text-center border-b-2 transition-colors ${
                    activeTab === 'commissions'
                      ? 'text-blue-600 border-blue-600'
                      : 'text-gray-500 border-transparent hover:text-gray-700'
                  }`}
                >
                  佣金记录
                </button>
                <button
                  onClick={() => setActiveTab('withdrawals')}
                  className={`flex-1 px-6 py-4 text-sm font-medium text-center border-b-2 transition-colors ${
                    activeTab === 'withdrawals'
                      ? 'text-blue-600 border-blue-600'
                      : 'text-gray-500 border-transparent hover:text-gray-700'
                  }`}
                >
                  提现管理
                </button>
              </div>
            </div>

            {/* 标签内容 */}
            {renderTabContent()}
          </div>
        </div>
      </div>
    </div>
  );
}