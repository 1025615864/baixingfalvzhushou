/**
 * MembershipBenefits 会员权益展示组件
 * 展示当前会员等级的权益详情
 * 
 * 会员等级体系：
 * - free: 免费用户
 * - monthly: 月度会员 ¥29/月
 * - annual: 年度会员 ¥299/年 (享8.6折)
 * - lifetime: 终身会员 ¥999 (一次购买终身权益)
 */

import type { LucideIcon } from 'lucide-react';
import { Check, X, MessageSquare, FileText, Headphones, Wand2, Code, Palette, Video, Star, Zap } from 'lucide-react';

import type { MembershipBenefits as BenefitsType, MembershipTier } from '../types';

interface MembershipBenefitsProps {
  benefits: BenefitsType | null;
  showComparison?: boolean;
}

interface BenefitItemProps {
  icon: LucideIcon;
  label: string;
  value: string | number | boolean;
  enabled: boolean;
}

// 等级配置
const tierConfig: Record<MembershipTier, {
  label: string;
  color: string;
  bgColor: string;
}> = {
  free: {
    label: '免费用户',
    color: 'text-slate-600',
    bgColor: 'bg-slate-100',
  },
  monthly: {
    label: '月度会员',
    color: 'text-blue-600',
    bgColor: 'bg-blue-100',
  },
  annual: {
    label: '年度会员',
    color: 'text-purple-600',
    bgColor: 'bg-purple-100',
  },
  lifetime: {
    label: '终身会员',
    color: 'text-amber-600',
    bgColor: 'bg-amber-100',
  },
};

function BenefitItem({ icon: Icon, label, value, enabled }: BenefitItemProps): JSX.Element {
  const StatusIcon = enabled ? Check : X;

  return (
    <div className="flex items-center justify-between py-2.5 border-b border-slate-100 last:border-0">
      <div className="flex items-center gap-3">
        <div className={`p-2 rounded-lg ${enabled ? 'bg-green-100' : 'bg-slate-100'}`}>
          <Icon className={`w-4 h-4 ${enabled ? 'text-green-600' : 'text-slate-400'}`} />
        </div>
        <span className="text-sm text-slate-700">{label}</span>
      </div>
      <div className="flex items-center gap-2">
        <span className={`text-sm font-medium ${enabled ? 'text-slate-900' : 'text-slate-400'}`}>
          {typeof value === 'boolean' ? '' : value}
        </span>
        <StatusIcon className={`w-4 h-4 ${enabled ? 'text-green-500' : 'text-slate-300'}`} />
      </div>
    </div>
  );
}

export function MembershipBenefits({
  benefits,
  showComparison = false,
}: MembershipBenefitsProps): JSX.Element {
  if (!benefits) {
    return (
      <div className="p-6 bg-slate-50 rounded-xl border border-slate-200">
        <div className="text-center">
          <div className="p-3 bg-slate-100 rounded-full w-12 h-12 mx-auto mb-3 flex items-center justify-center">
            <Star className="w-6 h-6 text-slate-400" />
          </div>
          <p className="text-slate-500">暂无权益信息</p>
          <p className="text-sm text-slate-400 mt-1">请登录后查看您的会员权益</p>
        </div>
      </div>
    );
  }

  const config = tierConfig[benefits.tier] || tierConfig.free;

  const benefitItems: Array<{
    key: string;
    icon: LucideIcon;
    label: string;
    value: string | number | boolean;
    enabled: boolean;
  }> = [
    {
      key: 'dailyAiChatLimit',
      icon: MessageSquare,
      label: '每日 AI 对话',
      value: benefits.unlimitedAiChat ? '无限' : `${benefits.dailyAiChatLimit}次`,
      enabled: benefits.dailyAiChatLimit > 0 || benefits.unlimitedAiChat,
    },
    {
      key: 'dailyDocumentLimit',
      icon: FileText,
      label: '每日文档生成',
      value: benefits.dailyDocumentLimit >= 1000000000 ? '无限' : `${benefits.dailyDocumentLimit || 0}次`,
      enabled: (benefits.dailyDocumentLimit || 0) > 0,
    },
    {
      key: 'contractReviewPerMonth',
      icon: FileText,
      label: '合同审查/月',
      value: benefits.unlimitedContractReview ? '无限' : `${benefits.contractReviewPerMonth || 0}次`,
      enabled: (benefits.contractReviewPerMonth || 0) > 0 || benefits.unlimitedContractReview,
    },
    {
      key: 'videoConsultationDiscount',
      icon: Video,
      label: '视频咨询优惠',
      value: benefits.videoConsultationDiscount > 0 ? `${benefits.videoConsultationDiscount * 10}折` : '无',
      enabled: benefits.videoConsultationDiscount > 0,
    },
    {
      key: 'freeVideoConsultationsPerMonth',
      icon: Video,
      label: '免费视频咨询/月',
      value: `${benefits.freeVideoConsultationsPerMonth || 0}次`,
      enabled: (benefits.freeVideoConsultationsPerMonth || 0) > 0,
    },
    {
      key: 'lawyerConsultationDiscount',
      icon: Zap,
      label: '律师咨询优惠',
      value: benefits.lawyerConsultationDiscount > 0 ? `${benefits.lawyerConsultationDiscount * 10}折` : '无',
      enabled: benefits.lawyerConsultationDiscount > 0,
    },
    {
      key: 'prioritySupport',
      icon: Headphones,
      label: '优先客服支持',
      value: benefits.prioritySupport,
      enabled: benefits.prioritySupport,
    },
    {
      key: 'advancedFeatures',
      icon: Wand2,
      label: '高级功能',
      value: benefits.advancedFeatures,
      enabled: benefits.advancedFeatures,
    },
    {
      key: 'apiAccess',
      icon: Code,
      label: 'API 访问',
      value: benefits.apiAccess,
      enabled: benefits.apiAccess,
    },
    {
      key: 'customBranding',
      icon: Palette,
      label: '自定义品牌',
      value: benefits.customBranding,
      enabled: benefits.customBranding,
    },
    {
      key: 'pointsMultiplier',
      icon: Star,
      label: '积分倍率',
      value: `${benefits.pointsMultiplier}x`,
      enabled: benefits.pointsMultiplier > 1,
    },
  ];

  return (
    <div className="bg-white rounded-xl border border-slate-200 overflow-hidden shadow-sm">
      {/* 头部 */}
      <div className={`px-5 py-4 border-b border-slate-200 ${config.bgColor}`}>
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-semibold text-slate-900">{benefits.name}</h3>
          <span className={`px-3 py-1 text-xs font-medium rounded-full ${config.bgColor} ${config.color} uppercase`}>
            {config.label}
          </span>
        </div>
      </div>
      
      {/* 权益列表 */}
      <div className="p-5">
        <div className="space-y-0">
          {benefitItems.map((item) => (
            <BenefitItem
              key={item.key}
              icon={item.icon}
              label={item.label}
              value={item.value}
              enabled={item.enabled}
            />
          ))}
        </div>
      </div>

      {/* 底部说明 */}
      {showComparison && (
        <div className="px-5 py-4 bg-slate-50 border-t border-slate-200">
          <p className="text-xs text-slate-500">
            * 以上权益仅限当前会员等级有效期内使用，会员到期后将恢复为免费用户权益
          </p>
        </div>
      )}
    </div>
  );
}

export default MembershipBenefits;