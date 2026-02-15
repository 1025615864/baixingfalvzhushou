/**
 * ForumAdminPage - 论坛管理页面
 */

import { useState } from 'react';

import { CategoryManager } from '../components/CategoryManager';
import { ContentModeration } from '../components/ContentModeration';
import { UserManagement } from '../components/UserManagement';
import { useForumStats } from '../hooks/useForumAdmin';

type TabType = 'overview' | 'categories' | 'moderation' | 'users';

/**
 * 论坛管理页面
 */
export function ForumAdminPage(): JSX.Element {
  const [activeTab, setActiveTab] = useState<TabType>('overview');

  const { data: stats, isLoading: isLoadingStats } = useForumStats();

  const tabs: { id: TabType; label: string }[] = [
    { id: 'overview', label: '概览' },
    { id: 'categories', label: '板块管理' },
    { id: 'moderation', label: '内容审核' },
    { id: 'users', label: '用户管理' },
  ];

  const renderOverview = (): JSX.Element => {
    if (isLoadingStats) {
      return (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {Array.from({ length: 8 }, (_, i) => (
            <div key={i} className="p-6 bg-white rounded-lg shadow-sm animate-pulse">
              <div className="h-4 bg-gray-200 rounded w-1/2 mb-2" />
              <div className="h-8 bg-gray-200 rounded w-1/3" />
            </div>
          ))}
        </div>
      );
    }

    if (!stats) {
      return (
        <div className="p-6 bg-white rounded-lg shadow-sm text-center text-gray-500">
          加载统计数据失败
        </div>
      );
    }

    const statCards = [
      { label: '总帖子数', value: stats.totalPosts, color: 'blue' },
      { label: '总评论数', value: stats.totalComments, color: 'green' },
      { label: '总用户数', value: stats.totalUsers, color: 'purple' },
      { label: '今日帖子', value: stats.todayPosts, color: 'indigo' },
      { label: '今日评论', value: stats.todayComments, color: 'teal' },
      { label: '今日新用户', value: stats.todayNewUsers, color: 'orange' },
      { label: '待审核内容', value: stats.pendingModeration, color: 'red' },
      { label: '被举报内容', value: stats.reportedContent, color: 'pink' },
    ];

    return (
      <div className="space-y-6">
        {/* 统计卡片 */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {statCards.map((card) => (
            <div key={card.label} className="p-6 bg-white rounded-lg shadow-sm">
              <p className="text-sm text-gray-500 mb-1">{card.label}</p>
              <p className={`text-3xl font-bold text-${card.color}-600`}>
                {card.value.toLocaleString()}
              </p>
            </div>
          ))}
        </div>

        {/* 活跃用户统计 */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="p-6 bg-white rounded-lg shadow-sm">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">活跃用户数</h3>
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-500">7天活跃</p>
                <p className="text-2xl font-bold text-blue-600">
                  {stats.activeUsers7d.toLocaleString()}
                </p>
              </div>
              <div>
                <p className="text-sm text-gray-500">30天活跃</p>
                <p className="text-2xl font-bold text-purple-600">
                  {stats.activeUsers30d.toLocaleString()}
                </p>
              </div>
            </div>
          </div>

          {/* 快捷入口 */}
          <div className="p-6 bg-white rounded-lg shadow-sm">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">快捷操作</h3>
            <div className="grid grid-cols-2 gap-4">
              <button
                onClick={() => setActiveTab('moderation')}
                className="p-4 text-left border border-gray-200 rounded-lg hover:border-blue-500 hover:bg-blue-50 transition-colors"
              >
                <p className="font-medium text-gray-900">内容审核</p>
                <p className="text-sm text-gray-500 mt-1">
                  {stats.pendingModeration} 条待审核
                </p>
              </button>
              <button
                onClick={() => setActiveTab('users')}
                className="p-4 text-left border border-gray-200 rounded-lg hover:border-purple-500 hover:bg-purple-50 transition-colors"
              >
                <p className="font-medium text-gray-900">用户管理</p>
                <p className="text-sm text-gray-500 mt-1">管理论坛用户</p>
              </button>
              <button
                onClick={() => setActiveTab('categories')}
                className="p-4 text-left border border-gray-200 rounded-lg hover:border-green-500 hover:bg-green-50 transition-colors"
              >
                <p className="font-medium text-gray-900">板块管理</p>
                <p className="text-sm text-gray-500 mt-1">配置论坛板块</p>
              </button>
              <div className="p-4 text-left border border-gray-200 rounded-lg">
                <p className="font-medium text-gray-900">系统配置</p>
                <p className="text-sm text-gray-500 mt-1">即将推出</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  };

  const renderContent = (): JSX.Element => {
    switch (activeTab) {
      case 'overview':
        return renderOverview();
      case 'categories':
        return <CategoryManager />;
      case 'moderation':
        return <ContentModeration />;
      case 'users':
        return <UserManagement />;
      default:
        return renderOverview();
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* 页面标题 */}
      <div className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">论坛管理</h1>
              <p className="mt-1 text-sm text-gray-500">
                管理论坛板块、审核内容、维护社区秩序
              </p>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        {/* 标签导航 */}
        <div className="mb-6 border-b border-gray-200">
          <nav className="flex space-x-8">
            {tabs.map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`py-4 px-1 border-b-2 font-medium text-sm transition-colors ${
                  activeTab === tab.id
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                {tab.label}
              </button>
            ))}
          </nav>
        </div>

        {/* 内容区域 */}
        <div className="space-y-6">{renderContent()}</div>
      </div>
    </div>
  );
}