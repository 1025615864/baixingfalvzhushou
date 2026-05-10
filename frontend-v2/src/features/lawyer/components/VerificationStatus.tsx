/**
 * 认证状态展示组件
 * 展示律师认证申请的当前状态
 */

import React from 'react';

import { useVerificationStatus } from '../hooks/useVerification';

interface VerificationStatusProps {
  onApplyClick?: () => void;
}

export const VerificationStatus: React.FC<VerificationStatusProps> = ({
  onApplyClick,
}) => {
  const { data: status, isLoading, isError } = useVerificationStatus();

  if (isLoading) {
    return (
      <div className="bg-white shadow rounded-lg p-6 animate-pulse">
        <div className="h-4 bg-gray-200 rounded w-1/3 mb-4"></div>
        <div className="h-4 bg-gray-200 rounded w-1/2"></div>
      </div>
    );
  }

  if (isError || !status) {
    return (
      <div className="bg-white shadow rounded-lg p-6">
        <div className="text-center">
          <svg
            className="mx-auto h-12 w-12 text-gray-400"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
            />
          </svg>
          <h3 className="mt-2 text-sm font-medium text-gray-900">无法获取认证状态</h3>
          <p className="mt-1 text-sm text-gray-500">请稍后重试</p>
        </div>
      </div>
    );
  }

  // 已认证状态
  if (status.isVerifiedLawyer) {
    return (
      <div className="bg-green-50 border border-green-200 rounded-lg p-6">
        <div className="flex items-center">
          <div className="flex-shrink-0">
            <svg
              className="h-8 w-8 text-green-400"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
              />
            </svg>
          </div>
          <div className="ml-4">
            <h3 className="text-lg font-medium text-green-800">认证通过</h3>
            <p className="mt-1 text-sm text-green-700">
              恭喜！您已成为认证律师，可以享受平台的全部功能。
            </p>
          </div>
        </div>
      </div>
    );
  }

  // 待审核状态
  if (status.verificationStatus === 'pending') {
    return (
      <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-6">
        <div className="flex items-center">
          <div className="flex-shrink-0">
            <svg
              className="h-8 w-8 text-yellow-400"
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
          </div>
          <div className="ml-4">
            <h3 className="text-lg font-medium text-yellow-800">审核中</h3>
            <p className="mt-1 text-sm text-yellow-700">
              您的认证申请正在审核中，请耐心等待。审核通常需要1-3个工作日。
            </p>
            {status.submittedAt && (
              <p className="mt-2 text-xs text-yellow-600">
                提交时间：{new Date(status.submittedAt).toLocaleString('zh-CN')}
              </p>
            )}
          </div>
        </div>
      </div>
    );
  }

  // 被拒绝状态
  if (status.verificationStatus === 'rejected') {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-6">
        <div className="flex items-start">
          <div className="flex-shrink-0">
            <svg
              className="h-8 w-8 text-red-400"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z"
              />
            </svg>
          </div>
          <div className="ml-4 flex-1">
            <h3 className="text-lg font-medium text-red-800">认证被拒绝</h3>
            <p className="mt-1 text-sm text-red-700">
              很抱歉，您的认证申请未通过审核。
            </p>
            {status.rejectReason && (
              <div className="mt-3 bg-red-100 rounded p-3">
                <p className="text-sm text-red-800">
                  <span className="font-medium">拒绝原因：</span>
                  {status.rejectReason}
                </p>
              </div>
            )}
            {status.reviewedAt && (
              <p className="mt-2 text-xs text-red-600">
                审核时间：{new Date(status.reviewedAt).toLocaleString('zh-CN')}
              </p>
            )}
            {onApplyClick && (
              <button
                onClick={onApplyClick}
                className="mt-4 px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-red-600 hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500"
              >
                重新申请
              </button>
            )}
          </div>
        </div>
      </div>
    );
  }

  // 未认证状态
  return (
    <div className="bg-white shadow rounded-lg p-6">
      <div className="text-center">
        <svg
          className="mx-auto h-12 w-12 text-gray-400"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
          />
        </svg>
        <h3 className="mt-2 text-sm font-medium text-gray-900">未认证</h3>
        <p className="mt-1 text-sm text-gray-500">
          您尚未完成律师认证，认证后可享受更多平台功能
        </p>
        {onApplyClick && (
          <div className="mt-6">
            <button
              onClick={onApplyClick}
              className="inline-flex items-center px-4 py-2 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
            >
              <svg
                className="-ml-1 mr-2 h-5 w-5"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
                />
              </svg>
              申请认证
            </button>
          </div>
        )}
      </div>
    </div>
  );
};

export default VerificationStatus;