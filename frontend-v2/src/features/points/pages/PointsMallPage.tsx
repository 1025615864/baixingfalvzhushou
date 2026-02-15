/**
 * PointsMallPage - 积分商城页面
 */

import { Link } from 'react-router-dom';

import { PointsBalance } from '../components/PointsBalance';
import { PointsMall } from '../components/PointsMall';
import { PointsTaskGuide } from '../components/PointsTaskGuide';

/**
 * 积分商城页面
 */
export function PointsMallPage(): JSX.Element {
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
              <PointsBalance continuousDays={0} />
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
              <PointsTaskGuide />
            </div>
          </div>

          {/* 右侧：积分商城 */}
          <div className="lg:col-span-2">
            <div className="bg-white rounded-xl shadow-sm p-6">
              <h2 className="text-lg font-medium text-gray-900 mb-4">积分兑换</h2>
              <PointsMall />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}