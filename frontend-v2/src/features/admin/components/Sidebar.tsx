/**
 * Sidebar 组件 - 管理后台侧边栏
 * 使用 Tailwind CSS 风格
 */

import React from 'react';
import {
  Home,
  Users,
  FileText,
  Settings,
  BarChart3,
  Activity,
  AlertTriangle,
  MessageSquare,
  Shield,
  Wallet,
  ListOrdered,
  Bell,
  Search,
  BookOpen,
  Monitor,
  ChevronLeft,
  ChevronRight,
  type LucideIcon,
} from 'lucide-react';

/** 侧边栏Props */
interface SidebarProps {
  collapsed: boolean;
  onCollapse: (collapsed: boolean) => void;
  selectedKey: string;
  onSelect: (key: string) => void;
}

/** 菜单项配置 */
interface MenuItem {
  key: string;
  icon: LucideIcon;
  label: string;
  path: string;
}

const MENU_ITEMS: MenuItem[] = [
  {
    key: 'dashboard',
    icon: Home,
    label: '概览',
    path: '/admin',
  },
  {
    key: 'monitor',
    icon: Monitor,
    label: '系统监控',
    path: '/admin/monitor',
  },
  {
    key: 'ai-quality',
    icon: Activity,
    label: 'AI质量监控',
    path: '/admin/ai-quality',
  },
  {
    key: 'moderation',
    icon: Shield,
    label: '内容审核',
    path: '/admin/moderation',
  },
  {
    key: 'lawyer-verifications',
    icon: Users,
    label: '律师认证',
    path: '/admin/lawyer/verifications',
  },
  {
    key: 'lawyer-firms',
    icon: Users,
    label: '律所管理',
    path: '/admin/lawyer/firms',
  },
  {
    key: 'posts',
    icon: ListOrdered,
    label: '帖子管理',
    path: '/admin/posts',
  },
  {
    key: 'notifications',
    icon: Bell,
    label: '系统通知',
    path: '/admin/notifications',
  },
  {
    key: 'withdrawals',
    icon: Wallet,
    label: '提现管理',
    path: '/admin/withdrawals',
  },
  {
    key: 'payment-callbacks',
    icon: BarChart3,
    label: '支付回调',
    path: '/admin/payment/callbacks',
  },
  {
    key: 'payment-settlement',
    icon: Wallet,
    label: '支付结算',
    path: '/admin/payment/settlement',
  },
  {
    key: 'document-templates',
    icon: FileText,
    label: '文档模板',
    path: '/admin/document-templates',
  },
  {
    key: 'consultation-templates',
    icon: MessageSquare,
    label: '咨询模板',
    path: '/admin/consultation-templates',
  },
  {
    key: 'knowledge',
    icon: BookOpen,
    label: '知识库管理',
    path: '/admin/knowledge',
  },
  {
    key: 'faq',
    icon: AlertTriangle,
    label: 'FAQ管理',
    path: '/admin/faq',
  },
  {
    key: 'news-sources',
    icon: Search,
    label: '新闻源管理',
    path: '/admin/news/sources',
  },
  {
    key: 'settings',
    icon: Settings,
    label: '系统设置',
    path: '/admin/settings',
  },
];

/**
 * 侧边栏组件
 */
export const Sidebar: React.FC<SidebarProps> = ({
  collapsed,
  onCollapse,
  selectedKey,
  onSelect,
}) => {
  return (
    <aside
      className={`
        relative bg-white border-r border-slate-200 flex flex-col
        transition-all duration-300 ease-in-out
        ${collapsed ? 'w-20' : 'w-64'}
      `}
      style={{ minHeight: '100vh' }}
    >
      {/* Logo区域 */}
      <div
        className="h-16 flex items-center justify-center border-b border-slate-200 bg-gradient-to-r from-primary-500 to-cyan-500"
      >
        <span className="text-white font-bold text-lg">
          {collapsed ? '管' : '管理后台'}
        </span>
      </div>

      {/* 菜单列表 */}
      <nav className="flex-1 py-4 overflow-y-auto">
        <ul className="space-y-1 px-3">
          {MENU_ITEMS.map((item) => {
            const Icon = item.icon;
            const isSelected = selectedKey === item.key;
            
            return (
              <li key={item.key}>
                <button
                  onClick={() => onSelect(item.key)}
                  className={`
                    w-full flex items-center gap-3 px-3 py-2.5 rounded-xl
                    transition-all duration-200 text-left
                    ${isSelected
                      ? 'bg-primary-50 text-primary-600 font-medium'
                      : 'text-slate-600 hover:bg-slate-50 hover:text-slate-900'
                    }
                  `}
                  title={collapsed ? item.label : undefined}
                >
                  <Icon className={`w-5 h-5 flex-shrink-0 ${isSelected ? 'text-primary-600' : 'text-slate-400'}`} />
                  {!collapsed && (
                    <span className="truncate text-sm">{item.label}</span>
                  )}
                </button>
              </li>
            );
          })}
        </ul>
      </nav>

      {/* 折叠按钮 */}
      <button
        onClick={() => onCollapse(!collapsed)}
        className="
          absolute top-20 -right-3 w-6 h-6
          bg-white border border-slate-200 rounded-full
          flex items-center justify-center
          shadow-sm hover:shadow-md transition-shadow
          text-slate-400 hover:text-slate-600
        "
      >
        {collapsed ? (
          <ChevronRight className="w-4 h-4" />
        ) : (
          <ChevronLeft className="w-4 h-4" />
        )}
      </button>

      {/* 版本信息 */}
      {!collapsed && (
        <div className="p-4 border-t border-slate-200 text-center">
          <div className="text-xs text-slate-400">百姓助手 v2.0</div>
          <div className="text-xs text-slate-300 mt-1">Admin Panel</div>
        </div>
      )}
    </aside>
  );
};