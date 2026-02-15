/**
 * UpgradePrompt 会员升级引导组件
 */

import { useState } from 'react';
import { Sparkles, X, ChevronRight, Loader2 } from 'lucide-react';

import type { MembershipTier } from '../types';

interface UpgradePromptProps {
  currentTier: MembershipTier;
  recommendedTier?: MembershipTier;
  recommendedReason?: string;
  onUpgrade: (tier: MembershipTier, duration: 'month' | 'quarter' | 'year') => void;
  onClose?: () => void;
  loading?: boolean;
}

const tierLabels: Record<MembershipTier, string> = {
  free: '免费用户',
  basic: '基础会员',
  standard: '标准会员',
  premium: '高级会员',
  enterprise: '企业会员',
};

const tierPrices: Record<MembershipTier, { month: number; quarter: number; year: number }> = {
  free: { month: 0, quarter: 0, year: 0 },
  basic: { month: 9.9, quarter: 26.9, year: 99 },
  standard: { month: 29.9, quarter: 79.9, year: 299 },
  premium: { month: 59.9, quarter: 159.9, year: 599 },
  enterprise: { month: 199, quarter: 549, year: 1999 },
};

export function UpgradePrompt({
  currentTier,
  recommendedTier = 'standard',
  recommendedReason = '解锁更多AI对话和高级功能',
  onUpgrade,
  onClose,
  loading = false,
}: UpgradePromptProps): JSX.Element {
  const [selectedTier, setSelectedTier] = useState<MembershipTier>(recommendedTier);
  const [selectedDuration, setSelectedDuration] = useState<'month' | 'quarter' | 'year'>('month');

  const handleUpgrade = () => {
    onUpgrade(selectedTier, selectedDuration);
  };

  const tiers: MembershipTier[] = ['basic', 'standard', 'premium', 'enterprise'];

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm">
      <div className="relative w-full max-w-lg mx-4 bg-white rounded-2xl shadow-2xl overflow-hidden">
        {/* 关闭按钮 */}
        {onClose && (
          <button
            onClick={onClose}
            className="absolute top-4 right-4 p-2 text-slate-400 hover:text-slate-600 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        )}

        {/* 头部 */}
        <div className="px-6 pt-8 pb-6 bg-gradient-to-r from-purple-500 to-pink-500 text-white">
          <div className="flex items-center gap-3 mb-3">
            <div className="p-2 bg-white/20 rounded-lg">
              <Sparkles className="w-6 h-6" />
            </div>
            <h2 className="text-xl font-bold">升级会员</h2>
          </div>
          <p className="text-purple-100">{recommendedReason}</p>
        </div>

        {/* 内容 */}
        <div className="p-6">
          {/* 当前等级 */}
          <div className="mb-6 p-4 bg-slate-50 rounded-xl">
            <p className="text-sm text-slate-500 mb-1">当前等级</p>
            <p className="text-lg font-semibold text-slate-900">{tierLabels[currentTier]}</p>
          </div>

          {/* 等级选择 */}
          <div className="mb-6">
            <p className="text-sm font-medium text-slate-700 mb-3">选择会员等级</p>
            <div className="grid grid-cols-2 gap-3">
              {tiers.map((tier) => (
                <button
                  key={tier}
                  onClick={() => setSelectedTier(tier)}
                  className={`
                    p-3 rounded-xl border-2 text-left transition-all
                    ${selectedTier === tier
                      ? 'border-purple-500 bg-purple-50'
                      : 'border-slate-200 hover:border-slate-300'
                    }
                  `}
                >
                  <p className={`font-semibold ${selectedTier === tier ? 'text-purple-700' : 'text-slate-900'}`}>
                    {tierLabels[tier]}
                  </p>
                  <p className="text-sm text-slate-500">
                    ¥{tierPrices[tier].month}/月
                  </p>
                </button>
              ))}
            </div>
          </div>

          {/* 时长选择 */}
          <div className="mb-6">
            <p className="text-sm font-medium text-slate-700 mb-3">选择时长</p>
            <div className="flex gap-3">
              {(['month', 'quarter', 'year'] as const).map((duration) => {
                const price = tierPrices[selectedTier][duration];
                const discount = duration === 'quarter' ? '省10%' : duration === 'year' ? '省30%' : null;

                return (
                  <button
                    key={duration}
                    onClick={() => setSelectedDuration(duration)}
                    className={`
                      flex-1 p-3 rounded-xl border-2 text-center transition-all relative
                      ${selectedDuration === duration
                        ? 'border-purple-500 bg-purple-50'
                        : 'border-slate-200 hover:border-slate-300'
                      }
                    `}
                  >
                    {discount && (
                      <span className="absolute -top-2 left-1/2 -translate-x-1/2 px-2 py-0.5 text-xs font-medium bg-red-500 text-white rounded-full">
                        {discount}
                      </span>
                    )}
                    <p className={`font-semibold ${selectedDuration === duration ? 'text-purple-700' : 'text-slate-900'}`}>
                      {duration === 'month' ? '月付' : duration === 'quarter' ? '季付' : '年付'}
                    </p>
                    <p className="text-sm text-slate-500">¥{price}</p>
                  </button>
                );
              })}
            </div>
          </div>

          {/* 升级按钮 */}
          <button
            onClick={handleUpgrade}
            disabled={loading}
            className="w-full py-3 px-4 bg-purple-600 hover:bg-purple-700 disabled:bg-purple-400 text-white font-semibold rounded-xl transition-colors flex items-center justify-center gap-2"
          >
            {loading ? (
              <>
                <Loader2 className="w-5 h-5 animate-spin" />
                处理中...
              </>
            ) : (
              <>
                立即升级
                <ChevronRight className="w-5 h-5" />
              </>
            )}
          </button>

          <p className="mt-4 text-center text-xs text-slate-400">
            升级即表示同意服务条款和隐私政策
          </p>
        </div>
      </div>
    </div>
  );
}