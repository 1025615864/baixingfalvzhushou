/**
 * WithdrawalPage - 提现管理页面
 * 
 * 包含可提现余额展示、提现申请表单、提现记录列表、提现规则说明
 */

import { useState, useMemo } from 'react';
import { Link } from 'react-router-dom';

import { usePromotionStats, useWithdrawals, useRequestWithdrawal } from '../hooks/usePromotion';
import { useToast } from '../../../components/ui/useToast';

/** 提现方式 */
type WithdrawalMethod = 'alipay' | 'wechat' | 'bank' | 'reward';

/**
 * 获取提现方式显示名称
 */
function getMethodLabel(method: WithdrawalMethod): string {
  const labels: Record<WithdrawalMethod, string> = {
    alipay: '支付宝',
    wechat: '微信支付',
    bank: '银行卡',
    reward: '奖励金',
  };
  return labels[method];
}

/**
 * 获取提现方式图标
 */
function getMethodIcon(method: WithdrawalMethod): string {
  const icons: Record<WithdrawalMethod, string> = {
    alipay: '💙',
    wechat: '💚',
    bank: '🏦',
    reward: '🎁',
  };
  return icons[method];
}

/**
 * 获取状态显示信息
 */
function getStatusInfo(status: string): { label: string; color: string } {
  const statusMap: Record<string, { label: string; color: string }> = {
    pending: { label: '待审核', color: 'text-yellow-600 bg-yellow-50' },
    processing: { label: '处理中', color: 'text-blue-600 bg-blue-50' },
    completed: { label: '已完成', color: 'text-green-600 bg-green-50' },
    rejected: { label: '已拒绝', color: 'text-red-600 bg-red-50' },
  };
  return statusMap[status] || { label: status, color: 'text-gray-600 bg-gray-50' };
}

/**
 * 余额卡片组件
 */
function BalanceCard({ 
  available, 
  pending, 
  paid, 
  total 
}: { 
  available: number; 
  pending: number; 
  paid: number;
  total: number;
}): JSX.Element {
  return (
    <div className="bg-gradient-to-r from-blue-600 to-purple-600 rounded-xl shadow-lg p-6 text-white">
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-6">
        {/* 可提现余额 */}
        <div>
          <p className="text-white/70 text-sm mb-1">可提现余额</p>
          <p className="text-3xl font-bold">¥{available.toFixed(2)}</p>
        </div>
        
        {/* 待确认佣金 */}
        <div>
          <p className="text-white/70 text-sm mb-1">待确认佣金</p>
          <p className="text-2xl font-semibold">¥{pending.toFixed(2)}</p>
        </div>
        
        {/* 已结算 */}
        <div>
          <p className="text-white/70 text-sm mb-1">已结算</p>
          <p className="text-2xl font-semibold">¥{paid.toFixed(2)}</p>
        </div>
        
        {/* 累计佣金 */}
        <div>
          <p className="text-white/70 text-sm mb-1">累计佣金</p>
          <p className="text-2xl font-semibold">¥{total.toFixed(2)}</p>
        </div>
      </div>
    </div>
  );
}

/**
 * 提现申请表单
 */
function WithdrawalForm({ 
  availableBalance, 
  onSuccess 
}: { 
  availableBalance: number; 
  onSuccess: () => void;
}): JSX.Element {
  const [amount, setAmount] = useState('');
  const [method, setMethod] = useState<WithdrawalMethod>('alipay');
  const [accountInfo, setAccountInfo] = useState('');
  const [errors, setErrors] = useState<Record<string, string>>({});
  
  const requestWithdrawal = useRequestWithdrawal();
  const toast = useToast();

  const MIN_WITHDRAWAL = 100; // 最小提现金额

  // 验证表单
  const validate = (): boolean => {
    const newErrors: Record<string, string> = {};
    
    const numAmount = parseFloat(amount);
    if (!amount || isNaN(numAmount) || numAmount <= 0) {
      newErrors.amount = '请输入有效的提现金额';
    } else if (numAmount < MIN_WITHDRAWAL) {
      newErrors.amount = `最低提现金额为 ¥${MIN_WITHDRAWAL}`;
    } else if (numAmount > availableBalance) {
      newErrors.amount = '提现金额不能超过可提现余额';
    }
    
    if (!accountInfo.trim()) {
      newErrors.accountInfo = '请输入收款账户信息';
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
        withdrawalMethod: method,
        accountInfo: accountInfo.trim(),
      });
      
      toast.success('提现申请已提交，请等待审核');
      setAmount('');
      setAccountInfo('');
      onSuccess();
    } catch (err) {
      toast.error(err instanceof Error ? err.message : '提现申请失败');
    }
  };

  // 快捷金额选项
  const quickAmounts = [100, 200, 500, 1000].filter(a => a <= availableBalance);

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
              value={amount}
              onChange={(e) => setAmount(e.target.value)}
              placeholder={`最低 ¥${MIN_WITHDRAWAL}`}
              className={`w-full pl-8 pr-4 py-3 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 ${
                errors.amount ? 'border-red-300' : 'border-gray-300'
              }`}
            />
          </div>
          {errors.amount && (
            <p className="mt-1 text-sm text-red-600">{errors.amount}</p>
          )}
          
          {/* 快捷金额 */}
          <div className="flex flex-wrap gap-2 mt-3">
            {quickAmounts.map((quickAmount) => (
              <button
                key={quickAmount}
                type="button"
                onClick={() => setAmount(String(quickAmount))}
                className="px-3 py-1.5 text-sm bg-gray-100 hover:bg-gray-200 rounded-lg transition-colors"
              >
                ¥{quickAmount}
              </button>
            ))}
            <button
              type="button"
              onClick={() => setAmount(String(Math.floor(availableBalance)))}
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
            {(['alipay', 'wechat', 'bank'] as WithdrawalMethod[]).map((m) => (
              <button
                key={m}
                type="button"
                onClick={() => setMethod(m)}
                className={`p-4 border rounded-xl text-center transition-all ${
                  method === m
                    ? 'border-blue-500 bg-blue-50 text-blue-700'
                    : 'border-gray-200 hover:border-gray-300'
                }`}
              >
                <div className="text-2xl mb-1">{getMethodIcon(m)}</div>
                <div className="text-sm font-medium">{getMethodLabel(m)}</div>
              </button>
            ))}
          </div>
        </div>

        {/* 收款账户 */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            {method === 'bank' ? '银行卡号' : '收款账号'} <span className="text-red-500">*</span>
          </label>
          <input
            type="text"
            value={accountInfo}
            onChange={(e) => setAccountInfo(e.target.value)}
            placeholder={
              method === 'alipay' ? '请输入支付宝账号' :
              method === 'wechat' ? '请输入微信账号' :
              '请输入银行卡号'
            }
            className={`w-full px-4 py-3 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 ${
              errors.accountInfo ? 'border-red-300' : 'border-gray-300'
            }`}
          />
          {errors.accountInfo && (
            <p className="mt-1 text-sm text-red-600">{errors.accountInfo}</p>
          )}
          <p className="mt-1 text-sm text-gray-500">
            {method === 'bank' ? '请确保银行卡号与实名认证信息一致' : '请确保账号信息准确无误'}
          </p>
        </div>

        {/* 提交按钮 */}
        <button
          type="submit"
          disabled={requestWithdrawal.isPending || availableBalance < MIN_WITHDRAWAL}
          className={`w-full py-3 rounded-lg font-medium transition-colors ${
            requestWithdrawal.isPending || availableBalance < MIN_WITHDRAWAL
              ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
              : 'bg-blue-600 text-white hover:bg-blue-700'
          }`}
        >
          {requestWithdrawal.isPending ? '提交中...' : '提交申请'}
        </button>
      </form>
    </div>
  );
}

/**
 * 提现记录列表
 */
function WithdrawalHistory(): JSX.Element {
  const { data: withdrawals, isLoading, refetch } = useWithdrawals();

  if (isLoading) {
    return (
      <div className="bg-white rounded-xl shadow-sm p-6">
        <div className="animate-pulse space-y-4">
          <div className="h-6 bg-gray-200 rounded w-1/4" />
          {Array.from({ length: 5 }).map((_, i) => (
            <div key={i} className="h-16 bg-gray-200 rounded" />
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-xl shadow-sm p-6">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-lg font-semibold text-gray-900">提现记录</h2>
        <button
          onClick={() => { void refetch(); }}
          className="text-sm text-blue-600 hover:text-blue-700"
        >
          刷新
        </button>
      </div>

      {withdrawals && withdrawals.length > 0 ? (
        <div className="space-y-3">
          {withdrawals.map((record) => {
            const statusInfo = getStatusInfo(record.status);
            return (
              <div
                key={record.id}
                className="flex items-center justify-between p-4 border border-gray-100 rounded-xl hover:bg-gray-50 transition-colors"
              >
                <div className="flex items-center gap-4">
                  <div className="text-2xl">{getMethodIcon(record.withdrawalMethod)}</div>
                  <div>
                    <p className="font-medium text-gray-900">
                      提现到{getMethodLabel(record.withdrawalMethod)}
                    </p>
                    <p className="text-sm text-gray-500">
                      {new Date(record.createdAt).toLocaleString('zh-CN')}
                    </p>
                    {record.remark && (
                      <p className="text-sm text-gray-400 mt-1">{record.remark}</p>
                    )}
                  </div>
                </div>
                <div className="text-right">
                  <p className="font-semibold text-gray-900">-¥{record.amount.toFixed(2)}</p>
                  <span className={`inline-block mt-1 px-2 py-1 text-xs rounded-full ${statusInfo.color}`}>
                    {statusInfo.label}
                  </span>
                </div>
              </div>
            );
          })}
        </div>
      ) : (
        <div className="text-center py-12 text-gray-500">
          <div className="text-4xl mb-3">📋</div>
          <p>暂无提现记录</p>
        </div>
      )}
    </div>
  );
}

/**
 * 提现规则说明
 */
function WithdrawalRules(): JSX.Element {
  const rules = [
    { icon: '💰', title: '最低提现金额', desc: '单笔最低提现金额为 ¥100' },
    { icon: '⏰', title: '处理时间', desc: '提现申请将在1-3个工作日内处理完成' },
    { icon: '🔒', title: '账户安全', desc: '请确保收款账户信息准确无误' },
    { icon: '📋', title: '审核机制', desc: '大额提现可能需要额外审核' },
    { icon: '💸', title: '手续费', desc: '目前提现免手续费' },
    { icon: '📞', title: '客服支持', desc: '如有问题请联系客服处理' },
  ];

  return (
    <div className="bg-white rounded-xl shadow-sm p-6">
      <h2 className="text-lg font-semibold text-gray-900 mb-6">提现规则</h2>
      <div className="space-y-4">
        {rules.map((rule, index) => (
          <div key={index} className="flex items-start gap-3">
            <span className="text-xl">{rule.icon}</span>
            <div>
              <h3 className="font-medium text-gray-900">{rule.title}</h3>
              <p className="text-sm text-gray-500">{rule.desc}</p>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

/**
 * 提现管理页面
 */
export function WithdrawalPage(): JSX.Element {
  const { data: stats, isLoading: statsLoading } = usePromotionStats();
  const { refetch: refetchWithdrawals } = useWithdrawals();

  // 计算可提现余额
  const availableBalance = useMemo(() => {
    if (!stats) return 0;
    return stats.totalCommission - stats.pendingCommission - stats.paidCommission;
  }, [stats]);

  if (statsLoading) {
    return (
      <div className="min-h-screen bg-gray-50 py-8">
        <div className="max-w-6xl mx-auto px-4">
          <div className="animate-pulse space-y-6">
            <div className="h-8 bg-gray-200 rounded w-1/4" />
            <div className="h-32 bg-gray-200 rounded-xl" />
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              <div className="lg:col-span-2 h-96 bg-gray-200 rounded-xl" />
              <div className="h-96 bg-gray-200 rounded-xl" />
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-6xl mx-auto px-4">
        {/* 页面标题 */}
        <div className="mb-6">
          <h1 className="text-2xl font-bold text-gray-900">提现管理</h1>
          <p className="text-gray-500 mt-1">查看佣金余额并申请提现</p>
        </div>

        {/* 余额卡片 */}
        {stats && (
          <div className="mb-8">
            <BalanceCard
              available={availableBalance}
              pending={stats.pendingCommission}
              paid={stats.paidCommission}
              total={stats.totalCommission}
            />
          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* 左侧：提现表单和记录 */}
          <div className="lg:col-span-2 space-y-6">
            <WithdrawalForm
              availableBalance={availableBalance}
              onSuccess={() => { void refetchWithdrawals(); }}
            />
            <WithdrawalHistory />
          </div>

          {/* 右侧：规则说明 */}
          <div className="space-y-6">
            <WithdrawalRules />
            
            {/* 推广链接入口 */}
            <div className="bg-gradient-to-br from-purple-500 to-pink-500 rounded-xl p-6 text-white">
              <h3 className="text-lg font-semibold mb-2">继续推广赚佣金</h3>
              <p className="text-white/80 text-sm mb-4">
                分享推广链接，邀请更多用户，赚取更多佣金
              </p>
              <Link
                to="/promotion"
                className="inline-block px-4 py-2 bg-white text-purple-600 rounded-lg font-medium hover:bg-purple-50 transition-colors"
              >
                去推广 →
              </Link>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}