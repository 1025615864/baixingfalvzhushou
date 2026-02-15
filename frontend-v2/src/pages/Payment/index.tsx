import { useState } from 'react';

import {
  OrderList,
  useWalletBalance,
  useTransactions,
} from '@/features/payment';

type TransactionType = 'income' | 'expense' | 'refund' | 'withdrawal';

interface Transaction {
  id: string;
  description: string;
  amount: number;
  type: TransactionType;
  balance: number;
  createdAt: string;
}

function formatAmount(amount: number, type: TransactionType): string {
  const prefix = type === 'expense' || type === 'withdrawal' ? '-' : '+';
  return `${prefix}¥${Math.abs(amount).toFixed(2)}`;
}

function getTransactionColor(type: TransactionType): string {
  switch (type) {
    case 'income':
      return 'text-green-600';
    case 'expense':
      return 'text-red-600';
    case 'refund':
      return 'text-blue-600';
    case 'withdrawal':
      return 'text-orange-600';
    default:
      return 'text-gray-600';
  }
}

export function PaymentPage(): JSX.Element {
  const [activeTab, setActiveTab] = useState<'orders' | 'wallet'>('orders');
  const { data: balance } = useWalletBalance() as { data: { balance: number } | undefined };
  const { data: transactions } = useTransactions() as { data: Transaction[] | undefined };

  const tabs = [
    { key: 'orders' as const, label: '我的订单' },
    { key: 'wallet' as const, label: '钱包' },
  ];

  return (
    <div className="container mx-auto px-4 py-6 max-w-4xl">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">支付中心</h1>
        <p className="text-gray-600 mt-1">管理您的订单和钱包</p>
      </div>

      {/* Tabs */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 mb-6">
        <div className="border-b border-gray-200">
          <div className="flex">
            {tabs.map((tab) => (
              <button
                key={tab.key}
                onClick={(): void => setActiveTab(tab.key)}
                className={`px-6 py-3 text-sm font-medium border-b-2 transition-colors ${
                  activeTab === tab.key
                    ? 'border-primary-600 text-primary-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700'
                }`}
                type="button"
              >
                {tab.label}
              </button>
            ))}
          </div>
        </div>

        <div className="p-6">
          {activeTab === 'orders' && (
            <OrderList />
          )}

          {activeTab === 'wallet' && (
            <div className="space-y-6">
              {/* Balance Card */}
              <div className="bg-gradient-to-r from-primary-500 to-primary-600 rounded-xl p-6 text-white">
                <p className="text-primary-100 text-sm mb-1">当前余额</p>
                <p className="text-4xl font-bold">
                  ¥{balance?.balance.toFixed(2) || '0.00'}
                </p>
                <div className="mt-4 flex gap-4">
                  <button
                    className="px-4 py-2 bg-white text-primary-600 rounded-lg text-sm font-medium hover:bg-primary-50 transition-colors"
                    type="button"
                  >
                    充值
                  </button>
                  <button
                    className="px-4 py-2 bg-primary-700 text-white rounded-lg text-sm font-medium hover:bg-primary-800 transition-colors"
                    type="button"
                  >
                    提现
                  </button>
                </div>
              </div>

              {/* Transaction History */}
              <div>
                <h3 className="text-lg font-semibold text-gray-900 mb-4">交易记录</h3>
                {transactions && transactions.length > 0 ? (
                  <div className="space-y-3">
                    {transactions.map((tx: Transaction) => (
                      <div
                        key={tx.id}
                        className="flex items-center justify-between p-4 bg-gray-50 rounded-lg"
                      >
                        <div>
                          <p className="font-medium text-gray-900">{tx.description}</p>
                          <time className="text-xs text-gray-400">
                            {new Date(tx.createdAt).toLocaleString('zh-CN')}
                          </time>
                        </div>
                        <div className="text-right">
                          <p className={`font-semibold ${getTransactionColor(tx.type)}`}>
                            {formatAmount(tx.amount, tx.type)}
                          </p>
                          <p className="text-xs text-gray-400">
                            余额 ¥{tx.balance.toFixed(2)}
                          </p>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-center text-gray-500 py-8">暂无交易记录</p>
                )}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}