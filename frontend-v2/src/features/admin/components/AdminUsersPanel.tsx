import { Suspense, lazy, useCallback, useState } from 'react';
import { Card, message } from 'antd';

import { useToggleUserActive, useUpdateUserRole, useUsers } from '../hooks/useAdmin';
import type { UserListItem, UserRole } from '../types';

const LazyUserTable = lazy(() => import('./UserTable').then((module) => ({ default: module.UserTable })));
const LazyUserEditDialog = lazy(() => import('./UserEditDialog').then((module) => ({ default: module.UserEditDialog })));

function AdminUsersSkeleton({ rows = 4 }: { rows?: number }): JSX.Element {
  return (
    <div className="space-y-4">
      {Array.from({ length: rows }).map((_, index) => (
        <div key={index} className="h-24 animate-pulse rounded-lg bg-slate-100" />
      ))}
    </div>
  );
}

export function AdminUsersPanel(): JSX.Element {
  const [userPagination, setUserPagination] = useState({
    current: 1,
    pageSize: 20,
  });
  const [keyword] = useState<string>('');
  const [editingUser, setEditingUser] = useState<UserListItem | null>(null);
  const [editDialogVisible, setEditDialogVisible] = useState<boolean>(false);

  const {
    data: usersData,
    isLoading: usersLoading,
    refetch: refetchUsers,
  } = useUsers({
    page: userPagination.current,
    pageSize: userPagination.pageSize,
    keyword: keyword || undefined,
  });

  const toggleUserActiveMutation = useToggleUserActive();
  const updateUserRoleMutation = useUpdateUserRole();

  const handlePageChange = useCallback((page: number, pageSize: number) => {
    setUserPagination({ current: page, pageSize });
  }, []);

  const handleToggleUserActive = useCallback(
    (userId: number, currentStatus: boolean) => {
      void (async () => {
        try {
          await toggleUserActiveMutation.mutateAsync({ userId });
          void message.success(`用户已${currentStatus ? '禁用' : '启用'}`);
          void refetchUsers();
        } catch {
          void message.error('操作失败，请重试');
        }
      })();
    },
    [toggleUserActiveMutation, refetchUsers]
  );

  const handleEditRole = useCallback((user: UserListItem) => {
    setEditingUser(user);
    setEditDialogVisible(true);
  }, []);

  const handleSaveRole = useCallback(
    (userId: number, newRole: UserRole) => {
      void (async () => {
        try {
          await updateUserRoleMutation.mutateAsync({ userId, role: newRole });
          void message.success('用户角色已更新');
          setEditDialogVisible(false);
          setEditingUser(null);
          void refetchUsers();
        } catch {
          void message.error('更新角色失败，请重试');
        }
      })();
    },
    [updateUserRoleMutation, refetchUsers]
  );

  const handleCancelEdit = useCallback(() => {
    setEditDialogVisible(false);
    setEditingUser(null);
  }, []);

  return (
    <>
      <Card title="用户管理" className="shadow-sm">
        <Suspense fallback={<AdminUsersSkeleton rows={4} />}>
          <LazyUserTable
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
        </Suspense>
      </Card>

      {editDialogVisible && (
        <Suspense fallback={null}>
          <LazyUserEditDialog
            user={editingUser}
            visible={editDialogVisible}
            onCancel={handleCancelEdit}
            onConfirm={handleSaveRole}
            loading={updateUserRoleMutation.isPending}
          />
        </Suspense>
      )}
    </>
  );
}
