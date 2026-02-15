// ============================================
// 管理后台仪表盘页面
// ============================================

import { useAdminStats } from '../../features/admin/hooks/useAdmin';

// 统计卡片组件
function StatCard({ 
  title, 
  value, 
  change, 
  changeType, 
  icon 
}: { 
  title: string; 
  value: string; 
  change?: string; 
  changeType?: 'up' | 'down'; 
  icon: React.ReactNode;
}) {
  return (
    <div className="bg-white rounded-lg p-6 shadow-sm border border-gray-100">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm text-gray-600 mb-1">{title}</p>
          <p className="text-2xl font-bold text-gray-900">{value}</p>
          {change && (
            <p className={`text-sm mt-1 ${changeType === 'up' ? 'text-green-600' : 'text-red-600'}`}>
              {changeType === 'up' ? '↑' : '↓'} {change}
            </p>
          )}
        </div>
        <div className="w-12 h-12 bg-blue-50 rounded-lg flex items-center justify-center text-blue-600">
          {icon}
        </div>
      </div>
    </div>
  );
}

export function AdminDashboardPage() {
  const { data: stats, isLoading } = useAdminStats();

  const formatNumber = (num: number) => num.toLocaleString('zh-CN');
  const formatCurrency = (num: number) => `¥${(num / 10000).toFixed(1)}万`;

  return (
    <div className="min-h-screen bg-gray-50">
      {/* 顶部导航 */}
      <header className="bg-white shadow-sm border-b border-gray-200 sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center gap-4">
              <h1 className="text-xl font-bold text-gray-900">管理后台</h1>
              <span className="px-2 py-1 bg-blue-100 text-blue-700 text-xs rounded">v2.0</span>
            </div>
            <div className="flex items-center gap-4">
              <button className="relative p-2 text-gray-400 hover:text-gray-600">
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
                </svg>
                <span className="absolute top-1 right-1 w-2 h-2 bg-red-500 rounded-full"></span>
              </button>
              <div className="w-8 h-8 bg-blue-600 rounded-full flex items-center justify-center text-white font-medium">
                A
              </div>
            </div>
          </div>
        </div>
      </header>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* 统计卡片 */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <StatCard
            title="总用户数"
            value={isLoading ? '-' : formatNumber(stats?.total_users || 0)}
            change="+12.5%"
            changeType="up"
            icon={<svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z" /></svg>}
          />
          <StatCard
            title="今日收入"
            value={isLoading ? '-' : formatCurrency(stats?.revenue_today || 0)}
            change="+8.2%"
            changeType="up"
            icon={<svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>}
          />
          <StatCard
            title="待处理咨询"
            value={isLoading ? '-' : String(stats?.pending_consultations || 0)}
            change="-3"
            changeType="down"
            icon={<svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" /></svg>}
          />
          <StatCard
            title="待审核提现"
            value={isLoading ? '-' : String(stats?.pending_withdrawals || 0)}
            icon={<svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 9V7a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2m2 4h10a2 2 0 002-2v-6a2 2 0 00-2-2H9a2 2 0 00-2 2v6a2 2 0 002 2zm7-5a2 2 0 11-4 0 2 2 0 014 0z" /></svg>}
          />
        </div>

        {/* 欢迎信息 */}
        <div className="bg-white rounded-lg p-8 shadow-sm border border-gray-100 text-center">
          <h2 className="text-2xl font-bold text-gray-900 mb-4">欢迎使用管理后台</h2>
          <p className="text-gray-600 mb-6">这里是百姓助手管理后台，您可以在这里管理用户、内容、订单等。</p>
          <div className="flex justify-center gap-4">
            <a href="/admin/users" className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors">
              用户管理
            </a>
            <a href="/admin/content" className="px-6 py-3 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 transition-colors">
              内容管理
            </a>
          </div>
        </div>
      </div>
    </div>
  );
}
