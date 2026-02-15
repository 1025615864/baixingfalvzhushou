/**
 * 推广链接管理页面
 */

import React, { useState } from 'react';

import { PromotionLinkGenerator } from '../components/PromotionLinkGenerator';
import { PromotionStats } from '../components/PromotionStats';
import { usePromotionLinks, useDeletePromotionLink } from '../hooks/usePromotions';
import type { LawyerPromotionLink } from '../types';

export const PromotionPage: React.FC = () => {
  const [selectedLinkId, setSelectedLinkId] = useState<string | null>(null);
  const { data: linksData, isLoading } = usePromotionLinks();
  const deleteMutation = useDeletePromotionLink();

  const handleDelete = async (linkId: string) => {
    if (window.confirm('确定要删除这个推广链接吗？')) {
      try {
        await deleteMutation.mutateAsync(linkId);
      } catch {
        // 错误已在hook中处理
      }
    }
  };

  const handleCopyLink = (linkCode: string) => {
    const baseUrl = window.location.origin;
    const fullUrl = `${baseUrl}/promo/${linkCode}`;
    void navigator.clipboard.writeText(fullUrl).then(() => {
      alert('链接已复制到剪贴板');
    });
  };

  const selectedLink = linksData?.items.find(link => link.id === selectedLinkId);

  return (
    <div className="max-w-6xl mx-auto py-8 px-4 sm:px-6 lg:px-8">
      {/* 页面标题 */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">推广链接管理</h1>
        <p className="mt-2 text-gray-600">
          创建和管理您的个人推广链接，追踪推广效果
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* 左侧：创建链接 */}
        <div className="lg:col-span-1">
          <PromotionLinkGenerator />
          
          {/* 使用说明 */}
          <div className="mt-6 bg-blue-50 rounded-lg p-4">
            <h3 className="text-sm font-medium text-blue-900 mb-2">使用说明</h3>
            <ul className="text-sm text-blue-700 space-y-1">
              <li>• 创建专属推广链接分享给客户</li>
              <li>• 通过链接访问的用户会被记录</li>
              <li>• 客户预约咨询后计入转化</li>
              <li>• 定期查看统计优化推广策略</li>
            </ul>
          </div>
        </div>

        {/* 右侧：链接列表和统计 */}
        <div className="lg:col-span-2 space-y-6">
          {/* 链接列表 */}
          <div className="bg-white shadow rounded-lg">
            <div className="px-6 py-4 border-b border-gray-200">
              <h2 className="text-lg font-medium text-gray-900">我的推广链接</h2>
            </div>

            {isLoading ? (
              <div className="p-6 text-center">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
              </div>
            ) : linksData?.items.length === 0 ? (
              <div className="p-6 text-center text-gray-500">
                暂无推广链接，请在左侧创建
              </div>
            ) : (
              <div className="divide-y divide-gray-200">
                {linksData?.items.map((link: LawyerPromotionLink) => (
                  <div
                    key={link.id}
                    className={`p-6 hover:bg-gray-50 cursor-pointer ${
                      selectedLinkId === link.id ? 'bg-blue-50' : ''
                    }`}
                    onClick={() => setSelectedLinkId(link.id)}
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex-1">
                        <div className="flex items-center">
                          <h3 className="text-sm font-medium text-gray-900">
                            {link.linkName || '未命名链接'}
                          </h3>
                          <span
                            className={`ml-2 inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${
                              link.isActive
                                ? 'bg-green-100 text-green-800'
                                : 'bg-gray-100 text-gray-800'
                            }`}
                          >
                            {link.isActive ? '生效中' : '已停用'}
                          </span>
                        </div>
                        {link.description && (
                          <p className="mt-1 text-sm text-gray-500">
                            {link.description}
                          </p>
                        )}
                        <div className="mt-2 flex items-center space-x-4 text-sm text-gray-500">
                          <span>点击: {link.clickCount}</span>
                          <span>咨询: {link.consultationCount}</span>
                          <span>转化: {link.conversionCount}</span>
                        </div>
                      </div>
                      <div className="ml-4 flex items-center space-x-2">
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            handleCopyLink(link.linkCode);
                          }}
                          className="p-2 text-gray-400 hover:text-gray-600"
                          title="复制链接"
                        >
                          <svg
                            className="w-5 h-5"
                            fill="none"
                            stroke="currentColor"
                            viewBox="0 0 24 24"
                          >
                            <path
                              strokeLinecap="round"
                              strokeLinejoin="round"
                              strokeWidth={2}
                              d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z"
                            />
                          </svg>
                        </button>
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            void handleDelete(link.id);
                          }}
                          className="p-2 text-gray-400 hover:text-red-600"
                          title="删除链接"
                        >
                          <svg
                            className="w-5 h-5"
                            fill="none"
                            stroke="currentColor"
                            viewBox="0 0 24 24"
                          >
                            <path
                              strokeLinecap="round"
                              strokeLinejoin="round"
                              strokeWidth={2}
                              d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"
                            />
                          </svg>
                        </button>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* 选中链接的统计 */}
          {selectedLink && (
            <PromotionStats
              linkId={selectedLink.id}
              linkCode={selectedLink.linkCode}
              linkName={selectedLink.linkName}
            />
          )}
        </div>
      </div>
    </div>
  );
};

export default PromotionPage;