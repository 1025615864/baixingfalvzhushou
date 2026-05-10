/**
 * 反馈页面
 * 普通用户提交反馈和查看反馈历史
 */

import { logger } from '@/shared/lib/logger';
import React, { useState } from 'react';

import type { CreateFeedbackDTO } from '../types';
import { useCreateFeedback, useMyFeedbackList } from '../hooks/useFeedback';
import { FeedbackForm } from '../components/FeedbackForm';
import { FeedbackSuccess } from '../components/FeedbackSuccess';
import { FeedbackList } from '../components/FeedbackList';

/**
 * 反馈页面
 */
export function FeedbackPage(): React.ReactElement {
  const [isSuccess, setIsSuccess] = useState(false);

  // 提交反馈 mutation
  const createFeedbackMutation = useCreateFeedback();

  // 我的反馈列表 query
  const myFeedbackQuery = useMyFeedbackList({ page: 1, pageSize: 10 });

  /**
   * 处理表单提交
   */
  const handleSubmit = async (data: CreateFeedbackDTO) => {
    try {
      await createFeedbackMutation.mutateAsync(data);
      setIsSuccess(true);
    } catch (error) {
      // 错误处理已在 mutation 中统一处理
      logger.error('提交反馈失败:', error);
    }
  };

  /**
   * 重置成功状态
   */
  const handleReset = () => {
    setIsSuccess(false);
  };

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-4xl mx-auto px-4">
        {/* 页面标题 */}
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">意见反馈</h1>
          <p className="text-gray-600">您的建议是我们进步的动力</p>
        </div>

        {/* 两栏布局 */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* 左侧：提交表单 */}
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-6 flex items-center">
              <svg
                className="w-5 h-5 mr-2 text-blue-600"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"
                />
              </svg>
              提交反馈
            </h2>

            {isSuccess ? (
              <FeedbackSuccess
                onBack={() => setIsSuccess(false)}
                onSubmitAgain={handleReset}
              />
            ) : (
              <FeedbackForm
                onSubmit={(data) => {
                  void handleSubmit(data);
                }}
                isSubmitting={createFeedbackMutation.isPending}
              />
            )}
          </div>

          {/* 右侧：反馈历史 */}
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-6 flex items-center">
              <svg
                className="w-5 h-5 mr-2 text-blue-600"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"
                />
              </svg>
              反馈历史
            </h2>

            <FeedbackList
              items={myFeedbackQuery.data?.items || []}
              isLoading={myFeedbackQuery.isLoading}
              emptyText="您还没有提交过反馈"
            />

            {/* 分页（简化版） */}
            {myFeedbackQuery.data && myFeedbackQuery.data.total > 0 && (
              <div className="mt-4 text-center text-sm text-gray-500">
                共 {myFeedbackQuery.data.total} 条反馈
              </div>
            )}
          </div>
        </div>

        {/* 底部说明 */}
        <div className="mt-8 text-center text-sm text-gray-500">
          <p>如有紧急问题，请联系客服热线：400-XXX-XXXX</p>
        </div>
      </div>
    </div>
  );
}