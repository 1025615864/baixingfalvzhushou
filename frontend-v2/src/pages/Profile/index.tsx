import { useState } from 'react';
import { Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';

import { useUserProfile, useUserStats } from '@/features/user/hooks/useUserProfile';
import { apiGetSessions } from '@/features/ai-consultation/api';
import { apiGetMyDocuments } from '@/features/document/api';
import type { AISession } from '@/features/ai-consultation/types';
import type { DocumentItem } from '@/features/document/types';

export function ProfilePage(): JSX.Element {
  const { data: profile, isLoading: profileLoading } = useUserProfile();
  const { data: stats, isLoading: statsLoading } = useUserStats();
  const [activeTab, setActiveTab] = useState<'overview' | 'consultations' | 'documents'>('overview');

  // 获取用户咨询记录
  const { data: consultationsData, isLoading: consultationsLoading } = useQuery({
    queryKey: ['user', 'consultations'],
    queryFn: () => apiGetSessions({ page: 1, pageSize: 10 }),
    enabled: activeTab === 'consultations',
    staleTime: 5 * 60 * 1000,
  });

  // 获取用户文档列表
  const { data: documentsData, isLoading: documentsLoading } = useQuery({
    queryKey: ['user', 'documents'],
    queryFn: () => apiGetMyDocuments({ page: 1, pageSize: 10 }),
    enabled: activeTab === 'documents',
    staleTime: 5 * 60 * 1000,
  });

  if (profileLoading || statsLoading) {
    return (
      <div className="container mx-auto px-4 py-6 max-w-5xl">
        <div className="animate-pulse space-y-4">
          <div className="h-32 bg-gray-200 rounded-lg" />
          <div className="h-64 bg-gray-200 rounded-lg" />
        </div>
      </div>
    );
  }

  if (!profile) {
    return (
      <div className="container mx-auto px-4 py-6 max-w-5xl">
        <p className="text-center text-gray-500">加载失败</p>
      </div>
    );
  }

  const tabs = [
    { key: 'overview' as const, label: '概览' },
    { key: 'consultations' as const, label: '我的咨询' },
    { key: 'documents' as const, label: '我的文档' },
  ];

  return (
    <div className="container mx-auto px-4 py-6 max-w-5xl">
      {/* Profile Header */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 mb-6">
        <div className="flex items-start gap-6">
          {/* Avatar */}
          <div className="flex-shrink-0">
            <div className="w-24 h-24 rounded-full bg-primary-100 flex items-center justify-center text-3xl font-bold text-primary-600">
              {profile.avatar ? (
                <img
                  src={profile.avatar}
                  alt={profile.name}
                  className="w-24 h-24 rounded-full object-cover"
                />
              ) : (
                profile.name.charAt(0)
              )}
            </div>
          </div>

          {/* Info */}
          <div className="flex-1">
            <div className="flex items-center gap-3 mb-2">
              <h1 className="text-2xl font-bold text-gray-900">{profile.name}</h1>
              {profile.isVerified && (
                <span className="px-2 py-0.5 bg-blue-50 text-blue-600 text-sm rounded">
                  已认证
                </span>
              )}
            </div>
            
            <p className="text-gray-600 mb-4">{profile.bio || '暂无个人简介'}</p>
            
            <div className="flex flex-wrap gap-4 text-sm text-gray-500">
              <span>📧 {profile.email}</span>
              {profile.phone && <span>📱 {profile.phone}</span>}
              {profile.location && <span>📍 {profile.location}</span>}
              {profile.company && <span>🏢 {profile.company}</span>}
            </div>
          </div>

          {/* Stats */}
          {stats && (
            <div className="flex-shrink-0 grid grid-cols-2 gap-4 text-center">
              <div className="bg-gray-50 rounded-lg p-4">
                <p className="text-2xl font-bold text-primary-600">{stats.consultationCount}</p>
                <p className="text-sm text-gray-500">咨询次数</p>
              </div>
              <div className="bg-gray-50 rounded-lg p-4">
                <p className="text-2xl font-bold text-primary-600">¥{stats.totalSpent}</p>
                <p className="text-sm text-gray-500">总消费</p>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Tabs */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200">
        <div className="border-b border-gray-200">
          <div className="flex">
            {tabs.map((tab) => (
              <button
                key={tab.key}
                onClick={(): void => setActiveTab(tab.key)}
                className={`px-6 py-3 text-sm font-medium border-b-2 transition-colors ${
                  activeTab === tab.key
                    ? 'border-primary-600 text-primary-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700'
                }`}
                type="button"
              >
                {tab.label}
              </button>
            ))}
          </div>
        </div>

        {/* Tab Content */}
        <div className="p-6">
          {activeTab === 'overview' && (
            <div className="space-y-6">
              <section>
                <h2 className="text-lg font-semibold text-gray-900 mb-3">基本信息</h2>
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <span className="text-gray-500">注册时间：</span>
                    <span>{new Date(profile.createdAt).toLocaleDateString('zh-CN')}</span>
                  </div>
                  <div>
                    <span className="text-gray-500">最后更新：</span>
                    <span>{new Date(profile.updatedAt).toLocaleDateString('zh-CN')}</span>
                  </div>
                  {profile.title && (
                    <div>
                      <span className="text-gray-500">职位：</span>
                      <span>{profile.title}</span>
                    </div>
                  )}
                  {profile.website && (
                    <div>
                      <span className="text-gray-500">网站：</span>
                      <a href={profile.website} className="text-primary-600 hover:underline">
                        {profile.website}
                      </a>
                    </div>
                  )}
                </div>
              </section>
            </div>
          )}

          {activeTab === 'consultations' && (
            <div className="space-y-4">
              <h2 className="text-lg font-semibold text-gray-900 mb-3">我的咨询记录</h2>
              
              {consultationsLoading ? (
                <div className="space-y-3">
                  {[1, 2, 3].map((i) => (
                    <div key={i} className="animate-pulse bg-gray-100 rounded-lg p-4">
                      <div className="h-4 bg-gray-200 rounded w-3/4 mb-2" />
                      <div className="h-3 bg-gray-200 rounded w-1/2" />
                    </div>
                  ))}
                </div>
              ) : consultationsData?.sessions && consultationsData.sessions.length > 0 ? (
                <div className="space-y-3">
                  {consultationsData.sessions.map((session: AISession) => (
                    <Link
                      key={session.id}
                      to={`/ai-consultation?sessionId=${session.id}`}
                      className="block bg-gray-50 rounded-lg p-4 hover:bg-gray-100 transition-colors"
                    >
                      <div className="flex items-start justify-between">
                        <div className="flex-1 min-w-0">
                          <h3 className="text-sm font-medium text-gray-900 truncate">
                            {session.title || '未命名咨询'}
                          </h3>
                          <p className="text-xs text-gray-500 mt-1">
                            {new Date(session.createdAt).toLocaleDateString('zh-CN', {
                              year: 'numeric',
                              month: 'long',
                              day: 'numeric',
                              hour: '2-digit',
                              minute: '2-digit',
                            })}
                          </p>
                          {session.context?.category && (
                            <span className="inline-block mt-2 px-2 py-0.5 bg-blue-50 text-blue-600 text-xs rounded">
                              {session.context.category}
                            </span>
                          )}
                        </div>
                        <div className="flex items-center gap-2 ml-4">
                          <span className={`px-2 py-0.5 text-xs rounded ${
                            session.status === 'active'
                              ? 'bg-green-50 text-green-600'
                              : 'bg-gray-100 text-gray-500'
                          }`}>
                            {session.status === 'active' ? '进行中' : '已归档'}
                          </span>
                          <svg className="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                          </svg>
                        </div>
                      </div>
                    </Link>
                  ))}
                  
                  {consultationsData.totalPages > 1 && (
                    <div className="text-center pt-4">
                      <Link
                        to="/ai-consultation"
                        className="text-sm text-primary-600 hover:text-primary-700"
                      >
                        查看全部 {consultationsData.total} 条记录 →
                      </Link>
                    </div>
                  )}
                </div>
              ) : (
                <div className="text-center py-8">
                  <div className="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-4">
                    <svg className="w-8 h-8 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
                    </svg>
                  </div>
                  <p className="text-gray-500 mb-4">暂无咨询记录</p>
                  <Link
                    to="/ai-consultation"
                    className="inline-flex items-center px-4 py-2 bg-primary-600 text-white text-sm rounded-lg hover:bg-primary-700 transition-colors"
                  >
                    开始咨询
                  </Link>
                </div>
              )}
            </div>
          )}

          {activeTab === 'documents' && (
            <div className="space-y-4">
              <h2 className="text-lg font-semibold text-gray-900 mb-3">我的文档</h2>
              
              {documentsLoading ? (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {[1, 2, 3, 4].map((i) => (
                    <div key={i} className="animate-pulse bg-gray-100 rounded-lg p-4">
                      <div className="h-4 bg-gray-200 rounded w-3/4 mb-2" />
                      <div className="h-3 bg-gray-200 rounded w-1/2" />
                    </div>
                  ))}
                </div>
              ) : documentsData?.items && documentsData.items.length > 0 ? (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {documentsData.items.map((doc: DocumentItem) => (
                    <Link
                      key={doc.id}
                      to={`/document/${doc.id}`}
                      className="block bg-gray-50 rounded-lg p-4 hover:bg-gray-100 transition-colors"
                    >
                      <div className="flex items-start gap-3">
                        <div className="flex-shrink-0 w-10 h-10 bg-blue-50 rounded-lg flex items-center justify-center">
                          <svg className="w-5 h-5 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                          </svg>
                        </div>
                        <div className="flex-1 min-w-0">
                          <h3 className="text-sm font-medium text-gray-900 truncate">
                            {doc.title}
                          </h3>
                          <p className="text-xs text-gray-500 mt-1">
                            {new Date(doc.createdAt).toLocaleDateString('zh-CN', {
                              year: 'numeric',
                              month: 'long',
                              day: 'numeric',
                            })}
                          </p>
                          <span className="inline-block mt-2 px-2 py-0.5 bg-gray-200 text-gray-600 text-xs rounded">
                            {doc.documentType}
                          </span>
                        </div>
                        <svg className="w-4 h-4 text-gray-400 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                        </svg>
                      </div>
                    </Link>
                  ))}
                </div>
              ) : (
                <div className="text-center py-8">
                  <div className="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-4">
                    <svg className="w-8 h-8 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                    </svg>
                  </div>
                  <p className="text-gray-500 mb-4">暂无文档</p>
                  <Link
                    to="/document"
                    className="inline-flex items-center px-4 py-2 bg-primary-600 text-white text-sm rounded-lg hover:bg-primary-700 transition-colors"
                  >
                    生成文档
                  </Link>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}