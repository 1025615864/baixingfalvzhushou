/**
 * 律师服务管理员 Dashboard
 * 律师认证审核、律所管理、案件派单、文书模板
 */

import React, { Suspense, lazy, useState } from 'react';
import { LayoutDashboard, Scale, Building2, FileText, Send, FileCheck } from 'lucide-react';
import { AdminShell } from '@/features/admin-shared/components/AdminShell';
import type { SidebarMenuItem } from '@/features/admin-shared/components/SidebarShell';

const LazyLawyerVerificationPanel = lazy(() =>
  import('@/features/admin/components/LawyerVerificationPanel').then(m => ({ default: m.LawyerVerificationPanel }))
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
  { key: 'verification', label: '律师认证', icon: React.createElement(Scale, { className: 'w-4 h-4' }) },
  { key: 'firms', label: '律所管理', icon: React.createElement(Building2, { className: 'w-4 h-4' }) },
  { key: 'cases', label: '案件派单', icon: React.createElement(Send, { className: 'w-4 h-4' }) },
  { key: 'documents', label: '文书模板', icon: React.createElement(FileCheck, { className: 'w-4 h-4' }) },
];

export function LawyerAdminPage(): JSX.Element {
  const [activeTab, setActiveTab] = useState<string>('overview');

  const renderContent = () => {
    switch (activeTab) {
      case 'overview':
        return (
          <div className="space-y-6">
            <h2 className="text-xl font-semibold text-slate-800">律师服务总览</h2>
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              {[
                { label: '注册律师', value: '856', color: 'text-blue-600', bg: 'bg-blue-50' },
                { label: '待认证', value: '3', color: 'text-orange-600', bg: 'bg-orange-50' },
                { label: '今日咨询', value: '47', color: 'text-green-600', bg: 'bg-green-50' },
                { label: '案件中', value: '128', color: 'text-purple-600', bg: 'bg-purple-50' },
              ].map(item => (
                <div key={item.label} className={`${item.bg} rounded-xl p-6`}>
                  <div className={`text-3xl font-bold ${item.color}`}>{item.value}</div>
                  <div className="text-sm text-slate-600 mt-1">{item.label}</div>
                </div>
              ))}
            </div>
          </div>
        );
      case 'verification':
        return <Suspense fallback={<SectionSkeleton />}><LazyLawyerVerificationPanel /></Suspense>;
      case 'firms':
        return <Placeholder title="律所管理" icon="🏢" text="管理注册律师事务所信息、资质审核" />;
      case 'cases':
        return <Placeholder title="案件派单" icon="📋" text="查看案件派单情况、调解案件分配" />;
      case 'documents':
        return <Placeholder title="文书模板" icon="📄" text="管理法律文书模板库" />;
      default:
        return null;
    }
  };

  return (
    <AdminShell title="律师管理" subtitle="律师认证与案件管理" menuItems={menuItems} selectedKey={activeTab}>
      {renderContent()}
    </AdminShell>
  );
}