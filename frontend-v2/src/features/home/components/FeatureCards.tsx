/**
 * FeatureCards 组件 - 功能卡片
 * 美化后的功能展示卡片，带有更好的视觉效果和交互
 */

import { Link } from 'react-router-dom';
import { ChevronRight, MessageSquare, FileText, Search, Calculator, Shield, Users, BookOpen, Gavel } from 'lucide-react';

import type { FeatureCard } from '../types';

interface FeatureCardsProps {
  cards: FeatureCard[];
  isLoading?: boolean;
  title?: string;
}

// 颜色样式映射
const colorStyles: Record<string, { 
  bg: string; 
  iconBg: string; 
  hover: string;
  border: string;
  gradient: string;
}> = {
  blue: {
    bg: 'bg-blue-50/50',
    iconBg: 'bg-gradient-to-br from-blue-500 to-blue-600',
    hover: 'hover:bg-blue-50',
    border: 'group-hover:border-blue-200',
    gradient: 'from-blue-500/20 to-blue-600/20',
  },
  green: {
    bg: 'bg-green-50/50',
    iconBg: 'bg-gradient-to-br from-green-500 to-green-600',
    hover: 'hover:bg-green-50',
    border: 'group-hover:border-green-200',
    gradient: 'from-green-500/20 to-green-600/20',
  },
  purple: {
    bg: 'bg-purple-50/50',
    iconBg: 'bg-gradient-to-br from-purple-500 to-purple-600',
    hover: 'hover:bg-purple-50',
    border: 'group-hover:border-purple-200',
    gradient: 'from-purple-500/20 to-purple-600/20',
  },
  orange: {
    bg: 'bg-orange-50/50',
    iconBg: 'bg-gradient-to-br from-orange-500 to-orange-600',
    hover: 'hover:bg-orange-50',
    border: 'group-hover:border-orange-200',
    gradient: 'from-orange-500/20 to-orange-600/20',
  },
  red: {
    bg: 'bg-red-50/50',
    iconBg: 'bg-gradient-to-br from-red-500 to-red-600',
    hover: 'hover:bg-red-50',
    border: 'group-hover:border-red-200',
    gradient: 'from-red-500/20 to-red-600/20',
  },
  teal: {
    bg: 'bg-teal-50/50',
    iconBg: 'bg-gradient-to-br from-teal-500 to-teal-600',
    hover: 'hover:bg-teal-50',
    border: 'group-hover:border-teal-200',
    gradient: 'from-teal-500/20 to-teal-600/20',
  },
  indigo: {
    bg: 'bg-indigo-50/50',
    iconBg: 'bg-gradient-to-br from-indigo-500 to-indigo-600',
    hover: 'hover:bg-indigo-50',
    border: 'group-hover:border-indigo-200',
    gradient: 'from-indigo-500/20 to-indigo-600/20',
  },
  amber: {
    bg: 'bg-amber-50/50',
    iconBg: 'bg-gradient-to-br from-amber-500 to-amber-600',
    hover: 'hover:bg-amber-50',
    border: 'group-hover:border-amber-200',
    gradient: 'from-amber-500/20 to-amber-600/20',
  },
};

// 图标映射
const iconMap: Record<string, React.ReactNode> = {
  ai: <MessageSquare className="w-6 h-6" />,
  document: <FileText className="w-6 h-6" />,
  search: <Search className="w-6 h-6" />,
  consultation: <Users className="w-6 h-6" />,
  shield: <Shield className="w-6 h-6" />,
  calculator: <Calculator className="w-6 h-6" />,
  knowledge: <BookOpen className="w-6 h-6" />,
  lawyer: <Gavel className="w-6 h-6" />,
};

// 默认功能卡片
const defaultCards: FeatureCard[] = [
  {
    id: '1',
    title: 'AI智能咨询',
    description: '基于大模型的智能法律助手，24小时在线解答您的法律问题，提供专业建议',
    icon: 'ai',
    link: '/chat',
    color: 'blue',
    stats: { label: '已解答', value: '100万+' },
  },
  {
    id: '2',
    title: '合同智能审查',
    description: '上传合同文件，AI自动识别风险条款，提供专业修改建议和风险提示',
    icon: 'document',
    link: '/contracts',
    color: 'purple',
    stats: { label: '审查合同', value: '50万+' },
  },
  {
    id: '3',
    title: '律师精准匹配',
    description: '根据您的需求和案件类型，智能推荐最合适的专业律师，一对一服务',
    icon: 'lawyer',
    link: '/lawyer',
    color: 'green',
    stats: { label: '入驻律师', value: '10万+' },
  },
  {
    id: '4',
    title: '法律文书生成',
    description: '输入关键信息，一键生成专业的法律文书，省时省力，规范标准',
    icon: 'calculator',
    link: '/document',
    color: 'orange',
    stats: { label: '生成文书', value: '200万+' },
  },
  {
    id: '5',
    title: '法律知识库',
    description: '海量法律知识库，涵盖各类法律问题，快速查找您需要的法律信息',
    icon: 'knowledge',
    link: '/knowledge',
    color: 'purple',
    stats: { label: '知识文章', value: '50万+' },
  },
  {
    id: '6',
    title: '隐私安全保护',
    description: '采用银行级加密技术，严格保护您的隐私和数据安全，让您安心使用',
    icon: 'shield',
    link: '/security',
    color: 'teal',
    stats: { label: '安全认证', value: 'ISO27001' },
  },
];

export function FeatureCards({ cards, isLoading = false, title = '核心功能' }: FeatureCardsProps): JSX.Element {
  const displayCards = cards.length > 0 ? cards : defaultCards;

  if (isLoading) {
    return (
      <section className="py-20 bg-slate-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="h-8 bg-slate-200 rounded-xl w-48 mx-auto mb-12" />
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {Array.from({ length: 6 }).map((_, index) => (
              <div key={index} className="animate-pulse bg-white rounded-2xl p-6 border border-slate-100">
                <div className="w-14 h-14 bg-slate-200 rounded-xl mb-4" />
                <div className="h-6 bg-slate-200 rounded-lg w-3/4 mb-3" />
                <div className="h-4 bg-slate-200 rounded w-full mb-2" />
                <div className="h-4 bg-slate-200 rounded w-2/3" />
              </div>
            ))}
          </div>
        </div>
      </section>
    );
  }

  return (
    <section className="py-20 bg-slate-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* 标题区域 */}
        <div className="text-center mb-16">
          <span className="inline-block px-4 py-1.5 bg-primary-100 text-primary-700 text-sm font-medium rounded-full mb-4">
            功能服务
          </span>
          <h2 className="text-3xl md:text-4xl font-bold text-slate-900 mb-4">
            {title}
          </h2>
          <p className="text-lg text-slate-600 max-w-2xl mx-auto">
            百姓助手为您提供全方位的法律服务，让法律问题变得简单易懂
          </p>
        </div>

        {/* 功能卡片网格 */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {displayCards.map((card, index) => {
            const styles = colorStyles[card.color] ?? colorStyles.blue;

            return (
              <Link
                key={card.id}
                to={card.link}
                className="group relative bg-white rounded-2xl p-6 border border-slate-100 shadow-soft transition-all duration-300 hover:shadow-soft-lg hover:-translate-y-1"
                style={{ animationDelay: `${index * 0.1}s` }}
              >
                {/* 背景渐变 */}
                <div className={`absolute inset-0 bg-gradient-to-br ${styles.gradient} opacity-0 group-hover:opacity-100 transition-opacity duration-300 rounded-2xl`} />
                
                <div className="relative">
                  {/* 图标和标题行 */}
                  <div className="flex items-start justify-between mb-4">
                    <div className={`${styles.iconBg} w-14 h-14 rounded-xl flex items-center justify-center text-white shadow-lg transform group-hover:scale-110 transition-transform duration-300`}>
                      {iconMap[card.icon] ?? iconMap.ai}
                    </div>
                    <div className="w-10 h-10 rounded-xl bg-slate-50 flex items-center justify-center text-slate-400 group-hover:bg-white group-hover:text-primary-600 transition-colors">
                      <ChevronRight className="w-5 h-5 transform group-hover:translate-x-0.5 group-hover:-translate-y-0.5 transition-transform" />
                    </div>
                  </div>

                  {/* 标题 */}
                  <h3 className="text-xl font-semibold text-slate-900 mb-2 group-hover:text-primary-700 transition-colors">
                    {card.title}
                  </h3>

                  {/* 描述 */}
                  <p className="text-slate-600 mb-4 line-clamp-2 leading-relaxed">
                    {card.description}
                  </p>

                  {/* 统计数据 */}
                  {card.stats && (
                    <div className="flex items-center gap-2 pt-4 border-t border-slate-100">
                      <span className="text-sm text-slate-500">{card.stats.label}</span>
                      <span className="text-lg font-bold text-slate-900">
                        {card.stats.value}
                      </span>
                    </div>
                  )}
                </div>
              </Link>
            );
          })}
        </div>
      </div>
    </section>
  );
}
