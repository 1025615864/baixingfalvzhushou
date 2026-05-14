/**
 * 新闻服务管理员 Dashboard
 * 新闻源管理、文章审核、分类管理
 */

import React, { useState } from 'react';
import { LayoutDashboard, Newspaper, GitBranch, Tag, FileCheck } from 'lucide-react';
import { AdminShell } from '@/features/admin-shared/components/AdminShell';
import type { SidebarMenuItem } from '@/features/admin-shared/components/SidebarShell';

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
  { key: 'sources', label: '新闻源管理', icon: React.createElement(GitBranch, { className: 'w-4 h-4' }) },
  { key: 'articles', label: '文章审核', icon: React.createElement(FileCheck, { className: 'w-4 h-4' }) },
  { key: 'categories', label: '分类管理', icon: React.createElement(Tag, { className: 'w-4 h-4' }) },
];

export function NewsAdminPage(): JSX.Element {
  const [activeTab, setActiveTab] = useState<string>('overview');

  const renderContent = () => {
    switch (activeTab) {
      case 'overview':
        return (
          <div className="space-y-6">
            <h2 className="text-xl font-semibold text-slate-800">新闻管理总览</h2>
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              {[
                { label: '今日采集', value: '256', color: 'text-blue-600', bg: 'bg-blue-50' },
                { label: '待审核', value: '12', color: 'text-orange-600', bg: 'bg-orange-50' },
                { label: '已发布', value: '1890', color: 'text-green-600', bg: 'bg-green-50' },
                { label: '新闻源', value: '34', color: 'text-purple-600', bg: 'bg-purple-50' },
              ].map(item => (
                <div key={item.label} className={`${item.bg} rounded-xl p-6`}>
                  <div className={`text-3xl font-bold ${item.color}`}>{item.value}</div>
                  <div className="text-sm text-slate-600 mt-1">{item.label}</div>
                </div>
              ))}
            </div>
          </div>
        );
      case 'sources':
        return <Placeholder title="新闻源管理" icon="📡" text="管理新闻采集来源（RSS、API等），配置爬取规则" />;
      case 'articles':
        return <Placeholder title="文章审核" icon="✅" text="审核待发布的新闻文章，确保内容合规" />;
      case 'categories':
        return <Placeholder title="分类管理" icon="🏷️" text="管理新闻分类标签体系" />;
      default:
        return null;
    }
  };

  return (
    <AdminShell title="新闻管理" subtitle="新闻内容与来源管理" menuItems={menuItems} selectedKey={activeTab}>
      {renderContent()}
    </AdminShell>
  );
}