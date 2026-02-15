/**
 * 律师认证申请页面
 */

import React, { useState } from 'react';

import { VerificationStatus } from '../components/VerificationStatus';
import { VerificationForm } from '../components/VerificationForm';
import { useCanApplyVerification } from '../hooks/useVerification';

type ViewMode = 'status' | 'form';

export const VerificationPage: React.FC = () => {
  const [viewMode, setViewMode] = useState<ViewMode>('status');
  const canApply = useCanApplyVerification();

  const handleApplyClick = () => {
    setViewMode('form');
  };

  const handleSuccess = () => {
    setViewMode('status');
  };

  const handleCancel = () => {
    setViewMode('status');
  };

  return (
    <div className="max-w-3xl mx-auto py-8 px-4 sm:px-6 lg:px-8">
      {/* 页面标题 */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">律师认证</h1>
        <p className="mt-2 text-gray-600">
          完成认证后，您可以享受平台的全部功能，包括创建个人主页、生成推广链接等
        </p>
      </div>

      {/* 认证状态或申请表单 */}
      {viewMode === 'status' ? (
        <div className="space-y-6">
          <VerificationStatus onApplyClick={canApply ? handleApplyClick : undefined} />

          {/* 认证说明 */}
          <div className="bg-white shadow rounded-lg p-6">
            <h3 className="text-lg font-medium text-gray-900 mb-4">认证流程</h3>
            <div className="space-y-4">
              <div className="flex items-start">
                <div className="flex-shrink-0">
                  <div className="flex items-center justify-center w-8 h-8 rounded-full bg-blue-100 text-blue-600 font-semibold">
                    1
                  </div>
                </div>
                <div className="ml-4">
                  <h4 className="text-sm font-medium text-gray-900">提交申请</h4>
                  <p className="text-sm text-gray-500">
                    填写真实信息并上传相关证件照片
                  </p>
                </div>
              </div>

              <div className="flex items-start">
                <div className="flex-shrink-0">
                  <div className="flex items-center justify-center w-8 h-8 rounded-full bg-blue-100 text-blue-600 font-semibold">
                    2
                  </div>
                </div>
                <div className="ml-4">
                  <h4 className="text-sm font-medium text-gray-900">资料审核</h4>
                  <p className="text-sm text-gray-500">
                    平台将在1-3个工作日内完成审核
                  </p>
                </div>
              </div>

              <div className="flex items-start">
                <div className="flex-shrink-0">
                  <div className="flex items-center justify-center w-8 h-8 rounded-full bg-blue-100 text-blue-600 font-semibold">
                    3
                  </div>
                </div>
                <div className="ml-4">
                  <h4 className="text-sm font-medium text-gray-900">认证成功</h4>
                  <p className="text-sm text-gray-500">
                    审核通过后即可成为认证律师
                  </p>
                </div>
              </div>
            </div>
          </div>

          {/* 认证权益 */}
          <div className="bg-white shadow rounded-lg p-6">
            <h3 className="text-lg font-medium text-gray-900 mb-4">认证权益</h3>
            <ul className="space-y-3">
              <li className="flex items-center text-sm text-gray-600">
                <svg
                  className="flex-shrink-0 mr-3 h-5 w-5 text-green-500"
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
                创建个人品牌主页
              </li>
              <li className="flex items-center text-sm text-gray-600">
                <svg
                  className="flex-shrink-0 mr-3 h-5 w-5 text-green-500"
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
                生成专属推广链接
              </li>
              <li className="flex items-center text-sm text-gray-600">
                <svg
                  className="flex-shrink-0 mr-3 h-5 w-5 text-green-500"
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
                设置快捷回复模板
              </li>
              <li className="flex items-center text-sm text-gray-600">
                <svg
                  className="flex-shrink-0 mr-3 h-5 w-5 text-green-500"
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
                优先展示在律师列表
              </li>
              <li className="flex items-center text-sm text-gray-600">
                <svg
                  className="flex-shrink-0 mr-3 h-5 w-5 text-green-500"
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
                获得认证标识
              </li>
            </ul>
          </div>
        </div>
      ) : (
        <div className="bg-white shadow rounded-lg p-6">
          <VerificationForm onSuccess={handleSuccess} onCancel={handleCancel} />
        </div>
      )}
    </div>
  );
};

export default VerificationPage;