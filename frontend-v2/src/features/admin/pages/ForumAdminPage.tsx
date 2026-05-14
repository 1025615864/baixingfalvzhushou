/**
 * 论坛服务管理员 Dashboard
 * 帖子管理、评论管理、内容审核、用户管理
 */

import React, { Suspense, lazy, useState } from 'react';
import { LayoutDashboard, FileText, MessageSquare, Shield, Users } from 'lucide-react';
import { AdminShell } from '@/features/admin-shared/components/AdminShell';
import type { SidebarMenuItem } from '@/features/admin-shared/components/SidebarShell';

const LazyContentModerationPanel = lazy(() =>
  import('@/features/admin/components/ContentModerationPanel').then(m => ({ default: m.ContentModerationPanel }))
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
  { key: 'moderation', label: '内容审核', icon: React.createElement(Shield, { className: 'w-4 h-4' }) },
  { key: 'posts', label: '帖子管理', icon: React.createElement(FileText, { className: 'w-4 h-4' }) },
  { key: 'comments', label: '评论管理', icon: React.createElement(MessageSquare, { className: 'w-4 h-4' }) },
  { key: 'users', label: '用户管理', icon: React.createElement(Users, { className: 'w-4 h-4' }) },
];

export function ForumAdminPage(): JSX.Element {
  const [activeTab, setActiveTab] = useState<string>('overview');

  const renderContent = () => {
    switch (activeTab) {
      case 'overview':
        return (
          <div className="space-y-6">
            <h2 className="text-xl font-semibold text-slate-800">论坛管理总览</h2>
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              {[
                { label: '今日帖子', value: '128', color: 'text-blue-600', bg: 'bg-blue-50' },
                { label: '待审核', value: '5', color: 'text-orange-600', bg: 'bg-orange-50' },
                { label: '活跃用户', value: '342', color: 'text-green-600', bg: 'bg-green-50' },
                { label: '举报处理', value: '3', color: 'text-red-600', bg: 'bg-red-50' },
              ].map(item => (
                <div key={item.label} className={`${item.bg} rounded-xl p-6`}>
                  <div className={`text-3xl font-bold ${item.color}`}>{item.value}</div>
                  <div className="text-sm text-slate-600 mt-1">{item.label}</div>
                </div>
              ))}
            </div>
          </div>
        );
      case 'moderation':
        return <Suspense fallback={<SectionSkeleton />}><LazyContentModerationPanel /></Suspense>;
      case 'posts':
        return <Placeholder title="帖子管理" icon="📋" text="可在此管理论坛所有帖子（置顶、加精、删除等）" />;
      case 'comments':
        return <Placeholder title="评论管理" icon="💬" text="可在此管理论坛所有评论（审核、删除等）" />;
      case 'users':
        return <Placeholder title="用户管理" icon="👥" text="可在此管理论坛用户（禁言、封禁等）" />;
      default:
        return null;
    }
  };

  return (
    <AdminShell title="论坛管理" subtitle="论坛内容与用户管理" menuItems={menuItems} selectedKey={activeTab}>
      {renderContent()}
    </AdminShell>
  );
}