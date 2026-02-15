import { useState } from 'react';

import { useUserProfile, useUserStats } from '@/features/user/hooks/useUserProfile';

export function ProfilePage(): JSX.Element {
  const { data: profile, isLoading: profileLoading } = useUserProfile();
  const { data: stats, isLoading: statsLoading } = useUserStats();
  const [activeTab, setActiveTab] = useState<'overview' | 'consultations' | 'documents'>('overview');

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
            <div className="text-center py-8 text-gray-500">
              <p>暂无咨询记录</p>
            </div>
          )}

          {activeTab === 'documents' && (
            <div className="text-center py-8 text-gray-500">
              <p>暂无文档</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}