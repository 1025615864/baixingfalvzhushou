/**
 * PointsHistoryPage - 积分历史页面
 */

import { PointsBalance } from '../components/PointsBalance';
import { PointsHistory } from '../components/PointsHistory';

/**
 * 积分历史页面
 */
export function PointsHistoryPage(): JSX.Element {
  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-4xl mx-auto px-4 py-8">
        {/* 页面标题 */}
        <div className="mb-6">
          <h1 className="text-2xl font-bold text-gray-900">积分明细</h1>
          <p className="text-gray-500 mt-1">查看您的积分变动记录</p>
        </div>

        {/* 积分余额卡片 */}
        <div className="bg-white rounded-xl shadow-sm p-6 mb-6">
          <h2 className="text-sm font-medium text-gray-500 mb-4">当前积分</h2>
          <PointsBalance continuousDays={0} />
        </div>

        {/* 积分历史列表 */}
        <div className="bg-white rounded-xl shadow-sm p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-medium text-gray-900">变动记录</h2>
            <a
              href="/points/mall"
              className="text-sm text-blue-600 hover:text-blue-700"
            >
              去积分商城 →
            </a>
          </div>
          <PointsHistory />
        </div>
      </div>
    </div>
  );
}