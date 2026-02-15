import { useState } from 'react';

import {
  SettlementList,
  useIncomeRecords,
  useWithdrawals,
  withdrawalStatusConfig,
} from '@/features/settlement';

interface IncomeRecord {
  id: string;
  description: string;
  amount: number;
  sourceType: string;
  settled: boolean;
  createdAt: string;
}

interface WithdrawalRequest {
  id: string;
  bankName: string;
  bankAccount: string;
  amount: number;
  status: 'pending' | 'processing' | 'completed' | 'rejected';
  createdAt: string;
  processedAt?: string;
}

export function SettlementPage(): JSX.Element {
  const [activeTab, setActiveTab] = useState<'settlements' | 'income' | 'withdrawals'>('settlements');
  const { data: incomeRecords } = useIncomeRecords() as { data: IncomeRecord[] | undefined };
  const { data: withdrawals } = useWithdrawals() as { data: WithdrawalRequest[] | undefined };

  const tabs = [
    { key: 'settlements' as const, label: '结算记录' },
    { key: 'income' as const, label: '收入明细' },
    { key: 'withdrawals' as const, label: '提现记录' },
  ];

  const getSourceTypeLabel = (type: string): string => {
    const labels: Record<string, string> = {
      consultation: '咨询',
      document: '文档',
      other: '其他',
    };
    return labels[type] || type;
  };

  return (
    <div className="container mx-auto px-4 py-6 max-w-4xl">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">收入结算</h1>
        <p className="text-gray-600 mt-1">管理您的服务收入和提现</p>
      </div>

      {/* Tabs */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200">
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
          {activeTab === 'settlements' && <SettlementList />}

          {activeTab === 'income' && (
            <div className="space-y-3">
              {incomeRecords && incomeRecords.length > 0 ? (
                incomeRecords.map((record: IncomeRecord) => (
                  <div
                    key={record.id}
                    className="flex items-center justify-between p-4 bg-gray-50 rounded-lg"
                  >
                    <div>
                      <p className="font-medium text-gray-900">{record.description}</p>
                      <div className="flex items-center gap-2 mt-1">
                        <span className="px-2 py-0.5 bg-blue-50 text-blue-600 text-xs rounded">
                          {getSourceTypeLabel(record.sourceType)}
                        </span>
                        <time className="text-xs text-gray-400">
                          {new Date(record.createdAt).toLocaleString('zh-CN')}
                        </time>
                      </div>
                    </div>
                    <div className="text-right">
                      <p className="font-semibold text-green-600">+¥{record.amount.toFixed(2)}</p>
                      <p className={`text-xs ${record.settled ? 'text-green-500' : 'text-yellow-500'}`}>
                        {record.settled ? '✓ 已结算' : '待结算'}
                      </p>
                    </div>
                  </div>
                ))
              ) : (
                <p className="text-center text-gray-500 py-8">暂无收入记录</p>
              )}
            </div>
          )}

          {activeTab === 'withdrawals' && (
            <div className="space-y-3">
              {withdrawals && withdrawals.length > 0 ? (
                withdrawals.map((withdrawal: WithdrawalRequest) => {
                  const status = withdrawalStatusConfig[withdrawal.status];
                  return (
                    <div
                      key={withdrawal.id}
                      className="flex items-center justify-between p-4 bg-gray-50 rounded-lg"
                    >
                      <div>
                        <p className="font-medium text-gray-900">
                          提现至 {withdrawal.bankName}
                        </p>
                        <p className="text-sm text-gray-500">{withdrawal.bankAccount}</p>
                        <div className="flex items-center gap-2 mt-1">
                          <span className={`px-2 py-0.5 text-xs rounded ${status.color}`}>
                            {status.label}
                          </span>
                          <time className="text-xs text-gray-400">
                            {new Date(withdrawal.createdAt).toLocaleString('zh-CN')}
                          </time>
                        </div>
                      </div>
                      <div className="text-right">
                        <p className="font-semibold text-gray-900">
                          -¥{withdrawal.amount.toFixed(2)}
                        </p>
                        {withdrawal.processedAt && (
                          <p className="text-xs text-gray-400">
                            处理时间: {new Date(withdrawal.processedAt).toLocaleString('zh-CN')}
                          </p>
                        )}
                      </div>
                    </div>
                  );
                })
              ) : (
                <p className="text-center text-gray-500 py-8">暂无提现记录</p>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}