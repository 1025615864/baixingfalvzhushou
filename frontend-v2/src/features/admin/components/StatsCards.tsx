/**
 * StatsCards 组件 - 统计卡片
 * 使用 Tailwind CSS + shadcn/ui 风格
 */

import React from 'react';
import { Users, FileText, BookOpen, Building2, MessageSquare, Headphones } from 'lucide-react';
import type { LucideIcon } from 'lucide-react';

import { Skeleton } from '@/components/ui/Skeleton';

import type { AdminStats } from '../types';


/** 统计卡片Props */
interface StatsCardsProps {
  stats: AdminStats | null;
  loading: boolean;
}

/** 统计项配置 */
const STAT_CONFIG: ReadonlyArray<{
  key: keyof AdminStats;
  title: string;
  icon: LucideIcon;
  iconColor: string;
  bgColor: string;
  borderColor: string;
  valueColor: string;
}> = [
  {
    key: 'users',
    title: '总用户数',
    icon: Users,
    iconColor: 'text-blue-600',
    bgColor: 'bg-blue-50',
    borderColor: 'border-blue-200',
    valueColor: 'text-blue-700',
  },
  {
    key: 'news',
    title: '新闻数量',
    icon: FileText,
    iconColor: 'text-green-600',
    bgColor: 'bg-green-50',
    borderColor: 'border-green-200',
    valueColor: 'text-green-700',
  },
  {
    key: 'posts',
    title: '帖子数量',
    icon: BookOpen,
    iconColor: 'text-amber-600',
    bgColor: 'bg-amber-50',
    borderColor: 'border-amber-200',
    valueColor: 'text-amber-700',
  },
  {
    key: 'lawfirms',
    title: '律所数量',
    icon: Building2,
    iconColor: 'text-purple-600',
    bgColor: 'bg-purple-50',
    borderColor: 'border-purple-200',
    valueColor: 'text-purple-700',
  },
  {
    key: 'comments',
    title: '评论数量',
    icon: MessageSquare,
    iconColor: 'text-pink-600',
    bgColor: 'bg-pink-50',
    borderColor: 'border-pink-200',
    valueColor: 'text-pink-700',
  },
  {
    key: 'consultations',
    title: '咨询数量',
    icon: Headphones,
    iconColor: 'text-cyan-600',
    bgColor: 'bg-cyan-50',
    borderColor: 'border-cyan-200',
    valueColor: 'text-cyan-700',
  },
];

/**
 * 格式化数字（大于1000显示为k）
 */
function formatNumber(num: number): string {
  if (num >= 1000000) {
    return `${(num / 1000000).toFixed(1)}M`;
  }
  if (num >= 1000) {
    return `${(num / 1000).toFixed(1)}K`;
  }
  return num.toString();
}

/**
 * 单个统计卡片组件
 */
interface StatCardProps {
  config: (typeof STAT_CONFIG)[number];
  value: number;
  loading: boolean;
}

const StatCard: React.FC<StatCardProps> = ({ config, value, loading }) => {
  const Icon = config.icon;
  
  return (
    <div
      className={`
        ${config.bgColor} ${config.borderColor}
        border rounded-2xl p-5 transition-all duration-300
        hover:shadow-lg hover:-translate-y-0.5
      `}
    >
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <p className="text-sm text-slate-500 mb-2">{config.title}</p>
          {loading ? (
            <Skeleton className="h-8 w-24" />
          ) : (
            <p className={`text-2xl font-bold ${config.valueColor}`}>
              {formatNumber(value)}
            </p>
          )}
        </div>
        <div className={`
          ${config.bgColor} ${config.iconColor}
          w-12 h-12 rounded-xl flex items-center justify-center
          border ${config.borderColor}
        `}>
          <Icon className="w-6 h-6" />
        </div>
      </div>
    </div>
  );
};

/**
 * 统计卡片组件
 */
export const StatsCards: React.FC<StatsCardsProps> = ({ stats, loading }) => {
  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-4">
      {STAT_CONFIG.map((config) => (
        <StatCard
          key={config.key}
          config={config}
          value={stats?.[config.key] ?? 0}
          loading={loading}
        />
      ))}
    </div>
  );
};