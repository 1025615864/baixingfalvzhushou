/**
 * WalletPage - 钱包管理页面
 * 
 * 功能：钱包余额、收支明细、充值提现入口
 */

import { useState } from 'react';
import { Link } from 'react-router-dom';

import { useWalletBalance, useIncomeRecords, useWithdrawals } from '../hooks/useSettlements';
import { formatCurrency } from '../utils/format';

type TabType = 'overview' | 'income' | 'withdrawal';

/**
 * 钱包概览卡片
 */
function WalletOverviewCard(): JSX.Element {
  const { data: wallet, isLoading, error } = useWalletBalance();

  if (isLoading) {
    return (
      <div className="bg-gradient-to-r from-blue-600 to-purple-600 rounded-xl shadow-lg p-6 text-white animate-pulse">
        <div className="h-8 bg-white/20 rounded w-1/3 mb-4"></div>
        <div className="h-12 bg-white/20 rounded w-1/2 mb-2"></div>
        <div className="h-4 bg-white/20 rounded w-1/4"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-xl p-6">
        <p className="text-red-600">加载钱包数据失败</p>
      </div>
    );
  }

  return (
    <div className="bg-gradient-to-r from-blue-600 to-purple-600 rounded-xl shadow-lg p-6 text-white" data-testid="wallet-balance">
      <p className="text-white/70 text-sm mb-2">可用余额</p>
      <p className="text-4xl font-bold mb-4" data-testid="wallet-available-balance">
        {formatCurrency(wallet?.availableAmount || 0)}
      </p>
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 pt-4 border-t border-white/20">
        <div>
          <p className="text-white/60 text-xs">累计收入</p>
          <p className="text-lg font-semibold">
            {formatCurrency(wallet?.totalIncome || 0)}
          </p>
        </div>
        <div>
          <p className="text-white/60 text-xs">已提现</p>
          <p className="text-lg font-semibold">
            {formatCurrency(wallet?.withdrawnAmount || 0)}
          </p>
        </div>
        <div>
          <p className="text-white/60 text-xs">待结算</p>
          <p className="text-lg font-semibold">
            {formatCurrency(wallet?.pendingAmount || 0)}
          </p>
        </div>
        <div>
          <p className="text-white/60 text-xs">冻结金额</p>
          <p className="text-lg font-semibold">
            {formatCurrency(wallet?.frozenBalance || 0)}
          </p>
        </div>
      </div>
    </div>
  );
}

/**
 * 快捷操作卡片
 */
function QuickActionsCard(): JSX.Element {
  const actions = [
    {
      label: '申请提现',
      icon: '💸',
      to: '/settlement/withdrawal',
      description: '将余额提现到银行卡',
      color: 'bg-blue-50 text-blue-600 hover:bg-blue-100',
    },
    {
      label: '银行卡管理',
      icon: '🏦',
      to: '/settlement/bank-account',
      description: '添加或管理收款账户',
      color: 'bg-green-50 text-green-600 hover:bg-green-100',
    },
    {
      label: '收入明细',
      icon: '📈',
      to: '/settlement/income',
      description: '查看所有收入记录',
      color: 'bg-purple-50 text-purple-600 hover:bg-purple-100',
    },
    {
      label: '提现记录',
      icon: '📋',
      to: '/settlement/withdrawal#records',
      description: '查看提现历史',
      color: 'bg-orange-50 text-orange-600 hover:bg-orange-100',
    },
  ];

  return (
    <div className="bg-white rounded-xl shadow-sm p-6">
      <h3 className="text-lg font-semibold text-gray-900 mb-4">快捷操作</h3>
      <div className="grid grid-cols-2 gap-3">
        {actions.map((action) => (
          <Link key={action.label} to={action.to}>
            <div
              className={`${action.color} rounded-xl p-4 text-center transition-colors cursor-pointer`}
            >
              <div className="text-2xl mb-2">{action.icon}</div>
              <div className="text-sm font-medium">{action.label}</div>
              <div className="text-xs opacity-70 mt-1">{action.description}</div>
            </div>
          </Link>
        ))}
      </div>
    </div>
  );
}

/**
 * 最近收入记录
 */
function RecentIncomeList(): JSX.Element {
  const { data, isLoading } = useIncomeRecords({ page: 1, pageSize: 5 });

  if (isLoading) {
    return (
      <div className="bg-white rounded-xl shadow-sm p-6 animate-pulse">
        <div className="h-6 bg-gray-200 rounded w-1/4 mb-4"></div>
        <div className="space-y-3">
          {[1, 2, 3].map((i) => (
            <div key={i} className="h-12 bg-gray-100 rounded"></div>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-xl shadow-sm p-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-gray-900">最近收入</h3>
        <Link
          to="/settlement/income"
          className="text-sm text-blue-600 hover:text-blue-700"
        >
          查看全部 →
        </Link>
      </div>
      <div className="space-y-3">
        {data?.items.length === 0 ? (
          <p className="text-gray-500 text-center py-8">暂无收入记录</p>
        ) : (
          data?.items.map((record) => (
            <div
              key={record.id}
              className="flex items-center justify-between p-3 bg-gray-50 rounded-lg"
            >
              <div>
                <p className="text-sm font-medium text-gray-900">
                  {record.description}
                </p>
                <p className="text-xs text-gray-500">
                  {new Date(record.createdAt).toLocaleDateString('zh-CN')}
                </p>
              </div>
              <p className="text-green-600 font-semibold">
                +{formatCurrency(record.lawyerIncome || record.amount)}
              </p>
            </div>
          ))
        )}
      </div>
    </div>
  );
}

/**
 * 最近提现记录
 */
function RecentWithdrawalList(): JSX.Element {
  const { data, isLoading } = useWithdrawals({ page: 1, pageSize: 5 });

  const getStatusInfo = (status: string): { label: string; color: string } => {
    const statusMap: Record<string, { label: string; color: string }> = {
      pending: { label: '待审核', color: 'text-yellow-600 bg-yellow-50' },
      approved: { label: '已批准', color: 'text-blue-600 bg-blue-50' },
      processing: { label: '处理中', color: 'text-purple-600 bg-purple-50' },
      completed: { label: '已完成', color: 'text-green-600 bg-green-50' },
      rejected: { label: '已拒绝', color: 'text-red-600 bg-red-50' },
      failed: { label: '失败', color: 'text-red-600 bg-red-50' },
    };
    return statusMap[status] || { label: status, color: 'text-gray-600 bg-gray-50' };
  };

  if (isLoading) {
    return (
      <div className="bg-white rounded-xl shadow-sm p-6 animate-pulse">
        <div className="h-6 bg-gray-200 rounded w-1/4 mb-4"></div>
        <div className="space-y-3">
          {[1, 2, 3].map((i) => (
            <div key={i} className="h-12 bg-gray-100 rounded"></div>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-xl shadow-sm p-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-gray-900">最近提现</h3>
        <Link
          to="/settlement/withdrawal#records"
          className="text-sm text-blue-600 hover:text-blue-700"
        >
          查看全部 →
        </Link>
      </div>
      <div className="space-y-3">
        {data?.items.length === 0 ? (
          <p className="text-gray-500 text-center py-8">暂无提现记录</p>
        ) : (
          data?.items.map((withdrawal) => {
            const statusInfo = getStatusInfo(withdrawal.status);
            return (
              <div
                key={withdrawal.id}
                className="flex items-center justify-between p-3 bg-gray-50 rounded-lg"
              >
                <div>
                  <p className="text-sm font-medium text-gray-900">
                    提现 {formatCurrency(withdrawal.amount)}
                  </p>
                  <p className="text-xs text-gray-500">
                    {new Date(withdrawal.createdAt).toLocaleDateString('zh-CN')}
                  </p>
                </div>
                <div className="text-right">
                  <span className={`text-xs px-2 py-1 rounded-full ${statusInfo.color}`}>
                    {statusInfo.label}
                  </span>
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}

/**
 * 钱包管理页面
 */
export function WalletPage(): JSX.Element {
  const [activeTab, setActiveTab] = useState<TabType>('overview');

  /**
   * 渲染标签页内容
   */
  const renderTabContent = (): JSX.Element => {
    switch (activeTab) {
      case 'overview':
        return (
          <div className="space-y-6">
            <WalletOverviewCard />
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <RecentIncomeList />
              <RecentWithdrawalList />
            </div>
            <QuickActionsCard />
          </div>
        );

      case 'income':
        return (
          <div className="bg-white rounded-xl shadow-sm p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">收入明细</h3>
            <p className="text-gray-600 mb-4">
              查看您的所有收入记录，包括咨询收入、奖励金等。
            </p>
            <Link
              to="/settlement/income"
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
            >
              进入收入管理页面 →
            </Link>
          </div>
        );

      case 'withdrawal':
        return (
          <div className="bg-white rounded-xl shadow-sm p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">提现管理</h3>
            <p className="text-gray-600 mb-4">
              申请提现、查看提现记录和状态跟踪。
            </p>
            <Link
              to="/settlement/withdrawal"
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
            >
              进入提现管理页面 →
            </Link>
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
          <h1 className="text-2xl font-bold text-gray-900">钱包管理</h1>
          <p className="text-gray-500 mt-1">管理您的钱包余额和收支记录</p>
        </div>

        {/* 标签导航 */}
        <div className="bg-white rounded-xl shadow-sm mb-6">
          <div className="flex border-b">
            {(['overview', 'income', 'withdrawal'] as TabType[]).map((tab) => (
              <button
                key={tab}
                onClick={() => setActiveTab(tab)}
                className={`flex-1 px-6 py-4 text-sm font-medium text-center border-b-2 transition-colors ${
                  activeTab === tab
                    ? 'text-blue-600 border-blue-600 bg-blue-50'
                    : 'text-gray-500 border-transparent hover:text-gray-700 hover:bg-gray-50'
                }`}
              >
                {tab === 'overview' && '📊 '}
                {tab === 'income' && '📈 '}
                {tab === 'withdrawal' && '💸 '}
                {tab === 'overview' && '概览'}
                {tab === 'income' && '收入'}
                {tab === 'withdrawal' && '提现'}
              </button>
            ))}
          </div>
        </div>

        {/* 标签内容 */}
        {renderTabContent()}
      </div>
    </div>
  );
}