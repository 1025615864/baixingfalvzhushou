/**
 * FAQDetail - FAQ详情组件
 */

import React from 'react';
import { ArrowLeft, Eye, Clock, Tag, CheckCircle } from 'lucide-react';

import type { FAQDetailProps } from '../types';

/**
 * 格式化日期
 */
function formatDate(dateString: string): string {
  const date = new Date(dateString);
  return date.toLocaleDateString('zh-CN', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
  });
}

/**
 * FAQ详情组件
 */
export const FAQDetail: React.FC<FAQDetailProps> = ({
  item,
  loading = false,
  onBack,
}) => {
  if (loading) {
    return (
      <div className="rounded-lg border border-gray-200 bg-white p-6">
        <div className="space-y-4">
          <div className="h-6 w-1/4 animate-pulse rounded bg-gray-200" />
          <div className="h-8 w-3/4 animate-pulse rounded bg-gray-200" />
          <div className="space-y-2">
            <div className="h-4 w-full animate-pulse rounded bg-gray-200" />
            <div className="h-4 w-full animate-pulse rounded bg-gray-200" />
            <div className="h-4 w-2/3 animate-pulse rounded bg-gray-200" />
          </div>
        </div>
      </div>
    );
  }

  if (!item) {
    return (
      <div className="flex flex-col items-center justify-center rounded-lg border border-dashed border-gray-300 bg-gray-50 py-16">
        <div className="rounded-full bg-gray-100 p-4">
          <CheckCircle className="h-8 w-8 text-gray-400" />
        </div>
        <p className="mt-4 text-gray-500">选择一个FAQ查看详情</p>
      </div>
    );
  }

  return (
    <article className="rounded-lg border border-gray-200 bg-white">
      {/* 头部 */}
      <div className="border-b border-gray-100 p-6">
        {onBack && (
          <button
            onClick={onBack}
            className="mb-4 flex items-center gap-2 text-sm text-gray-500 transition-colors hover:text-gray-700"
          >
            <ArrowLeft className="h-4 w-4" />
            返回列表
          </button>
        )}
        
        {/* 分类标签 */}
        {item.category && (
          <span className="mb-3 inline-block rounded-full bg-blue-100 px-3 py-1 text-sm font-medium text-blue-700">
            {item.category}
          </span>
        )}
        
        {/* 问题标题 */}
        <h1 className="text-xl font-semibold text-gray-900 md:text-2xl">
          {item.question}
        </h1>
        
        {/* 元信息 */}
        <div className="mt-4 flex flex-wrap items-center gap-4 text-sm text-gray-500">
          <span className="flex items-center gap-1.5">
            <Eye className="h-4 w-4" />
            {item.viewCount.toLocaleString()} 次浏览
          </span>
          <span className="flex items-center gap-1.5">
            <Clock className="h-4 w-4" />
            更新于 {formatDate(item.updatedAt)}
          </span>
          {!item.isActive && (
            <span className="rounded-full bg-gray-100 px-2 py-0.5 text-xs text-gray-600">
              未激活
            </span>
          )}
        </div>
      </div>
      
      {/* 答案内容 */}
      <div className="p-6">
        <div className="prose prose-gray max-w-none">
          <div className="whitespace-pre-wrap text-gray-700 leading-relaxed">
            {item.answer}
          </div>
        </div>
        
        {/* 标签 */}
        {item.tags && item.tags.length > 0 && (
          <div className="mt-8 pt-6 border-t border-gray-100">
            <div className="flex items-center gap-2 text-sm text-gray-500 mb-2">
              <Tag className="h-4 w-4" />
              相关标签
            </div>
            <div className="flex flex-wrap gap-2">
              {item.tags.map((tag, index) => (
                <span
                  key={index}
                  className="rounded-md bg-gray-100 px-2.5 py-1 text-sm text-gray-600"
                >
                  {tag}
                </span>
              ))}
            </div>
          </div>
        )}
      </div>
      
      {/* 底部信息 */}
      <div className="border-t border-gray-100 bg-gray-50 px-6 py-3">
        <div className="flex items-center justify-between text-xs text-gray-400">
          <span>ID: {item.id}</span>
          <span>优先级: {item.priority}</span>
        </div>
      </div>
    </article>
  );
};

FAQDetail.displayName = 'FAQDetail';