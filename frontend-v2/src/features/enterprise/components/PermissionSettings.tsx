/**
 * PermissionSettings - 权限设置组件
 */

import { useState } from 'react';

import type { TeamMemberRole, PermissionItem, RolePermissionConfig } from '../types';
import { usePermissions, useRolePermissions, useUpdateRolePermissions } from '../hooks/useEnterprise';

interface PermissionSettingsProps {
  accountId: number;
}

const roleLabels: Record<TeamMemberRole, string> = {
  owner: '所有者',
  admin: '管理员',
  member: '成员',
  viewer: '观察者',
};

const roleDescriptions: Record<TeamMemberRole, string> = {
  owner: '拥有所有权限，可以管理企业账号',
  admin: '可以管理团队和查看大部分数据',
  member: '可以使用大部分功能',
  viewer: '只能查看数据，不能修改',
};

/**
 * 权限设置组件
 */
export function PermissionSettings({ accountId }: PermissionSettingsProps): JSX.Element {
  const [activeRole, setActiveRole] = useState<TeamMemberRole>('admin');
  const [hasChanges, setHasChanges] = useState<boolean>(false);

  const { data: permissions, isLoading: permissionsLoading, error: permissionsError } = usePermissions();
  const { data: rolePermissions, isLoading: rolePermissionsLoading } = useRolePermissions(accountId);
  const updateMutation = useUpdateRolePermissions(accountId);

  const [localConfig, setLocalConfig] = useState<Record<TeamMemberRole, string[]>>({
    owner: [],
    admin: [],
    member: [],
    viewer: [],
  });

  // 初始化本地配置
  if (rolePermissions && localConfig[activeRole].length === 0 && !hasChanges) {
    const initialConfig: Record<TeamMemberRole, string[]> = {
      owner: [],
      admin: [],
      member: [],
      viewer: [],
    };
    rolePermissions.forEach((config: RolePermissionConfig) => {
      initialConfig[config.role] = config.permissions;
    });
    setLocalConfig(initialConfig);
  }

  const handleTogglePermission = (permissionCode: string): void => {
    if (activeRole === 'owner') return; // 所有者权限不能修改

    setLocalConfig(prev => {
      const currentPermissions = prev[activeRole];
      const newPermissions = currentPermissions.includes(permissionCode)
        ? currentPermissions.filter(p => p !== permissionCode)
        : [...currentPermissions, permissionCode];
      return {
        ...prev,
        [activeRole]: newPermissions,
      };
    });
    setHasChanges(true);
  };

  const handleSave = (): void => {
    if (activeRole === 'owner') return;

    void updateMutation.mutateAsync({
      role: activeRole,
      permissions: localConfig[activeRole],
    }).then(() => {
      setHasChanges(false);
    });
  };

  const handleReset = (): void => {
    if (!rolePermissions) return;

    const config = rolePermissions.find((p: RolePermissionConfig) => p.role === activeRole);
    if (config) {
      setLocalConfig(prev => ({
        ...prev,
        [activeRole]: config.permissions,
      }));
      setHasChanges(false);
    }
  };

  const groupPermissionsByCategory = (perms: PermissionItem[]): Record<string, PermissionItem[]> => {
    return perms.reduce((acc, perm) => {
      if (!acc[perm.category]) {
        acc[perm.category] = [];
      }
      acc[perm.category].push(perm);
      return acc;
    }, {} as Record<string, PermissionItem[]>);
  };

  const categoryLabels: Record<string, string> = {
    enterprise: '企业管理',
    team: '团队管理',
    contract: '合同审查',
    order: '订单管理',
    analytics: '数据分析',
    setting: '系统设置',
  };

  if (permissionsLoading || rolePermissionsLoading) {
    return (
      <div className="p-6 bg-white rounded-lg shadow-sm">
        <div className="animate-pulse space-y-4">
          <div className="h-8 bg-gray-200 rounded w-1/3" />
          <div className="h-10 bg-gray-200 rounded" />
          <div className="space-y-2">
            <div className="h-12 bg-gray-200 rounded" />
            <div className="h-12 bg-gray-200 rounded" />
          </div>
        </div>
      </div>
    );
  }

  if (permissionsError || !permissions) {
    return (
      <div className="p-6 bg-white rounded-lg shadow-sm">
        <div className="text-red-500">加载权限数据失败</div>
      </div>
    );
  }

  const groupedPermissions = groupPermissionsByCategory(permissions);
  const currentPermissions = localConfig[activeRole];

  return (
    <div className="p-6 bg-white rounded-lg shadow-sm">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-xl font-semibold text-gray-900">权限设置</h2>
          <p className="text-sm text-gray-500 mt-1">管理不同角色的权限配置</p>
        </div>
        {hasChanges && activeRole !== 'owner' && (
          <div className="flex gap-3">
            <button
              onClick={handleReset}
              className="px-4 py-2 text-sm font-medium text-gray-600 bg-gray-100 rounded-md hover:bg-gray-200 transition-colors"
            >
              重置
            </button>
            <button
              onClick={handleSave}
              disabled={updateMutation.isPending}
              className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700 transition-colors disabled:opacity-50"
            >
              {updateMutation.isPending ? '保存中...' : '保存'}
            </button>
          </div>
        )}
      </div>

      {/* 角色选择 */}
      <div className="flex gap-2 mb-6 p-1 bg-gray-100 rounded-lg">
        {(Object.keys(roleLabels) as TeamMemberRole[]).map((role) => (
          <button
            key={role}
            onClick={() => setActiveRole(role)}
            className={`flex-1 px-4 py-2 text-sm font-medium rounded-md transition-colors ${
              activeRole === role
                ? 'bg-white text-gray-900 shadow-sm'
                : 'text-gray-600 hover:text-gray-900'
            }`}
          >
            {roleLabels[role]}
          </button>
        ))}
      </div>

      {/* 角色说明 */}
      <div className="mb-6 p-4 bg-blue-50 rounded-lg">
        <p className="text-sm text-blue-800">
          <span className="font-medium">{roleLabels[activeRole]}</span>：{roleDescriptions[activeRole]}
        </p>
      </div>

      {/* 权限列表 */}
      <div className="space-y-6">
        {Object.entries(groupedPermissions).map(([category, perms]) => (
          <div key={category} className="border-b border-gray-200 last:border-0 pb-6 last:pb-0">
            <h3 className="text-sm font-medium text-gray-700 mb-3">
              {categoryLabels[category] || category}
            </h3>
            <div className="space-y-2">
              {perms.map((permission) => {
                const isChecked = currentPermissions?.includes(permission.code) ||
                  permission.defaultRoles.includes(activeRole);
                const isDisabled = activeRole === 'owner' || permission.defaultRoles.includes('owner');

                return (
                  <label
                    key={permission.id}
                    className={`flex items-start gap-3 p-3 rounded-lg border ${
                      isDisabled
                        ? 'border-gray-100 bg-gray-50 opacity-60'
                        : 'border-gray-200 hover:border-blue-300 cursor-pointer'
                    }`}
                  >
                    <input
                      type="checkbox"
                      checked={isChecked}
                      onChange={() => handleTogglePermission(permission.code)}
                      disabled={isDisabled}
                      className="mt-0.5 h-4 w-4 text-blue-600 rounded border-gray-300 focus:ring-blue-500 disabled:opacity-50"
                    />
                    <div className="flex-1">
                      <div className="flex items-center gap-2">
                        <span className="font-medium text-gray-900 text-sm">{permission.name}</span>
                        {permission.defaultRoles.includes(activeRole) && (
                          <span className="text-xs text-gray-500 bg-gray-100 px-2 py-0.5 rounded">
                            默认
                          </span>
                        )}
                      </div>
                      <p className="text-xs text-gray-500 mt-1">{permission.description}</p>
                    </div>
                  </label>
                );
              })}
            </div>
          </div>
        ))}
      </div>

      {/* 提示 */}
      {activeRole === 'owner' && (
        <div className="mt-6 p-4 bg-yellow-50 rounded-lg">
          <p className="text-sm text-yellow-800">
            所有者角色的权限是固定的，无法修改。
          </p>
        </div>
      )}
    </div>
  );
}