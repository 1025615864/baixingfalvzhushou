/**
 * VipPage 会员中心页面
 * 
 * 会员等级体系：
 * - free: 免费用户
 * - monthly: 月度会员 ¥29/月
 * - annual: 年度会员 ¥299/年 (享8.6折)
 * - lifetime: 终身会员 ¥999 (一次购买终身权益)
 */

import { useState, useMemo } from 'react';
import {
  Crown,
  CreditCard,
  History,
  TrendingUp,
  Loader2,
  Settings,
  ChevronRight,
  Zap,
  Shield,
  Gift,
} from 'lucide-react';

import { MembershipCard } from '../components/MembershipCard';
import { MembershipBenefits } from '../components/MembershipBenefits';
import { MembershipComparison } from '../components/MembershipComparison';
import { PricingCard } from '../components/PricingCard';
import { PurchaseFlow } from '../components/PurchaseFlow';
import {
  useMembershipInfo,
  useMembershipLevels,
  useMembershipPricing,
  useConversionHistory,
} from '../hooks/useMembership';
import type { MembershipTier, MembershipPricing } from '../types';

// 默认价格配置（API 不可用时的后备）
const defaultPricing: MembershipPricing[] = [
  { tier: 'free', name: '免费用户', monthlyPrice: 0, annualPrice: 0, annualDiscount: 0, lifetimePrice: 0, savingsAnnual: 0 },
  { tier: 'monthly', name: '月度会员', monthlyPrice: 29, annualPrice: 348, annualDiscount: 0, lifetimePrice: 0, savingsAnnual: 0 },
  { tier: 'annual', name: '年度会员', monthlyPrice: 29, annualPrice: 299, annualDiscount: 14, lifetimePrice: 0, savingsAnnual: 49 },
  { tier: 'lifetime', name: '终身会员', monthlyPrice: 29, annualPrice: 299, annualDiscount: 14, lifetimePrice: 999, savingsAnnual: 49 },
];

// 页面标签页
type TabType = 'overview' | 'pricing' | 'comparison';

const tabs: { id: TabType; label: string }[] = [
  { id: 'overview', label: '会员概览' },
  { id: 'pricing', label: '价格方案' },
  { id: 'comparison', label: '权益对比' },
];

/**
 * VIP 页面组件
 */
export function VipPage(): JSX.Element {
  const [activeTab, setActiveTab] = useState<TabType>('overview');
  const [billingCycle, setBillingCycle] = useState<'monthly' | 'annual' | 'lifetime'>('annual');
  const [selectedTier, setSelectedTier] = useState<MembershipTier | null>(null);
  const [showPurchaseFlow, setShowPurchaseFlow] = useState(false);

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

  // 获取价格配置
  const {
    data: pricingData,
    isLoading: isLoadingPricing,
  } = useMembershipPricing();

  // 获取转化历史
  const {
    data: conversionHistory,
    isLoading: isLoadingHistory,
  } = useConversionHistory({ page: 1, pageSize: 5 });

  // 使用 API 数据或默认数据
  const pricing = useMemo(() => {
    return pricingData && pricingData.length > 0 ? pricingData : defaultPricing;
  }, [pricingData]);

  // 当前会员等级
  const currentTier = membershipInfo?.level || 'free';

  // 处理卡片选择
  const handleCardSelect = (tier: MembershipTier) => {
    setSelectedTier(tier);
    setShowPurchaseFlow(true);
  };

  // 处理购买成功
  const handlePurchaseSuccess = () => {
    setShowPurchaseFlow(false);
    setSelectedTier(null);
    // 可以在这里添加成功提示
  };

  // 加载状态
  if (isLoadingInfo) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-purple-50 via-white to-pink-50 flex items-center justify-center">
        <div className="flex flex-col items-center gap-4">
          <Loader2 className="w-10 h-10 animate-spin text-purple-600" />
          <p className="text-slate-600 font-medium">加载会员信息...</p>
        </div>
      </div>
    );
  }

  // 错误状态
  if (infoError) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-purple-50 via-white to-pink-50 flex items-center justify-center">
        <div className="text-center">
          <div className="p-4 bg-red-100 rounded-full w-16 h-16 mx-auto mb-4 flex items-center justify-center">
            <Crown className="w-8 h-8 text-red-500" />
          </div>
          <p className="text-red-600 mb-2 font-medium">加载失败</p>
          <p className="text-slate-500 text-sm">{infoError.message}</p>
          <button 
            onClick={() => window.location.reload()}
            className="mt-4 px-6 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors"
          >
            重试
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-50 via-white to-pink-50">
      {/* 页面头部 */}
      <div className="bg-gradient-to-r from-purple-600 to-pink-500 text-white">
        <div className="max-w-6xl mx-auto px-4 py-8">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold flex items-center gap-3">
                <Crown className="w-8 h-8" />
                会员中心
              </h1>
              <p className="mt-2 text-purple-100">
                管理您的会员权益，享受更多专属服务
              </p>
            </div>
            <button className="p-2 bg-white/20 rounded-lg hover:bg-white/30 transition-colors">
              <Settings className="w-6 h-6" />
            </button>
          </div>

          {/* 标签页导航 */}
          <div className="mt-6 flex gap-1 bg-white/10 p-1 rounded-xl w-fit">
            {tabs.map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`
                  px-6 py-2 rounded-lg text-sm font-medium transition-all
                  ${activeTab === tab.id
                    ? 'bg-white text-purple-600 shadow'
                    : 'text-white/80 hover:text-white hover:bg-white/10'
                  }
                `}
              >
                {tab.label}
              </button>
            ))}
          </div>
        </div>
      </div>

      <div className="max-w-6xl mx-auto px-4 py-8">
        {/* 概览标签页 */}
        {activeTab === 'overview' && (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
            {/* 左侧：当前会员信息 */}
            <div className="lg:col-span-2 space-y-6">
              {/* 会员卡 */}
              <section>
                <h2 className="text-lg font-semibold text-slate-900 mb-4 flex items-center gap-2">
                  <CreditCard className="w-5 h-5 text-purple-600" />
                  我的会员
                </h2>
                <MembershipCard
                  tier={currentTier}
                  memberName={membershipInfo?.levelName || '用户'}
                  expiryDate={membershipInfo?.endDate || undefined}
                  isCurrent
                />
              </section>

              {/* 快捷功能 */}
              <section>
                <h2 className="text-lg font-semibold text-slate-900 mb-4">快捷功能</h2>
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
                  {[
                    { icon: Zap, label: '升级会员', color: 'text-amber-600', bg: 'bg-amber-50', onClick: () => setActiveTab('pricing') },
                    { icon: Gift, label: '邀请好友', color: 'text-pink-600', bg: 'bg-pink-50', onClick: () => {} },
                    { icon: History, label: '订单记录', color: 'text-blue-600', bg: 'bg-blue-50', onClick: () => {} },
                    { icon: Shield, label: '会员保障', color: 'text-green-600', bg: 'bg-green-50', onClick: () => {} },
                  ].map((item, index) => {
                    const Icon = item.icon;
                    return (
                      <button
                        key={index}
                        onClick={item.onClick}
                        className={`
                          flex flex-col items-center gap-2 p-4 rounded-xl border border-slate-200 
                          bg-white hover:shadow-md transition-all group
                        `}
                      >
                        <div className={`p-3 rounded-lg ${item.bg} group-hover:scale-110 transition-transform`}>
                          <Icon className={`w-6 h-6 ${item.color}`} />
                        </div>
                        <span className="text-sm font-medium text-slate-700">{item.label}</span>
                      </button>
                    );
                  })}
                </div>
              </section>

              {/* 升级推荐 */}
              {currentTier === 'free' && (
                <section className="bg-gradient-to-r from-purple-500 to-pink-500 rounded-2xl p-6 text-white">
                  <div className="flex items-center justify-between">
                    <div>
                      <h3 className="text-lg font-bold flex items-center gap-2">
                        <Zap className="w-5 h-5" />
                        升级会员，解锁更多权益
                      </h3>
                      <p className="mt-1 text-purple-100 text-sm">
                        无限 AI 对话、专属客服、积分双倍返还等特权等你来享
                      </p>
                    </div>
                    <button
                      onClick={() => setActiveTab('pricing')}
                      className="px-6 py-3 bg-white text-purple-600 rounded-xl font-semibold hover:bg-purple-50 transition-colors flex items-center gap-2"
                    >
                      立即升级
                      <ChevronRight className="w-4 h-4" />
                    </button>
                  </div>
                </section>
              )}

              {/* 使用额度 */}
              <section>
                <h2 className="text-lg font-semibold text-slate-900 mb-4 flex items-center gap-2">
                  <TrendingUp className="w-5 h-5 text-purple-600" />
                  今日使用额度
                </h2>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm">
                    <p className="text-sm text-slate-500 mb-2">AI 对话</p>
                    <div className="flex items-baseline gap-2">
                      <span className="text-3xl font-bold text-slate-900">0</span>
                      <span className="text-slate-500">
                        / {currentTier === 'free' ? '5' : currentTier === 'annual' || currentTier === 'lifetime' ? '无限' : '100'}
                      </span>
                    </div>
                    <div className="mt-3 h-2 bg-slate-100 rounded-full overflow-hidden">
                      <div
                        className="h-full bg-gradient-to-r from-purple-500 to-pink-500 rounded-full"
                        style={{ width: '0%' }}
                      />
                    </div>
                  </div>

                  <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm">
                    <p className="text-sm text-slate-500 mb-2">文档生成</p>
                    <div className="flex items-baseline gap-2">
                      <span className="text-3xl font-bold text-slate-900">0</span>
                      <span className="text-slate-500">
                        / {currentTier === 'free' ? '3' : currentTier === 'annual' || currentTier === 'lifetime' ? '无限' : '50'}
                      </span>
                    </div>
                    <div className="mt-3 h-2 bg-slate-100 rounded-full overflow-hidden">
                      <div
                        className="h-full bg-gradient-to-r from-blue-500 to-cyan-500 rounded-full"
                        style={{ width: '0%' }}
                      />
                    </div>
                  </div>
                </div>
              </section>

              {/* 转化历史 */}
              <section>
                <h2 className="text-lg font-semibold text-slate-900 mb-4 flex items-center gap-2">
                  <History className="w-5 h-5 text-purple-600" />
                  最近订单记录
                </h2>
                <div className="bg-white rounded-xl border border-slate-200 overflow-hidden shadow-sm">
                  {isLoadingHistory ? (
                    <div className="p-8 text-center">
                      <Loader2 className="w-6 h-6 animate-spin mx-auto text-slate-400" />
                    </div>
                  ) : !conversionHistory?.items?.length ? (
                    <div className="p-8 text-center">
                      <div className="p-3 bg-slate-100 rounded-full w-12 h-12 mx-auto mb-3 flex items-center justify-center">
                        <History className="w-6 h-6 text-slate-400" />
                      </div>
                      <p className="text-slate-500">暂无订单记录</p>
                      <button
                        onClick={() => setActiveTab('pricing')}
                        className="mt-3 text-purple-600 hover:text-purple-700 text-sm font-medium"
                      >
                        立即开通会员 →
                      </button>
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
                        {conversionHistory?.items.map((item) => (
                          <tr key={item.orderNo} className="hover:bg-slate-50">
                            <td className="px-4 py-3 text-sm text-slate-900 font-mono">
                              {item.orderNo}
                            </td>
                            <td className="px-4 py-3 text-sm text-slate-600">
                              {item.orderType || '会员订单'}
                            </td>
                            <td className="px-4 py-3 text-sm text-slate-900 text-right font-medium">
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
        )}

        {/* 价格方案标签页 */}
        {activeTab === 'pricing' && (
          <div className="space-y-8">
            {/* 计费周期选择 */}
            <div className="flex justify-center">
              <div className="inline-flex bg-white rounded-xl p-1 shadow-sm border border-slate-200">
                {[
                  { value: 'monthly' as const, label: '月付' },
                  { value: 'annual' as const, label: '年付', discount: '省14%' },
                  { value: 'lifetime' as const, label: '终身', discount: '超值' },
                ].map((cycle) => (
                  <button
                    key={cycle.value}
                    onClick={() => setBillingCycle(cycle.value)}
                    className={`
                      relative px-6 py-3 rounded-lg text-sm font-medium transition-all
                      ${billingCycle === cycle.value
                        ? 'bg-purple-600 text-white shadow'
                        : 'text-slate-600 hover:text-slate-900'
                      }
                    `}
                  >
                    {cycle.label}
                    {cycle.discount && (
                      <span className={`
                        absolute -top-2 -right-2 px-2 py-0.5 text-xs rounded-full
                        ${billingCycle === cycle.value
                          ? 'bg-pink-500 text-white'
                          : 'bg-pink-100 text-pink-600'
                        }
                      `}>
                        {cycle.discount}
                      </span>
                    )}
                  </button>
                ))}
              </div>
            </div>

            {/* 价格卡片 */}
            {isLoadingPricing ? (
              <div className="flex justify-center py-12">
                <Loader2 className="w-8 h-8 animate-spin text-purple-600" />
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                {pricing
                  .filter((p) => p.tier !== 'free')
                  .map((p) => (
                    <PricingCard
                      key={p.tier}
                      tier={p.tier}
                      pricing={p}
                      isCurrent={p.tier === currentTier}
                      isSelected={selectedTier === p.tier}
                      isPopular={p.tier === 'annual'}
                      onSelect={handleCardSelect}
                      billingCycle={billingCycle}
                    />
                  ))}
              </div>
            )}

            {/* 服务保障 */}
            <div className="bg-white rounded-2xl p-8 border border-slate-200">
              <h3 className="text-lg font-semibold text-slate-900 mb-6 text-center">服务保障</h3>
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-6">
                {[
                  { icon: Shield, title: '安全支付', desc: '支持支付宝、微信等主流支付方式' },
                  { icon: Gift, title: '7天无理由退款', desc: '不满意可申请全额退款' },
                  { icon: Zap, title: '即时生效', desc: '支付成功后会员权益立即生效' },
                ].map((item, index) => {
                  const Icon = item.icon;
                  return (
                    <div key={index} className="flex flex-col items-center text-center">
                      <div className="p-3 bg-purple-100 rounded-lg mb-3">
                        <Icon className="w-6 h-6 text-purple-600" />
                      </div>
                      <h4 className="font-medium text-slate-900">{item.title}</h4>
                      <p className="text-sm text-slate-500 mt-1">{item.desc}</p>
                    </div>
                  );
                })}
              </div>
            </div>
          </div>
        )}

        {/* 权益对比标签页 */}
        {activeTab === 'comparison' && (
          <div className="space-y-8">
            {isLoadingLevels ? (
              <div className="flex justify-center py-12">
                <Loader2 className="w-8 h-8 animate-spin text-purple-600" />
              </div>
            ) : (
              <MembershipComparison
                benefits={membershipLevels || []}
                currentTier={currentTier}
                onSelectTier={handleCardSelect}
              />
            )}

            {/* FAQ */}
            <div className="bg-white rounded-2xl p-8 border border-slate-200">
              <h3 className="text-lg font-semibold text-slate-900 mb-6">常见问题</h3>
              <div className="space-y-4">
                {[
                  {
                    q: '会员可以随时取消吗？',
                    a: '是的，您可以随时取消会员订阅。取消后，您仍可使用会员权益直到当前计费周期结束。',
                  },
                  {
                    q: '终身会员真的永久有效吗？',
                    a: '是的，终身会员一次购买后永久有效，无需续费。我们承诺至少提供 10 年的服务保障。',
                  },
                  {
                    q: '如何申请退款？',
                    a: '在购买后 7 天内，您可以通过客服或个人中心申请无理由退款，我们将在 3-5 个工作日内处理。',
                  },
                  {
                    q: '升级会员后原有权益会怎样？',
                    a: '升级后您将立即享受新等级的所有权益。如果您有剩余的会员时长，我们会按比例折算。',
                  },
                ].map((item, index) => (
                  <div key={index} className="border-b border-slate-100 pb-4 last:border-0 last:pb-0">
                    <h4 className="font-medium text-slate-900">{item.q}</h4>
                    <p className="text-sm text-slate-500 mt-1">{item.a}</p>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}
      </div>

      {/* 购买流程弹窗 */}
      <PurchaseFlow
        isOpen={showPurchaseFlow}
        onClose={() => {
          setShowPurchaseFlow(false);
          setSelectedTier(null);
        }}
        selectedTier={selectedTier || undefined}
        pricing={pricing}
        benefits={membershipLevels || []}
        currentTier={currentTier}
        onSuccess={handlePurchaseSuccess}
      />
    </div>
  );
}

export default VipPage;