/**
 * AdminDashboardPage 页面 - 管理后台首页
 */

import React, { useState, useCallback } from 'react';
import { Layout, message, Typography, Button, Space, Card } from 'antd';
import {
  DashboardOutlined,
  TeamOutlined,
  FileTextOutlined,
  BarChartOutlined,
  ExportOutlined,
  DownloadOutlined,
} from '@ant-design/icons';

import { Sidebar } from '../components/Sidebar';
import { StatsCards } from '../components/StatsCards';
import { UserTable } from '../components/UserTable';
import { UserEditDialog } from '../components/UserEditDialog';
import {
  useUsers,
  useToggleUserActive,
  useUpdateUserRole,
  useAdminStats,
  useExportUsers,
  useExportPosts,
  useExportNews,
  useExportLawfirms,
} from '../hooks/useAdmin';
import type { UserListItem, UserRole } from '../types';

const { Content, Header } = Layout;
const { Title } = Typography;

/**
 * 数据导出卡片组件
 */
const ExportCard: React.FC<{
  title: string;
  description: string;
  icon: React.ReactNode;
  onExport: () => void;
  loading: boolean;
}> = ({ title, description, icon, onExport, loading }) => (
  <Card className="h-full">
    <div className="flex items-start justify-between">
      <div>
        <div className="flex items-center gap-2 mb-2">
          {icon}
          <span className="font-medium">{title}</span>
        </div>
        <p className="text-gray-500 text-sm mb-4">{description}</p>
        <Button
          type="primary"
          icon={<DownloadOutlined />}
          onClick={onExport}
          loading={loading}
          size="small"
        >
          导出 CSV
        </Button>
      </div>
    </div>
  </Card>
);

/**
 * 管理后台首页组件
 */
export const AdminDashboardPage: React.FC = () => {
  // ============ 状态管理 ============
  const [sidebarCollapsed, setSidebarCollapsed] = useState<boolean>(false);
  const [activeTab, setActiveTab] = useState<string>('dashboard');
  const [userPagination, setUserPagination] = useState({
    current: 1,
    pageSize: 20,
  });
  const [keyword, _setKeyword] = useState<string>('');
  const [editingUser, setEditingUser] = useState<UserListItem | null>(null);
  const [editDialogVisible, setEditDialogVisible] = useState<boolean>(false);

  // ============ 数据获取 ============
  const {
    data: usersData,
    isLoading: usersLoading,
    refetch: refetchUsers,
  } = useUsers({
    page: userPagination.current,
    pageSize: userPagination.pageSize,
    keyword: keyword || undefined,
  });

  const { data: statsData, isLoading: statsLoading } = useAdminStats();

  // ============ 数据操作 ============
  const toggleUserActiveMutation = useToggleUserActive();
  const updateUserRoleMutation = useUpdateUserRole();
  const exportUsersMutation = useExportUsers();
  const exportPostsMutation = useExportPosts();
  const exportNewsMutation = useExportNews();
  const exportLawfirmsMutation = useExportLawfirms();

  // ============ 事件处理 ============

  /** 处理页码变化 */
  const handlePageChange = useCallback((page: number, pageSize: number) => {
    setUserPagination({ current: page, pageSize });
  }, []);


  /** 处理切换用户状态 */
  const handleToggleUserActive = useCallback(
    (userId: number, currentStatus: boolean) => {
      void (async () => {
        try {
          await toggleUserActiveMutation.mutateAsync({ userId });
          void message.success(`用户已${currentStatus ? '禁用' : '启用'}`);
          void refetchUsers();
        } catch (error) {
          void message.error('操作失败，请重试');
        }
      })();
    },
    [toggleUserActiveMutation, refetchUsers]
  );

  /** 处理编辑角色 */
  const handleEditRole = useCallback((user: UserListItem) => {
    setEditingUser(user);
    setEditDialogVisible(true);
  }, []);

  /** 处理保存角色 */
  const handleSaveRole = useCallback(
    (userId: number, newRole: UserRole) => {
      void (async () => {
        try {
          await updateUserRoleMutation.mutateAsync({ userId, role: newRole });
          void message.success('用户角色已更新');
          setEditDialogVisible(false);
          setEditingUser(null);
          void refetchUsers();
        } catch (error) {
          void message.error('更新角色失败，请重试');
        }
      })();
    },
    [updateUserRoleMutation, refetchUsers]
  );

  /** 处理取消编辑 */
  const handleCancelEdit = useCallback(() => {
    setEditDialogVisible(false);
    setEditingUser(null);
  }, []);

  /** 处理菜单选择 */
  const handleMenuSelect = useCallback((key: string) => {
    setActiveTab(key);
  }, []);

  // ============ 渲染内容 ============

  /** 渲染概览页面 */
  const renderDashboard = () => (
    <div className="space-y-6">
      <StatsCards stats={statsData || null} loading={statsLoading} />
      
      <Card title="快速入口" className="mt-6">
        <Space size="large">
          <Button
            type="primary"
            icon={<TeamOutlined />}
            onClick={() => setActiveTab('users')}
          >
            用户管理
          </Button>
          <Button
            icon={<BarChartOutlined />}
            onClick={() => setActiveTab('analytics')}
          >
            查看统计
          </Button>
          <Button
            icon={<ExportOutlined />}
            onClick={() => setActiveTab('export')}
          >
            数据导出
          </Button>
        </Space>
      </Card>

      <Card title="系统状态" className="mt-6">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="p-4 bg-green-50 rounded-lg">
            <div className="text-green-600 font-medium">系统运行正常</div>
            <div className="text-green-400 text-sm">所有服务正常</div>
          </div>
          <div className="p-4 bg-blue-50 rounded-lg">
            <div className="text-blue-600 font-medium">API 响应正常</div>
            <div className="text-blue-400 text-sm">平均响应时间: 45ms</div>
          </div>
          <div className="p-4 bg-purple-50 rounded-lg">
            <div className="text-purple-600 font-medium">数据库连接正常</div>
            <div className="text-purple-400 text-sm">连接池: 8/20</div>
          </div>
        </div>
      </Card>
    </div>
  );

  /** 渲染用户管理页面 */
  const renderUsers = () => (
    <Card title="用户管理" className="shadow-sm">
      <UserTable
        users={usersData?.users || []}
        loading={usersLoading}
        pagination={{
          current: userPagination.current,
          pageSize: userPagination.pageSize,
          total: usersData?.total || 0,
        }}
        onPageChange={handlePageChange}
        onToggleActive={handleToggleUserActive}
        onEditRole={handleEditRole}
      />
    </Card>
  );

  /** 渲染数据统计页面 */
  const renderAnalytics = () => (
    <Card title="数据统计" className="shadow-sm">
      <StatsCards stats={statsData || null} loading={statsLoading} />
      <div className="mt-8 p-8 text-center text-gray-400">
        <BarChartOutlined style={{ fontSize: 48 }} />
        <p className="mt-4">详细统计图表功能开发中...</p>
      </div>
    </Card>
  );

  /** 渲染数据导出页面 */
  const renderExport = () => (
    <div className="space-y-6">
      <Title level={4}>数据导出</Title>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <ExportCard
          title="导出用户数据"
          description="导出所有用户的基本信息，包含用户名、邮箱、角色等字段"
          icon={<TeamOutlined />}
          onExport={() => exportUsersMutation.mutate()}
          loading={exportUsersMutation.isPending}
        />
        <ExportCard
          title="导出帖子数据"
          description="导出论坛所有帖子的标题、作者、浏览量等信息"
          icon={<FileTextOutlined />}
          onExport={() => exportPostsMutation.mutate()}
          loading={exportPostsMutation.isPending}
        />
        <ExportCard
          title="导出新闻数据"
          description="导出新闻资讯的标题、分类、浏览量等统计信息"
          icon={<DashboardOutlined />}
          onExport={() => exportNewsMutation.mutate()}
          loading={exportNewsMutation.isPending}
        />
        <ExportCard
          title="导出律所数据"
          description="导出所有律所的名称、地址、评分等信息"
          icon={<DashboardOutlined />}
          onExport={() => exportLawfirmsMutation.mutate()}
          loading={exportLawfirmsMutation.isPending}
        />
      </div>
    </div>
  );

  /** 渲染内容管理页面 */
  const renderContentManagement = () => (
    <Card title="内容管理" className="shadow-sm">
      <div className="p-8 text-center text-gray-400">
        <FileTextOutlined style={{ fontSize: 48 }} />
        <p className="mt-4">内容管理功能开发中...</p>
      </div>
    </Card>
  );

  /** 渲染系统设置页面 */
  const renderSettings = () => (
    <Card title="系统设置" className="shadow-sm">
      <div className="p-8 text-center text-gray-400">
        <DashboardOutlined style={{ fontSize: 48 }} />
        <p className="mt-4">系统设置功能开发中...</p>
      </div>
    </Card>
  );

  /** 根据当前标签渲染内容 */
  const renderContent = () => {
    switch (activeTab) {
      case 'dashboard':
        return renderDashboard();
      case 'users':
        return renderUsers();
      case 'analytics':
        return renderAnalytics();
      case 'export':
        return renderExport();
      case 'content':
        return renderContentManagement();
      case 'settings':
        return renderSettings();
      default:
        return renderDashboard();
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

      {/* 用户编辑对话框 */}
      <UserEditDialog
        user={editingUser}
        visible={editDialogVisible}
        onCancel={handleCancelEdit}
        onConfirm={handleSaveRole}
        loading={updateUserRoleMutation.isPending}
      />
    </Layout>
  );
};