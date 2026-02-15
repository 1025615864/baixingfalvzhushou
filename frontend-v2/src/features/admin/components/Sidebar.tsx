/**
 * Sidebar 组件 - 管理后台侧边栏
 */

import React from 'react';
import { Layout, Menu } from 'antd';
import {
  DashboardOutlined,
  TeamOutlined,
  FileTextOutlined,
  SettingOutlined,
  BarChartOutlined,
  ExportOutlined,
} from '@ant-design/icons';

const { Sider } = Layout;

/** 侧边栏Props */
interface SidebarProps {
  collapsed: boolean;
  onCollapse: (collapsed: boolean) => void;
  selectedKey: string;
  onSelect: (key: string) => void;
}

/** 菜单项配置 */
const MENU_ITEMS = [
  {
    key: 'dashboard',
    icon: <DashboardOutlined />,
    label: '概览',
  },
  {
    key: 'users',
    icon: <TeamOutlined />,
    label: '用户管理',
  },
  {
    key: 'content',
    icon: <FileTextOutlined />,
    label: '内容管理',
  },
  {
    key: 'analytics',
    icon: <BarChartOutlined />,
    label: '数据统计',
  },
  {
    key: 'export',
    icon: <ExportOutlined />,
    label: '数据导出',
  },
  {
    key: 'settings',
    icon: <SettingOutlined />,
    label: '系统设置',
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
    <Sider
      collapsible
      collapsed={collapsed}
      onCollapse={onCollapse}
      theme="light"
      style={{
        boxShadow: '2px 0 8px rgba(0,0,0,0.06)',
        zIndex: 10,
      }}
    >
      {/* Logo区域 */}
      <div
        className="h-16 flex items-center justify-center border-b border-gray-200"
        style={{
          background: 'linear-gradient(90deg, #1890ff 0%, #36cfc9 100%)',
        }}
      >
        <span className="text-white font-bold text-lg">
          {collapsed ? '管' : '管理后台'}
        </span>
      </div>

      {/* 菜单 */}
      <Menu
        mode="inline"
        selectedKeys={[selectedKey]}
        items={MENU_ITEMS}
        onClick={({ key }) => onSelect(key)}
        style={{ borderRight: 0 }}
      />

      {/* 版本信息 */}
      {!collapsed && (
        <div className="absolute bottom-4 left-0 right-0 text-center text-xs text-gray-400">
          <div>百姓助手 v2.0</div>
          <div>Admin Panel</div>
        </div>
      )}
    </Sider>
  );
};