/**
 * AI 服务管理员 Dashboard
 * AI 模型配置、质量监控、咨询模板管理
 */

import React, { Suspense, lazy, useState } from 'react';
import { LayoutDashboard, Brain, Activity, FileText, BarChart3 } from 'lucide-react';
import { AdminShell } from '@/features/admin-shared/components/AdminShell';
import type { SidebarMenuItem } from '@/features/admin-shared/components/SidebarShell';

const LazyAdminAIConfigPanel = lazy(() =>
  import('@/features/admin/components/AdminAIConfigPanel').then(m => ({ default: m.AdminAIConfigPanel }))
);
const LazySystemMonitorPanel = lazy(() =>
  import('@/features/admin/components/SystemMonitorPanel').then(m => ({ default: m.SystemMonitorPanel }))
);

function SectionSkeleton(): JSX.Element {
  return <div className="space-y-4">{[1, 2, 3].map(i => <div key={i} className="h-24 animate-pulse rounded-lg bg-slate-100" />)}</div>;
}

function Placeholder({ title, icon, text }: { title: string; icon: React.ReactNode; text: string }): JSX.Element {
  return (
    <div className="bg-white rounded-xl border border-slate-200 p-12 text-center">
      <div className="text-5xl mb-4">{icon}</div>
      <h3 className="text-lg font-semibold text-slate-700 mb-2">{title}</h3>
      <p className="text-slate-400">{text}</p>
    </div>
  );
}

const menuItems: SidebarMenuItem[] = [
  { key: 'overview', label: '管理总览', icon: React.createElement(LayoutDashboard, { className: 'w-4 h-4' }) },
  { key: 'config', label: '模型配置', icon: React.createElement(Brain, { className: 'w-4 h-4' }) },
  { key: 'quality', label: '质量监控', icon: React.createElement(Activity, { className: 'w-4 h-4' }) },
  { key: 'templates', label: '咨询模板', icon: React.createElement(FileText, { className: 'w-4 h-4' }) },
  { key: 'usage', label: '使用统计', icon: React.createElement(BarChart3, { className: 'w-4 h-4' }) },
];

export function AIAdminPage(): JSX.Element {
  const [activeTab, setActiveTab] = useState<string>('overview');

  const renderContent = () => {
    switch (activeTab) {
      case 'overview':
        return (
          <div className="space-y-6">
            <h2 className="text-xl font-semibold text-slate-800">AI 服务总览</h2>
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              {[
                { label: '今日咨询', value: '1,234', color: 'text-blue-600', bg: 'bg-blue-50' },
                { label: '平均响应', value: '1.2s', color: 'text-green-600', bg: 'bg-green-50' },
                { label: '准确率', value: '96.8%', color: 'text-purple-600', bg: 'bg-purple-50' },
                { label: '活跃模型', value: '3', color: 'text-amber-600', bg: 'bg-amber-50' },
              ].map(item => (
                <div key={item.label} className={`${item.bg} rounded-xl p-6`}>
                  <div className={`text-3xl font-bold ${item.color}`}>{item.value}</div>
                  <div className="text-sm text-slate-600 mt-1">{item.label}</div>
                </div>
              ))}
            </div>
          </div>
        );
      case 'config':
        return <Suspense fallback={<SectionSkeleton />}><LazyAdminAIConfigPanel /></Suspense>;
      case 'quality':
        return <Suspense fallback={<SectionSkeleton />}><LazySystemMonitorPanel /></Suspense>;
      case 'templates':
        return <Placeholder title="咨询模板" icon="📝" text="管理 AI 咨询模板，包含提示词和回答模板" />;
      case 'usage':
        return <Placeholder title="使用统计" icon="📊" text="AI 服务使用统计，包含请求量、成功率、用户分布等" />;
      default:
        return null;
    }
  };

  return (
    <AdminShell title="AI 管理" subtitle="AI 模型与质量监控" menuItems={menuItems} selectedKey={activeTab}>
      {renderContent()}
    </AdminShell>
  );
}