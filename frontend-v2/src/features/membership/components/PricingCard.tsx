/**
 * PricingCard 价格卡片组件
 * 展示单个会员等级的价格和权益
 * 
 * 会员等级体系：
 * - free: 免费用户
 * - monthly: 月度会员 ¥29/月
 * - annual: 年度会员 ¥299/年 (享8.6折)
 * - lifetime: 终身会员 ¥999 (一次购买终身权益)
 */

import type { LucideIcon } from 'lucide-react';
import { Check, Star, Crown, Infinity as InfinityIcon, Sparkles } from 'lucide-react';

import type { MembershipTier, MembershipPricing } from '../types';

interface PricingCardProps {
  tier: MembershipTier;
  pricing: MembershipPricing;
  isCurrent?: boolean;
  isSelected?: boolean;
  isPopular?: boolean;
  onSelect?: (tier: MembershipTier) => void;
  billingCycle: 'monthly' | 'annual' | 'lifetime';
  features?: string[];
}

const tierConfig: Record<MembershipTier, {
  label: string;
  description: string;
  color: string;
  bgColor: string;
  borderColor: string;
  icon: LucideIcon;
  gradient: string;
  features: string[];
}> = {
  free: {
    label: '免费用户',
    description: '体验基础功能',
    color: 'text-slate-600',
    bgColor: 'bg-slate-50',
    borderColor: 'border-slate-200',
    icon: Star,
    gradient: 'from-slate-100 to-slate-200',
    features: [
      '每日 5 次 AI 对话',
      '基础法律咨询',
      '查看法律知识库',
      '社区提问',
    ],
  },
  monthly: {
    label: '月度会员',
    description: '灵活按月订阅',
    color: 'text-blue-600',
    bgColor: 'bg-blue-50',
    borderColor: 'border-blue-300',
    icon: Crown,
    gradient: 'from-blue-400 to-blue-600',
    features: [
      '每日 100 次 AI 对话',
      '无限法律咨询',
      '合同智能审查',
      '优先客服支持',
      '专属法律文书模板',
    ],
  },
  annual: {
    label: '年度会员',
    description: '最受欢迎的选择',
    color: 'text-purple-600',
    bgColor: 'bg-purple-50',
    borderColor: 'border-purple-400',
    icon: Sparkles,
    gradient: 'from-purple-400 to-purple-600',
    features: [
      '无限 AI 对话',
      '无限法律咨询',
      '无限合同审查',
      '专属律师通道',
      '视频咨询 8 折优惠',
      '积分双倍返还',
    ],
  },
  lifetime: {
    label: '终身会员',
    description: '一次购买，终身权益',
    color: 'text-amber-600',
    bgColor: 'bg-amber-50',
    borderColor: 'border-amber-400',
    icon: InfinityIcon,
    gradient: 'from-amber-400 to-orange-500',
    features: [
      '所有年度会员权益',
      '永久免费更新',
      '1 对 1 专属顾问',
      '视频咨询免费额度',
      'VIP 专属活动',
      '优先体验新功能',
    ],
  },
};

export function PricingCard({
  tier,
  pricing,
  isCurrent = false,
  isSelected = false,
  isPopular = false,
  onSelect,
  billingCycle,
  features,
}: PricingCardProps): JSX.Element {
  const config = tierConfig[tier];
  const Icon = config.icon;

  // 根据计费周期获取价格
  const getPrice = () => {
    switch (billingCycle) {
      case 'monthly':
        return pricing.monthlyPrice;
      case 'annual':
        return pricing.annualPrice / 12; // 显示月均价
      case 'lifetime':
        return pricing.lifetimePrice;
      default:
        return pricing.monthlyPrice;
    }
  };

  const price = getPrice();
  const displayFeatures = features || config.features;

  // 计算节省金额
  const getSavings = () => {
    if (billingCycle === 'annual') {
      return pricing.savingsAnnual;
    }
    if (billingCycle === 'lifetime' && pricing.monthlyPrice > 0) {
      // 终身会员相比月度会员 3 年的费用
      return pricing.monthlyPrice * 36 - pricing.lifetimePrice;
    }
    return 0;
  };

  const savings = getSavings();

  return (
    <div
      onClick={() => onSelect?.(tier)}
      className={`
        relative overflow-hidden rounded-2xl transition-all duration-300 cursor-pointer
        ${isSelected 
          ? 'ring-2 ring-offset-2 ring-purple-500 shadow-xl scale-[1.02]' 
          : 'shadow-md hover:shadow-lg hover:scale-[1.01]'
        }
        ${isCurrent ? 'opacity-75' : ''}
      `}
    >
      {/* 推荐标签 */}
      {isPopular && (
        <div className="absolute -right-12 top-6 bg-gradient-to-r from-purple-500 to-pink-500 text-white px-12 py-1 text-xs font-bold transform rotate-45">
          最受欢迎
        </div>
      )}

      {/* 当前会员标签 */}
      {isCurrent && (
        <div className="absolute top-4 left-4 z-10">
          <span className="px-3 py-1 text-xs font-medium bg-green-100 text-green-700 rounded-full">
            当前等级
          </span>
        </div>
      )}

      {/* 卡片内容 */}
      <div className={`bg-white border-2 ${isSelected ? config.borderColor : 'border-slate-200'} rounded-2xl`}>
        {/* 头部渐变背景 */}
        <div className={`bg-gradient-to-r ${config.gradient} p-6 ${isCurrent ? 'pt-12' : ''}`}>
          <div className="flex items-center gap-3">
            <div className="p-3 bg-white/20 backdrop-blur-sm rounded-xl">
              <Icon className="w-8 h-8 text-white" />
            </div>
            <div>
              <h3 className="text-xl font-bold text-white">{config.label}</h3>
              <p className="text-sm text-white/80">{config.description}</p>
            </div>
          </div>
        </div>

        {/* 价格区域 */}
        <div className="p-6 border-b border-slate-100">
          <div className="flex items-baseline gap-1">
            <span className="text-4xl font-bold text-slate-900">
              ¥{price.toFixed(0)}
            </span>
            {billingCycle !== 'lifetime' && (
              <span className="text-slate-500">
                /{billingCycle === 'annual' ? '月' : '月'}
              </span>
            )}
          </div>
          
          {billingCycle === 'annual' && (
            <p className="mt-1 text-sm text-slate-500">
              年付 ¥{pricing.annualPrice}，节省 ¥{savings}
            </p>
          )}
          
          {billingCycle === 'lifetime' && savings > 0 && (
            <p className="mt-1 text-sm text-amber-600 font-medium">
              相比月付 3 年节省 ¥{savings.toFixed(0)}
            </p>
          )}
        </div>

        {/* 权益列表 */}
        <div className="p-6">
          <ul className="space-y-3">
            {displayFeatures.map((feature, index) => (
              <li key={index} className="flex items-start gap-3">
                <Check className="w-5 h-5 text-green-500 flex-shrink-0 mt-0.5" />
                <span className="text-sm text-slate-600">{feature}</span>
              </li>
            ))}
          </ul>
        </div>

        {/* 操作按钮 */}
        <div className="p-6 pt-0">
          {isCurrent ? (
            <button
              disabled
              className="w-full py-3 px-4 bg-slate-100 text-slate-500 font-semibold rounded-xl cursor-not-allowed"
            >
              当前等级
            </button>
          ) : (
            <button
              onClick={(e) => {
                e.stopPropagation();
                onSelect?.(tier);
              }}
              className={`
                w-full py-3 px-4 font-semibold rounded-xl transition-all
                ${isSelected
                  ? `bg-gradient-to-r ${config.gradient} text-white`
                  : `bg-slate-100 ${config.color} hover:bg-slate-200`
                }
              `}
            >
              {isSelected ? '已选择' : '选择此方案'}
            </button>
          )}
        </div>
      </div>
    </div>
  );
}

export default PricingCard;