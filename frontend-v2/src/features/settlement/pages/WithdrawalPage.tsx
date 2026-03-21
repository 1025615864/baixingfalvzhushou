/**
 * WithdrawalPage - 提现申请页面
 * 
 * 功能：提现申请表单、提现记录、状态跟踪
 */

import { useState, useRef, useEffect } from 'react';

import { useWalletBalance, useWithdrawals, useRequestWithdrawal, useBankAccounts } from '../hooks/useSettlements';
import { formatCurrency, formatDateTime } from '../utils/format';
import { useToast } from '../../../components/ui/useToast';
import type { WithdrawMethod, WithdrawalStatus } from '../types';

/**
 * 状态标签配置
 */
const statusConfig: Record<WithdrawalStatus, { label: string; color: string }> = {
  pending: { label: '待审核', color: 'text-yellow-600 bg-yellow-50' },
  approved: { label: '已批准', color: 'text-blue-600 bg-blue-50' },
  processing: { label: '处理中', color: 'text-purple-600 bg-purple-50' },
  completed: { label: '已完成', color: 'text-green-600 bg-green-50' },
  rejected: { label: '已拒绝', color: 'text-red-600 bg-red-50' },
  failed: { label: '失败', color: 'text-red-600 bg-red-50' },
};

/**
 * 提现方式配置
 */
const withdrawMethodConfig: Record<WithdrawMethod, { label: string; icon: string }> = {
  bank_transfer: { label: '银行卡', icon: '🏦' },
  alipay: { label: '支付宝', icon: '💙' },
  wechat_pay: { label: '微信支付', icon: '💚' },
};

/**
 * 余额卡片组件
 */
function BalanceCard(): JSX.Element {
  const { data: wallet, isLoading } = useWalletBalance();

  if (isLoading) {
    return (
      <div className="bg-gradient-to-r from-blue-600 to-purple-600 rounded-xl shadow-lg p-6 text-white animate-pulse">
        <div className="h-8 bg-white/20 rounded w-1/3 mb-4"></div>
        <div className="h-12 bg-white/20 rounded w-1/2 mb-2"></div>
      </div>
    );
  }

  return (
    <div className="bg-gradient-to-r from-blue-600 to-purple-600 rounded-xl shadow-lg p-6 text-white">
      <p className="text-white/70 text-sm mb-2">可提现余额</p>
      <p className="text-4xl font-bold mb-4">
        {formatCurrency(wallet?.availableAmount || 0)}
      </p>
      <div className="grid grid-cols-2 gap-4 pt-4 border-t border-white/20">
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
 * 提现申请表单
 */
function WithdrawalForm({ onSuccess }: { onSuccess: () => void }): JSX.Element {
  const { data: wallet } = useWalletBalance();
  const { data: bankAccounts } = useBankAccounts();
  const requestWithdrawal = useRequestWithdrawal();
  const toast = useToast();

  const [amount, setAmount] = useState('');
  const [method, setMethod] = useState<WithdrawMethod>('bank_transfer');
  const [bankAccountId, setBankAccountId] = useState('');
  const [errors, setErrors] = useState<Record<string, string>>({});

  const MIN_WITHDRAWAL = 100; // 最小提现金额

  // 初始化默认银行卡
  useEffect(() => {
    if (bankAccounts && bankAccounts.length > 0) {
      const defaultAccount = bankAccounts.find((acc) => acc.isDefault) || bankAccounts[0];
      setBankAccountId(defaultAccount.id);
    }
  }, [bankAccounts]);

  // 验证表单
  const validate = (): boolean => {
    const newErrors: Record<string, string> = {};

    const numAmount = parseFloat(amount);
    if (!amount || isNaN(numAmount) || numAmount <= 0) {
      newErrors.amount = '请输入有效的提现金额';
    } else if (numAmount < MIN_WITHDRAWAL) {
      newErrors.amount = `最低提现金额为 ${formatCurrency(MIN_WITHDRAWAL)}`;
    } else if (numAmount > (wallet?.availableAmount || 0)) {
      newErrors.amount = '提现金额不能超过可提现余额';
    }

    if (!bankAccountId) {
      newErrors.bankAccount = '请选择收款账户';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  // 提交申请
  const handleSubmit = async (e: React.FormEvent): Promise<void> => {
    e.preventDefault();

    if (!validate()) return;

    try {
      await requestWithdrawal.mutateAsync({
        amount: parseFloat(amount),
        withdrawMethod: method,
        bankAccountId: bankAccountId || undefined,
      });

      toast.success('提现申请已提交，请等待审核');
      setAmount('');
      onSuccess();
    } catch (err) {
      toast.error(err instanceof Error ? err.message : '提现申请失败');
    }
  };

  // 快捷金额选项
  const availableAmount = wallet?.availableAmount || 0;
  const quickAmounts = [100, 200, 500, 1000].filter((a) => a <= availableAmount);

  return (
    <div className="bg-white rounded-xl shadow-sm p-6">
      <h2 className="text-lg font-semibold text-gray-900 mb-6">申请提现</h2>

      <form onSubmit={(e) => void handleSubmit(e)} className="space-y-6">
        {/* 提现金额 */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            提现金额 <span className="text-red-500">*</span>
          </label>
          <div className="relative">
            <span className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-500">¥</span>
            <input
              type="number"
              data-testid="withdrawal-amount"
              value={amount}
              onChange={(e) => setAmount(e.target.value)}
              placeholder={`最低 ${formatCurrency(MIN_WITHDRAWAL)}`}
              className={`w-full pl-8 pr-4 py-3 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 ${
                errors.amount ? 'border-red-300' : 'border-gray-300'
              }`}
            />
          </div>
          {errors.amount && <p className="mt-1 text-sm text-red-600">{errors.amount}</p>}

          {/* 快捷金额 */}
          <div className="flex flex-wrap gap-2 mt-3">
            {quickAmounts.map((quickAmount) => (
              <button
                key={quickAmount}
                type="button"
                onClick={() => setAmount(String(quickAmount))}
                className="px-3 py-1.5 text-sm bg-gray-100 hover:bg-gray-200 rounded-lg transition-colors"
              >
                {formatCurrency(quickAmount)}
              </button>
            ))}
            <button
              type="button"
              onClick={() => setAmount(String(Math.floor(availableAmount)))}
              className="px-3 py-1.5 text-sm bg-blue-50 text-blue-600 hover:bg-blue-100 rounded-lg transition-colors"
            >
              全部提现
            </button>
          </div>
        </div>

        {/* 提现方式 */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-3">
            提现方式 <span className="text-red-500">*</span>
          </label>
          <div className="grid grid-cols-3 gap-3">
            {(['bank_transfer', 'alipay', 'wechat_pay'] as WithdrawMethod[]).map((m) => (
              <button
                key={m}
                type="button"
                onClick={() => setMethod(m)}
                className={`p-4 border rounded-xl text-center transition-all ${
                  method === m ? 'border-blue-500 bg-blue-50 text-blue-700' : 'border-gray-200 hover:border-gray-300'
                }`}
              >
                <div className="text-2xl mb-1">{withdrawMethodConfig[m].icon}</div>
                <div className="text-sm font-medium">{withdrawMethodConfig[m].label}</div>
              </button>
            ))}
          </div>
        </div>

        {/* 收款账户 */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-3">
            收款账户 <span className="text-red-500">*</span>
          </label>
          {bankAccounts && bankAccounts.length > 0 ? (
            <div className="space-y-2" data-testid="bank-card-select">
              {bankAccounts.map((account, index) => (
                <button
                  key={account.id}
                  type="button"
                  data-testid={`bank-card-option-${index}`}
                  onClick={() => setBankAccountId(account.id)}
                  className={`w-full p-4 border rounded-xl text-left transition-all ${
                    bankAccountId === account.id
                      ? 'border-blue-500 bg-blue-50'
                      : 'border-gray-200 hover:border-gray-300'
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="text-lg">
                          {account.accountType === 'personal' ? '👤' : '🏢'}
                        </span>
                        <span className="font-medium text-gray-900">
                          {account.accountType === 'personal' ? '个人账户' : '企业账户'}
                        </span>
                        {account.isDefault && (
                          <span className="text-xs bg-blue-100 text-blue-600 px-2 py-0.5 rounded">
                            默认
                          </span>
                        )}
                      </div>
                      <div className="text-sm text-gray-500 mt-1">{account.accountNo}</div>
                    </div>
                    <div
                      className={`w-5 h-5 rounded-full border-2 ${
                        bankAccountId === account.id ? 'border-blue-500 bg-blue-500' : 'border-gray-300'
                      }`}
                    />
                  </div>
                </button>
              ))}
            </div>
          ) : (
            <div className="text-center py-8 bg-gray-50 rounded-lg">
              <p className="text-gray-500 mb-2">暂无收款账户</p>
              <a
                href="/settlement/bank-account"
                className="text-blue-600 hover:text-blue-700 text-sm font-medium"
              >
                添加银行卡 →
              </a>
            </div>
          )}
          {errors.bankAccount && <p className="mt-1 text-sm text-red-600">{errors.bankAccount}</p>}
        </div>

        {/* 提现说明 */}
        <div className="bg-blue-50 rounded-lg p-4">
          <h4 className="text-sm font-medium text-blue-900 mb-2">💡 提现说明</h4>
          <ul className="text-sm text-blue-700 space-y-1">
            <li>• 最低提现金额：{formatCurrency(MIN_WITHDRAWAL)}</li>
            <li>• 工作日 9:00-17:00 提交的申请将在 24 小时内处理</li>
            <li>• 非工作时间提交的申请将顺延至下一工作日处理</li>
            <li>• 提现成功后资金将在 1-3 个工作日内到账</li>
          </ul>
        </div>

        {/* 提交按钮 */}
        <button
          type="submit"
          data-testid="withdrawal-submit"
          disabled={requestWithdrawal.isPending || !bankAccounts || bankAccounts.length === 0}
          className="w-full py-3 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {requestWithdrawal.isPending ? '提交中...' : '确认提现'}
        </button>
      </form>
    </div>
  );
}

/**
 * 提现记录列表
 */
function WithdrawalRecords(): JSX.Element {
  const recordsRef = useRef<HTMLDivElement>(null);
  const [page, setPage] = useState(1);
  const pageSize = 10;

  const { data, isLoading } = useWithdrawals({ page, pageSize });

  const records = data?.items || [];
  const meta = data?.meta;
  const totalPages = meta?.totalPages || 1;

  // 检查是否需要滚动到记录列表
  useEffect(() => {
    const hash = window.location.hash;
    if (hash === '#records' && recordsRef.current) {
      recordsRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, []);

  return (
    <div ref={recordsRef} className="bg-white rounded-xl shadow-sm p-6">
      <h3 className="text-lg font-semibold text-gray-900 mb-4">提现记录</h3>

      {isLoading ? (
        <div className="space-y-3">
          {[1, 2, 3].map((i) => (
            <div key={i} className="h-16 bg-gray-100 rounded animate-pulse"></div>
          ))}
        </div>
      ) : records.length === 0 ? (
        <div className="text-center py-12">
          <div className="w-16 h-16 mx-auto mb-4 bg-gray-100 rounded-full flex items-center justify-center">
            <svg
              className="w-8 h-8 text-gray-400"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M17 9V7a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2m2 4h10a2 2 0 002-2v-6a2 2 0 00-2-2H9a2 2 0 00-2 2v6a2 2 0 002 2zm7-5a2 2 0 11-4 0 2 2 0 014 0z"
              />
            </svg>
          </div>
          <h3 className="text-lg font-medium text-gray-900 mb-2">暂无提现记录</h3>
          <p className="text-gray-500">您可以点击上方表单申请提现</p>
        </div>
      ) : (
        <>
          {/* 记录列表 */}
          <div className="space-y-3">
            {records.map((withdrawal) => {
              const statusInfo = statusConfig[withdrawal.status];
              return (
                <div
                  key={withdrawal.id}
                  className="flex items-center justify-between p-4 bg-gray-50 rounded-lg"
                >
                  <div className="flex-1">
                    <div className="flex items-center gap-3">
                      <span className="text-lg">
                        {withdrawMethodConfig[withdrawal.withdrawMethod]?.icon || '💰'}
                      </span>
                      <div>
                        <p className="text-sm font-medium text-gray-900">
                          提现 {formatCurrency(withdrawal.amount)}
                        </p>
                        <p className="text-xs text-gray-500">
                          手续费：{formatCurrency(withdrawal.fee)} | 实际到账：
                          {formatCurrency(withdrawal.actualAmount)}
                        </p>
                      </div>
                    </div>
                    <div className="mt-2 text-xs text-gray-500">
                      申请时间：{formatDateTime(withdrawal.createdAt)}
                    </div>
                  </div>
                  <div className="text-right">
                    <span
                      className={`inline-flex px-3 py-1 text-xs font-semibold rounded-full ${statusInfo.color}`}
                    >
                      {statusInfo.label}
                    </span>
                    {withdrawal.rejectReason && (
                      <p className="text-xs text-red-600 mt-1">原因：{withdrawal.rejectReason}</p>
                    )}
                  </div>
                </div>
              );
            })}
          </div>

          {/* 分页 */}
          {totalPages > 1 && (
            <div className="mt-4 flex items-center justify-between">
              <div className="text-sm text-gray-500">
                第 {meta?.page || 1} 页，共 {meta?.totalPages || 1} 页
              </div>
              <div className="flex gap-2">
                <button
                  onClick={() => setPage((p) => Math.max(1, p - 1))}
                  disabled={page === 1}
                  className="px-4 py-2 border rounded-lg text-sm font-medium disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50"
                >
                  上一页
                </button>
                <button
                  onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                  disabled={page === totalPages}
                  className="px-4 py-2 border rounded-lg text-sm font-medium disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50"
                >
                  下一页
                </button>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}

/**
 * 提现申请页面
 */
export function WithdrawalPage(): JSX.Element {
  const [refreshKey, setRefreshKey] = useState(0);

  const handleSuccess = (): void => {
    setRefreshKey((prev) => prev + 1);
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-6xl mx-auto px-4 py-8">
        {/* 页面标题 */}
        <div className="mb-6">
          <h1 className="text-2xl font-bold text-gray-900">提现管理</h1>
          <p className="text-gray-500 mt-1">申请提现、查看提现记录和状态跟踪</p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* 左侧：余额和表单 */}
          <div className="lg:col-span-1 space-y-6">
            <BalanceCard />
            <WithdrawalForm onSuccess={handleSuccess} />
          </div>

          {/* 右侧：记录列表 */}
          <div className="lg:col-span-2">
            <WithdrawalRecords key={refreshKey} />
          </div>
        </div>
      </div>
    </div>
  );
}