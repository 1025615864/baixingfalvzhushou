/**
 * MembershipComparison 会员权益对比组件
 * 展示各等级会员权益对比表格
 * 
 * 会员等级体系：
 * - free: 免费用户
 * - monthly: 月度会员 ¥29/月
 * - annual: 年度会员 ¥299/年 (享8.6折)
 * - lifetime: 终身会员 ¥999 (一次购买终身权益)
 */

import type { LucideIcon } from 'lucide-react';
import { Check, X, HelpCircle, MessageSquare, FileText, Video, Headphones, Zap, Star, Crown, Sparkles, Infinity as InfinityIcon } from 'lucide-react';

import type { MembershipTier, MembershipBenefits } from '../types';

interface MembershipComparisonProps {
  benefits: MembershipBenefits[];
  currentTier?: MembershipTier;
  onSelectTier?: (tier: MembershipTier) => void;
}

interface FeatureRow {
  key: string;
  label: string;
  icon: LucideIcon;
  description?: string;
  getValue: (benefits: MembershipBenefits) => string | number | boolean;
}

// 权益对比配置
const featureRows: FeatureRow[] = [
  {
    key: 'dailyAiChatLimit',
    label: '每日 AI 对话',
    icon: MessageSquare,
    description: '每天可使用的 AI 法律咨询次数',
    getValue: (b) => (b.unlimitedAiChat ? '无限' : b.dailyAiChatLimit),
  },
  {
    key: 'dailyDocumentLimit',
    label: '每日文档生成',
    icon: FileText,
    description: '每天可生成的法律文档数量',
    getValue: (b) => (b.dailyDocumentLimit >= 1000000000 ? '无限' : b.dailyDocumentLimit || 0),
  },
  {
    key: 'contractReviewPerMonth',
    label: '合同审查/月',
    icon: FileText,
    description: '每月可进行的合同智能审查次数',
    getValue: (b) => (b.unlimitedContractReview ? '无限' : b.contractReviewPerMonth || 0),
  },
  {
    key: 'videoConsultationDiscount',
    label: '视频咨询优惠',
    icon: Video,
    description: '视频律师咨询的折扣力度',
    getValue: (b) => (b.videoConsultationDiscount > 0 ? `${b.videoConsultationDiscount * 10}折` : '无'),
  },
  {
    key: 'freeVideoConsultationsPerMonth',
    label: '免费视频咨询/月',
    icon: Video,
    description: '每月免费视频咨询次数',
    getValue: (b) => b.freeVideoConsultationsPerMonth || 0,
  },
  {
    key: 'lawyerConsultationDiscount',
    label: '律师咨询优惠',
    icon: Zap,
    description: '一对一律师咨询的折扣力度',
    getValue: (b) => (b.lawyerConsultationDiscount > 0 ? `${b.lawyerConsultationDiscount * 10}折` : '无'),
  },
  {
    key: 'prioritySupport',
    label: '优先客服支持',
    icon: Headphones,
    description: '享受专属客服优先响应',
    getValue: (b) => b.prioritySupport,
  },
  {
    key: 'pointsMultiplier',
    label: '积分倍率',
    icon: Star,
    description: '消费获得积分的倍率',
    getValue: (b) => `${b.pointsMultiplier}x`,
  },
];

// 等级配置
const tierConfig: Record<MembershipTier, {
  label: string;
  color: string;
  bgColor: string;
  icon: LucideIcon;
}> = {
  free: {
    label: '免费用户',
    color: 'text-slate-600',
    bgColor: 'bg-slate-100',
    icon: Star,
  },
  monthly: {
    label: '月度会员',
    color: 'text-blue-600',
    bgColor: 'bg-blue-100',
    icon: Crown,
  },
  annual: {
    label: '年度会员',
    color: 'text-purple-600',
    bgColor: 'bg-purple-100',
    icon: Sparkles,
  },
  lifetime: {
    label: '终身会员',
    color: 'text-amber-600',
    bgColor: 'bg-amber-100',
    icon: InfinityIcon,
  },
};

/**
 * 渲染权益值
 */
function renderValue(value: string | number | boolean, tier: MembershipTier): JSX.Element {
  const config = tierConfig[tier];
  
  if (typeof value === 'boolean') {
    return value ? (
      <Check className={`w-5 h-5 mx-auto text-green-500`} />
    ) : (
      <X className="w-5 h-5 mx-auto text-slate-300" />
    );
  }
  
  if (value === 0 || value === '0' || value === '无') {
    return <X className="w-5 h-5 mx-auto text-slate-300" />;
  }
  
  return (
    <span className={`font-medium ${config.color}`}>
      {value}
    </span>
  );
}

export function MembershipComparison({
  benefits,
  currentTier,
  onSelectTier,
}: MembershipComparisonProps): JSX.Element {
  // 按 tier 排序
  const tierOrder: MembershipTier[] = ['free', 'monthly', 'annual', 'lifetime'];
  const sortedBenefits = tierOrder
    .map((tier) => benefits.find((b) => b.tier === tier))
    .filter((b): b is MembershipBenefits => b !== undefined);

  if (sortedBenefits.length === 0) {
    return (
      <div className="p-6 bg-slate-50 rounded-xl">
        <p className="text-center text-slate-500">暂无权益对比信息</p>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-2xl shadow-lg overflow-hidden">
      {/* 标题 */}
      <div className="px-6 py-5 bg-gradient-to-r from-purple-600 to-pink-500">
        <h2 className="text-xl font-bold text-white flex items-center gap-2">
          <Crown className="w-6 h-6" />
          会员权益对比
        </h2>
        <p className="mt-1 text-purple-100 text-sm">
          选择最适合您的会员等级
        </p>
      </div>

      {/* 对比表格 */}
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead>
            <tr className="bg-slate-50">
              <th className="px-4 py-4 text-left text-sm font-medium text-slate-600 sticky left-0 bg-slate-50 z-10">
                权益项目
              </th>
              {sortedBenefits.map((benefit) => {
                const config = tierConfig[benefit.tier];
                const Icon = config.icon;
                const isCurrent = currentTier === benefit.tier;
                
                return (
                  <th key={benefit.tier} className="px-4 py-4 text-center min-w-[140px]">
                    <div className={`inline-flex flex-col items-center gap-2 ${isCurrent ? 'opacity-100' : ''}`}>
                      <div className={`p-2 rounded-lg ${config.bgColor}`}>
                        <Icon className={`w-6 h-6 ${config.color}`} />
                      </div>
                      <span className={`font-semibold ${config.color}`}>
                        {config.label}
                      </span>
                      {isCurrent && (
                        <span className="px-2 py-0.5 text-xs bg-green-100 text-green-700 rounded-full">
                          当前等级
                        </span>
                      )}
                    </div>
                  </th>
                );
              })}
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {featureRows.map((row, index) => {
              const Icon = row.icon;
              
              return (
                <tr 
                  key={row.key} 
                  className={index % 2 === 0 ? 'bg-white' : 'bg-slate-50/50'}
                >
                  <td className="px-4 py-4 sticky left-0 z-10 bg-inherit">
                    <div className="flex items-center gap-3">
                      <div className="p-2 bg-slate-100 rounded-lg">
                        <Icon className="w-4 h-4 text-slate-500" />
                      </div>
                      <div>
                        <span className="text-sm font-medium text-slate-700">
                          {row.label}
                        </span>
                        {row.description && (
                          <div className="flex items-center gap-1 text-xs text-slate-400">
                            <HelpCircle className="w-3 h-3" />
                            {row.description}
                          </div>
                        )}
                      </div>
                    </div>
                  </td>
                  {sortedBenefits.map((benefit) => (
                    <td key={benefit.tier} className="px-4 py-4 text-center">
                      {renderValue(row.getValue(benefit), benefit.tier)}
                    </td>
                  ))}
                </tr>
              );
            })}
          </tbody>
          {/* 底部操作行 */}
          <tfoot>
            <tr className="bg-slate-50 border-t-2 border-slate-200">
              <td className="px-4 py-4 sticky left-0 bg-slate-50 z-10">
                <span className="font-medium text-slate-700">操作</span>
              </td>
              {sortedBenefits.map((benefit) => {
                const config = tierConfig[benefit.tier];
                const isCurrent = currentTier === benefit.tier;
                const isFree = benefit.tier === 'free';
                
                return (
                  <td key={benefit.tier} className="px-4 py-4 text-center">
                    {isCurrent ? (
                      <span className="px-4 py-2 text-sm font-medium text-green-600 bg-green-50 rounded-lg">
                        当前等级
                      </span>
                    ) : isFree ? (
                      <span className="px-4 py-2 text-sm text-slate-400">
                        基础版
                      </span>
                    ) : (
                      <button
                        onClick={() => onSelectTier?.(benefit.tier)}
                        className={`
                          px-4 py-2 text-sm font-medium rounded-lg transition-all
                          ${config.bgColor} ${config.color} hover:opacity-80
                        `}
                      >
                        立即开通
                      </button>
                    )}
                  </td>
                );
              })}
            </tr>
          </tfoot>
        </table>
      </div>

      {/* 说明 */}
      <div className="px-6 py-4 bg-slate-50 border-t border-slate-200">
        <p className="text-xs text-slate-500">
          * 以上权益仅限会员有效期内使用，会员到期后将恢复为免费用户权益
        </p>
      </div>
    </div>
  );
}

export default MembershipComparison;