/**
 * StatsSection 组件 - 统计数据
 * 美化后的统计数据展示区域
 */

import { MessageSquare, Users, CheckCircle, Smile, TrendingUp } from 'lucide-react';

import type { HomeStats } from '../types';

interface StatsSectionProps {
  stats?: HomeStats;
  isLoading?: boolean;
}

// 数字动画格式化
function formatNumber(num: number): string {
  if (num >= 1000000) {
    return `${(num / 1000000).toFixed(1)}M`;
  }
  if (num >= 1000) {
    return `${(num / 1000).toFixed(1)}K`;
  }
  return num.toString();
}

// 统计数据项配置
interface StatItem {
  key: keyof HomeStats;
  label: string;
  suffix?: string;
  icon: React.ReactNode;
  color: string;
}

const statItems: StatItem[] = [
  {
    key: 'totalConsultations',
    label: '累计咨询',
    suffix: '+',
    icon: <MessageSquare className="w-6 h-6" />,
    color: 'from-blue-500 to-blue-600',
  },
  {
    key: 'totalLawyers',
    label: '专业律师',
    suffix: '+',
    icon: <Users className="w-6 h-6" />,
    color: 'from-green-500 to-green-600',
  },
  {
    key: 'totalUsers',
    label: '服务用户',
    suffix: '+',
    icon: <TrendingUp className="w-6 h-6" />,
    color: 'from-purple-500 to-purple-600',
  },
  {
    key: 'solvedCases',
    label: '成功案例',
    suffix: '+',
    icon: <CheckCircle className="w-6 h-6" />,
    color: 'from-orange-500 to-orange-600',
  },
  {
    key: 'satisfactionRate',
    label: '满意度',
    suffix: '%',
    icon: <Smile className="w-6 h-6" />,
    color: 'from-teal-500 to-teal-600',
  },
];

// 默认统计数据
const defaultStats: HomeStats = {
  totalConsultations: 1000000,
  totalLawyers: 10000,
  totalUsers: 500000,
  totalArticles: 50000,
  solvedCases: 800000,
  satisfactionRate: 98,
};

export function StatsSection({ stats, isLoading = false }: StatsSectionProps): JSX.Element {
  const displayStats = stats ?? defaultStats;

  if (isLoading) {
    return (
      <section className="py-20 bg-gradient-primary relative overflow-hidden">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid grid-cols-2 md:grid-cols-5 gap-8">
            {Array.from({ length: 5 }).map((_, index) => (
              <div key={index} className="animate-pulse text-center">
                <div className="h-12 bg-white/10 rounded-xl w-24 mx-auto mb-3" />
                <div className="h-4 bg-white/10 rounded-lg w-16 mx-auto" />
              </div>
            ))}
          </div>
        </div>
      </section>
    );
  }

  return (
    <section className="py-20 bg-gradient-primary relative overflow-hidden">
      {/* 背景装饰 */}
      <div className="absolute inset-0">
        <div className="absolute top-0 left-1/4 w-64 h-64 bg-white/5 rounded-full blur-3xl" />
        <div className="absolute bottom-0 right-1/4 w-64 h-64 bg-white/5 rounded-full blur-3xl" />
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative">
        {/* 标题 */}
        <div className="text-center mb-12">
          <h2 className="text-3xl md:text-4xl font-bold text-white mb-4">
            数据见证实力
          </h2>
          <p className="text-lg text-white/70 max-w-2xl mx-auto">
            百姓助手已为数百万用户提供专业法律服务
          </p>
        </div>

        {/* 统计数据网格 */}
        <div className="grid grid-cols-2 md:grid-cols-5 gap-6 md:gap-8">
          {statItems.map((item, index) => {
            const value = displayStats[item.key];
            const formattedValue = typeof value === 'number' ? formatNumber(value) : '0';

            return (
              <div 
                key={item.key} 
                className="text-center group"
                style={{ animationDelay: `${index * 0.1}s` }}
              >
                <div className={`inline-flex items-center justify-center w-14 h-14 bg-gradient-to-br ${item.color} rounded-2xl text-white mb-4 shadow-lg transform group-hover:scale-110 transition-transform duration-300`}>
                  {item.icon}
                </div>
                <div className="text-3xl md:text-4xl font-bold text-white mb-2">
                  {formattedValue}
                  {item.suffix && <span className="text-2xl text-white/80">{item.suffix}</span>}
                </div>
                <div className="text-white/60 font-medium">{item.label}</div>
              </div>
            );
          })}
        </div>
      </div>
    </section>
  );
}
