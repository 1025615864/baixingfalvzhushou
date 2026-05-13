/**
 * HomePage 首页主页面
 * 百姓助手法律服务平台首页
 * 优化：添加新用户引导入口、个性化推荐卡片
 */

import { Link } from 'react-router-dom';
import {
  ChevronRight,
  MessageSquare,
  Users,
  FileText,
  Shield,
  Scale,
  BookOpen,
  Clock,
  CheckCircle,
  ChevronRight as ArrowRight,
} from 'lucide-react';

import { Button } from '@/components/ui/Button';

import type { FeatureCard } from '../types';
import { HeroSection } from '../components/HeroSection';
import { QuickActions } from '../components/QuickActions';
import { Recommendations } from '../components/Recommendations';
import { FeatureCards } from '../components/FeatureCards';
import { StatsSection } from '../components/StatsSection';
import { useHomePageData } from '../hooks/useHome';
import { useLawyers } from '@/features/lawyer/hooks/useLawyers';

/**
 * 首页功能卡片数据 - 展示平台核心功能入口
 */
const featureCardsData: FeatureCard[] = [
  {
    id: 'ai-consultation',
    title: 'AI智能咨询',
    description: '基于大模型的智能法律助手，24小时在线解答您的法律问题，提供专业建议',
    icon: 'ai',
    link: '/ai-consultation',
    color: 'blue',
    stats: { label: '已解答', value: '100万+' },
  },
  {
    id: 'find-lawyer',
    title: '找律师',
    description: '根据您的需求和案件类型，智能推荐最合适的专业律师，一对一服务',
    icon: 'lawyer',
    link: '/lawyer',
    color: 'green',
    stats: { label: '入驻律师', value: '10万+' },
  },
  {
    id: 'knowledge-base',
    title: '法律知识库',
    description: '海量法律知识库，涵盖各类法律问题，快速查找您需要的法律信息',
    icon: 'knowledge',
    link: '/knowledge',
    color: 'purple',
    stats: { label: '知识文章', value: '50万+' },
  },
  {
    id: 'contract-review',
    title: '合同审查',
    description: '上传合同文件，AI自动识别风险条款，提供专业修改建议和风险提示',
    icon: 'document',
    link: '/contracts',
    color: 'orange',
    stats: { label: '审查合同', value: '50万+' },
  },
  {
    id: 'points-mall',
    title: '积分商城',
    description: '使用积分兑换精美礼品和优惠券，参与活动赚取更多积分',
    icon: 'points',
    link: '/points/mall',
    color: 'red',
    stats: { label: '精选好礼', value: '1000+' },
  },
  {
    id: 'vip-center',
    title: '会员中心',
    description: '开通会员享专属权益，包括优先咨询、专属客服、更多免费额度等',
    icon: 'vip',
    link: '/vip',
    color: 'amber',
    stats: { label: '会员特权', value: '20项' },
  },
];

export function HomePage(): JSX.Element {
  const {
    banners,
    quickActions,
    recommendations,
    stats,
    isLoading,
  } = useHomePageData();

  const { data: lawyersData, isLoading: lawyersLoading } = useLawyers({ page_size: 4 } as Parameters<typeof useLawyers>[0]);
  const featuredLawyers = lawyersData?.lawyers ?? [];

  return (
    <div className="min-h-screen">
      {/* 首页横幅 */}
      <HeroSection banners={banners} isLoading={isLoading} />

      {/* 快捷入口 */}
      <QuickActions actions={quickActions} isLoading={isLoading} />

      {/* 核心功能 */}
      <FeatureCards cards={featureCardsData} isLoading={isLoading} />

      {/* 统计数据 */}
      <StatsSection stats={stats} isLoading={isLoading} />

      {/* 为什么选择我们 */}
      <section className="py-20 bg-white relative overflow-hidden">
        {/* 背景装饰 */}
        <div className="absolute inset-0 bg-dots opacity-30" />

        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative">
          <div className="text-center mb-16">
            <div className="inline-flex items-center gap-2 px-4 py-1.5 bg-secondary-50 text-secondary-700 text-sm font-medium rounded-full border border-secondary-200 mb-4">
              <Scale className="w-4 h-4" />
              我们的优势
            </div>
            <h2 className="text-3xl md:text-4xl font-bold text-slate-900 mb-4">
              为什么选择<span className="text-primary-600">百姓助手</span>
            </h2>
            <p className="text-lg text-slate-600 max-w-2xl mx-auto">
              我们致力于让每个人都能获得专业、便捷、可信赖的法律服务
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
            {[
              {
                icon: MessageSquare,
                title: 'AI智能咨询',
                description: '7×24小时在线，即时响应您的法律问题，提供专业建议',
                color: 'bg-primary-50 text-primary-600',
                borderColor: 'border-primary-200',
              },
              {
                icon: Users,
                title: '专业律师团队',
                description: '汇聚全国10万+专业律师，覆盖各领域法律问题',
                color: 'bg-secondary-50 text-secondary-600',
                borderColor: 'border-secondary-200',
              },
              {
                icon: FileText,
                title: '智能文书生成',
                description: '一键生成专业法律文书，省时省力，规范标准',
                color: 'bg-gold-50 text-gold-600',
                borderColor: 'border-gold-200',
              },
              {
                icon: Shield,
                title: '隐私安全保障',
                description: '银行级加密技术，严格保护您的隐私和数据安全',
                color: 'bg-teal-50 text-teal-600',
                borderColor: 'border-teal-200',
              },
            ].map((item, index) => (
              <div
                key={index}
                className={`relative p-6 bg-white rounded-2xl border ${item.borderColor} hover:shadow-lg hover:-translate-y-1 transition-all duration-300 group`}
              >
                <div className={`inline-flex items-center justify-center w-14 h-14 ${item.color} rounded-xl mb-5 transform group-hover:scale-110 transition-transform duration-300`}>
                  <item.icon className="w-7 h-7" />
                </div>
                <h3 className="text-lg font-semibold text-slate-900 mb-2">
                  {item.title}
                </h3>
                <p className="text-slate-600 text-sm leading-relaxed">
                  {item.description}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* 服务流程 */}
      <section className="py-20 bg-slate-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <div className="inline-flex items-center gap-2 px-4 py-1.5 bg-primary-50 text-primary-700 text-sm font-medium rounded-full border border-primary-200 mb-4">
              <BookOpen className="w-4 h-4" />
              服务流程
            </div>
            <h2 className="text-3xl md:text-4xl font-bold text-slate-900 mb-4">
              简单三步，获取专业法律服务
            </h2>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            {[
              {
                step: '01',
                title: '描述问题',
                description: '通过AI对话或文字描述您的法律问题',
                icon: MessageSquare,
              },
              {
                step: '02',
                title: '智能分析',
                description: 'AI系统快速分析并匹配相关法律知识',
                icon: Scale,
              },
              {
                step: '03',
                title: '专业解答',
                description: '获得专业建议或推荐合适的律师服务',
                icon: CheckCircle,
              },
            ].map((item, index) => (
              <div key={index} className="relative">
                {/* 连接线 */}
                {index < 2 && (
                  <div className="hidden md:block absolute top-12 left-[60%] w-[80%] h-0.5 bg-gradient-to-r from-primary-300 to-primary-100" />
                )}

                <div className="relative bg-white rounded-2xl p-8 shadow-soft border border-slate-100 hover:shadow-soft-lg transition-shadow">
                  <div className="flex items-center gap-4 mb-6">
                    <div className="w-12 h-12 bg-gradient-hero rounded-xl flex items-center justify-center text-white font-bold text-lg shadow-lg shadow-primary-500/30">
                      {item.step}
                    </div>
                    <item.icon className="w-6 h-6 text-primary-600" />
                  </div>
                  <h3 className="text-xl font-semibold text-slate-900 mb-3">
                    {item.title}
                  </h3>
                  <p className="text-slate-600">
                    {item.description}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* 推荐内容 */}
      <Recommendations
        recommendations={recommendations}
        isLoading={isLoading}
        title="为您推荐"
      />

      {/* 律师推荐区 */}
      <section className="py-20 bg-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex flex-col md:flex-row items-center justify-between gap-6 mb-12">
            <div>
              <h2 className="text-2xl md:text-3xl font-bold text-slate-900 mb-2">
                推荐律师
              </h2>
              <p className="text-slate-600">
                专业律师团队，为您提供优质服务
              </p>
            </div>
            <Link to="/lawyer">
              <Button
                variant="outline"
                rightIcon={<ArrowRight className="w-4 h-4" />}
              >
                查看全部
              </Button>
            </Link>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            {lawyersLoading && Array.from({ length: 4 }).map((_, i) => (
              <div key={i} className="bg-slate-50 rounded-2xl p-6 animate-pulse">
                <div className="flex items-center gap-4 mb-4">
                  <div className="w-14 h-14 bg-slate-200 rounded-xl" />
                  <div className="flex-1">
                    <div className="h-5 bg-slate-200 rounded w-16 mb-2" />
                    <div className="h-4 bg-slate-200 rounded w-24" />
                  </div>
                </div>
                <div className="h-4 bg-slate-200 rounded w-20" />
              </div>
            ))}
            {!lawyersLoading && featuredLawyers.length === 0 && (
              <div className="col-span-full text-center py-8 text-slate-400">暂无推荐律师</div>
            )}
            {!lawyersLoading && featuredLawyers.map((lawyer) => (
              <div
                key={lawyer.id}
                className="bg-slate-50 rounded-2xl p-6 hover:shadow-lg hover:-translate-y-1 transition-all duration-300 cursor-pointer group"
              >
                <div className="flex items-center gap-4 mb-4">
                  <div className="w-14 h-14 bg-gradient-to-br from-primary-500 to-primary-600 rounded-xl flex items-center justify-center text-white font-bold text-lg shadow-md group-hover:shadow-lg transition-shadow">
                    {(lawyer.name || '?').charAt(0)}
                  </div>
                  <div>
                    <h3 className="font-semibold text-slate-900">{lawyer.name}</h3>
                    <p className="text-sm text-slate-500">{String(lawyer.specialties ?? '').split(',').filter(Boolean).slice(0, 2).join(' · ') || '执业律师'}</p>
                  </div>
                </div>
                <div className="flex items-center justify-between text-sm">
                  <span className="text-slate-600">执业{lawyer.experienceYears ?? 0}年</span>
                  <span className="flex items-center gap-1 text-gold-600">
                    <svg className="w-4 h-4 fill-current" viewBox="0 0 20 20">
                      <path d="M10 15l-5.878 3.09 1.123-6.545L.489 6.91l6.572-.955L10 0l2.939 5.955 6.572.955-4.756 4.635 1.123 6.545z" />
                    </svg>
                    {lawyer.rating?.toFixed(1) ?? '-'}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* 底部 CTA 区域 */}
      <section className="py-20 bg-gradient-hero relative overflow-hidden">
        {/* 背景装饰 */}
        <div className="absolute inset-0">
          <div className="absolute top-0 left-1/4 w-96 h-96 bg-white/5 rounded-full blur-3xl" />
          <div className="absolute bottom-0 right-1/4 w-96 h-96 bg-secondary-500/10 rounded-full blur-3xl" />
          <div className="absolute inset-0 bg-dots opacity-10" />
        </div>

        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 text-center relative">
          <div className="inline-flex items-center gap-2 px-4 py-2 bg-white/10 backdrop-blur-sm rounded-full border border-white/20 mb-8">
            <Clock className="w-4 h-4 text-accent-400" />
            <span className="text-sm font-medium text-white/90">7×24小时在线服务</span>
          </div>

          <h2 className="text-3xl md:text-4xl font-bold text-white mb-4">
            准备好开始了吗？
          </h2>
          <p className="text-lg text-white/70 mb-10 max-w-2xl mx-auto">
            立即体验百姓助手的AI法律服务，让专业法律帮助触手可及
          </p>

          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Link to="/chat">
              <Button
                variant="white"
                size="lg"
                rightIcon={<ChevronRight className="w-5 h-5" />}
                className="shadow-xl shadow-black/20"
              >
                免费咨询
              </Button>
            </Link>
            <Link to="/lawyer">
              <Button
                variant="outline"
                size="lg"
                className="border-white/30 text-white hover:bg-white/10 hover:border-white/50"
              >
                联系律师
              </Button>
            </Link>
          </div>

          {/* 信任指标 */}
          <div className="flex flex-wrap items-center justify-center gap-8 mt-12 pt-8 border-t border-white/10">
            <div className="text-center">
              <div className="text-3xl font-bold text-white">100万+</div>
              <div className="text-sm text-white/60">用户信赖</div>
            </div>
            <div className="w-px h-12 bg-white/10 hidden sm:block" />
            <div className="text-center">
              <div className="text-3xl font-bold text-white">98%</div>
              <div className="text-sm text-white/60">满意度</div>
            </div>
            <div className="w-px h-12 bg-white/10 hidden sm:block" />
            <div className="text-center">
              <div className="text-3xl font-bold text-white">10万+</div>
              <div className="text-sm text-white/60">专业律师</div>
            </div>
            <div className="w-px h-12 bg-white/10 hidden sm:block" />
            <div className="text-center">
              <div className="text-3xl font-bold text-white">ISO</div>
              <div className="text-sm text-white/60">安全认证</div>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}
