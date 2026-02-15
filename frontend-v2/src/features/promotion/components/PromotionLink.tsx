/**
 * PromotionLink - 推广链接生成组件
 */

import { useState } from 'react';

import { usePromotionLink, useGeneratePromotionLink } from '../hooks/usePromotion';

interface PromotionLinkProps {
  className?: string;
}

/**
 * 推广链接生成组件
 */
export function PromotionLink({ className = '' }: PromotionLinkProps): JSX.Element {
  const { data: link, isLoading, error } = usePromotionLink();
  const generateMutation = useGeneratePromotionLink();
  const [copied, setCopied] = useState(false);

  /**
   * 复制链接到剪贴板
   */
  const handleCopyLink = async (): Promise<void> => {
    if (link?.url) {
      await navigator.clipboard.writeText(link.url);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  /**
   * 生成新链接
   */
  const handleGenerateLink = (): void => {
    generateMutation.mutate();
  };

  if (isLoading) {
    return (
      <div className={`bg-white rounded-xl shadow-sm p-6 ${className}`}>
        <div className="animate-pulse space-y-4">
          <div className="h-4 bg-gray-200 rounded w-1/3" />
          <div className="h-10 bg-gray-200 rounded" />
          <div className="flex gap-2">
            <div className="h-10 bg-gray-200 rounded flex-1" />
            <div className="h-10 bg-gray-200 rounded w-24" />
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className={`bg-white rounded-xl shadow-sm p-6 ${className}`}>
        <div className="text-center text-red-500">
          <p>获取推广链接失败</p>
          <button
            onClick={handleGenerateLink}
            disabled={generateMutation.isPending}
            className="mt-4 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
          >
            {generateMutation.isPending ? '生成中...' : '生成推广链接'}
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className={`bg-white rounded-xl shadow-sm p-6 ${className}`}>
      <h3 className="text-lg font-semibold text-gray-900 mb-4">我的推广链接</h3>

      {link ? (
        <div className="space-y-4">
          {/* 链接显示 */}
          <div className="flex items-center gap-2 p-3 bg-gray-50 rounded-lg border">
            <input
              type="text"
              value={link.url}
              readOnly
              className="flex-1 bg-transparent text-sm text-gray-600 outline-none"
            />
            <button
              onClick={() => void handleCopyLink()}
              className="px-3 py-1.5 text-sm font-medium text-blue-600 hover:text-blue-700 whitespace-nowrap"
            >
              {copied ? '已复制!' : '复制'}
            </button>
          </div>

          {/* 统计信息 */}
          <div className="grid grid-cols-2 gap-4">
            <div className="text-center p-3 bg-blue-50 rounded-lg">
              <div className="text-2xl font-bold text-blue-600">{link.clickCount}</div>
              <div className="text-sm text-gray-500">点击次数</div>
            </div>
            <div className="text-center p-3 bg-green-50 rounded-lg">
              <div className="text-2xl font-bold text-green-600">{link.conversionCount}</div>
              <div className="text-sm text-gray-500">转化次数</div>
            </div>
          </div>

          {/* 重新生成按钮 */}
          <button
            onClick={handleGenerateLink}
            disabled={generateMutation.isPending}
            className="w-full px-4 py-2 text-sm font-medium text-gray-600 bg-gray-100 rounded-lg hover:bg-gray-200 disabled:opacity-50"
          >
            {generateMutation.isPending ? '生成中...' : '重新生成链接'}
          </button>
        </div>
      ) : (
        <div className="text-center py-8">
          <div className="w-16 h-16 mx-auto mb-4 bg-blue-100 rounded-full flex items-center justify-center">
            <svg
              className="w-8 h-8 text-blue-600"
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
          </div>
          <p className="text-gray-500 mb-4">您还没有推广链接</p>
          <button
            onClick={handleGenerateLink}
            disabled={generateMutation.isPending}
            className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
          >
            {generateMutation.isPending ? '生成中...' : '生成推广链接'}
          </button>
        </div>
      )}
    </div>
  );
}