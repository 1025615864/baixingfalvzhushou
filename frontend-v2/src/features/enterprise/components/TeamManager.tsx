/**
 * TeamManager - 团队管理组件
 */

import { useState } from 'react';

import type { TeamMember, TeamMemberRole, MemberStatus } from '../types';
import {
  useTeamMembers,
  useAddTeamMember,
  useRemoveTeamMember,
  useUpdateMemberRole,
} from '../hooks/useEnterprise';

interface TeamManagerProps {
  accountId: number;
}

const roleLabels: Record<TeamMemberRole, string> = {
  owner: '所有者',
  admin: '管理员',
  member: '成员',
  viewer: '观察者',
};

const roleColors: Record<TeamMemberRole, string> = {
  owner: 'bg-purple-100 text-purple-800',
  admin: 'bg-blue-100 text-blue-800',
  member: 'bg-green-100 text-green-800',
  viewer: 'bg-gray-100 text-gray-800',
};

const statusLabels: Record<MemberStatus, string> = {
  active: '正常',
  pending: '待激活',
  disabled: '已禁用',
};

const statusColors: Record<MemberStatus, string> = {
  active: 'bg-green-100 text-green-800',
  pending: 'bg-yellow-100 text-yellow-800',
  disabled: 'bg-red-100 text-red-800',
};

/**
 * 团队管理组件
 */
export function TeamManager({ accountId }: TeamManagerProps): JSX.Element {
  const [showAddModal, setShowAddModal] = useState<boolean>(false);
  const [newMemberEmail, setNewMemberEmail] = useState<string>('');
  const [newMemberName, setNewMemberName] = useState<string>('');
  const [newMemberRole, setNewMemberRole] = useState<TeamMemberRole>('member');
  const [editingMember, setEditingMember] = useState<TeamMember | null>(null);

  const { data: members, isLoading, error } = useTeamMembers(accountId);
  const addMutation = useAddTeamMember(accountId);
  const removeMutation = useRemoveTeamMember(accountId);
  const updateRoleMutation = useUpdateMemberRole(accountId);

  const handleAddMember = (): void => {
    if (!newMemberEmail.trim() || !newMemberName.trim()) return;

    void addMutation.mutateAsync({
      email: newMemberEmail,
      name: newMemberName,
      role: newMemberRole,
    }).then(() => {
      setShowAddModal(false);
      setNewMemberEmail('');
      setNewMemberName('');
      setNewMemberRole('member');
    });
  };

  const handleRemoveMember = (memberId: number): void => {
    if (!window.confirm('确定要移除该成员吗？')) return;

    void removeMutation.mutateAsync({ memberId });
  };

  const handleUpdateRole = (): void => {
    if (!editingMember) return;

    void updateRoleMutation.mutateAsync({
      memberId: editingMember.id,
      role: editingMember.role,
    }).then(() => {
      setEditingMember(null);
    });
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
        <div className="text-red-500">加载团队成员失败</div>
      </div>
    );
  }

  return (
    <div className="p-6 bg-white rounded-lg shadow-sm">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-xl font-semibold text-gray-900">团队管理</h2>
          <p className="text-sm text-gray-500 mt-1">共 {members?.length || 0} 名成员</p>
        </div>
        <button
          onClick={() => setShowAddModal(true)}
          className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700 transition-colors"
        >
          添加成员
        </button>
      </div>

      {/* 成员列表 */}
      <div className="overflow-x-auto">
        <table className="w-full text-left">
          <thead>
            <tr className="border-b border-gray-200">
              <th className="pb-3 font-medium text-gray-700">成员</th>
              <th className="pb-3 font-medium text-gray-700">角色</th>
              <th className="pb-3 font-medium text-gray-700">状态</th>
              <th className="pb-3 font-medium text-gray-700">加入时间</th>
              <th className="pb-3 font-medium text-gray-700 text-right">操作</th>
            </tr>
          </thead>
          <tbody>
            {members?.map((member) => (
              <tr key={member.id} className="border-b border-gray-100 last:border-0">
                <td className="py-4">
                  <div className="flex items-center gap-3">
                    {member.avatar ? (
                      <img
                        src={member.avatar}
                        alt={member.name}
                        className="w-10 h-10 rounded-full object-cover"
                      />
                    ) : (
                      <div className="w-10 h-10 rounded-full bg-blue-100 flex items-center justify-center text-blue-600 font-medium">
                        {member.name.charAt(0)}
                      </div>
                    )}
                    <div>
                      <p className="font-medium text-gray-900">{member.name}</p>
                      <p className="text-sm text-gray-500">{member.email}</p>
                    </div>
                  </div>
                </td>
                <td className="py-4">
                  <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${roleColors[member.role]}`}>
                    {roleLabels[member.role]}
                  </span>
                </td>
                <td className="py-4">
                  <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${statusColors[member.status]}`}>
                    {statusLabels[member.status]}
                  </span>
                </td>
                <td className="py-4 text-gray-600">
                  {new Date(member.joinedAt).toLocaleDateString('zh-CN')}
                </td>
                <td className="py-4 text-right">
                  <div className="flex items-center justify-end gap-2">
                    <button
                      onClick={() => setEditingMember(member)}
                      className="px-3 py-1 text-sm text-blue-600 hover:bg-blue-50 rounded transition-colors"
                    >
                      编辑角色
                    </button>
                    {member.role !== 'owner' && (
                      <button
                        onClick={() => handleRemoveMember(member.id)}
                        className="px-3 py-1 text-sm text-red-600 hover:bg-red-50 rounded transition-colors"
                      >
                        移除
                      </button>
                    )}
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* 添加成员弹窗 */}
      {showAddModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-md">
            <h3 className="text-lg font-semibold mb-4">添加团队成员</h3>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">姓名</label>
                <input
                  type="text"
                  value={newMemberName}
                  onChange={(e) => setNewMemberName(e.target.value)}
                  placeholder="请输入成员姓名"
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">邮箱</label>
                <input
                  type="email"
                  value={newMemberEmail}
                  onChange={(e) => setNewMemberEmail(e.target.value)}
                  placeholder="请输入成员邮箱"
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">角色</label>
                <select
                  value={newMemberRole}
                  onChange={(e) => setNewMemberRole(e.target.value as TeamMemberRole)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="member">成员</option>
                  <option value="admin">管理员</option>
                  <option value="viewer">观察者</option>
                </select>
              </div>
            </div>
            <div className="flex justify-end gap-3 mt-6">
              <button
                onClick={() => setShowAddModal(false)}
                className="px-4 py-2 text-sm font-medium text-gray-600 bg-gray-100 rounded-md hover:bg-gray-200 transition-colors"
              >
                取消
              </button>
              <button
                onClick={handleAddMember}
                disabled={addMutation.isPending || !newMemberEmail.trim() || !newMemberName.trim()}
                className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700 transition-colors disabled:opacity-50"
              >
                {addMutation.isPending ? '添加中...' : '添加'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* 编辑角色弹窗 */}
      {editingMember && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-md">
            <h3 className="text-lg font-semibold mb-4">编辑成员角色</h3>
            <p className="text-sm text-gray-600 mb-4">成员: {editingMember.name}</p>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">角色</label>
              <select
                value={editingMember.role}
                onChange={(e) => setEditingMember({ ...editingMember, role: e.target.value as TeamMemberRole })}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="member">成员</option>
                <option value="admin">管理员</option>
                <option value="viewer">观察者</option>
              </select>
            </div>
            <div className="flex justify-end gap-3 mt-6">
              <button
                onClick={() => setEditingMember(null)}
                className="px-4 py-2 text-sm font-medium text-gray-600 bg-gray-100 rounded-md hover:bg-gray-200 transition-colors"
              >
                取消
              </button>
              <button
                onClick={handleUpdateRole}
                disabled={updateRoleMutation.isPending}
                className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700 transition-colors disabled:opacity-50"
              >
                {updateRoleMutation.isPending ? '保存中...' : '保存'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}