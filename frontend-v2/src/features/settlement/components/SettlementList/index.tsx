import { useWalletBalance, useIncomeRecords, useWithdrawals } from '../../hooks/useSettlements';
import type { IncomeRecord, WithdrawalRequest } from '../../types';

export function SettlementList(): JSX.Element {
  const { data: wallet, isLoading: isWalletLoading, isError: isWalletError } = useWalletBalance();
  const { data: incomeData, isLoading: isIncomeLoading } = useIncomeRecords();
  const { data: withdrawalData, isLoading: isWithdrawalLoading } = useWithdrawals();

  const isLoading = isWalletLoading || isIncomeLoading || isWithdrawalLoading;
  const isError = isWalletError;

  if (isLoading) {
    return (
      <div className="space-y-4">
        {Array.from({ length: 2 }, (_, index) => (
          <div
            key={index}
            className="bg-white rounded-lg shadow-sm border border-gray-200 p-4 animate-pulse"
          >
            <div className="space-y-3">
              <div className="h-6 bg-gray-200 rounded w-1/4" />
              <div className="h-4 bg-gray-200 rounded w-3/4" />
              <div className="h-4 bg-gray-200 rounded w-1/2" />
            </div>
          </div>
        ))}
      </div>
    );
  }

  if (isError) {
    return (
      <div className="text-center py-8">
        <p className="text-red-600">加载结算记录失败</p>
      </div>
    );
  }

  const incomeRecords = incomeData?.items ?? [];
  const withdrawals = withdrawalData?.items ?? [];

  if (!wallet || (incomeRecords.length === 0 && withdrawals.length === 0)) {
    return (
      <div className="text-center py-8 bg-white rounded-lg border border-gray-200">
        <p className="text-gray-500">暂无结算记录</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* 钱包余额卡片 */}
      {wallet && (
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
          <h3 className="text-sm font-medium text-gray-500 mb-3">钱包余额</h3>
          <div className="grid grid-cols-4 gap-4">
            <div className="text-center">
              <p className="text-2xl font-bold text-green-600">¥{(wallet.balance ?? 0).toFixed(2)}</p>
              <p className="text-xs text-gray-400">可用余额</p>
            </div>
            <div className="text-center">
              <p className="text-lg font-medium text-gray-900">¥{(wallet.totalIncome ?? 0).toFixed(2)}</p>
              <p className="text-xs text-gray-400">累计收入</p>
            </div>
            <div className="text-center">
              <p className="text-lg font-medium text-blue-600">¥{(wallet.pendingAmount ?? 0).toFixed(2)}</p>
              <p className="text-xs text-gray-400">待结算</p>
            </div>
            <div className="text-center">
              <p className="text-lg font-medium text-orange-600">¥{(wallet.frozenBalance ?? 0).toFixed(2)}</p>
              <p className="text-xs text-gray-400">冻结金额</p>
            </div>
          </div>
        </div>
      )}

      {/* 最近收入记录 */}
      {incomeRecords.length > 0 && (
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
          <h3 className="text-sm font-medium text-gray-500 mb-3">最近收入</h3>
          <div className="space-y-3">
            {incomeRecords.slice(0, 5).map((record: IncomeRecord) => (
              <div key={record.id} className="flex items-center justify-between py-2 border-b border-gray-100 last:border-0">
                <div>
                  <p className="text-sm font-medium text-gray-900">{record.description}</p>
                  <p className="text-xs text-gray-400">{new Date(record.createdAt).toLocaleDateString('zh-CN')}</p>
                </div>
                <p className="text-sm font-medium text-green-600">+¥{record.amount.toFixed(2)}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* 最近提现记录 */}
      {withdrawals.length > 0 && (
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
          <h3 className="text-sm font-medium text-gray-500 mb-3">最近提现</h3>
          <div className="space-y-3">
            {withdrawals.slice(0, 5).map((record: WithdrawalRequest) => (
              <div key={record.id} className="flex items-center justify-between py-2 border-b border-gray-100 last:border-0">
                <div>
                  <p className="text-sm font-medium text-gray-900">{record.accountInfoMasked}</p>
                  <p className="text-xs text-gray-400">{new Date(record.createdAt).toLocaleDateString('zh-CN')}</p>
                </div>
                <div className="text-right">
                  <p className="text-sm font-medium text-gray-900">¥{record.actualAmount.toFixed(2)}</p>
                  <p className="text-xs text-gray-400">{record.status}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}