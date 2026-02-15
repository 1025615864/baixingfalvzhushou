/**
 * VipPage 会员中心页面
 */

import { useState } from 'react';
import { Crown, CreditCard, History, TrendingUp, Loader2 } from 'lucide-react';

import { MembershipCard } from '../components/MembershipCard';
import { MembershipBenefits } from '../components/MembershipBenefits';
import { UpgradePrompt } from '../components/UpgradePrompt';
import {
  useMembershipInfo,
  useMembershipLevels,
  useConversionHistory,
  useUpgradeMembership,
} from '../hooks/useMembership';
import type { MembershipTier } from '../types';

/**
 * VIP 页面组件
 */
export function VipPage(): JSX.Element {
  const [showUpgradePrompt, setShowUpgradePrompt] = useState(false);
  const [selectedTier, setSelectedTier] = useState<MembershipTier | null>(null);

  // 获取会员信息
  const {
    data: membershipInfo,
    isLoading: isLoadingInfo,
    error: infoError,
  } = useMembershipInfo();

  // 获取会员等级列表
  const {
    data: membershipLevels,
    isLoading: isLoadingLevels,
  } = useMembershipLevels();

  // 获取转化历史
  const {
    data: conversionHistory,
    isLoading: isLoadingHistory,
  } = useConversionHistory({ page: 1, pageSize: 5 });

  // 升级会员 mutation
  const {
    mutate: upgradeMembership,
    isPending: isUpgrading,
  } = useUpgradeMembership();

  // 处理升级
  const handleUpgrade = (tier: MembershipTier, duration: 'month' | 'quarter' | 'year') => {
    upgradeMembership(
      { tier, duration },
      {
        onSuccess: () => {
          setShowUpgradePrompt(false);
          setSelectedTier(null);
        },
      }
    );
  };

  // 处理卡片选择
  const handleCardSelect = (tier: MembershipTier) => {
    setSelectedTier(tier);
    setShowUpgradePrompt(true);
  };

  // 加载状态
  if (isLoadingInfo) {
    return (
      <div className="min-h-screen bg-slate-50 flex items-center justify-center">
        <div className="flex flex-col items-center gap-4">
          <Loader2 className="w-8 h-8 animate-spin text-purple-600" />
          <p className="text-slate-600">加载会员信息...</p>
        </div>
      </div>
    );
  }

  // 错误状态
  if (infoError) {
    return (
      <div className="min-h-screen bg-slate-50 flex items-center justify-center">
        <div className="text-center">
          <p className="text-red-600 mb-2">加载失败</p>
          <p className="text-slate-500">{infoError.message}</p>
        </div>
      </div>
    );
  }

  const currentTier = membershipInfo?.tier || 'free';

  return (
    <div className="min-h-screen bg-slate-50 py-8 px-4">
      <div className="max-w-6xl mx-auto">
        {/* 页面标题 */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-slate-900 flex items-center gap-3">
            <Crown className="w-8 h-8 text-purple-600" />
            会员中心
          </h1>
          <p className="mt-2 text-slate-600">
            管理您的会员权益，享受更多专属服务
          </p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* 左侧：当前会员信息 */}
          <div className="lg:col-span-2 space-y-6">
            {/* 会员卡 */}
            <section>
              <h2 className="text-lg font-semibold text-slate-900 mb-4 flex items-center gap-2">
                <CreditCard className="w-5 h-5" />
                我的会员
              </h2>
              <MembershipCard
                tier={currentTier}
                memberName={membershipInfo?.benefits?.name || '用户'}
                isCurrent
              />
            </section>

            {/* 使用额度 */}
            <section>
              <h2 className="text-lg font-semibold text-slate-900 mb-4 flex items-center gap-2">
                <TrendingUp className="w-5 h-5" />
                今日使用额度
              </h2>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div className="bg-white p-4 rounded-xl border border-slate-200">
                  <p className="text-sm text-slate-500 mb-1">AI 对话</p>
                  <div className="flex items-baseline gap-2">
                    <span className="text-2xl font-bold text-slate-900">
                      {membershipInfo?.quota.aiChat.used || 0}
                    </span>
                    <span className="text-slate-500">
                      / {membershipInfo?.quota.aiChat.limit === 1000000000
                        ? '无限'
                        : membershipInfo?.quota.aiChat.limit || 0}
                    </span>
                  </div>
                  <div className="mt-2 h-2 bg-slate-100 rounded-full overflow-hidden">
                    <div
                      className="h-full bg-purple-500 rounded-full"
                      style={{
                        width: `${Math.min(
                          ((membershipInfo?.quota.aiChat.used || 0) /
                            (membershipInfo?.quota.aiChat.limit || 1)) * 100,
                          100
                        )}%`,
                      }}
                    />
                  </div>
                </div>

                <div className="bg-white p-4 rounded-xl border border-slate-200">
                  <p className="text-sm text-slate-500 mb-1">文档生成</p>
                  <div className="flex items-baseline gap-2">
                    <span className="text-2xl font-bold text-slate-900">
                      {membershipInfo?.quota.documentGenerate.used || 0}
                    </span>
                    <span className="text-slate-500">
                      / {membershipInfo?.quota.documentGenerate.limit === 1000000000
                        ? '无限'
                        : membershipInfo?.quota.documentGenerate.limit || 0}
                    </span>
                  </div>
                  <div className="mt-2 h-2 bg-slate-100 rounded-full overflow-hidden">
                    <div
                      className="h-full bg-blue-500 rounded-full"
                      style={{
                        width: `${Math.min(
                          ((membershipInfo?.quota.documentGenerate.used || 0) /
                            (membershipInfo?.quota.documentGenerate.limit || 1)) * 100,
                          100
                        )}%`,
                      }}
                    />
                  </div>
                </div>
              </div>
            </section>

            {/* 升级选项 */}
            <section>
              <h2 className="text-lg font-semibold text-slate-900 mb-4">升级会员</h2>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                {isLoadingLevels ? (
                  <div className="col-span-2 text-center py-8">
                    <Loader2 className="w-6 h-6 animate-spin mx-auto text-slate-400" />
                  </div>
                ) : (
                  membershipLevels
                    ?.filter((level) => level.tier !== 'free' && level.tier !== currentTier)
                    .map((level) => (
                      <MembershipCard
                        key={level.tier}
                        tier={level.tier}
                        memberName={level.name}
                        onSelect={handleCardSelect}
                      />
                    ))
                )}
              </div>
            </section>

            {/* 转化历史 */}
            <section>
              <h2 className="text-lg font-semibold text-slate-900 mb-4 flex items-center gap-2">
                <History className="w-5 h-5" />
                最近转化记录
              </h2>
              <div className="bg-white rounded-xl border border-slate-200 overflow-hidden">
                {isLoadingHistory ? (
                  <div className="p-8 text-center">
                    <Loader2 className="w-6 h-6 animate-spin mx-auto text-slate-400" />
                  </div>
                ) : conversionHistory?.items.length === 0 ? (
                  <div className="p-8 text-center text-slate-500">
                    暂无转化记录
                  </div>
                ) : (
                  <table className="w-full">
                    <thead className="bg-slate-50">
                      <tr>
                        <th className="px-4 py-3 text-left text-sm font-medium text-slate-700">订单号</th>
                        <th className="px-4 py-3 text-left text-sm font-medium text-slate-700">类型</th>
                        <th className="px-4 py-3 text-right text-sm font-medium text-slate-700">金额</th>
                        <th className="px-4 py-3 text-left text-sm font-medium text-slate-700">时间</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-200">
                      {conversionHistory?.items.map((item, index) => (
                        <tr key={index}>
                          <td className="px-4 py-3 text-sm text-slate-900 font-mono">
                            {item.orderNo}
                          </td>
                          <td className="px-4 py-3 text-sm text-slate-600">
                            {item.orderType || '普通订单'}
                          </td>
                          <td className="px-4 py-3 text-sm text-slate-900 text-right">
                            ¥{item.amount.toFixed(2)}
                          </td>
                          <td className="px-4 py-3 text-sm text-slate-500">
                            {item.paidAt
                              ? new Date(item.paidAt).toLocaleDateString('zh-CN')
                              : '-'}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                )}
              </div>
            </section>
          </div>

          {/* 右侧：权益详情 */}
          <div className="lg:col-span-1">
            <div className="sticky top-8">
              <h2 className="text-lg font-semibold text-slate-900 mb-4">当前权益</h2>
              <MembershipBenefits
                benefits={membershipInfo?.benefits || null}
                showComparison
              />
            </div>
          </div>
        </div>
      </div>

      {/* 升级弹窗 */}
      {showUpgradePrompt && (
        <UpgradePrompt
          currentTier={currentTier}
          recommendedTier={selectedTier || 'standard'}
          onUpgrade={handleUpgrade}
          onClose={() => {
            setShowUpgradePrompt(false);
            setSelectedTier(null);
          }}
          loading={isUpgrading}
        />
      )}
    </div>
  );
}

export default VipPage;