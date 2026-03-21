/**
 * SettlementPage - 结算管理主页
 *
 * 功能：结算功能导航、钱包概览、收入摘要
 */

import { useState } from 'react';
import { Link } from 'react-router-dom';

import { useWalletBalance, useIncomeRecords } from '../hooks/useSettlements';

/**
 * 格式化货币
 */
function formatCurrency(value: number): string {
  return `¥${value.toLocaleString('zh-CN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
}

type TabType = 'overview' | 'wallet' | 'income' | 'withdrawal' | 'bank-account';

/**
 * 标签页配置
 */
const tabs: Array<{ id: TabType; label: string; icon: string }> = [
  { id: 'overview', label: '概览', icon: '📊' },
  { id: 'wallet', label: '钱包', icon: '💰' },
  { id: 'income', label: '收入', icon: '📈' },
  { id: 'withdrawal', label: '提现', icon: '💸' },
  { id: 'bank-account', label: '银行卡', icon: '🏦' },
];

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
    <div className="bg-gradient-to-r from-blue-600 to-purple-600 rounded-xl shadow-lg p-6 text-white">
      <p className="text-white/70 text-sm mb-2">可用余额</p>
      <p className="text-4xl font-bold mb-4">
        {formatCurrency(wallet?.availableAmount || 0)}
      </p>
      <div className="grid grid-cols-3 gap-4 pt-4 border-t border-white/20">
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
      </div>
    </div>
  );
}

/**
 * 收入摘要卡片
 */
function IncomeSummaryCard(): JSX.Element {
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
 * 快捷操作卡片
 */
function QuickActionsCard(): JSX.Element {
  const actions = [
    {
      label: '申请提现',
      icon: '💸',
      to: '/settlement/withdrawal',
      color: 'bg-blue-50 text-blue-600 hover:bg-blue-100',
    },
    {
      label: '银行卡管理',
      icon: '🏦',
      to: '/settlement/bank-account',
      color: 'bg-green-50 text-green-600 hover:bg-green-100',
    },
    {
      label: '收入明细',
      icon: '📈',
      to: '/settlement/income',
      color: 'bg-purple-50 text-purple-600 hover:bg-purple-100',
    },
    {
      label: '钱包详情',
      icon: '💰',
      to: '/settlement/wallet',
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
            </div>
          </Link>
        ))}
      </div>
    </div>
  );
}

/**
 * 结算管理主页
 */
export function SettlementPage(): JSX.Element {
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
              <IncomeSummaryCard />
              <QuickActionsCard />
            </div>
          </div>
        );

      case 'wallet':
        return (
          <div className="space-y-6">
            <WalletOverviewCard />
            <div className="bg-white rounded-xl shadow-sm p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">
                钱包功能
              </h3>
              <p className="text-gray-600 mb-4">
                钱包功能包括余额查询、收支明细、充值提现等。
              </p>
              <div className="flex gap-3">
                <Link
                  to="/settlement/withdrawal"
                  className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
                >
                  申请提现
                </Link>
                <Link
                  to="/settlement/income"
                  className="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors"
                >
                  查看收支明细
                </Link>
              </div>
            </div>
          </div>
        );

      case 'income':
        return (
          <div className="bg-white rounded-xl shadow-sm p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">收入记录</h3>
            <p className="text-gray-600 mb-4">
              查看您的所有收入记录，支持筛选和导出功能。
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

      case 'bank-account':
        return (
          <div className="bg-white rounded-xl shadow-sm p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">
              银行卡管理
            </h3>
            <p className="text-gray-600 mb-4">
              管理您的收款银行卡，支持添加、编辑和删除。
            </p>
            <Link
              to="/settlement/bank-account"
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
            >
              进入银行卡管理页面 →
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
          <h1 className="text-2xl font-bold text-gray-900">结算管理</h1>
          <p className="text-gray-500 mt-1">管理您的钱包、收入和提现</p>
        </div>

        {/* 标签导航 */}
        <div className="bg-white rounded-xl shadow-sm mb-6 overflow-x-auto">
          <div className="flex min-w-max">
            {tabs.map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`flex items-center gap-2 px-6 py-4 text-sm font-medium border-b-2 transition-colors whitespace-nowrap ${
                  activeTab === tab.id
                    ? 'text-blue-600 border-blue-600 bg-blue-50'
                    : 'text-gray-500 border-transparent hover:text-gray-700 hover:bg-gray-50'
                }`}
              >
                <span>{tab.icon}</span>
                <span>{tab.label}</span>
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