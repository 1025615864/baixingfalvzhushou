/**
 * 反馈弹窗组件
 */

import React, { useState } from 'react';

import type { CreateFeedbackDTO } from '../types';

import { FeedbackForm } from './FeedbackForm';
import { FeedbackSuccess } from './FeedbackSuccess';

/**
 * FeedbackModalProps 接口
 */
export interface FeedbackModalProps {
  /** 是否显示 */
  isOpen: boolean;
  /** 关闭回调 */
  onClose: () => void;
  /** 提交回调 */
  onSubmit: (data: CreateFeedbackDTO) => void;
  /** 提交中状态 */
  isSubmitting?: boolean;
  /** 提交成功状态 */
  isSuccess?: boolean;
  /** 重置成功状态回调 */
  onResetSuccess?: () => void;
}

/**
 * 反馈弹窗组件
 */
export function FeedbackModal({
  isOpen,
  onClose,
  onSubmit,
  isSubmitting = false,
  isSuccess = false,
  onResetSuccess,
}: FeedbackModalProps): React.ReactElement | null {
  const [activeTab, setActiveTab] = useState<'form' | 'history'>('form');

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      {/* 背景遮罩 */}
      <div
        className="absolute inset-0 bg-black/50 backdrop-blur-sm"
        onClick={!isSubmitting ? onClose : undefined}
      />

      {/* 弹窗内容 */}
      <div className="relative bg-white rounded-2xl shadow-xl w-full max-w-2xl max-h-[90vh] overflow-hidden">
        {/* 头部 */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-200">
          <div className="flex items-center gap-2">
            <svg
              className="w-6 h-6 text-blue-600"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z"
              />
            </svg>
            <h2 className="text-xl font-bold text-gray-900">意见反馈</h2>
          </div>
          {!isSubmitting && (
            <button
              onClick={onClose}
              className="p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-full transition-colors"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M6 18L18 6M6 6l12 12"
                />
              </svg>
            </button>
          )}
        </div>

        {/* 标签切换（仅在非成功状态时显示） */}
        {!isSuccess && (
          <div className="flex border-b border-gray-200">
            <button
              onClick={() => setActiveTab('form')}
              className={`
                flex-1 py-3 text-sm font-medium text-center transition-colors
                ${activeTab === 'form'
                  ? 'text-blue-600 border-b-2 border-blue-600'
                  : 'text-gray-500 hover:text-gray-700'
                }
              `}
            >
              提交反馈
            </button>
            <button
              onClick={() => setActiveTab('history')}
              className={`
                flex-1 py-3 text-sm font-medium text-center transition-colors
                ${activeTab === 'history'
                  ? 'text-blue-600 border-b-2 border-blue-600'
                  : 'text-gray-500 hover:text-gray-700'
                }
              `}
            >
              反馈历史
            </button>
          </div>
        )}

        {/* 内容区域 */}
        <div className="p-6 overflow-y-auto max-h-[calc(90vh-200px)]">
          {isSuccess ? (
            <FeedbackSuccess
              onBack={onClose}
              onSubmitAgain={() => {
                onResetSuccess?.();
                setActiveTab('form');
              }}
            />
          ) : activeTab === 'form' ? (
            <FeedbackForm
              onSubmit={onSubmit}
              isSubmitting={isSubmitting}
              onCancel={onClose}
            />
          ) : (
            <div className="text-center py-8 text-gray-500">
              <p>反馈历史功能开发中...</p>
              <p className="text-sm mt-2">您可以在个人中心查看所有反馈记录</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}