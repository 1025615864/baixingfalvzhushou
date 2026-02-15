/**
 * EnterprisePanel - 企业综合面板组件
 */

import { useState } from 'react';

import type { ContractReview } from '../types';
import { useContractReviews } from '../hooks/useEnterprise';

import { ComplianceDashboard } from './ComplianceDashboard';
import { ComplianceCheckList } from './ComplianceCheckList';
import { ComplianceReport } from './ComplianceReport';
import { DocumentManager } from './DocumentManager';
import { TeamManager } from './TeamManager';
import { EnterpriseInfo } from './EnterpriseInfo';

interface EnterprisePanelProps {
  accountId: number;
  className?: string;
}

type TabType = 'overview' | 'compliance' | 'documents' | 'team' | 'settings';

/**
 * 企业综合面板组件
 */
export function EnterprisePanel({ accountId, className = '' }: EnterprisePanelProps): JSX.Element {
  const [activeTab, setActiveTab] = useState<TabType>('overview');
  const [selectedReview, setSelectedReview] = useState<ContractReview | null>(null);

  const { data: reviews, isLoading: reviewsLoading } = useContractReviews(accountId);

  const tabs: { key: TabType; label: string }[] = [
    { key: 'overview', label: '概览' },
    { key: 'compliance', label: '合规' },
    { key: 'documents', label: '文档' },
    { key: 'team', label: '团队' },
    { key: 'settings', label: '设置' },
  ];

  return (
    <div className={`bg-white rounded-xl shadow-sm ${className}`}>
      {/* 标签导航 */}
      <div className="border-b border-gray-200">
        <nav className="flex -mb-px">
          {tabs.map((tab) => (
            <button
              key={tab.key}
              onClick={() => setActiveTab(tab.key)}
              className={`px-6 py-4 text-sm font-medium border-b-2 transition-colors ${
                activeTab === tab.key
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
      <div className="p-6">
        {activeTab === 'overview' && (
          <div className="space-y-6">
            <ComplianceDashboard accountId={accountId} />
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <ComplianceCheckList
                reviews={reviews || []}
                isLoading={reviewsLoading}
                onReviewClick={setSelectedReview}
              />
              <ComplianceReport review={selectedReview} />
            </div>
          </div>
        )}

        {activeTab === 'compliance' && (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <ComplianceCheckList
              reviews={reviews || []}
              isLoading={reviewsLoading}
              onReviewClick={setSelectedReview}
            />
            <ComplianceReport review={selectedReview} />
          </div>
        )}

        {activeTab === 'documents' && (
          <DocumentManager
            documents={[]}
            onUpload={(file) => { void file; }}
            onDelete={(id) => { void id; }}
            onDownload={(id) => { void id; }}
          />
        )}

        {activeTab === 'team' && <TeamManager accountId={accountId} />}

        {activeTab === 'settings' && <EnterpriseInfo accountId={accountId} />}
      </div>
    </div>
  );
}