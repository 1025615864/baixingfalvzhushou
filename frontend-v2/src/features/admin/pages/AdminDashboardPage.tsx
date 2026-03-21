/**
 * AdminDashboardPage 页面 - 管理后台首页
 */

import React, { Suspense, lazy, useCallback, useState } from 'react';
import { BarChartOutlined, DashboardOutlined, FileTextOutlined } from '@ant-design/icons';
import { Card, Layout, Typography } from 'antd';

import { Sidebar } from '../components/Sidebar';

const { Content, Header } = Layout;
const { Title } = Typography;

const LazyAdminOverviewPanel = lazy(() =>
  import('../components/AdminOverviewPanel').then((module) => ({ default: module.AdminOverviewPanel }))
);
const LazyAdminUsersPanel = lazy(() =>
  import('../components/AdminUsersPanel').then((module) => ({ default: module.AdminUsersPanel }))
);
const LazyAdminAIConfigPanel = lazy(() =>
  import('../components/AdminAIConfigPanel').then((module) => ({ default: module.AdminAIConfigPanel }))
);
const LazyAdminExportPanel = lazy(() =>
  import('../components/AdminExportPanel').then((module) => ({ default: module.AdminExportPanel }))
);

function AdminSectionSkeleton({ rows = 3 }: { rows?: number }): JSX.Element {
  return (
    <div className="space-y-4">
      {Array.from({ length: rows }).map((_, index) => (
        <div key={index} className="h-24 animate-pulse rounded-lg bg-slate-100" />
      ))}
    </div>
  );
}

function PlaceholderPanel({ title, icon, text }: { title: string; icon: React.ReactNode; text: string }): JSX.Element {
  return (
    <Card title={title} className="shadow-sm">
      <div className="p-8 text-center text-gray-400">
        {icon}
        <p className="mt-4">{text}</p>
      </div>
    </Card>
  );
}

/**
 * 管理后台首页组件
 */
export const AdminDashboardPage: React.FC = () => {
  const [sidebarCollapsed, setSidebarCollapsed] = useState<boolean>(false);
  const [activeTab, setActiveTab] = useState<string>('dashboard');

  const handleMenuSelect = useCallback((key: string) => {
    setActiveTab(key);
  }, []);

  const renderContent = () => {
    switch (activeTab) {
      case 'dashboard':
        return (
          <Suspense fallback={<AdminSectionSkeleton rows={3} />}>
            <LazyAdminOverviewPanel onNavigate={setActiveTab} />
          </Suspense>
        );
      case 'users':
        return (
          <Suspense fallback={<AdminSectionSkeleton rows={4} />}>
            <LazyAdminUsersPanel />
          </Suspense>
        );
      case 'ai-config':
        return (
          <Suspense fallback={<AdminSectionSkeleton rows={4} />}>
            <LazyAdminAIConfigPanel />
          </Suspense>
        );
      case 'analytics':
        return (
          <PlaceholderPanel
            title="数据统计"
            icon={<BarChartOutlined style={{ fontSize: 48 }} />}
            text="详细统计图表功能开发中..."
          />
        );
      case 'export':
        return (
          <Suspense fallback={<AdminSectionSkeleton rows={3} />}>
            <LazyAdminExportPanel />
          </Suspense>
        );
      case 'content':
        return (
          <PlaceholderPanel
            title="内容管理"
            icon={<FileTextOutlined style={{ fontSize: 48 }} />}
            text="内容管理功能开发中..."
          />
        );
      case 'settings':
        return (
          <PlaceholderPanel
            title="系统设置"
            icon={<DashboardOutlined style={{ fontSize: 48 }} />}
            text="系统设置功能开发中..."
          />
        );
      default:
        return (
          <Suspense fallback={<AdminSectionSkeleton rows={3} />}>
            <LazyAdminOverviewPanel onNavigate={setActiveTab} />
          </Suspense>
        );
    }
  };

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Sidebar
        collapsed={sidebarCollapsed}
        onCollapse={setSidebarCollapsed}
        selectedKey={activeTab}
        onSelect={handleMenuSelect}
      />
      <Layout>
        <Header className="bg-white shadow-sm px-6 flex items-center">
          <Title level={4} className="!m-0">
            管理后台
          </Title>
        </Header>
        <Content className="m-6 p-6 bg-white rounded-lg shadow-sm">{renderContent()}</Content>
      </Layout>
    </Layout>
  );
};
