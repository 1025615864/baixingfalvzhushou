/**
 * 管理后台通用布局 Shell
 * 提供统一的 Sider + Header + Content 布局
 */

import React, { useCallback, useState } from 'react';
import { Layout, Typography } from 'antd';
import { SidebarShell, type SidebarMenuItem } from './SidebarShell';

const { Content, Header } = Layout;
const { Title } = Typography;

export interface AdminShellProps {
  title: string;
  subtitle?: string;
  menuItems: SidebarMenuItem[];
  defaultOpenKeys?: string[];
  selectedKey?: string;
  children: React.ReactNode;
}

export function AdminShell({
  title,
  subtitle,
  menuItems,
  defaultOpenKeys,
  selectedKey,
  children,
}: AdminShellProps): JSX.Element {
  const [collapsed, setCollapsed] = useState<boolean>(false);

  const handleCollapse = useCallback((val: boolean) => {
    setCollapsed(val);
  }, []);

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <SidebarShell
        title={title}
        subtitle={subtitle}
        menuItems={menuItems}
        collapsed={collapsed}
        onCollapse={handleCollapse}
        selectedKey={selectedKey}
        defaultOpenKeys={defaultOpenKeys}
      />
      <Layout>
        <Header className="bg-white shadow-sm px-6 flex items-center justify-between">
          <Title level={4} className="!m-0">
            {title}
          </Title>
        </Header>
        <Content className="m-6 p-6 bg-white rounded-lg shadow-sm min-h-[calc(100vh-120px)]">
          {children}
        </Content>
      </Layout>
    </Layout>
  );
}