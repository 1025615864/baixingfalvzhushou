/**
 * 反馈提交成功提示组件
 */

import React from 'react';

/**
 * FeedbackSuccessProps 接口
 */
export interface FeedbackSuccessProps {
  /** 返回回调 */
  onBack?: () => void;
  /** 再次提交回调 */
  onSubmitAgain?: () => void;
  /** 自定义类名 */
  className?: string;
}

/**
 * 反馈提交成功提示组件
 */
export function FeedbackSuccess({
  onBack,
  onSubmitAgain,
  className = '',
}: FeedbackSuccessProps): React.ReactElement {
  return (
    <div className={`text-center py-12 ${className}`}>
      {/* 成功图标 */}
      <div className="mx-auto w-20 h-20 bg-green-100 rounded-full flex items-center justify-center mb-6">
        <svg
          className="w-10 h-10 text-green-500"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M5 13l4 4L19 7"
          />
        </svg>
      </div>

      {/* 成功标题 */}
      <h3 className="text-2xl font-bold text-gray-900 mb-2">提交成功！</h3>

      {/* 成功描述 */}
      <p className="text-gray-600 mb-8 max-w-md mx-auto">
        感谢您的反馈！我们会认真查看每一条反馈，并尽快处理您的问题。如有需要，我们会通过您提供的联系方式与您联系。
      </p>

      {/* 操作按钮 */}
      <div className="flex flex-col sm:flex-row items-center justify-center space-y-3 sm:space-y-0 sm:space-x-4">
        {onBack && (
          <button
            onClick={onBack}
            className="w-full sm:w-auto px-6 py-2.5 text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200 transition-colors font-medium"
          >
            返回
          </button>
        )}
        {onSubmitAgain && (
          <button
            onClick={onSubmitAgain}
            className="w-full sm:w-auto px-6 py-2.5 text-white bg-blue-600 rounded-lg hover:bg-blue-700 transition-colors font-medium"
          >
            继续提交反馈
          </button>
        )}
      </div>

      {/* 提示信息 */}
      <div className="mt-8 p-4 bg-blue-50 rounded-lg max-w-md mx-auto">
        <div className="flex items-start">
          <svg
            className="w-5 h-5 text-blue-500 mt-0.5 mr-2 flex-shrink-0"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
            />
          </svg>
          <div className="text-left text-sm text-blue-700">
            <p className="font-medium mb-1">温馨提示</p>
            <ul className="space-y-1 list-disc list-inside">
              <li>您可以在个人中心查看反馈进度</li>
              <li>一般问题我们会在3个工作日内处理</li>
              <li>紧急情况请拨打客服热线</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
}