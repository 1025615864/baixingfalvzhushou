/**
 * PointsMallPage - 积分商城页面
 */

import { lazy, Suspense, useEffect, useState } from 'react';
import { Link } from 'react-router-dom';

import { PointsBalance } from '../components/PointsBalance';
import { apiGetPointsBalance } from '../api';
import type { PointsBalance as PointsBalanceType } from '../types';

const LazyPointsMall = lazy(() => import('../components/PointsMall').then((module) => ({ default: module.PointsMall })));
const LazyPointsTaskGuide = lazy(() => import('../components/PointsTaskGuide').then((module) => ({ default: module.PointsTaskGuide })));

/**
 * 积分商城页面
 */
export function PointsMallPage(): JSX.Element {
  const [balanceData, setBalanceData] = useState<PointsBalanceType>({
    balance: 0,
    continuousDays: 0,
  });
  const [isLoading, setIsLoading] = useState(true);

  // 获取积分余额数据
  useEffect(() => {
    const fetchBalance = async () => {
      try {
        const data = await apiGetPointsBalance();
        setBalanceData(data);
      } catch (error) {
        console.error('获取积分余额失败:', error);
      } finally {
        setIsLoading(false);
      }
    };

    void fetchBalance();
  }, []);

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-6xl mx-auto px-4 py-8">
        {/* 页面标题 */}
        <div className="mb-6">
          <h1 className="text-2xl font-bold text-gray-900">积分商城</h1>
          <p className="text-gray-500 mt-1">使用积分兑换精美商品和专属服务</p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* 左侧：积分余额和任务 */}
          <div className="lg:col-span-1 space-y-6">
            {/* 积分余额卡片 */}
            <div className="bg-white rounded-xl shadow-sm p-6">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-sm font-medium text-gray-500">我的积分</h2>
                <Link
                  to="/points/checkin"
                  className="text-sm px-3 py-1 bg-yellow-100 text-yellow-700 rounded-full hover:bg-yellow-200"
                >
                  去签到
                </Link>
              </div>
              {isLoading ? (
                <div className="animate-pulse">
                  <div className="h-8 bg-gray-200 rounded w-24 mb-2" />
                  <div className="h-4 bg-gray-200 rounded w-32" />
                </div>
              ) : (
                <PointsBalance continuousDays={balanceData.continuousDays} />
              )}
              <div className="mt-4 pt-4 border-t flex justify-between">
                <Link
                  to="/points/history"
                  className="text-sm text-blue-600 hover:text-blue-700"
                >
                  查看积分明细 →
                </Link>
                <Link
                  to="/points/rules"
                  className="text-sm text-gray-500 hover:text-gray-700"
                >
                  积分规则
                </Link>
              </div>
            </div>

            {/* 任务引导 */}
            <div className="bg-white rounded-xl shadow-sm p-6">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-lg font-medium text-gray-900">赚积分</h2>
                <Link
                  to="/points/activities"
                  className="text-sm text-blue-600 hover:text-blue-700"
                >
                  更多任务 →
                </Link>
              </div>
              <Suspense fallback={<div className="space-y-3">{Array.from({ length: 4 }).map((_, index) => (<div key={index} className="h-16 rounded-lg bg-gray-100 animate-pulse" />))}</div>}>
                <LazyPointsTaskGuide />
              </Suspense>
            </div>
          </div>

          {/* 右侧：积分商城 */}
          <div className="lg:col-span-2">
            <div className="bg-white rounded-xl shadow-sm p-6">
              <h2 className="text-lg font-medium text-gray-900 mb-4">积分兑换</h2>
              <Suspense fallback={<div className="grid grid-cols-1 sm:grid-cols-2 gap-4">{Array.from({ length: 4 }).map((_, index) => (<div key={index} className="h-64 rounded-lg bg-gray-100 animate-pulse" />))}</div>}>
                <LazyPointsMall />
              </Suspense>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}