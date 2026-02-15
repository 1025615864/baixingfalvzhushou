/**
 * QuickActions 组件 - 快捷入口
 * 美化后的快捷入口组件，带有更好的视觉效果
 */

import { Link } from 'react-router-dom';
import { MessageSquare, Users, FileText, BookOpen, Shield, Gavel, FileText as Newspaper, Crown, Sparkles } from 'lucide-react';

import type { QuickAction } from '../types';

interface QuickActionsProps {
  actions: QuickAction[];
  isLoading?: boolean;
}

// 图标映射
const iconMap: Record<string, React.ReactNode> = {
  ai: <Sparkles className="w-6 h-6" />,
  chat: <MessageSquare className="w-6 h-6" />,
  consultation: <Users className="w-6 h-6" />,
  lawyer: <Gavel className="w-6 h-6" />,
  knowledge: <BookOpen className="w-6 h-6" />,
  document: <FileText className="w-6 h-6" />,
  contract: <Shield className="w-6 h-6" />,
  forum: <MessageSquare className="w-6 h-6" />,
  calendar: <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" /></svg>,
  news: <Newspaper className="w-6 h-6" />,
  points: <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>,
  promotion: <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5.882V19.24a1.76 1.76 0 01-3.417.592l-2.147-6.15M18 13a3 3 0 100-6M5.436 13.683A4.001 4.001 0 017 6h1.832c4.1 0 7.625-1.234 9.168-3v14c-1.543-1.766-5.067-3-9.168-3H7a3.988 3.988 0 01-1.564-.317z" /></svg>,
  vip: <Crown className="w-6 h-6" />,
  search: <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" /></svg>,
};

// 颜色映射
const colorMap: Record<string, { bg: string; text: string; ring: string }> = {
  blue: { bg: 'bg-blue-50', text: 'text-blue-600', ring: 'ring-blue-200' },
  green: { bg: 'bg-green-50', text: 'text-green-600', ring: 'ring-green-200' },
  purple: { bg: 'bg-purple-50', text: 'text-purple-600', ring: 'ring-purple-200' },
  orange: { bg: 'bg-orange-50', text: 'text-orange-600', ring: 'ring-orange-200' },
  red: { bg: 'bg-red-50', text: 'text-red-600', ring: 'ring-red-200' },
  teal: { bg: 'bg-teal-50', text: 'text-teal-600', ring: 'ring-teal-200' },
  indigo: { bg: 'bg-indigo-50', text: 'text-indigo-600', ring: 'ring-indigo-200' },
  amber: { bg: 'bg-amber-50', text: 'text-amber-600', ring: 'ring-amber-200' },
  primary: { bg: 'bg-primary-50', text: 'text-primary-600', ring: 'ring-primary-200' },
  secondary: { bg: 'bg-secondary-50', text: 'text-secondary-600', ring: 'ring-secondary-200' },
  accent: { bg: 'bg-accent-50', text: 'text-accent-600', ring: 'ring-accent-200' },
};

// 默认快捷入口
const defaultActions: QuickAction[] = [
  {
    id: '1',
    title: 'AI咨询',
    description: '智能法律助手',
    icon: 'ai',
    link: '/chat',
    color: 'primary',
    isNew: true,
    order: 1,
  },
  {
    id: '2',
    title: '找律师',
    description: '专业律师服务',
    icon: 'lawyer',
    link: '/lawyer',
    color: 'blue',
    order: 2,
  },
  {
    id: '3',
    title: '法律咨询',
    description: '一对一咨询',
    icon: 'consultation',
    link: '/consultation',
    color: 'green',
    order: 3,
  },
  {
    id: '4',
    title: '法律知识',
    description: '海量法律知识',
    icon: 'knowledge',
    link: '/knowledge',
    color: 'indigo',
    order: 4,
  },
  {
    id: '5',
    title: '合同审查',
    description: 'AI智能审查',
    icon: 'contract',
    link: '/contracts',
    color: 'purple',
    isNew: true,
    order: 5,
  },
  {
    id: '6',
    title: '文书生成',
    description: '快速生成文书',
    icon: 'document',
    link: '/document',
    color: 'orange',
    order: 6,
  },
  {
    id: '7',
    title: '法律论坛',
    description: '交流讨论',
    icon: 'forum',
    link: '/forum',
    color: 'teal',
    order: 7,
  },
  {
    id: '8',
    title: '会员中心',
    description: '尊享特权',
    icon: 'vip',
    link: '/vip',
    color: 'amber',
    order: 8,
  },
];

export function QuickActions({ actions, isLoading = false }: QuickActionsProps): JSX.Element {
  const displayActions = actions.length > 0 ? actions : defaultActions;

  if (isLoading) {
    return (
      <section className="py-8 bg-white border-b border-slate-100">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid grid-cols-4 md:grid-cols-8 gap-4">
            {Array.from({ length: 8 }).map((_, index) => (
              <div key={index} className="animate-pulse flex flex-col items-center">
                <div className="w-14 h-14 bg-slate-100 rounded-2xl mb-3" />
                <div className="h-4 bg-slate-100 rounded w-16 mb-1" />
                <div className="h-3 bg-slate-100 rounded w-12" />
              </div>
            ))}
          </div>
        </div>
      </section>
    );
  }

  return (
    <section className="py-8 bg-white border-b border-slate-100">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="grid grid-cols-4 md:grid-cols-8 gap-4">
          {displayActions.map((action) => {
            const colors = colorMap[action.color || 'primary'];
            
            return (
              <Link
                key={action.id}
                to={action.link}
                className="group flex flex-col items-center p-3 rounded-2xl hover:bg-slate-50 transition-all duration-200"
              >
                <div className="relative mb-3">
                  <div className={`w-14 h-14 ${colors.bg} ${colors.text} rounded-2xl flex items-center justify-center shadow-sm group-hover:shadow-md group-hover:scale-110 transition-all duration-300 ring-2 ring-transparent group-hover:${colors.ring}`}>
                    {iconMap[action.icon] ?? iconMap.ai}
                  </div>
                  {action.isNew && (
                    <span className="absolute -top-1 -right-1 bg-gradient-to-r from-red-500 to-red-600 text-white text-[10px] font-bold px-1.5 py-0.5 rounded-full shadow-sm">
                      NEW
                    </span>
                  )}
                  {action.badge && !action.isNew && (
                    <span className="absolute -top-1 -right-1 bg-gradient-to-r from-primary-500 to-primary-600 text-white text-[10px] font-bold px-1.5 py-0.5 rounded-full shadow-sm">
                      {action.badge}
                    </span>
                  )}
                </div>
                <span className="text-sm font-semibold text-slate-900 text-center group-hover:text-primary-600 transition-colors">
                  {action.title}
                </span>
                {action.description && (
                  <span className="text-xs text-slate-500 text-center mt-0.5 hidden sm:block">
                    {action.description}
                  </span>
                )}
              </Link>
            );
          })}
        </div>
      </div>
    </section>
  );
}
