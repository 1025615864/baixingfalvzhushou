/**
 * EnterpriseInfo - 企业信息展示组件
 */

import { useState } from 'react';

import type { IndustryType, EnterpriseScale, SubscriptionPlan } from '../types';
import { useEnterpriseInfo, useUpdateEnterpriseInfo } from '../hooks/useEnterprise';

interface EnterpriseInfoProps {
  accountId: number;
}

const industryLabels: Record<IndustryType, string> = {
  general: '通用',
  technology: '科技',
  finance: '金融',
  manufacturing: '制造业',
  retail: '零售',
  healthcare: '医疗',
  education: '教育',
  realestate: '房地产',
  legal: '法律',
  other: '其他',
};

const scaleLabels: Record<EnterpriseScale, string> = {
  smb: '小微企业',
  mid: '中型企业',
  enterprise: '大型企业',
};

const planLabels: Record<SubscriptionPlan, string> = {
  basic: '基础版',
  standard: '标准版',
  premium: '高级版',
};

const planColors: Record<SubscriptionPlan, string> = {
  basic: 'bg-gray-100 text-gray-800',
  standard: 'bg-blue-100 text-blue-800',
  premium: 'bg-purple-100 text-purple-800',
};

/**
 * 企业信息展示组件
 */
export function EnterpriseInfo({ accountId }: EnterpriseInfoProps): JSX.Element {
  const [isEditing, setIsEditing] = useState<boolean>(false);
  const { data: enterprise, isLoading, error } = useEnterpriseInfo(accountId);
  const updateMutation = useUpdateEnterpriseInfo(accountId);

  const handleSave = (): void => {
    const form = document.getElementById('enterprise-form') as HTMLFormElement;
    const formData = new FormData(form);

    void updateMutation.mutateAsync({
      companyName: String(formData.get('companyName') || ''),
      industry: String(formData.get('industry') || 'general') as IndustryType,
      scale: String(formData.get('scale') || 'smb') as EnterpriseScale,
      subscriptionPlan: String(formData.get('subscriptionPlan') || 'basic') as SubscriptionPlan,
      contactPhone: String(formData.get('contactPhone') || ''),
      contactName: String(formData.get('contactName') || ''),
      address: String(formData.get('address') || ''),
      website: String(formData.get('website') || ''),
      description: String(formData.get('description') || ''),
    }).then(() => {
      setIsEditing(false);
    });
  };

  if (isLoading) {
    return (
      <div className="p-6 bg-white rounded-lg shadow-sm">
        <div className="animate-pulse space-y-4">
          <div className="h-8 bg-gray-200 rounded w-1/3" />
          <div className="grid grid-cols-2 gap-4">
            <div className="h-4 bg-gray-200 rounded" />
            <div className="h-4 bg-gray-200 rounded" />
            <div className="h-4 bg-gray-200 rounded" />
            <div className="h-4 bg-gray-200 rounded" />
          </div>
        </div>
      </div>
    );
  }

  if (error || !enterprise) {
    return (
      <div className="p-6 bg-white rounded-lg shadow-sm">
        <div className="text-red-500">加载企业信息失败</div>
      </div>
    );
  }

  return (
    <div className="p-6 bg-white rounded-lg shadow-sm">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-xl font-semibold text-gray-900">企业信息</h2>
          <p className="text-sm text-gray-500 mt-1">管理您的企业账号信息</p>
        </div>
        <button
          onClick={() => isEditing ? handleSave() : setIsEditing(true)}
          disabled={updateMutation.isPending}
          className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700 transition-colors disabled:opacity-50"
        >
          {updateMutation.isPending ? '保存中...' : isEditing ? '保存' : '编辑'}
        </button>
      </div>

      <form id="enterprise-form" className="space-y-6">
        {/* 基本信息 */}
        <div>
          <h3 className="text-sm font-medium text-gray-700 mb-3">基本信息</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-medium text-gray-500 mb-1">企业名称</label>
              {isEditing ? (
                <input
                  type="text"
                  name="companyName"
                  defaultValue={enterprise.companyName}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm"
                />
              ) : (
                <p className="text-gray-900 font-medium">{enterprise.companyName}</p>
              )}
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-500 mb-1">订阅计划</label>
              {isEditing ? (
                <select
                  name="subscriptionPlan"
                  defaultValue={enterprise.subscriptionPlan}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm"
                >
                  <option value="basic">基础版</option>
                  <option value="standard">标准版</option>
                  <option value="premium">高级版</option>
                </select>
              ) : (
                <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${planColors[enterprise.subscriptionPlan]}`}>
                  {planLabels[enterprise.subscriptionPlan]}
                </span>
              )}
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-500 mb-1">行业</label>
              {isEditing ? (
                <select
                  name="industry"
                  defaultValue={enterprise.industry}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm"
                >
                  {Object.entries(industryLabels).map(([key, label]) => (
                    <option key={key} value={key}>{label}</option>
                  ))}
                </select>
              ) : (
                <p className="text-gray-900">{industryLabels[enterprise.industry]}</p>
              )}
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-500 mb-1">企业规模</label>
              {isEditing ? (
                <select
                  name="scale"
                  defaultValue={enterprise.scale}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm"
                >
                  {Object.entries(scaleLabels).map(([key, label]) => (
                    <option key={key} value={key}>{label}</option>
                  ))}
                </select>
              ) : (
                <p className="text-gray-900">{scaleLabels[enterprise.scale]}</p>
              )}
            </div>
          </div>
        </div>

        {/* 联系信息 */}
        <div>
          <h3 className="text-sm font-medium text-gray-700 mb-3">联系信息</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-medium text-gray-500 mb-1">管理员邮箱</label>
              <p className="text-gray-900">{enterprise.adminEmail}</p>
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-500 mb-1">联系电话</label>
              {isEditing ? (
                <input
                  type="tel"
                  name="contactPhone"
                  defaultValue={enterprise.contactPhone || ''}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm"
                />
              ) : (
                <p className="text-gray-900">{enterprise.contactPhone || '未设置'}</p>
              )}
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-500 mb-1">联系人</label>
              {isEditing ? (
                <input
                  type="text"
                  name="contactName"
                  defaultValue={enterprise.contactName || ''}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm"
                />
              ) : (
                <p className="text-gray-900">{enterprise.contactName || '未设置'}</p>
              )}
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-500 mb-1">网址</label>
              {isEditing ? (
                <input
                  type="url"
                  name="website"
                  defaultValue={enterprise.website || ''}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm"
                />
              ) : (
                <p className="text-gray-900">{enterprise.website || '未设置'}</p>
              )}
            </div>
          </div>
        </div>

        {/* 地址 */}
        <div>
          <h3 className="text-sm font-medium text-gray-700 mb-3">企业地址</h3>
          {isEditing ? (
            <textarea
              name="address"
              defaultValue={enterprise.address || ''}
              rows={3}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm"
            />
          ) : (
            <p className="text-gray-900">{enterprise.address || '未设置'}</p>
          )}
        </div>

        {/* 描述 */}
        <div>
          <h3 className="text-sm font-medium text-gray-700 mb-3">企业简介</h3>
          {isEditing ? (
            <textarea
              name="description"
              defaultValue={enterprise.description || ''}
              rows={4}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm"
            />
          ) : (
            <p className="text-gray-900">{enterprise.description || '未设置'}</p>
          )}
        </div>

        {/* 使用情况 */}
        <div className="pt-4 border-t border-gray-200">
          <h3 className="text-sm font-medium text-gray-700 mb-3">使用情况</h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="bg-gray-50 p-4 rounded-lg">
              <p className="text-2xl font-bold text-gray-900">{enterprise.memberCount}</p>
              <p className="text-xs text-gray-500">团队成员</p>
            </div>
            <div className="bg-gray-50 p-4 rounded-lg">
              <p className="text-2xl font-bold text-gray-900">{enterprise.contractCount}</p>
              <p className="text-xs text-gray-500">合同审查</p>
            </div>
            <div className="bg-gray-50 p-4 rounded-lg">
              <p className="text-2xl font-bold text-gray-900">{enterprise.quotaUsed}</p>
              <p className="text-xs text-gray-500">已使用额度</p>
            </div>
            <div className="bg-gray-50 p-4 rounded-lg">
              <p className="text-2xl font-bold text-gray-900">{enterprise.quotaTotal}</p>
              <p className="text-xs text-gray-500">总额度</p>
            </div>
          </div>
          {/* 额度进度条 */}
          <div className="mt-4">
            <div className="flex justify-between text-xs text-gray-500 mb-1">
              <span>额度使用</span>
              <span>{Math.round((enterprise.quotaUsed / enterprise.quotaTotal) * 100)}%</span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div
                className="bg-blue-600 h-2 rounded-full transition-all"
                style={{ width: `${Math.min((enterprise.quotaUsed / enterprise.quotaTotal) * 100, 100)}%` }}
              />
            </div>
          </div>
        </div>
      </form>
    </div>
  );
}