/**
 * 可配置侧边栏 Shell 组件
 * 接受菜单项 + 标题，渲染统一风格的侧边栏
 */

import { useMemo } from 'react';
import { Layout, Menu } from 'antd';
import { useNavigate, useLocation } from 'react-router-dom';
import type { ItemType } from 'antd/es/menu/interface';

const { Sider } = Layout;

export interface SidebarMenuItem {
  key: string;
  label: string;
  icon?: React.ReactNode;
  children?: SidebarMenuItem[];
}

export interface SidebarShellProps {
  title: string;
  subtitle?: string;
  menuItems: SidebarMenuItem[];
  collapsed: boolean;
  onCollapse: (collapsed: boolean) => void;
  selectedKey?: string;
  defaultOpenKeys?: string[];
}

export function SidebarShell({
  title,
  subtitle,
  menuItems,
  collapsed,
  onCollapse,
  selectedKey,
  defaultOpenKeys,
}: SidebarShellProps): JSX.Element {
  const navigate = useNavigate();
  const location = useLocation();

  const effectiveSelectedKey = useMemo(() => {
    if (selectedKey) return selectedKey;
    const currentPath = location.pathname;
    const matched = menuItems.find((item) => {
      if (currentPath.includes(item.key)) return true;
      if (item.children) {
        return item.children.some((child) => currentPath.includes(child.key));
      }
      return false;
    });
    return matched?.key ?? menuItems[0]?.key ?? '';
  }, [selectedKey, location.pathname, menuItems]);

  const antdItems: ItemType[] = useMemo(
    () =>
      menuItems.map((item) => ({
        key: item.key,
        label: item.label,
        icon: item.icon,
        children: item.children?.map((child) => ({
          key: child.key,
          label: child.label,
          icon: child.icon,
        })),
      })),
    [menuItems],
  );

  const handleMenuClick = (info: { key: string }): void => {
    navigate(info.key);
  };

  return (
    <Sider
      collapsible
      collapsed={collapsed}
      onCollapse={onCollapse}
      width={220}
      className="border-r border-slate-200"
      style={{ background: '#fff' }}
    >
      <div className="flex flex-col items-center justify-center h-16 border-b border-slate-100 px-4">
        {collapsed ? (
          <span className="text-lg font-bold text-primary-600">{title.slice(0, 2)}</span>
        ) : (
          <div className="w-full truncate">
            <div className="text-sm font-semibold text-slate-800 truncate">{title}</div>
            {subtitle && (
              <div className="text-xs text-slate-400 truncate">{subtitle}</div>
            )}
          </div>
        )}
      </div>

      <Menu
        mode="inline"
        selectedKeys={[effectiveSelectedKey]}
        defaultOpenKeys={defaultOpenKeys}
        items={antdItems}
        onClick={handleMenuClick}
        style={{ borderInlineEnd: 'none' }}
      />
    </Sider>
  );
}