/**
 * UserManagement - 用户管理组件
 */

import { useState } from 'react';

import type { ForumUser, ForumUserStatus, UserLevel, UserActionRecord } from '../types';
import {
  useForumUsers,
  useUpdateUserStatus,
  useSetModerator,
  useUserActionRecords,
} from '../hooks/useForumAdmin';

const statusLabels: Record<ForumUserStatus, string> = {
  active: '正常',
  banned: '封禁',
  muted: '禁言',
  unverified: '未验证',
};

const statusColors: Record<ForumUserStatus, string> = {
  active: 'bg-green-100 text-green-800',
  banned: 'bg-red-100 text-red-800',
  muted: 'bg-orange-100 text-orange-800',
  unverified: 'bg-gray-100 text-gray-800',
};

const levelLabels: Record<UserLevel, string> = {
  newbie: '新手',
  member: '成员',
  active: '活跃',
  senior: '资深',
  expert: '专家',
  legend: '传说',
};

const levelColors: Record<UserLevel, string> = {
  newbie: 'bg-gray-100 text-gray-800',
  member: 'bg-blue-100 text-blue-800',
  active: 'bg-green-100 text-green-800',
  senior: 'bg-purple-100 text-purple-800',
  expert: 'bg-orange-100 text-orange-800',
  legend: 'bg-red-100 text-red-800',
};

const actionLabels: Record<UserActionRecord['action'], string> = {
  ban: '封禁',
  unban: '解封',
  mute: '禁言',
  unmute: '解除禁言',
  warn: '警告',
  delete_post: '删除帖子',
};

/**
 * 用户管理组件
 */
export function UserManagement(): JSX.Element {
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [selectedStatus, setSelectedStatus] = useState<ForumUserStatus | undefined>();
  const [selectedLevel, setSelectedLevel] = useState<UserLevel | undefined>();
  const [viewingUser, setViewingUser] = useState<ForumUser | null>(null);
  const [managingUser, setManagingUser] = useState<ForumUser | null>(null);
  const [actionReason, setActionReason] = useState<string>('');
  const [actionDuration, setActionDuration] = useState<number>(24); // 小时

  const { data: usersData, isLoading, error } = useForumUsers({
    status: selectedStatus,
    level: selectedLevel,
    search: searchQuery,
    limit: 50,
  });

  const { data: userRecords } = useUserActionRecords(viewingUser?.id || 0);
  const updateStatusMutation = useUpdateUserStatus();
  const setModeratorMutation = useSetModerator();

  const handleSearch = (): void => {
    // 搜索通过 query key 自动触发重新获取
  };

  const handleUpdateStatus = async (status: ForumUserStatus): Promise<void> => {
    if (!managingUser) return;

    await updateStatusMutation.mutateAsync({
      userId: managingUser.id,
      status,
      reason: actionReason,
      duration: status === 'banned' || status === 'muted' ? actionDuration : undefined,
    });

    setManagingUser(null);
    setActionReason('');
    setActionDuration(24);
  };

  const handleSetModerator = async (isGlobal: boolean): Promise<void> => {
    if (!managingUser) return;

    await setModeratorMutation.mutateAsync({
      userId: managingUser.id,
      categoryIds: [],
      isGlobal,
    });

    setManagingUser(null);
  };

  const _formatDuration = (hours: number): string => {
    if (hours === 0) return '永久';
    if (hours < 24) return `${hours}小时`;
    if (hours < 168) return `${Math.floor(hours / 24)}天`;
    return `${Math.floor(hours / 168)}周`;
  };

  if (isLoading) {
    return (
      <div className="p-6 bg-white rounded-lg shadow-sm">
        <div className="animate-pulse space-y-4">
          <div className="h-4 bg-gray-200 rounded w-1/4" />
          <div className="space-y-2">
            <div className="h-12 bg-gray-200 rounded" />
            <div className="h-12 bg-gray-200 rounded" />
            <div className="h-12 bg-gray-200 rounded" />
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-6 bg-white rounded-lg shadow-sm">
        <div className="text-red-500">加载用户列表失败</div>
      </div>
    );
  }

  return (
    <div className="p-6 bg-white rounded-lg shadow-sm">
      {/* 头部 */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-xl font-semibold text-gray-900">用户管理</h2>
          <p className="text-sm text-gray-500 mt-1">共 {usersData?.total || 0} 位用户</p>
        </div>
      </div>

      {/* 筛选器 */}
      <div className="flex flex-wrap items-center gap-4 mb-6">
        <div className="flex-1 min-w-[200px]">
          <div className="flex gap-2">
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="搜索用户名、邮箱..."
              className="flex-1 px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
            <button
              onClick={handleSearch}
              className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700 transition-colors"
            >
              搜索
            </button>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <label className="text-sm font-medium text-gray-700">状态:</label>
          <select
            value={selectedStatus || ''}
            onChange={(e) => setSelectedStatus(e.target.value as ForumUserStatus || undefined)}
            className="px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="">全部</option>
            <option value="active">正常</option>
            <option value="banned">封禁</option>
            <option value="muted">禁言</option>
            <option value="unverified">未验证</option>
          </select>
        </div>
        <div className="flex items-center gap-2">
          <label className="text-sm font-medium text-gray-700">等级:</label>
          <select
            value={selectedLevel || ''}
            onChange={(e) => setSelectedLevel(e.target.value as UserLevel || undefined)}
            className="px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="">全部</option>
            <option value="newbie">新手</option>
            <option value="member">成员</option>
            <option value="active">活跃</option>
            <option value="senior">资深</option>
            <option value="expert">专家</option>
            <option value="legend">传说</option>
          </select>
        </div>
      </div>

      {/* 用户列表 */}
      <div className="overflow-x-auto">
        <table className="w-full text-left">
          <thead>
            <tr className="border-b border-gray-200">
              <th className="pb-3 font-medium text-gray-700">用户</th>
              <th className="pb-3 font-medium text-gray-700">状态</th>
              <th className="pb-3 font-medium text-gray-700">等级</th>
              <th className="pb-3 font-medium text-gray-700">帖子/评论</th>
              <th className="pb-3 font-medium text-gray-700">声望</th>
              <th className="pb-3 font-medium text-gray-700">角色</th>
              <th className="pb-3 font-medium text-gray-700 text-right">操作</th>
            </tr>
          </thead>
          <tbody>
            {usersData?.users.map((user) => (
              <tr key={user.id} className="border-b border-gray-100 last:border-0">
                <td className="py-4">
                  <div className="flex items-center gap-3">
                    {user.avatar ? (
                      <img src={user.avatar} alt={user.nickname} className="w-10 h-10 rounded-full object-cover" />
                    ) : (
                      <div className="w-10 h-10 rounded-full bg-blue-100 flex items-center justify-center text-blue-600 font-medium">
                        {user.nickname.charAt(0)}
                      </div>
                    )}
                    <div>
                      <p className="font-medium text-gray-900">{user.nickname}</p>
                      <p className="text-sm text-gray-500">{user.email}</p>
                      {user.bannedUntil && (
                        <p className="text-xs text-red-500">
                          封禁至: {new Date(user.bannedUntil).toLocaleString('zh-CN')}
                        </p>
                      )}
                      {user.muteUntil && (
                        <p className="text-xs text-orange-500">
                          禁言至: {new Date(user.muteUntil).toLocaleString('zh-CN')}
                        </p>
                      )}
                    </div>
                  </div>
                </td>
                <td className="py-4">
                  <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${statusColors[user.status]}`}>
                    {statusLabels[user.status]}
                  </span>
                </td>
                <td className="py-4">
                  <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${levelColors[user.level]}`}>
                    {levelLabels[user.level]}
                  </span>
                </td>
                <td className="py-4 text-gray-600">
                  {user.postCount} / {user.commentCount}
                </td>
                <td className="py-4">
                  <span className="text-sm font-medium text-blue-600">{user.reputation}</span>
                </td>
                <td className="py-4">
                  {user.isAdmin ? (
                    <span className="px-2 py-1 text-xs font-semibold bg-red-100 text-red-800 rounded-full">管理员</span>
                  ) : user.isModerator ? (
                    <span className="px-2 py-1 text-xs font-semibold bg-purple-100 text-purple-800 rounded-full">版主</span>
                  ) : (
                    <span className="px-2 py-1 text-xs font-semibold bg-gray-100 text-gray-800 rounded-full">普通用户</span>
                  )}
                </td>
                <td className="py-4 text-right">
                  <div className="flex items-center justify-end gap-2">
                    <button
                      onClick={() => setViewingUser(user)}
                      className="px-3 py-1 text-sm text-blue-600 hover:bg-blue-50 rounded transition-colors"
                    >
                      详情
                    </button>
                    <button
                      onClick={() => setManagingUser(user)}
                      className="px-3 py-1 text-sm text-gray-600 hover:bg-gray-100 rounded transition-colors"
                    >
                      管理
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* 用户详情弹窗 */}
      {viewingUser && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-lg max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold">用户详情</h3>
              <button
                onClick={() => setViewingUser(null)}
                className="text-gray-500 hover:text-gray-700"
              >
                ✕
              </button>
            </div>
            <div className="space-y-4">
              <div className="flex items-center gap-4">
                {viewingUser.avatar ? (
                  <img src={viewingUser.avatar} alt={viewingUser.nickname} className="w-16 h-16 rounded-full object-cover" />
                ) : (
                  <div className="w-16 h-16 rounded-full bg-blue-100 flex items-center justify-center text-blue-600 text-2xl font-medium">
                    {viewingUser.nickname.charAt(0)}
                  </div>
                )}
                <div>
                  <p className="text-xl font-medium text-gray-900">{viewingUser.nickname}</p>
                  <p className="text-sm text-gray-500">{viewingUser.email}</p>
                  <div className="flex items-center gap-2 mt-1">
                    <span className={`px-2 py-0.5 text-xs font-semibold rounded-full ${statusColors[viewingUser.status]}`}>
                      {statusLabels[viewingUser.status]}
                    </span>
                    <span className={`px-2 py-0.5 text-xs font-semibold rounded-full ${levelColors[viewingUser.level]}`}>
                      {levelLabels[viewingUser.level]}
                    </span>
                  </div>
                </div>
              </div>
              <div className="grid grid-cols-3 gap-4 p-4 bg-gray-50 rounded-lg">
                <div className="text-center">
                  <p className="text-2xl font-semibold text-gray-900">{viewingUser.postCount}</p>
                  <p className="text-sm text-gray-500">帖子</p>
                </div>
                <div className="text-center">
                  <p className="text-2xl font-semibold text-gray-900">{viewingUser.commentCount}</p>
                  <p className="text-sm text-gray-500">评论</p>
                </div>
                <div className="text-center">
                  <p className="text-2xl font-semibold text-blue-600">{viewingUser.reputation}</p>
                  <p className="text-sm text-gray-500">声望</p>
                </div>
              </div>
              <div className="text-sm text-gray-600 space-y-1">
                <p>用户名: {viewingUser.username}</p>
                <p>注册时间: {new Date(viewingUser.joinedAt).toLocaleString('zh-CN')}</p>
                <p>最后活跃: {new Date(viewingUser.lastActiveAt).toLocaleString('zh-CN')}</p>
                {viewingUser.phone && <p>手机号: {viewingUser.phone}</p>}
              </div>
              {userRecords && userRecords.total > 0 && (
                <div>
                  <h4 className="font-medium text-gray-900 mb-2">操作记录</h4>
                  <div className="space-y-2 max-h-48 overflow-y-auto">
                    {userRecords.records.map((record) => (
                      <div key={record.id} className="p-3 bg-gray-50 rounded text-sm">
                        <div className="flex items-center justify-between">
                          <span className="font-medium text-gray-700">{actionLabels[record.action]}</span>
                          <span className="text-xs text-gray-500">
                            {new Date(record.performedAt).toLocaleString('zh-CN')}
                          </span>
                        </div>
                        <p className="text-gray-600 mt-1">{record.reason}</p>
                        <p className="text-xs text-gray-500 mt-1">操作人: {record.performedByName}</p>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* 用户管理弹窗 */}
      {managingUser && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-md">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold">管理用户</h3>
              <button
                onClick={() => setManagingUser(null)}
                className="text-gray-500 hover:text-gray-700"
              >
                ✕
              </button>
            </div>
            <div className="mb-4 p-3 bg-gray-50 rounded-lg">
              <p className="font-medium text-gray-900">{managingUser.nickname}</p>
              <p className="text-sm text-gray-500">{managingUser.email}</p>
            </div>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">操作原因</label>
                <textarea
                  value={actionReason}
                  onChange={(e) => setActionReason(e.target.value)}
                  placeholder="请输入操作原因..."
                  rows={2}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
              {(managingUser.status !== 'banned') && (
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">封禁时长</label>
                  <select
                    value={actionDuration}
                    onChange={(e) => setActionDuration(parseInt(e.target.value))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value={24}>1天</option>
                    <option value={72}>3天</option>
                    <option value={168}>1周</option>
                    <option value={720}>1个月</option>
                    <option value={0}>永久</option>
                  </select>
                </div>
              )}
              <div className="grid grid-cols-2 gap-3">
                {managingUser.status !== 'active' && (
                  <button
                    onClick={() => void handleUpdateStatus('active')}
                    disabled={updateStatusMutation.isPending}
                    className="px-4 py-2 text-sm font-medium text-green-700 bg-green-100 rounded-md hover:bg-green-200 transition-colors disabled:opacity-50"
                  >
                    {updateStatusMutation.isPending ? '处理中...' : '解除限制'}
                  </button>
                )}
                {managingUser.status !== 'banned' && (
                  <button
                    onClick={() => void handleUpdateStatus('banned')}
                    disabled={updateStatusMutation.isPending}
                    className="px-4 py-2 text-sm font-medium text-red-700 bg-red-100 rounded-md hover:bg-red-200 transition-colors disabled:opacity-50"
                  >
                    {updateStatusMutation.isPending ? '处理中...' : '封禁用户'}
                  </button>
                )}
                {managingUser.status !== 'muted' && (
                  <button
                    onClick={() => void handleUpdateStatus('muted')}
                    disabled={updateStatusMutation.isPending}
                    className="px-4 py-2 text-sm font-medium text-orange-700 bg-orange-100 rounded-md hover:bg-orange-200 transition-colors disabled:opacity-50"
                  >
                    {updateStatusMutation.isPending ? '处理中...' : '禁言用户'}
                  </button>
                )}
              </div>
              <div className="border-t border-gray-200 pt-4">
                <p className="text-sm font-medium text-gray-700 mb-2">版主设置</p>
                <div className="flex gap-3">
                  {!managingUser.isModerator ? (
                    <button
                      onClick={() => void handleSetModerator(true)}
                      disabled={setModeratorMutation.isPending}
                      className="flex-1 px-4 py-2 text-sm font-medium text-purple-700 bg-purple-100 rounded-md hover:bg-purple-200 transition-colors disabled:opacity-50"
                    >
                      {setModeratorMutation.isPending ? '处理中...' : '设为版主'}
                    </button>
                  ) : (
                    <button
                      onClick={() => void handleSetModerator(false)}
                      disabled={setModeratorMutation.isPending}
                      className="flex-1 px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 rounded-md hover:bg-gray-200 transition-colors disabled:opacity-50"
                    >
                      {setModeratorMutation.isPending ? '处理中...' : '取消版主'}
                    </button>
                  )}
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}