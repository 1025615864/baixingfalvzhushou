/**
 * PromotionPanel - 推广面板组件
 */

import { useState } from 'react';

import { PromotionLink } from './PromotionLink';
import { PromotionStats } from './PromotionStats';
import { PromotionList } from './PromotionList';
import { QRCodeGenerator } from './QRCodeGenerator';

interface PromotionPanelProps {
  className?: string;
}

type TabType = 'link' | 'stats' | 'records' | 'qrcode';

/**
 * 推广面板组件
 */
export function PromotionPanel({ className = '' }: PromotionPanelProps): JSX.Element {
  const [activeTab, setActiveTab] = useState<TabType>('link');

  const tabs: { key: TabType; label: string }[] = [
    { key: 'link', label: '推广链接' },
    { key: 'stats', label: '数据统计' },
    { key: 'records', label: '佣金记录' },
    { key: 'qrcode', label: '二维码' },
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
        {activeTab === 'link' && <PromotionLink className="max-w-2xl mx-auto" />}

        {activeTab === 'stats' && <PromotionStats />}

        {activeTab === 'records' && <PromotionList />}

        {activeTab === 'qrcode' && (
          <div className="max-w-md mx-auto">
            <QRCodeGenerator
              value={`${window.location.origin}/register?ref=${Date.now()}`}
              title="扫码注册"
              description="扫描二维码快速注册成为会员"
              size={250}
              className="flex justify-center"
            />
          </div>
        )}
      </div>
    </div>
  );
}