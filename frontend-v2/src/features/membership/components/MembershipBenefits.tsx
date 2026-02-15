/**
 * MembershipBenefits 会员权益展示组件
 */

import type { LucideIcon } from 'lucide-react';
import { Check, X, MessageSquare, FileText, Headphones, Wand2, Code, Palette } from 'lucide-react';

import type { MembershipBenefits as BenefitsType } from '../types';

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

function BenefitItem({ icon: Icon, label, value, enabled }: BenefitItemProps): JSX.Element {
  const StatusIcon = enabled ? Check : X;

  return (
    <div className="flex items-center justify-between py-2">
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
      <div className="p-6 bg-slate-50 rounded-xl">
        <p className="text-center text-slate-500">暂无权益信息</p>
      </div>
    );
  }

  const benefitItems: Array<{
    key: keyof BenefitsType;
    icon: LucideIcon;
    label: string;
    value: string | number | boolean;
  }> = [
    {
      key: 'dailyAiChatLimit',
      icon: MessageSquare,
      label: '每日AI对话次数',
      value: benefits.dailyAiChatLimit >= 1000000000 ? '无限' : benefits.dailyAiChatLimit,
    },
    {
      key: 'dailyDocumentLimit',
      icon: FileText,
      label: '每日文档生成次数',
      value: benefits.dailyDocumentLimit >= 1000000000 ? '无限' : benefits.dailyDocumentLimit,
    },
    {
      key: 'prioritySupport',
      icon: Headphones,
      label: '优先客服支持',
      value: benefits.prioritySupport,
    },
    {
      key: 'advancedFeatures',
      icon: Wand2,
      label: '高级功能',
      value: benefits.advancedFeatures,
    },
    {
      key: 'apiAccess',
      icon: Code,
      label: 'API 访问',
      value: benefits.apiAccess,
    },
    {
      key: 'customBranding',
      icon: Palette,
      label: '自定义品牌',
      value: benefits.customBranding,
    },
  ];

  return (
    <div className="bg-white rounded-xl border border-slate-200 overflow-hidden">
      <div className="px-6 py-4 border-b border-slate-200 bg-slate-50">
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-semibold text-slate-900">{benefits.name}</h3>
          <span className="px-3 py-1 text-xs font-medium rounded-full bg-slate-200 text-slate-700 uppercase">
            {benefits.tier}
          </span>
        </div>
      </div>
      
      <div className="p-6">
        <div className="space-y-1 divide-y divide-slate-100">
          {benefitItems.map((item) => (
            <BenefitItem
              key={item.key}
              icon={item.icon}
              label={item.label}
              value={item.value}
              enabled={typeof item.value === 'boolean' ? item.value : Number(item.value) > 0}
            />
          ))}
        </div>
      </div>

      {showComparison && (
        <div className="px-6 py-4 bg-slate-50 border-t border-slate-200">
          <p className="text-xs text-slate-500">
            * 以上权益仅限当前会员等级有效期内使用
          </p>
        </div>
      )}
    </div>
  );
}