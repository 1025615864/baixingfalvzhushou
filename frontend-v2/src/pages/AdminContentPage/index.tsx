// ============================================
// 管理后台 - 内容管理页面
// ============================================

import { useState, useEffect } from 'react';

import { api } from '@/shared/lib/api/client';

interface ContentItem {
  id: number;
  title: string;
  type: string;
  author: string;
  status: string;
  created_at: string;
  views: number;
  likes: number;
}

const DEFAULT_CONTENTS: ContentItem[] = [];

export function AdminContentPage() {
  const [contents, setContents] = useState<ContentItem[]>(DEFAULT_CONTENTS);
  const [searchTerm, setSearchTerm] = useState('');
  const [typeFilter, setTypeFilter] = useState('all');
  const [statusFilter, setStatusFilter] = useState('all');

  useEffect(() => {
    const fetchContents = async () => {
      try {
        const data = await api.get<ContentItem[]>('/admin/content');
        if (data && data.length > 0) {
          setContents(data);
        }
      } catch {
        // TODO: Backend /api/admin/content not yet available, using defaults
      }
    };
    void fetchContents();
  }, []);

  const filteredContents = contents.filter((content) => {
    const matchesSearch = content.title.includes(searchTerm) || content.author.includes(searchTerm);
    const matchesType = typeFilter === 'all' || content.type === typeFilter;
    const matchesStatus = statusFilter === 'all' || content.status === statusFilter;
    return matchesSearch && matchesType && matchesStatus;
  });

  const getTypeBadge = (type: string) => {
    const styles: Record<string, string> = {
      forum_post: 'bg-blue-100 text-blue-700',
      knowledge: 'bg-green-100 text-green-700',
      news: 'bg-purple-100 text-purple-700',
      document: 'bg-amber-100 text-amber-700',
    };
    const labels: Record<string, string> = {
      forum_post: '论坛帖子',
      knowledge: '知识库',
      news: '资讯',
      document: '文档',
    };
    return (
      <span className={`px-2 py-1 rounded-full text-xs font-medium ${styles[type] || 'bg-gray-100 text-gray-700'}`}>
        {labels[type] || type}
      </span>
    );
  };

  const getStatusBadge = (status: string) => {
    const styles: Record<string, string> = {
      published: 'bg-green-100 text-green-700',
      pending: 'bg-amber-100 text-amber-700',
      reviewing: 'bg-blue-100 text-blue-700',
      flagged: 'bg-red-100 text-red-700',
      draft: 'bg-gray-100 text-gray-700',
    };
    const labels: Record<string, string> = {
      published: '已发布',
      pending: '待审核',
      reviewing: '审核中',
      flagged: '被标记',
      draft: '草稿',
    };
    return (
      <span className={`px-2 py-1 rounded-full text-xs font-medium ${styles[status] || 'bg-gray-100 text-gray-700'}`}>
        {labels[status] || status}
      </span>
    );
  };

  const getActionButtons = (status: string) => {
    if (status === 'flagged' || status === 'pending') {
      return (
        <>
          <button className="text-green-600 hover:text-green-900 mr-3">通过</button>
          <button className="text-red-600 hover:text-red-900">拒绝</button>
        </>
      );
    }
    if (status === 'published') {
      return (
        <>
          <button className="text-blue-600 hover:text-blue-900 mr-3">编辑</button>
          <button className="text-red-600 hover:text-red-900">下架</button>
        </>
      );
    }
    return (
      <>
        <button className="text-blue-600 hover:text-blue-900 mr-3">编辑</button>
        <button className="text-gray-600 hover:text-gray-900">预览</button>
      </>
    );
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* 顶部导航 */}
      <header className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center gap-4">
              <h1 className="text-xl font-bold text-gray-900">内容管理</h1>
            </div>
            <div className="flex gap-3">
              <button className="px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors flex items-center gap-2">
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                </svg>
                审核规则
              </button>
              <button className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors flex items-center gap-2">
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                </svg>
                发布内容
              </button>
            </div>
          </div>
        </div>
      </header>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* 统计卡片 */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
          <div className="bg-white rounded-lg p-4 shadow-sm border border-gray-100">
            <div className="text-sm text-gray-500 mb-1">待审核</div>
            <div className="text-2xl font-bold text-amber-600">12</div>
          </div>
          <div className="bg-white rounded-lg p-4 shadow-sm border border-gray-100">
            <div className="text-sm text-gray-500 mb-1">已标记</div>
            <div className="text-2xl font-bold text-red-600">5</div>
          </div>
          <div className="bg-white rounded-lg p-4 shadow-sm border border-gray-100">
            <div className="text-sm text-gray-500 mb-1">今日发布</div>
            <div className="text-2xl font-bold text-green-600">28</div>
          </div>
          <div className="bg-white rounded-lg p-4 shadow-sm border border-gray-100">
            <div className="text-sm text-gray-500 mb-1">总内容数</div>
            <div className="text-2xl font-bold text-blue-600">1,234</div>
          </div>
        </div>

        {/* 筛选栏 */}
        <div className="bg-white rounded-lg p-4 shadow-sm border border-gray-100 mb-6">
          <div className="flex flex-wrap items-center gap-4">
            <div className="flex-1 min-w-[200px]">
              <input
                type="text"
                placeholder="搜索标题或作者..."
                value={searchTerm}
                onChange={(e) => { setSearchTerm(e.target.value); }}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>
            <select
              value={typeFilter}
              onChange={(e) => { setTypeFilter(e.target.value); }}
              className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
            >
              <option value="all">全部类型</option>
              <option value="forum_post">论坛帖子</option>
              <option value="knowledge">知识库</option>
              <option value="news">资讯</option>
              <option value="document">文档</option>
            </select>
            <select
              value={statusFilter}
              onChange={(e) => { setStatusFilter(e.target.value); }}
              className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
            >
              <option value="all">全部状态</option>
              <option value="published">已发布</option>
              <option value="pending">待审核</option>
              <option value="reviewing">审核中</option>
              <option value="flagged">被标记</option>
            </select>
          </div>
        </div>

        {/* 内容列表 */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-100 overflow-hidden">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">标题</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">类型</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">作者</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">状态</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">数据</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">发布时间</th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">操作</th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {filteredContents.map((content) => (
                <tr key={content.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4">
                    <div className="text-sm font-medium text-gray-900 max-w-md truncate">{content.title}</div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    {getTypeBadge(content.type)}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-sm text-gray-900">{content.author}</div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    {getStatusBadge(content.status)}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-sm text-gray-500">
                      <span className="mr-3">👁 {content.views}</span>
                      <span>❤️ {content.likes}</span>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {content.created_at}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                    {getActionButtons(content.status)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          
          {/* 分页 */}
          <div className="px-6 py-4 border-t border-gray-200 flex items-center justify-between">
            <div className="text-sm text-gray-500">
              显示 1 到 {filteredContents.length} 条，共 {filteredContents.length} 条
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