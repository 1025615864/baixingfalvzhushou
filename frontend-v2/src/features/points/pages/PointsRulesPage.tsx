/**
 * PointsRulesPage - 积分规则页
 * 
 * 包含积分获取方式说明、积分使用规则、积分有效期说明、常见问题
 */

import { useState } from 'react';
import { Link } from 'react-router-dom';

import { usePointsRules, usePointsBalance } from '../hooks/usePoints';

/**
 * 获取动作显示文本
 */
function getActionLabel(action: string): string {
  const actionMap: Record<string, string> = {
    sign_in: '每日签到',
    post_create: '发布帖子',
    comment_create: '发表评论',
    like: '点赞互动',
    share: '分享内容',
    consultation_complete: '完成咨询',
    document_upload: '上传文档',
    profile_complete: '完善资料',
    invite_friend: '邀请好友',
    exchange_product: '兑换商品',
    bonus: '系统奖励',
  };
  return actionMap[action] || action;
}

/**
 * 获取动作图标
 */
function getActionIcon(action: string): string {
  const iconMap: Record<string, string> = {
    sign_in: '📅',
    post_create: '📝',
    comment_create: '💬',
    like: '❤️',
    share: '📤',
    consultation_complete: '🤝',
    document_upload: '📄',
    profile_complete: '👤',
    invite_friend: '👥',
    exchange_product: '🎁',
    bonus: '🎉',
  };
  return iconMap[action] || '✨';
}

/**
 * FAQ 手风琴项
 */
function FAQItem({ 
  question, 
  answer, 
  isOpen, 
  onToggle 
}: { 
  question: string; 
  answer: string; 
  isOpen: boolean;
  onToggle: () => void;
}): JSX.Element {
  return (
    <div className="border-b border-gray-200 last:border-0">
      <button
        onClick={onToggle}
        className="w-full flex items-center justify-between py-4 text-left"
      >
        <span className="font-medium text-gray-900">{question}</span>
        <svg 
          className={`w-5 h-5 text-gray-400 transition-transform ${isOpen ? 'rotate-180' : ''}`}
          fill="none" 
          viewBox="0 0 24 24" 
          stroke="currentColor"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
      </button>
      <div className={`overflow-hidden transition-all ${isOpen ? 'max-h-96 pb-4' : 'max-h-0'}`}>
        <p className="text-gray-600 leading-relaxed">{answer}</p>
      </div>
    </div>
  );
}

/**
 * 规则卡片组件
 */
function RuleCard({ 
  icon, 
  title, 
  description, 
  points, 
  limit 
}: { 
  icon: string;
  title: string;
  description: string;
  points: number;
  limit: number;
}): JSX.Element {
  return (
    <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-100 hover:shadow-md transition-shadow">
      <div className="flex items-start gap-4">
        <div className="text-3xl">{icon}</div>
        <div className="flex-1">
          <h3 className="font-semibold text-gray-900 mb-1">{title}</h3>
          <p className="text-sm text-gray-500 mb-3">{description}</p>
          <div className="flex items-center gap-3">
            <span className="px-3 py-1 bg-orange-100 text-orange-700 rounded-full text-sm font-medium">
              +{points} 积分
            </span>
            <span className="text-sm text-gray-400">
              每日限{limit}次
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}

/**
 * 积分获取规则列表
 */
function PointsEarningRules(): JSX.Element {
  const { data: rules, isLoading } = usePointsRules();

  if (isLoading) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {Array.from({ length: 6 }).map((_, i) => (
          <div key={i} className="h-32 bg-gray-100 rounded-xl animate-pulse" />
        ))}
      </div>
    );
  }

  const earningRules = rules?.filter(r => 
    r.action !== 'exchange_product' && r.action !== 'bonus'
  ) || [];

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
      {earningRules.map((rule) => (
        <RuleCard
          key={rule.action}
          icon={getActionIcon(rule.action)}
          title={getActionLabel(rule.action)}
          description={rule.description}
          points={rule.points}
          limit={rule.dailyLimit}
        />
      ))}
    </div>
  );
}

/**
 * 积分使用规则
 */
function PointsUsageRules(): JSX.Element {
  const usageRules = [
    {
      icon: '🛒',
      title: '积分商城兑换',
      description: '在积分商城中使用积分兑换精美商品、虚拟服务或优惠券',
      examples: ['实物商品', '虚拟服务', '优惠券', '会员权益'],
    },
    {
      icon: '🎁',
      title: '参与活动',
      description: '使用积分参与平台举办的各类活动，赢取更多奖励',
      examples: ['抽奖活动', '限时秒杀', '积分竞拍'],
    },
    {
      icon: '⭐',
      title: '提升等级',
      description: '累计积分可提升用户等级，解锁更多特权',
      examples: ['专属标识', '优先客服', '专属活动'],
    },
  ];

  return (
    <div className="space-y-4">
      {usageRules.map((rule, index) => (
        <div key={index} className="bg-white rounded-xl p-6 shadow-sm border border-gray-100">
          <div className="flex items-start gap-4">
            <div className="text-4xl">{rule.icon}</div>
            <div className="flex-1">
              <h3 className="font-semibold text-gray-900 text-lg mb-2">{rule.title}</h3>
              <p className="text-gray-600 mb-4">{rule.description}</p>
              <div className="flex flex-wrap gap-2">
                {rule.examples.map((example, i) => (
                  <span 
                    key={i}
                    className="px-3 py-1 bg-blue-50 text-blue-600 rounded-full text-sm"
                  >
                    {example}
                  </span>
                ))}
              </div>
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}

/**
 * 积分有效期说明
 */
function PointsValidityInfo(): JSX.Element {
  const validityRules = [
    {
      title: '积分有效期',
      content: '积分自获得之日起有效期为365天，过期未使用的积分将自动清零。',
      icon: '📅',
    },
    {
      title: '优先使用',
      content: '使用积分时，系统会优先扣除即将到期的积分，确保您的权益最大化。',
      icon: '🔄',
    },
    {
      title: '过期提醒',
      content: '积分过期前30天，系统将通过消息推送提醒您及时使用。',
      icon: '🔔',
    },
    {
      title: '特殊情况',
      content: '活动赠送积分可能有特殊有效期，具体以活动规则为准。',
      icon: '⚠️',
    },
  ];

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
      {validityRules.map((rule, index) => (
        <div key={index} className="bg-gradient-to-br from-blue-50 to-indigo-50 rounded-xl p-6 border border-blue-100">
          <div className="flex items-start gap-4">
            <div className="text-3xl">{rule.icon}</div>
            <div>
              <h3 className="font-semibold text-gray-900 mb-2">{rule.title}</h3>
              <p className="text-gray-600 text-sm leading-relaxed">{rule.content}</p>
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}

/**
 * FAQ 常见问题
 */
function FAQSection(): JSX.Element {
  const [openIndex, setOpenIndex] = useState<number | null>(0);

  const faqs = [
    {
      question: '积分是如何计算的？',
      answer: '积分根据您在平台的活跃度计算。完成签到、发布内容、互动交流等行为均可获得相应积分。不同行为获得的积分数量不同，每日有获取上限。',
    },
    {
      question: '积分可以转让吗？',
      answer: '目前积分不支持转让或赠送，仅限本人账户使用。但您可以通过邀请好友注册，获得额外的邀请奖励积分。',
    },
    {
      question: '积分兑换的商品可以退换吗？',
      answer: '虚拟商品兑换后不支持退换。实物商品如存在质量问题，可在收到商品后7天内联系客服处理。',
    },
    {
      question: '为什么我的积分被扣减了？',
      answer: '积分扣减可能是因为：1)兑换了商品或服务；2)发布了违规内容被扣除；3)积分已过期自动清零。您可以在积分明细中查看具体记录。',
    },
    {
      question: '如何快速提升积分？',
      answer: '建议每日完成签到任务，积极参与社区互动，发布优质内容。连续签到还可获得额外奖励积分。',
    },
    {
      question: '积分商城多久更新一次？',
      answer: '积分商城每周更新一次商品，每月会有大型促销活动。建议关注平台公告，及时了解最新优惠信息。',
    },
  ];

  return (
    <div className="bg-white rounded-xl shadow-sm">
      {faqs.map((faq, index) => (
        <FAQItem
          key={index}
          question={faq.question}
          answer={faq.answer}
          isOpen={openIndex === index}
          onToggle={() => setOpenIndex(openIndex === index ? null : index)}
        />
      ))}
    </div>
  );
}

/**
 * 积分规则页面
 */
export function PointsRulesPage(): JSX.Element {
  const { data: balance } = usePointsBalance();

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-6xl mx-auto px-4">
        {/* 页面标题 */}
        <div className="mb-6">
          <h1 className="text-2xl font-bold text-gray-900">积分规则说明</h1>
          <p className="text-gray-500 mt-1">了解积分的获取方式、使用规则和注意事项</p>
        </div>

        {/* 积分余额卡片 */}
        <div className="mb-8 bg-gradient-to-r from-orange-500 to-pink-500 rounded-xl shadow-lg p-6 text-white">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-white/80 mb-1">当前积分余额</p>
              <p className="text-4xl font-bold">{balance?.balance.toLocaleString() || '0'}</p>
            </div>
            <div className="flex gap-3">
              <Link 
                to="/points/activities"
                className="px-4 py-2 bg-white/20 hover:bg-white/30 rounded-lg text-white transition-colors"
              >
                去做任务
              </Link>
              <Link 
                to="/points/mall"
                className="px-4 py-2 bg-white text-orange-600 hover:bg-orange-50 rounded-lg transition-colors"
              >
                去兑换
              </Link>
            </div>
          </div>
        </div>

        {/* 规则内容 */}
        <div className="space-y-8">
          {/* 积分获取方式 */}
          <section>
            <div className="flex items-center gap-3 mb-4">
              <div className="w-10 h-10 bg-green-100 rounded-full flex items-center justify-center text-xl">
                💎
              </div>
              <h2 className="text-xl font-semibold text-gray-900">积分获取方式</h2>
            </div>
            <PointsEarningRules />
          </section>

          {/* 积分使用规则 */}
          <section>
            <div className="flex items-center gap-3 mb-4">
              <div className="w-10 h-10 bg-blue-100 rounded-full flex items-center justify-center text-xl">
                🛍️
              </div>
              <h2 className="text-xl font-semibold text-gray-900">积分使用规则</h2>
            </div>
            <PointsUsageRules />
          </section>

          {/* 积分有效期 */}
          <section>
            <div className="flex items-center gap-3 mb-4">
              <div className="w-10 h-10 bg-purple-100 rounded-full flex items-center justify-center text-xl">
                ⏰
              </div>
              <h2 className="text-xl font-semibold text-gray-900">积分有效期说明</h2>
            </div>
            <PointsValidityInfo />
          </section>

          {/* 常见问题 */}
          <section>
            <div className="flex items-center gap-3 mb-4">
              <div className="w-10 h-10 bg-yellow-100 rounded-full flex items-center justify-center text-xl">
                ❓
              </div>
              <h2 className="text-xl font-semibold text-gray-900">常见问题</h2>
            </div>
            <FAQSection />
          </section>
        </div>

        {/* 底部导航 */}
        <div className="mt-12 flex flex-wrap gap-4 justify-center">
          <Link
            to="/points/activities"
            className="px-6 py-3 bg-white rounded-lg shadow-sm text-gray-700 hover:text-blue-600 hover:shadow-md transition-all"
          >
            ← 返回活动中心
          </Link>
          <Link
            to="/points/checkin"
            className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            立即签到 →
          </Link>
        </div>
      </div>
    </div>
  );
}