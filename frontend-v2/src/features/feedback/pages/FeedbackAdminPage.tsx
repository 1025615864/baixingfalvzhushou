/**
 * 反馈管理页面（管理员）
 */

import React, { useState } from 'react';

import type { FeedbackStatus, FeedbackQueryParams } from '../types';
import { useFeedbackStats, useAdminFeedbackList, useUpdateFeedback } from '../hooks/useFeedback';
import { FeedbackList } from '../components/FeedbackList';

/**
 * 反馈管理页面（管理员）
 */
export function FeedbackAdminPage(): React.ReactElement {
  // 查询参数
  const [params, setParams] = useState<FeedbackQueryParams>({
    page: 1,
    pageSize: 20,
    status: undefined,
    keyword: '',
  });

  // 反馈统计
  const statsQuery = useFeedbackStats();

  // 反馈列表
  const listQuery = useAdminFeedbackList(params);

  // 更新反馈 mutation
  const updateMutation = useUpdateFeedback();

  /**
   * 处理状态筛选
   */
  const handleStatusFilter = (status: FeedbackStatus | undefined) => {
    setParams((prev) => ({ ...prev, status, page: 1 }));
  };

  /**
   * 处理搜索
   */
  const handleSearch = (keyword: string) => {
    setParams((prev) => ({ ...prev, keyword: keyword || undefined, page: 1 }));
  };

  /**
   * 处理回复
   */
  const handleReply = (id: number, reply: string) => {
    updateMutation.mutate({
      ticketId: id,
      data: { adminReply: reply },
    });
  };

  /**
   * 处理状态变更
   */
  const handleStatusChange = (id: number, status: FeedbackStatus) => {
    updateMutation.mutate({
      ticketId: id,
      data: { status },
    });
  };

  /**
   * 处理分页
   */
  const handlePageChange = (page: number) => {
    setParams((prev) => ({ ...prev, page }));
  };

  // 统计卡片数据
  const statCards = [
    { key: 'total', label: '全部工单', color: 'bg-gray-50 text-gray-700' },
    { key: 'open', label: '待处理', color: 'bg-yellow-50 text-yellow-700' },
    { key: 'processing', label: '处理中', color: 'bg-blue-50 text-blue-700' },
    { key: 'closed', label: '已解决', color: 'bg-green-50 text-green-700' },
    { key: 'unassigned', label: '未分配', color: 'bg-red-50 text-red-700' },
  ] as const;

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-7xl mx-auto px-4">
        {/* 页面标题 */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">反馈工单管理</h1>
          <p className="text-gray-600 mt-1">管理和回复用户反馈工单</p>
        </div>

        {/* 统计卡片 */}
        {statsQuery.data && (
          <div className="grid grid-cols-2 md:grid-cols-5 gap-4 mb-6">
            {statCards.map((card) => {
              const value = statsQuery.data[card.key as keyof typeof statsQuery.data];
              const isActive =
                (card.key === 'total' && !params.status) ||
                (card.key === params.status && params.status !== undefined);

              return (
                <button
                  key={card.key}
                  onClick={() => handleStatusFilter(card.key === 'total' ? undefined : (card.key as FeedbackStatus))}
                  className={`
                    p-4 rounded-xl text-left transition-all
                    ${isActive ? 'ring-2 ring-blue-500 bg-white shadow-sm' : 'bg-white hover:shadow-sm'}
                  `}
                >
                  <p className={`text-2xl font-bold ${card.color.split(' ')[1]}`}>{value}</p>
                  <p className={`text-sm mt-1 ${card.color.split(' ')[1].replace('700', '600')}`}>
                    {card.label}
                  </p>
                </button>
              );
            })}
          </div>
        )}

        {/* 主内容区域 */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-200">
          {/* 工具栏 */}
          <div className="p-4 border-b border-gray-200 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            {/* 搜索框 */}
            <div className="relative flex-1 max-w-md">
              <input
                type="text"
                placeholder="搜索反馈内容..."
                value={params.keyword || ''}
                onChange={(e) => handleSearch(e.target.value)}
                className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
              <svg
                className="absolute left-3 top-2.5 w-5 h-5 text-gray-400"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
                />
              </svg>
            </div>

            {/* 状态筛选标签 */}
            <div className="flex items-center space-x-2">
              <button
                onClick={() => handleStatusFilter(undefined)}
                className={`
                  px-3 py-1.5 text-sm font-medium rounded-full transition-colors
                  ${!params.status ? 'bg-gray-900 text-white' : 'bg-gray-100 text-gray-600 hover:bg-gray-200'}
                `}
              >
                全部
              </button>
              <button
                onClick={() => handleStatusFilter('open')}
                className={`
                  px-3 py-1.5 text-sm font-medium rounded-full transition-colors
                  ${params.status === 'open' ? 'bg-yellow-500 text-white' : 'bg-yellow-50 text-yellow-700 hover:bg-yellow-100'}
                `}
              >
                待处理
              </button>
              <button
                onClick={() => handleStatusFilter('processing')}
                className={`
                  px-3 py-1.5 text-sm font-medium rounded-full transition-colors
                  ${params.status === 'processing' ? 'bg-blue-500 text-white' : 'bg-blue-50 text-blue-700 hover:bg-blue-100'}
                `}
              >
                处理中
              </button>
              <button
                onClick={() => handleStatusFilter('closed')}
                className={`
                  px-3 py-1.5 text-sm font-medium rounded-full transition-colors
                  ${params.status === 'closed' ? 'bg-green-500 text-white' : 'bg-green-50 text-green-700 hover:bg-green-100'}
                `}
              >
                已解决
              </button>
            </div>
          </div>

          {/* 反馈列表 */}
          <div className="p-4">
            <FeedbackList
              items={listQuery.data?.items || []}
              isLoading={listQuery.isLoading}
              isAdmin={true}
              onReply={handleReply}
              onStatusChange={handleStatusChange}
              emptyText="暂无符合条件的反馈工单"
            />
          </div>

          {/* 分页 */}
          {listQuery.data && listQuery.data.total > 0 && (
            <div className="p-4 border-t border-gray-200">
              <div className="flex items-center justify-between">
                <p className="text-sm text-gray-600">
                  共 {listQuery.data.total} 条，第 {listQuery.data.page} /{' '}
                  {Math.ceil(listQuery.data.total / listQuery.data.pageSize)} 页
                </p>
                <div className="flex items-center space-x-2">
                  <button
                    onClick={() => handlePageChange((params.page ?? 1) - 1)}
                    disabled={params.page === 1}
                    className="px-3 py-1.5 text-sm text-gray-600 bg-gray-100 rounded hover:bg-gray-200 disabled:opacity-50"
                  >
                    上一页
                  </button>
                  <button
                    onClick={() => handlePageChange((params.page ?? 1) + 1)}
                    disabled={(params.page ?? 1) * (params.pageSize ?? 10) >= listQuery.data.total}
                    className="px-3 py-1.5 text-sm text-gray-600 bg-gray-100 rounded hover:bg-gray-200 disabled:opacity-50"
                  >
                    下一页
                  </button>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}