/**
 * MembershipCard 会员卡组件
 
 会员等级体系：
 - free: 免费用户
 - monthly: 月度会员 ¥29/月
 - annual: 年度会员 ¥299/年 (享8.6折)
 - lifetime: 终身会员 ¥999 (一次购买终身权益)
 */

import type { LucideIcon } from 'lucide-react';
import { Sparkles, Crown, Star, Infinity as InfinityIcon } from 'lucide-react';

import type { MembershipTier } from '../types';

interface MembershipCardProps {
  tier: MembershipTier;
  memberName: string;
  expiryDate?: string;
  isCurrent?: boolean;
  onSelect?: (tier: MembershipTier) => void;
}

const tierConfig: Record<MembershipTier, {
  label: string;
  color: string;
  bgColor: string;
  icon: LucideIcon;
  gradient: string;
  popular?: boolean;
}> = {
  free: {
    label: '免费用户',
    color: 'text-slate-600',
    bgColor: 'bg-slate-100',
    icon: Star,
    gradient: 'from-slate-200 to-slate-300',
  },
  monthly: {
    label: '月度会员',
    color: 'text-blue-600',
    bgColor: 'bg-blue-50',
    icon: Crown,
    gradient: 'from-blue-400 to-blue-500',
  },
  annual: {
    label: '年度会员',
    color: 'text-purple-600',
    bgColor: 'bg-purple-50',
    icon: Sparkles,
    gradient: 'from-purple-400 to-purple-500',
    popular: true,
  },
  lifetime: {
    label: '终身会员',
    color: 'text-amber-600',
    bgColor: 'bg-amber-50',
    icon: InfinityIcon,
    gradient: 'from-amber-400 to-amber-500',
  },
};

export function MembershipCard({
  tier,
  memberName,
  expiryDate,
  isCurrent = false,
  onSelect,
}: MembershipCardProps): JSX.Element {
  const config = tierConfig[tier];
  const Icon = config.icon;

  return (
    <div
      onClick={() => onSelect?.(tier)}
      className={`
        relative overflow-hidden rounded-2xl p-6 cursor-pointer
        transition-all duration-300 ease-out
        ${isCurrent ? 'ring-2 ring-offset-2 ring-primary shadow-xl scale-105' : 'shadow-md hover:shadow-lg hover:scale-102'}
      `}
    >
      {/* 背景渐变 */}
      <div className={`absolute inset-0 bg-gradient-to-br ${config.gradient} opacity-90`} />
      
      {/* 装饰性背景图案 */}
      <div className="absolute inset-0 opacity-10">
        <div className="absolute -right-8 -top-8 w-32 h-32 rounded-full bg-white" />
        <div className="absolute -left-8 -bottom-8 w-24 h-24 rounded-full bg-white" />
      </div>

      {/* 内容 */}
      <div className="relative z-10">
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-3">
            <div className={`p-3 rounded-xl ${config.bgColor}`}>
              <Icon className={`w-6 h-6 ${config.color}`} />
            </div>
            <div>
              <h3 className={`text-lg font-bold ${config.color}`}>{config.label}</h3>
              <p className="text-sm text-slate-600">{memberName || '未登录用户'}</p>
            </div>
          </div>
          {isCurrent && (
            <span className="px-3 py-1 text-xs font-medium bg-white/80 backdrop-blur-sm rounded-full text-slate-700">
              当前等级
            </span>
          )}
        </div>

        {expiryDate && (
          <div className="mt-4 pt-4 border-t border-white/30">
            <p className="text-sm text-slate-700">
              有效期至: <span className="font-medium">{new Date(expiryDate).toLocaleDateString('zh-CN')}</span>
            </p>
          </div>
        )}

        {!expiryDate && tier !== 'free' && (
          <div className="mt-4 pt-4 border-t border-white/30">
            <p className="text-sm text-slate-600 italic">
              点击选择此会员等级
            </p>
          </div>
        )}
      </div>
    </div>
  );
}