/**
 * ComplianceDashboard - 合规仪表盘组件
 */

import { useEnterpriseInfo } from '../hooks/useEnterprise';

interface ComplianceDashboardProps {
  accountId: number;
  className?: string;
}

interface StatCardProps {
  title: string;
  value: string | number;
  trend?: string;
  trendType?: 'up' | 'down' | 'neutral';
  color: 'blue' | 'green' | 'yellow' | 'red';
}

/**
 * 统计卡片组件
 */
function StatCard({ title, value, trend, trendType = 'neutral', color }: StatCardProps): JSX.Element {
  const colorClasses = {
    blue: 'bg-blue-50 border-blue-100 text-blue-900',
    green: 'bg-green-50 border-green-100 text-green-900',
    yellow: 'bg-yellow-50 border-yellow-100 text-yellow-900',
    red: 'bg-red-50 border-red-100 text-red-900',
  };

  const trendColors = {
    up: 'text-green-600',
    down: 'text-red-600',
    neutral: 'text-gray-500',
  };

  return (
    <div className={`p-4 rounded-lg border ${colorClasses[color]}`}>
      <h4 className="text-sm font-medium opacity-80">{title}</h4>
      <div className="mt-2 flex items-baseline gap-2">
        <span className="text-2xl font-bold">{value}</span>
        {trend && <span className={`text-sm ${trendColors[trendType]}`}>{trend}</span>}
      </div>
    </div>
  );
}

/**
 * 合规仪表盘组件
 */
export function ComplianceDashboard({ accountId, className = '' }: ComplianceDashboardProps): JSX.Element {
  const { data: enterprise, isLoading, error } = useEnterpriseInfo(accountId);

  if (isLoading) {
    return (
      <div className={`bg-white rounded-xl shadow-sm p-6 ${className}`}>
        <div className="animate-pulse space-y-4">
          <div className="h-6 bg-gray-200 rounded w-1/3" />
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {[1, 2, 3, 4].map((i) => (
              <div key={i} className="h-20 bg-gray-200 rounded" />
            ))}
          </div>
        </div>
      </div>
    );
  }

  if (error || !enterprise) {
    return (
      <div className={`bg-white rounded-xl shadow-sm p-6 ${className}`}>
        <div className="text-center text-red-500">
          <p>加载企业信息失败</p>
        </div>
      </div>
    );
  }

  const quotaPercent = Math.round((enterprise.quotaUsed / enterprise.quotaTotal) * 100);

  return (
    <div className={`bg-white rounded-xl shadow-sm p-6 ${className}`}>
      <div className="mb-6">
        <h3 className="text-lg font-semibold text-gray-900">合规概览</h3>
        <p className="text-sm text-gray-500">{enterprise.companyName}</p>
      </div>

      {/* 核心指标 */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
        <StatCard
          title="团队成员"
          value={enterprise.memberCount}
          trend="+2 本月"
          trendType="up"
          color="blue"
        />
        <StatCard
          title="合同审查"
          value={enterprise.contractCount}
          trend="12 待处理"
          trendType="neutral"
          color="yellow"
        />
        <StatCard
          title="订阅计划"
          value={enterprise.subscriptionPlan.toUpperCase()}
          color="green"
        />
        <StatCard
          title="配额使用"
          value={`${quotaPercent}%`}
          trend={`${enterprise.quotaUsed}/${enterprise.quotaTotal}`}
          trendType={quotaPercent > 80 ? 'down' : 'neutral'}
          color={quotaPercent > 80 ? 'red' : 'blue'}
        />
      </div>

      {/* 配额进度条 */}
      <div className="mb-6">
        <div className="flex justify-between text-sm mb-2">
          <span className="text-gray-600">配额使用情况</span>
          <span className={`font-medium ${quotaPercent > 80 ? 'text-red-600' : 'text-gray-900'}`}>
            {enterprise.quotaUsed} / {enterprise.quotaTotal}
          </span>
        </div>
        <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
          <div
            className={`h-full rounded-full transition-all duration-500 ${
              quotaPercent > 80 ? 'bg-red-500' : quotaPercent > 50 ? 'bg-yellow-500' : 'bg-green-500'
            }`}
            style={{ width: `${Math.min(quotaPercent, 100)}%` }}
          ></div>
        </div>
      </div>

      {/* 企业信息 */}
      <div className="border-t border-gray-100 pt-4">
        <h4 className="text-sm font-medium text-gray-700 mb-3">企业信息</h4>
        <div className="grid grid-cols-2 gap-4 text-sm">
          <div>
            <span className="text-gray-500">行业:</span>
            <span className="ml-2 text-gray-900">{enterprise.industry}</span>
          </div>
          <div>
            <span className="text-gray-500">规模:</span>
            <span className="ml-2 text-gray-900">{enterprise.scale}</span>
          </div>
          <div>
            <span className="text-gray-500">状态:</span>
            <span
              className={`ml-2 px-2 py-0.5 rounded-full text-xs ${
                enterprise.status === 'active'
                  ? 'bg-green-100 text-green-800'
                  : 'bg-red-100 text-red-800'
              }`}
            >
              {enterprise.status === 'active' ? '正常' : '异常'}
            </span>
          </div>
          <div>
            <span className="text-gray-500">加入时间:</span>
            <span className="ml-2 text-gray-900">
              {new Date(enterprise.createdAt).toLocaleDateString('zh-CN')}
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}