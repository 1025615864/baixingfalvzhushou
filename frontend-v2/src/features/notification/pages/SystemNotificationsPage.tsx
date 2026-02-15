/**
 * System Notifications Page
 * 系统通知管理页面（管理员用）
 */

import { useState } from 'react';
import { Plus, Pencil, Trash2, Send, RotateCcw, Search, Bell, Users } from 'lucide-react';

import { Card, Input, Button, Badge, Pagination } from '@/components/ui';

import {
  useSystemNotifications,
  useCreateSystemNotification,
  useUpdateSystemNotification,
  useDeleteSystemNotification,
  usePublishSystemNotification,
  useRevokeSystemNotification,
} from '../hooks/useSystemNotifications';
import type { SystemNotification, NotificationTargetType } from '../types';

const TARGET_TYPE_LABELS: Record<NotificationTargetType, string> = {
  all: '全部用户',
  users: '普通用户',
  lawyers: '律师',
  admins: '管理员',
  specific: '指定用户',
};

/**
 * 系统通知管理页面
 */
export function SystemNotificationsPage(): JSX.Element {
  const [page, setPage] = useState(1);
  const [pageSize] = useState(20);
  const [keyword, setKeyword] = useState('');
  const [statusFilter, setStatusFilter] = useState<boolean | null>(null);
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  const [isEditModalOpen, setIsEditModalOpen] = useState(false);
  const [editingNotification, setEditingNotification] = useState<SystemNotification | null>(null);

  // 表单状态
  const [formData, setFormData] = useState({
    title: '',
    content: '',
    targetType: 'all' as NotificationTargetType,
    targetIds: '',
    expiresAt: '',
  });

  // 数据查询
  const { data: notificationsData, isLoading } = useSystemNotifications({
    page,
    pageSize,
    keyword: keyword || undefined,
    isPublished: statusFilter ?? undefined,
  });

  // Mutations
  const createMutation = useCreateSystemNotification();
  const updateMutation = useUpdateSystemNotification();
  const deleteMutation = useDeleteSystemNotification();
  const publishMutation = usePublishSystemNotification();
  const revokeMutation = useRevokeSystemNotification();

  const notifications = notificationsData?.items ?? [];
  const totalPages = Math.ceil((notificationsData?.total ?? 0) / pageSize);

  // 处理创建
  const handleCreate = (): void => {
    createMutation.mutate(
      {
        title: formData.title,
        content: formData.content,
        targetType: formData.targetType,
        targetIds: formData.targetIds ? formData.targetIds.split(',').map((id) => id.trim()) : undefined,
        expiresAt: formData.expiresAt || undefined,
      },
      {
        onSuccess: () => {
          setIsCreateModalOpen(false);
          resetForm();
        },
      }
    );
  };

  // 处理编辑
  const handleEdit = (notification: SystemNotification): void => {
    setEditingNotification(notification);
    setFormData({
      title: notification.title,
      content: notification.content,
      targetType: notification.targetType,
      targetIds: notification.targetIds?.join(', ') ?? '',
      expiresAt: notification.expiresAt ?? '',
    });
    setIsEditModalOpen(true);
  };

  // 处理更新
  const handleUpdate = (): void => {
    if (!editingNotification) return;
    updateMutation.mutate(
      {
        id: editingNotification.id,
        request: {
          title: formData.title,
          content: formData.content,
          targetType: formData.targetType,
          targetIds: formData.targetIds ? formData.targetIds.split(',').map((id) => id.trim()) : undefined,
          expiresAt: formData.expiresAt || null,
        },
      },
      {
        onSuccess: () => {
          setIsEditModalOpen(false);
          setEditingNotification(null);
          resetForm();
        },
      }
    );
  };

  // 处理删除
  const handleDelete = (id: string): void => {
    if (!window.confirm('确定要删除这条通知吗？')) return;
    deleteMutation.mutate(id);
  };

  // 处理发布
  const handlePublish = (id: string): void => {
    if (!window.confirm('确定要发布这条通知吗？')) return;
    publishMutation.mutate(id);
  };

  // 处理撤销
  const handleRevoke = (id: string): void => {
    if (!window.confirm('确定要撤销这条通知吗？')) return;
    revokeMutation.mutate(id);
  };

  // 重置表单
  const resetForm = (): void => {
    setFormData({
      title: '',
      content: '',
      targetType: 'all',
      targetIds: '',
      expiresAt: '',
    });
  };

  return (
    <div className="container mx-auto py-6">
      {/* 页面头部 */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">系统通知管理</h1>
          <p className="text-slate-600 mt-1">创建和管理系统通知</p>
        </div>
        <Button onClick={() => setIsCreateModalOpen(true)}>
          <Plus className="h-4 w-4 mr-1" />
          新建通知
        </Button>
      </div>

      {/* 筛选栏 */}
      <Card className="mb-6">
        <div className="p-4 flex flex-wrap items-center gap-4">
          <div className="flex items-center gap-2">
            <Bell className="h-4 w-4 text-slate-500" />
            <span className="text-sm text-slate-700">状态：</span>
            <div className="flex gap-2">
              <Button
                variant={statusFilter === null ? 'primary' : 'ghost'}
                size="sm"
                onClick={() => setStatusFilter(null)}
              >
                全部
              </Button>
              <Button
                variant={statusFilter === true ? 'primary' : 'ghost'}
                size="sm"
                onClick={() => setStatusFilter(true)}
              >
                已发布
              </Button>
              <Button
                variant={statusFilter === false ? 'primary' : 'ghost'}
                size="sm"
                onClick={() => setStatusFilter(false)}
              >
                未发布
              </Button>
            </div>
          </div>
          <div className="flex-1 min-w-[200px] ml-auto">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
              <Input
                placeholder="搜索通知标题..."
                value={keyword}
                onChange={(e: React.ChangeEvent<HTMLInputElement>) => {
                  setKeyword(e.target.value);
                  setPage(1);
                }}
                className="pl-10"
              />
            </div>
          </div>
        </div>
      </Card>

      {/* 通知列表 */}
      <Card>
        {isLoading ? (
          <div className="p-6 space-y-4">
            {Array.from({ length: 5 }).map((_, i) => (
              <div key={i} className="h-24 bg-slate-100 rounded animate-pulse" />
            ))}
          </div>
        ) : (
          <>
            <div className="divide-y divide-slate-200">
              {notifications.map((notification) => (
                <div key={notification.id} className="p-4 hover:bg-slate-50">
                  <div className="flex items-start justify-between">
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-2">
                        <h3 className="font-medium text-slate-900">{notification.title}</h3>
                        {notification.isPublished ? (
                          <Badge variant="success" size="sm">已发布</Badge>
                        ) : (
                          <Badge variant="default" size="sm">未发布</Badge>
                        )}
                      </div>
                      <p className="text-sm text-slate-600 line-clamp-2 mb-2">{notification.content}</p>
                      <div className="flex items-center gap-4 text-sm text-slate-500">
                        <span className="flex items-center gap-1">
                          <Users className="h-3 w-3" />
                          {TARGET_TYPE_LABELS[notification.targetType]}
                        </span>
                        <span>发送: {notification.sentCount}</span>
                        <span>已读: {notification.readCount}</span>
                        {notification.expiresAt && (
                          <span>过期: {new Date(notification.expiresAt).toLocaleDateString('zh-CN')}</span>
                        )}
                        <span>创建: {new Date(notification.createdAt).toLocaleString('zh-CN')}</span>
                      </div>
                    </div>
                    <div className="flex items-center gap-2 ml-4">
                      {!notification.isPublished ? (
                        <>
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => handleEdit(notification)}
                            title="编辑"
                          >
                            <Pencil className="h-4 w-4" />
                          </Button>
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => handlePublish(notification.id)}
                            disabled={publishMutation.isPending}
                            title="发布"
                          >
                            <Send className="h-4 w-4 text-green-500" />
                          </Button>
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => handleDelete(notification.id)}
                            disabled={deleteMutation.isPending}
                            title="删除"
                          >
                            <Trash2 className="h-4 w-4 text-red-500" />
                          </Button>
                        </>
                      ) : (
                        <>
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => handleRevoke(notification.id)}
                            disabled={revokeMutation.isPending}
                            title="撤销"
                          >
                            <RotateCcw className="h-4 w-4 text-orange-500" />
                          </Button>
                        </>
                      )}
                    </div>
                  </div>
                </div>
              ))}
              {!notifications.length && (
                <div className="p-10 text-center text-slate-500">
                  <Bell className="h-12 w-12 mx-auto mb-4 text-slate-300" />
                  <p>暂无系统通知</p>
                  <p className="text-sm mt-1">点击&quot;新建通知&quot;按钮创建</p>
                </div>
              )}
            </div>
            {totalPages > 1 && (
              <div className="p-4 border-t border-slate-200">
                <Pagination
                  currentPage={page}
                  totalPages={totalPages}
                  onPageChange={setPage}
                />
              </div>
            )}
          </>
        )}
      </Card>

      {/* 创建弹窗 */}
      {isCreateModalOpen && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl w-full max-w-lg mx-4">
            <div className="p-6 border-b border-slate-200">
              <h2 className="text-lg font-semibold">新建系统通知</h2>
            </div>
            <div className="p-6 space-y-4">
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">
                  标题 *
                </label>
                <Input
                  value={formData.title}
                  onChange={(e: React.ChangeEvent<HTMLInputElement>) => setFormData({ ...formData, title: e.target.value })}
                  placeholder="请输入通知标题"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">
                  内容 *
                </label>
                <textarea
                  value={formData.content}
                  onChange={(e: React.ChangeEvent<HTMLTextAreaElement>) => setFormData({ ...formData, content: e.target.value })}
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  rows={4}
                  placeholder="请输入通知内容"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">
                  目标用户 *
                </label>
                <select
                  value={formData.targetType}
                  onChange={(e) => setFormData({ ...formData, targetType: e.target.value as NotificationTargetType })}
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                >
                  {Object.entries(TARGET_TYPE_LABELS).map(([value, label]) => (
                    <option key={value} value={value}>{label}</option>
                  ))}
                </select>
              </div>
              {formData.targetType === 'specific' && (
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1">
                    用户ID列表
                  </label>
                  <Input
                    value={formData.targetIds}
                    onChange={(e: React.ChangeEvent<HTMLInputElement>) => setFormData({ ...formData, targetIds: e.target.value })}
                    placeholder="请输入用户ID，用逗号分隔"
                  />
                </div>
              )}
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">
                  过期时间
                </label>
                <input
                  type="datetime-local"
                  value={formData.expiresAt}
                  onChange={(e) => setFormData({ ...formData, expiresAt: e.target.value })}
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                />
              </div>
            </div>
            <div className="p-6 border-t border-slate-200 flex justify-end gap-3">
              <Button variant="ghost" onClick={() => { setIsCreateModalOpen(false); resetForm(); }}>
                取消
              </Button>
              <Button
                onClick={handleCreate}
                disabled={!formData.title.trim() || !formData.content.trim() || createMutation.isPending}
              >
                {createMutation.isPending ? '创建中...' : '创建'}
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* 编辑弹窗 */}
      {isEditModalOpen && editingNotification && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl w-full max-w-lg mx-4">
            <div className="p-6 border-b border-slate-200">
              <h2 className="text-lg font-semibold">编辑系统通知</h2>
            </div>
            <div className="p-6 space-y-4">
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">
                  标题 *
                </label>
                <Input
                  value={formData.title}
                  onChange={(e: React.ChangeEvent<HTMLInputElement>) => setFormData({ ...formData, title: e.target.value })}
                  placeholder="请输入通知标题"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">
                  内容 *
                </label>
                <textarea
                  value={formData.content}
                  onChange={(e: React.ChangeEvent<HTMLTextAreaElement>) => setFormData({ ...formData, content: e.target.value })}
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  rows={4}
                  placeholder="请输入通知内容"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">
                  目标用户 *
                </label>
                <select
                  value={formData.targetType}
                  onChange={(e) => setFormData({ ...formData, targetType: e.target.value as NotificationTargetType })}
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                >
                  {Object.entries(TARGET_TYPE_LABELS).map(([value, label]) => (
                    <option key={value} value={value}>{label}</option>
                  ))}
                </select>
              </div>
              {formData.targetType === 'specific' && (
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1">
                    用户ID列表
                  </label>
                  <Input
                    value={formData.targetIds}
                    onChange={(e: React.ChangeEvent<HTMLInputElement>) => setFormData({ ...formData, targetIds: e.target.value })}
                    placeholder="请输入用户ID，用逗号分隔"
                  />
                </div>
              )}
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">
                  过期时间
                </label>
                <input
                  type="datetime-local"
                  value={formData.expiresAt}
                  onChange={(e) => setFormData({ ...formData, expiresAt: e.target.value })}
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                />
              </div>
            </div>
            <div className="p-6 border-t border-slate-200 flex justify-end gap-3">
              <Button variant="ghost" onClick={() => { setIsEditModalOpen(false); setEditingNotification(null); resetForm(); }}>
                取消
              </Button>
              <Button
                onClick={handleUpdate}
                disabled={!formData.title.trim() || !formData.content.trim() || updateMutation.isPending}
              >
                {updateMutation.isPending ? '保存中...' : '保存'}
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
