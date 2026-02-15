/**
 * 推广统计组件
 * 展示推广链接的统计数据
 */

import React from 'react';

import { usePromotionLinkStats } from '../hooks/usePromotions';
import { generatePromotionUrl } from '../hooks/usePromotions';

interface PromotionStatsProps {
  linkId: string;
  linkCode: string;
  linkName: string | null;
}

export const PromotionStats: React.FC<PromotionStatsProps> = ({
  linkId,
  linkCode,
  linkName,
}) => {
  const { data: stats, isLoading, isError } = usePromotionLinkStats(linkId);

  if (isLoading) {
    return (
      <div className="bg-white shadow rounded-lg p-6 animate-pulse">
        <div className="h-4 bg-gray-200 rounded w-1/3 mb-4"></div>
        <div className="grid grid-cols-4 gap-4">
          {[1, 2, 3, 4].map(i => (
            <div key={i} className="h-20 bg-gray-200 rounded"></div>
          ))}
        </div>
      </div>
    );
  }

  if (isError || !stats) {
    return (
      <div className="bg-white shadow rounded-lg p-6">
        <div className="text-center text-gray-500">
          <p>无法加载统计数据</p>
        </div>
      </div>
    );
  }

  const statCards = [
    {
      title: '总点击',
      value: stats.clickCount,
      icon: (
        <svg className="h-6 w-6 text-blue-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
        </svg>
      ),
      color: 'blue',
    },
    {
      title: '咨询数',
      value: stats.consultationCount,
      icon: (
        <svg className="h-6 w-6 text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
        </svg>
      ),
      color: 'green',
    },
    {
      title: '转化数',
      value: stats.conversionCount,
      icon: (
        <svg className="h-6 w-6 text-purple-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
      ),
      color: 'purple',
    },
    {
      title: '转化率',
      value: `${(stats.conversionRate * 100).toFixed(1)}%`,
      icon: (
        <svg className="h-6 w-6 text-orange-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
        </svg>
      ),
      color: 'orange',
    },
  ];

  return (
    <div className="bg-white shadow rounded-lg p-6">
      <div className="mb-6">
        <h3 className="text-lg font-medium text-gray-900">
          {linkName || '未命名链接'} 统计数据
        </h3>
        <p className="mt-1 text-sm text-gray-500">
          链接代码: {linkCode}
        </p>
        <p className="mt-1 text-sm text-gray-500">
          推广链接: {generatePromotionUrl(linkCode)}
        </p>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {statCards.map((card, index) => (
          <div
            key={index}
            className={`bg-${card.color}-50 rounded-lg p-4 border border-${card.color}-100`}
          >
            <div className="flex items-center">
              <div className={`flex-shrink-0 p-2 bg-${card.color}-100 rounded-md`}>
                {card.icon}
              </div>
              <div className="ml-3">
                <p className="text-sm font-medium text-gray-500">{card.title}</p>
                <p className="text-2xl font-semibold text-gray-900">{card.value}</p>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* 转化漏斗图 */}
      <div className="mt-6">
        <h4 className="text-sm font-medium text-gray-900 mb-4">转化漏斗</h4>
        <div className="space-y-3">
          <div>
            <div className="flex justify-between text-sm mb-1">
              <span className="text-gray-600">点击 → 咨询</span>
              <span className="text-gray-900 font-medium">
                {stats.clickCount > 0
                  ? ((stats.consultationCount / stats.clickCount) * 100).toFixed(1)
                  : 0}%
              </span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div
                className="bg-green-500 h-2 rounded-full"
                style={{
                  width: `${stats.clickCount > 0
                    ? (stats.consultationCount / stats.clickCount) * 100
                    : 0}%`,
                }}
              />
            </div>
          </div>

          <div>
            <div className="flex justify-between text-sm mb-1">
              <span className="text-gray-600">咨询 → 转化</span>
              <span className="text-gray-900 font-medium">
                {stats.consultationCount > 0
                  ? ((stats.conversionCount / stats.consultationCount) * 100).toFixed(1)
                  : 0}%
              </span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div
                className="bg-purple-500 h-2 rounded-full"
                style={{
                  width: `${stats.consultationCount > 0
                    ? (stats.conversionCount / stats.consultationCount) * 100
                    : 0}%`,
                }}
              />
            </div>
          </div>

          <div>
            <div className="flex justify-between text-sm mb-1">
              <span className="text-gray-600">点击 → 转化</span>
              <span className="text-gray-900 font-medium">
                {(stats.conversionRate * 100).toFixed(1)}%
              </span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div
                className="bg-orange-500 h-2 rounded-full"
                style={{ width: `${stats.conversionRate * 100}%` }}
              />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default PromotionStats;