import React, { Suspense, lazy, useCallback, useState } from 'react';
import { Layout, Typography } from 'antd';

import { Sidebar } from '../components/Sidebar';

const { Content, Header } = Layout;
const { Title } = Typography;

const LazyAdminOverviewPanel = lazy(() =>
  import('../components/AdminOverviewPanel').then(m => ({ default: m.AdminOverviewPanel }))
);
const LazyAdminUsersPanel = lazy(() =>
  import('../components/AdminUsersPanel').then(m => ({ default: m.AdminUsersPanel }))
);
const LazyAdminAIConfigPanel = lazy(() =>
  import('../components/AdminAIConfigPanel').then(m => ({ default: m.AdminAIConfigPanel }))
);
const LazyAdminExportPanel = lazy(() =>
  import('../components/AdminExportPanel').then(m => ({ default: m.AdminExportPanel }))
);
const LazySystemMonitorPanel = lazy(() =>
  import('../components/SystemMonitorPanel').then(m => ({ default: m.SystemMonitorPanel }))
);
const LazyContentModerationPanel = lazy(() =>
  import('../components/ContentModerationPanel').then(m => ({ default: m.ContentModerationPanel }))
);
const LazyLawyerVerificationPanel = lazy(() =>
  import('../components/LawyerVerificationPanel').then(m => ({ default: m.LawyerVerificationPanel }))
);
const LazySystemSettingsPanel = lazy(() =>
  import('../components/SystemSettingsPanel').then(m => ({ default: m.SystemSettingsPanel }))
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
    <div className="bg-white rounded-xl border border-slate-200 p-12 text-center">
      <div className="text-5xl mb-4">{icon}</div>
      <h3 className="text-lg font-semibold text-slate-700 mb-2">{title}</h3>
      <p className="text-slate-400">{text}</p>
    </div>
  );
}

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

      case 'monitor':
        return (
          <Suspense fallback={<AdminSectionSkeleton rows={4} />}>
            <LazySystemMonitorPanel />
          </Suspense>
        );

      case 'ai-config':
      case 'ai-quality':
        return (
          <Suspense fallback={<AdminSectionSkeleton rows={4} />}>
            <LazyAdminAIConfigPanel />
          </Suspense>
        );

      case 'moderation':
        return (
          <Suspense fallback={<AdminSectionSkeleton rows={4} />}>
            <LazyContentModerationPanel />
          </Suspense>
        );

      case 'lawyer-verifications':
        return (
          <Suspense fallback={<AdminSectionSkeleton rows={4} />}>
            <LazyLawyerVerificationPanel />
          </Suspense>
        );

      case 'lawyer-firms':
        return (
          <PlaceholderPanel
            title="律所管理"
            icon="🏢"
            text="律所管理功能可通过 /admin/law-firms 路径访问，建议使用独立页面管理"
          />
        );

      case 'posts':
        return (
          <PlaceholderPanel
            title="帖子管理"
            icon="📋"
            text="帖子管理功能可通过 /admin/posts 路径访问管理界面"
          />
        );

      case 'notifications':
        return (
          <PlaceholderPanel
            title="系统通知"
            icon="🔔"
            text="系统通知管理功能可通过 /admin/notifications 路径访问"
          />
        );

      case 'withdrawals':
        return (
          <PlaceholderPanel
            title="提现管理"
            icon="💰"
            text="提现管理功能可通过 /admin/withdrawals 路径访问"
          />
        );

      case 'payment-callbacks':
        return (
          <PlaceholderPanel
            title="支付回调"
            icon="💳"
            text="支付回调管理功能可通过 /admin/payment/callbacks 路径访问"
          />
        );

      case 'payment-settlement':
        return (
          <PlaceholderPanel
            title="支付结算"
            icon="📊"
            text="支付结算功能可通过 /admin/payment/settlement 路径访问"
          />
        );

      case 'document-templates':
        return (
          <PlaceholderPanel
            title="文档模板"
            icon="📄"
            text="文档模板管理功能可通过 /admin/document-templates 路径访问"
          />
        );

      case 'consultation-templates':
        return (
          <PlaceholderPanel
            title="咨询模板"
            icon="💬"
            text="咨询模板管理功能可通过 /admin/consultation-templates 路径访问"
          />
        );

      case 'knowledge':
        return (
          <PlaceholderPanel
            title="知识库管理"
            icon="📚"
            text="知识库管理功能可通过 /admin/knowledge 独立页面访问"
          />
        );

      case 'faq':
        return (
          <PlaceholderPanel
            title="FAQ 管理"
            icon="❓"
            text="FAQ 管理功能可通过 /admin/faq 独立页面访问"
          />
        );

      case 'news-sources':
        return (
          <PlaceholderPanel
            title="新闻源管理"
            icon="📰"
            text="新闻源管理功能可通过 /admin/news/sources 独立页面访问"
          />
        );

      case 'settings':
        return (
          <Suspense fallback={<AdminSectionSkeleton rows={4} />}>
            <LazySystemSettingsPanel />
          </Suspense>
        );

      case 'export':
        return (
          <Suspense fallback={<AdminSectionSkeleton rows={3} />}>
            <LazyAdminExportPanel />
          </Suspense>
        );

      case 'analytics':
        return (
          <PlaceholderPanel
            title="数据统计"
            icon="📈"
            text="详细统计功能可通过独立的数据看板页面访问"
          />
        );

      case 'content':
        return (
          <PlaceholderPanel
            title="内容管理"
            icon="📝"
            text="可使用左侧菜单中的具体模块（帖子管理、知识库管理、FAQ管理等）进行内容管理"
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
        <Content className="m-6 p-6 bg-white rounded-lg shadow-sm">
          {renderContent()}
        </Content>
      </Layout>
    </Layout>
  );
};