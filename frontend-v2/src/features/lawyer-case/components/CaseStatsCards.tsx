import { Briefcase, CheckCircle, TrendingUp, Users } from 'lucide-react';
import { Card } from '@/components/ui/Card';
import type { CaseStats } from '../types';

interface CaseStatsCardsProps {
  stats: CaseStats | undefined;
  isLoading: boolean;
}

export function CaseStatsCards({ stats, isLoading }: CaseStatsCardsProps): JSX.Element {
  const items = [
    {
      label: '进行中案件',
      value: stats?.activeCount ?? 0,
      icon: Briefcase,
      color: 'text-blue-600',
      bg: 'bg-blue-50',
    },
    {
      label: '已结案件',
      value: stats?.closedCount ?? 0,
      icon: CheckCircle,
      color: 'text-green-600',
      bg: 'bg-green-50',
    },
    {
      label: '胜诉案件',
      value: stats?.winCount ?? 0,
      icon: TrendingUp,
      color: 'text-amber-600',
      bg: 'bg-amber-50',
    },
    {
      label: '胜诉率',
      value: stats ? `${stats.winRate}%` : '--',
      icon: Users,
      color: 'text-purple-600',
      bg: 'bg-purple-50',
      isPercentage: true,
    },
  ];

  if (isLoading) {
    return (
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {[1, 2, 3, 4].map((i) => (
          <Card key={i} padding="md" className="animate-pulse">
            <div className="h-16 bg-gray-100 rounded" />
          </Card>
        ))}
      </div>
    );
  }

  return (
    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
      {items.map((item) => (
        <Card key={item.label} padding="md">
          <div className="flex items-center gap-3">
            <div className={`p-2.5 rounded-lg ${item.bg}`}>
              <item.icon className={`w-5 h-5 ${item.color}`} />
            </div>
            <div>
              <p className="text-sm text-gray-500">{item.label}</p>
              <p className="text-2xl font-bold text-gray-900">{item.value}</p>
            </div>
          </div>
        </Card>
      ))}
    </div>
  );
}