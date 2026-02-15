/**
 * EnterprisePage - 企业服务页面
 */

import { useState } from 'react';

import { EnterpriseInfo } from '../components/EnterpriseInfo';
import { TeamManager } from '../components/TeamManager';
import { EnterpriseOrders } from '../components/EnterpriseOrders';
import { PermissionSettings } from '../components/PermissionSettings';

// 示例企业ID，实际项目中应该从路由参数或用户状态获取
const MOCK_ACCOUNT_ID = 1;

type TabType = 'info' | 'team' | 'orders' | 'permissions';

interface TabItem {
  id: TabType;
  label: string;
  icon: JSX.Element;
}

const tabs: TabItem[] = [
  {
    id: 'info',
    label: '企业信息',
    icon: (
      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
      </svg>
    ),
  },
  {
    id: 'team',
    label: '团队管理',
    icon: (
      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z" />
      </svg>
    ),
  },
  {
    id: 'orders',
    label: '企业订单',
    icon: (
      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
      </svg>
    ),
  },
  {
    id: 'permissions',
    label: '权限设置',
    icon: (
      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
      </svg>
    ),
  },
];

/**
 * 企业服务页面
 */
export function EnterprisePage(): JSX.Element {
  const [activeTab, setActiveTab] = useState<TabType>('info');

  const renderContent = (): JSX.Element => {
    switch (activeTab) {
      case 'info':
        return <EnterpriseInfo accountId={MOCK_ACCOUNT_ID} />;
      case 'team':
        return <TeamManager accountId={MOCK_ACCOUNT_ID} />;
      case 'orders':
        return <EnterpriseOrders accountId={MOCK_ACCOUNT_ID} />;
      case 'permissions':
        return <PermissionSettings accountId={MOCK_ACCOUNT_ID} />;
      default:
        return <EnterpriseInfo accountId={MOCK_ACCOUNT_ID} />;
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 py-8 px-4 sm:px-6 lg:px-8">
      {/* 页面头部 */}
      <div className="max-w-7xl mx-auto mb-8">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">企业服务</h1>
            <p className="mt-2 text-sm text-gray-600">
              管理您的企业账号、团队成员和订阅服务
            </p>
          </div>
        </div>
      </div>

      {/* 标签页导航 */}
      <div className="max-w-7xl mx-auto">
        <div className="flex flex-wrap gap-2 mb-6">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex items-center gap-2 px-4 py-2.5 rounded-lg text-sm font-medium transition-colors ${
                activeTab === tab.id
                  ? 'bg-blue-600 text-white shadow-sm'
                  : 'bg-white text-gray-600 hover:text-gray-900 hover:bg-gray-50'
              }`}
            >
              {tab.icon}
              {tab.label}
            </button>
          ))}
        </div>

        {/* 内容区域 */}
        <div className="min-h-[500px]">
          {renderContent()}
        </div>
      </div>
    </div>
  );
}