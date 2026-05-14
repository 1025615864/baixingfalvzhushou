/**
 * 客服工作台 Dashboard
 * 反馈处理、支持工单、申诉处理
 */

import React, { useState } from 'react';
import { LayoutDashboard, Headphones, MessageSquare, FileWarning, AlertTriangle } from 'lucide-react';
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
  { key: 'overview', label: '工作台总览', icon: React.createElement(LayoutDashboard, { className: 'w-4 h-4' }) },
  { key: 'tickets', label: '支持工单', icon: React.createElement(MessageSquare, { className: 'w-4 h-4' }) },
  { key: 'feedback', label: '用户反馈', icon: React.createElement(FileWarning, { className: 'w-4 h-4' }) },
  { key: 'appeals', label: '申诉处理', icon: React.createElement(AlertTriangle, { className: 'w-4 h-4' }) },
];

export function CSAdminPage(): JSX.Element {
  const [activeTab, setActiveTab] = useState<string>('overview');

  const renderContent = () => {
    switch (activeTab) {
      case 'overview':
        return (
          <div className="space-y-6">
            <h2 className="text-xl font-semibold text-slate-800">客服工作台</h2>
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              {[
                { label: '待处理工单', value: '8', color: 'text-orange-600', bg: 'bg-orange-50' },
                { label: '今日反馈', value: '23', color: 'text-blue-600', bg: 'bg-blue-50' },
                { label: '待处理申诉', value: '2', color: 'text-red-600', bg: 'bg-red-50' },
                { label: '已解决', value: '156', color: 'text-green-600', bg: 'bg-green-50' },
              ].map(item => (
                <div key={item.label} className={`${item.bg} rounded-xl p-6`}>
                  <div className={`text-3xl font-bold ${item.color}`}>{item.value}</div>
                  <div className="text-sm text-slate-600 mt-1">{item.label}</div>
                </div>
              ))}
            </div>
          </div>
        );
      case 'tickets':
        return <Placeholder title="支持工单" icon="🎫" text="处理用户提交的技术支持和问题工单" />;
      case 'feedback':
        return <Placeholder title="用户反馈" icon="📝" text="查看和处理用户反馈与建议" />;
      case 'appeals':
        return <Placeholder title="申诉处理" icon="⚖️" text="处理用户对处罚、封禁等的申诉" />;
      default:
        return null;
    }
  };

  return (
    <AdminShell title="客服工作台" subtitle="反馈处理与用户支持" menuItems={menuItems} selectedKey={activeTab}>
      {renderContent()}
    </AdminShell>
  );
}