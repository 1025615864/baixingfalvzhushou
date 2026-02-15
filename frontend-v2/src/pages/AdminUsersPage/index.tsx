// ============================================
// 管理后台 - 用户管理页面
// ============================================

import { useState } from 'react';

// Mock 用户数据
const MOCK_USERS = [
  { id: 1, name: '张三', email: 'zhangsan@example.com', role: 'user', status: 'active', created_at: '2026-01-15', phone: '138****8888' },
  { id: 2, name: '李四', email: 'lisi@example.com', role: 'lawyer', status: 'active', created_at: '2026-01-14', phone: '139****9999' },
  { id: 3, name: '王五', email: 'wangwu@example.com', role: 'user', status: 'inactive', created_at: '2026-01-10', phone: '137****7777' },
  { id: 4, name: '赵六', email: 'zhaoliu@example.com', role: 'admin', status: 'active', created_at: '2026-01-01', phone: '136****6666' },
  { id: 5, name: '钱七', email: 'qianqi@example.com', role: 'lawyer', status: 'pending', created_at: '2026-02-01', phone: '135****5555' },
];

export function AdminUsersPage() {
  const [searchTerm, setSearchTerm] = useState('');
  const [roleFilter, setRoleFilter] = useState('all');
  const [statusFilter, setStatusFilter] = useState('all');

  const filteredUsers = MOCK_USERS.filter((user) => {
    const matchesSearch = user.name.includes(searchTerm) || user.email.includes(searchTerm);
    const matchesRole = roleFilter === 'all' || user.role === roleFilter;
    const matchesStatus = statusFilter === 'all' || user.status === statusFilter;
    return matchesSearch && matchesRole && matchesStatus;
  });

  const getRoleBadge = (role: string) => {
    const styles: Record<string, string> = {
      user: 'bg-gray-100 text-gray-700',
      lawyer: 'bg-blue-100 text-blue-700',
      admin: 'bg-purple-100 text-purple-700',
    };
    const labels: Record<string, string> = {
      user: '普通用户',
      lawyer: '律师',
      admin: '管理员',
    };
    return (
      <span className={`px-2 py-1 rounded-full text-xs font-medium ${styles[role] || styles.user}`}>
        {labels[role] || role}
      </span>
    );
  };

  const getStatusBadge = (status: string) => {
    const styles: Record<string, string> = {
      active: 'bg-green-100 text-green-700',
      inactive: 'bg-red-100 text-red-700',
      pending: 'bg-amber-100 text-amber-700',
    };
    const labels: Record<string, string> = {
      active: '正常',
      inactive: '禁用',
      pending: '待审核',
    };
    return (
      <span className={`px-2 py-1 rounded-full text-xs font-medium ${styles[status] || styles.inactive}`}>
        {labels[status] || status}
      </span>
    );
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* 顶部导航 */}
      <header className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center gap-4">
              <h1 className="text-xl font-bold text-gray-900">用户管理</h1>
            </div>
            <button className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors flex items-center gap-2">
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
              </svg>
              新增用户
            </button>
          </div>
        </div>
      </header>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* 筛选栏 */}
        <div className="bg-white rounded-lg p-4 shadow-sm border border-gray-100 mb-6">
          <div className="flex flex-wrap items-center gap-4">
            <div className="flex-1 min-w-[200px]">
              <input
                type="text"
                placeholder="搜索用户姓名或邮箱..."
                value={searchTerm}
                onChange={(e) => { setSearchTerm(e.target.value); }}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>
            <select
              value={roleFilter}
              onChange={(e) => { setRoleFilter(e.target.value); }}
              className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
            >
              <option value="all">全部角色</option>
              <option value="user">普通用户</option>
              <option value="lawyer">律师</option>
              <option value="admin">管理员</option>
            </select>
            <select
              value={statusFilter}
              onChange={(e) => { setStatusFilter(e.target.value); }}
              className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
            >
              <option value="all">全部状态</option>
              <option value="active">正常</option>
              <option value="inactive">禁用</option>
              <option value="pending">待审核</option>
            </select>
          </div>
        </div>

        {/* 用户列表 */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-100 overflow-hidden">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">用户</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">角色</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">状态</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">手机号</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">注册时间</th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">操作</th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {filteredUsers.map((user) => (
                <tr key={user.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="flex items-center">
                      <div className="w-10 h-10 rounded-full bg-blue-100 flex items-center justify-center text-blue-600 font-medium">
                        {user.name[0]}
                      </div>
                      <div className="ml-4">
                        <div className="text-sm font-medium text-gray-900">{user.name}</div>
                        <div className="text-sm text-gray-500">{user.email}</div>
                      </div>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    {getRoleBadge(user.role)}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    {getStatusBadge(user.status)}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {user.phone}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {user.created_at}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                    <button className="text-blue-600 hover:text-blue-900 mr-3">编辑</button>
                    <button className="text-red-600 hover:text-red-900">禁用</button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          
          {/* 分页 */}
          <div className="px-6 py-4 border-t border-gray-200 flex items-center justify-between">
            <div className="text-sm text-gray-500">
              显示 1 到 {filteredUsers.length} 条，共 {filteredUsers.length} 条
            </div>
            <div className="flex gap-2">
              <button className="px-3 py-1 border border-gray-300 rounded hover:bg-gray-50 disabled:opacity-50" disabled>
                上一页
              </button>
              <button className="px-3 py-1 border border-gray-300 rounded hover:bg-gray-50 disabled:opacity-50" disabled>
                下一页
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}