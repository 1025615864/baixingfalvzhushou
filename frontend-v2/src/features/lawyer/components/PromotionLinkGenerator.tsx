/**
 * 推广链接生成器组件
 * 用于律师创建和管理推广链接
 */

import React, { useState } from 'react';

import { useCreatePromotionLink, usePromotionLinks, generatePromotionUrl, copyPromotionLink } from '../hooks/usePromotions';

interface PromotionLinkGeneratorProps {
  onSuccess?: () => void;
}

export const PromotionLinkGenerator: React.FC<PromotionLinkGeneratorProps> = ({
  onSuccess,
}) => {
  const [linkName, setLinkName] = useState('');
  const [description, setDescription] = useState('');
  const [copiedId, setCopiedId] = useState<string | null>(null);

  const { data: links, isLoading } = usePromotionLinks();
  const createMutation = useCreatePromotionLink();

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!linkName.trim()) return;

    try {
      await createMutation.mutateAsync({
        linkName: linkName.trim(),
        description: description.trim() || undefined,
      });
      setLinkName('');
      setDescription('');
      onSuccess?.();
    } catch {
      // 错误由 mutation 处理
    }
  };

  const handleCopy = async (linkCode: string, linkId: string) => {
    const success = await copyPromotionLink(linkCode);
    if (success) {
      setCopiedId(linkId);
      setTimeout(() => setCopiedId(null), 2000);
    }
  };

  if (isLoading) {
    return (
      <div className="animate-pulse">
        <div className="h-8 bg-gray-200 rounded w-1/3 mb-4"></div>
        <div className="h-32 bg-gray-200 rounded"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* 创建新链接表单 */}
      <div className="bg-white shadow rounded-lg p-6">
        <h3 className="text-lg font-medium text-gray-900 mb-4">创建推广链接</h3>
        <form onSubmit={(e) => { void handleCreate(e); }} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700">
              链接名称 <span className="text-red-500">*</span>
            </label>
            <input
              type="text"
              value={linkName}
              onChange={e => setLinkName(e.target.value)}
              placeholder="例如：微信推广、朋友圈分享"
              className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700">
              描述（可选）
            </label>
            <input
              type="text"
              value={description}
              onChange={e => setDescription(e.target.value)}
              placeholder="描述这个链接的用途"
              className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
            />
          </div>

          <div className="flex justify-end">
            <button
              type="submit"
              disabled={createMutation.isPending || !linkName.trim()}
              className="px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {createMutation.isPending ? '创建中...' : '创建链接'}
            </button>
          </div>

          {createMutation.isError && (
            <p className="text-sm text-red-600">
              {createMutation.error?.message || '创建失败，请重试'}
            </p>
          )}
        </form>
      </div>

      {/* 链接列表 */}
      <div className="bg-white shadow rounded-lg overflow-hidden">
        <div className="px-6 py-4 border-b border-gray-200">
          <h3 className="text-lg font-medium text-gray-900">我的推广链接</h3>
        </div>

        {!links || links.items.length === 0 ? (
          <div className="p-6 text-center text-gray-500">
            <svg
              className="mx-auto h-12 w-12 text-gray-400 mb-3"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1"
              />
            </svg>
            <p>暂无推广链接，创建第一个链接开始推广吧！</p>
          </div>
        ) : (
          <ul className="divide-y divide-gray-200">
            {links.items.map(link => (
              <li key={link.id} className="p-6 hover:bg-gray-50">
                <div className="flex items-center justify-between">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center">
                      <h4 className="text-sm font-medium text-gray-900 truncate">
                        {link.linkName || '未命名链接'}
                      </h4>
                      <span
                        className={`ml-2 px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${
                          link.isActive
                            ? 'bg-green-100 text-green-800'
                            : 'bg-gray-100 text-gray-800'
                        }`}
                      >
                        {link.isActive ? '生效中' : '已停用'}
                      </span>
                    </div>
                    {link.description && (
                      <p className="mt-1 text-sm text-gray-500 truncate">
                        {link.description}
                      </p>
                    )}
                    <div className="mt-2 flex items-center text-sm text-gray-500 space-x-4">
                      <span>点击：{link.clickCount}</span>
                      <span>咨询：{link.consultationCount}</span>
                      <span>转化：{link.conversionCount}</span>
                    </div>
                    <div className="mt-2 flex items-center">
                      <input
                        type="text"
                        readOnly
                        value={generatePromotionUrl(link.linkCode)}
                        className="flex-1 min-w-0 block w-full px-3 py-2 rounded-l-md border border-gray-300 bg-gray-50 text-gray-500 sm:text-sm"
                      />
                      <button
                        onClick={() => { void handleCopy(link.linkCode, link.id); }}
                        className="inline-flex items-center px-4 py-2 border border-l-0 border-gray-300 rounded-r-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none"
                      >
                        {copiedId === link.id ? '已复制!' : '复制'}
                      </button>
                    </div>
                  </div>
                </div>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
};

export default PromotionLinkGenerator;