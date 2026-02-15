/**
 * 律师主页页面
 * 支持查看模式和编辑模式
 */

import React, { useState } from 'react';
import { useParams, Link } from 'react-router-dom';

import { usePublicHomepage } from '../hooks/useHomepage';
import { HomepageEditor } from '../components/HomepageEditor';

interface LawyerHomepageProps {
  lawyerId?: string;
}

export const LawyerHomepage: React.FC<LawyerHomepageProps> = () => {
  const { lawyerId } = useParams<{ lawyerId: string }>();
  const [isEditMode, setIsEditMode] = useState(false);

  const { data: homepage, isLoading, error } = usePublicHomepage(lawyerId || '');

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (error || !homepage) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <h2 className="text-2xl font-bold text-gray-900 mb-2">页面加载失败</h2>
          <p className="text-gray-600 mb-4">无法加载律师主页信息</p>
          <Link to="/" className="text-blue-600 hover:text-blue-800">
            返回首页
          </Link>
        </div>
      </div>
    );
  }

  // 编辑模式
  if (isEditMode) {
    return (
      <div className="min-h-screen bg-gray-50 py-8">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="mb-6 flex items-center justify-between">
            <h1 className="text-2xl font-bold text-gray-900">编辑个人主页</h1>
            <button
              onClick={() => setIsEditMode(false)}
              className="text-gray-600 hover:text-gray-900"
            >
              返回预览
            </button>
          </div>
          <HomepageEditor />
        </div>
      </div>
    );
  }

  // 查看模式
  return (
    <div className="min-h-screen bg-gray-50">
      {/* 头部背景 */}
      <div className="bg-gradient-to-r from-blue-600 to-blue-800 h-48"></div>

      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 -mt-24">
        <div className="bg-white shadow-lg rounded-lg overflow-hidden">
          {/* 律师基本信息 */}
          <div className="p-6 sm:p-8">
            <div className="sm:flex sm:items-start">
              {/* 头像 */}
              <div className="flex-shrink-0 mx-auto sm:mx-0">
                <img
                  src={homepage.avatarUrl || '/default-avatar.png'}
                  alt={homepage.name}
                  className="w-32 h-32 rounded-full border-4 border-white shadow-md object-cover"
                />
              </div>

              {/* 信息 */}
              <div className="mt-6 sm:mt-0 sm:ml-6 text-center sm:text-left flex-1">
                <div className="flex items-center justify-center sm:justify-start flex-wrap gap-2">
                  <h1 className="text-2xl font-bold text-gray-900">
                    {homepage.name}
                  </h1>
                  {homepage.isVerified && (
                    <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                      <svg
                        className="w-3 h-3 mr-1"
                        fill="currentColor"
                        viewBox="0 0 20 20"
                      >
                        <path
                          fillRule="evenodd"
                          d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
                          clipRule="evenodd"
                        />
                      </svg>
                      认证律师
                    </span>
                  )}
                </div>

                <p className="mt-2 text-gray-600">{homepage.title}</p>

                {homepage.firmName && (
                  <p className="mt-1 text-sm text-gray-500">
                    {homepage.firmName}
                  </p>
                )}

                {homepage.location && (
                  <p className="mt-1 text-sm text-gray-500 flex items-center justify-center sm:justify-start">
                    <svg
                      className="w-4 h-4 mr-1"
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z"
                      />
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M15 11a3 3 0 11-6 0 3 3 0 016 0z"
                      />
                    </svg>
                    {homepage.location}
                  </p>
                )}

                {/* 操作按钮 */}
                <div className="mt-4 flex items-center justify-center sm:justify-start space-x-3">
                  <button
                    onClick={() => setIsEditMode(true)}
                    className="inline-flex items-center px-4 py-2 border border-gray-300 shadow-sm text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                  >
                    <svg
                      className="w-4 h-4 mr-2"
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
                    编辑主页
                  </button>
                  <Link
                    to="/lawyer/schedule"
                    className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                  >
                    <svg
                      className="w-4 h-4 mr-2"
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"
                      />
                    </svg>
                    预约咨询
                  </Link>
                </div>
              </div>
            </div>
          </div>

          {/* 个人简介 */}
          {homepage.bio && (
            <div className="border-t border-gray-200 px-6 py-6 sm:px-8">
              <h2 className="text-lg font-medium text-gray-900 mb-3">个人简介</h2>
              <p className="text-gray-600 whitespace-pre-wrap">{homepage.bio}</p>
            </div>
          )}

          {/* 专长领域 */}
          {homepage.specialties && homepage.specialties.length > 0 && (
            <div className="border-t border-gray-200 px-6 py-6 sm:px-8">
              <h2 className="text-lg font-medium text-gray-900 mb-3">专长领域</h2>
              <div className="flex flex-wrap gap-2">
                {homepage.specialties.map((specialty, index) => (
                  <span
                    key={index}
                    className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-blue-100 text-blue-800"
                  >
                    {specialty}
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* 成功案例 */}
          {homepage.cases && homepage.cases.length > 0 && (
            <div className="border-t border-gray-200 px-6 py-6 sm:px-8">
              <h2 className="text-lg font-medium text-gray-900 mb-4">成功案例</h2>
              <div className="space-y-4">
                {homepage.cases.map((caseItem, index) => (
                  <div
                    key={index}
                    className="bg-gray-50 rounded-lg p-4"
                  >
                    <h3 className="font-medium text-gray-900 mb-2">
                      {caseItem.title}
                    </h3>
                    <p className="text-sm text-gray-600 mb-2">
                      {caseItem.description}
                    </p>
                    {caseItem.outcome && (
                      <p className="text-sm text-green-600">
                        结果：{caseItem.outcome}
                      </p>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* 客户评价 */}
          {homepage.reviews && homepage.reviews.length > 0 && (
            <div className="border-t border-gray-200 px-6 py-6 sm:px-8">
              <h2 className="text-lg font-medium text-gray-900 mb-4">客户评价</h2>
              <div className="space-y-4">
                {homepage.reviews.map((review, index) => (
                  <div
                    key={index}
                    className="border-b border-gray-200 last:border-0 pb-4 last:pb-0"
                  >
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center">
                        <span className="font-medium text-gray-900">
                          {review.userName}
                        </span>
                        <div className="ml-2 flex">
                          {Array.from({ length: 5 }).map((_, i) => (
                            <svg
                              key={i}
                              className={`w-4 h-4 ${
                                i < review.rating
                                  ? 'text-yellow-400'
                                  : 'text-gray-300'
                              }`}
                              fill="currentColor"
                              viewBox="0 0 20 20"
                            >
                              <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
                            </svg>
                          ))}
                        </div>
                      </div>
                      <span className="text-sm text-gray-500">
                        {new Date(review.createdAt).toLocaleDateString('zh-CN')}
                      </span>
                    </div>
                    <p className="text-gray-600 text-sm">{review.content}</p>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* 联系方式 */}
          {(homepage.phone || homepage.email || homepage.weixin) && (
            <div className="border-t border-gray-200 px-6 py-6 sm:px-8">
              <h2 className="text-lg font-medium text-gray-900 mb-3">联系方式</h2>
              <div className="space-y-2">
                {homepage.phone && (
                  <p className="flex items-center text-gray-600">
                    <svg
                      className="w-5 h-5 mr-2 text-gray-400"
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M3 5a2 2 0 012-2h3.28a1 1 0 01.948.684l1.498 4.493a1 1 0 01-.502 1.21l-2.257 1.13a11.042 11.042 0 005.516 5.516l1.13-2.257a1 1 0 011.21-.502l4.493 1.498a1 1 0 01.684.949V19a2 2 0 01-2 2h-1C9.716 21 3 14.284 3 6V5z"
                      />
                    </svg>
                    {homepage.phone}
                  </p>
                )}
                {homepage.email && (
                  <p className="flex items-center text-gray-600">
                    <svg
                      className="w-5 h-5 mr-2 text-gray-400"
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"
                      />
                    </svg>
                    {homepage.email}
                  </p>
                )}
                {homepage.weixin && (
                  <p className="flex items-center text-gray-600">
                    <svg
                      className="w-5 h-5 mr-2 text-gray-400"
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"
                      />
                    </svg>
                    微信：{homepage.weixin}
                  </p>
                )}
              </div>
            </div>
          )}

          {/* 数据统计 */}
          <div className="border-t border-gray-200 px-6 py-6 sm:px-8 bg-gray-50">
            <div className="grid grid-cols-3 gap-4 text-center">
              <div>
                <p className="text-2xl font-bold text-gray-900">
                  {homepage.consultationCount || 0}
                </p>
                <p className="text-sm text-gray-500">咨询次数</p>
              </div>
              <div>
                <p className="text-2xl font-bold text-gray-900">
                  {homepage.reviewCount || 0}
                </p>
                <p className="text-sm text-gray-500">客户评价</p>
              </div>
              <div>
                <p className="text-2xl font-bold text-gray-900">
                  {homepage.responseRate
                    ? `${(homepage.responseRate * 100).toFixed(0)}%`
                    : '0%'}
                </p>
                <p className="text-sm text-gray-500">回复率</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default LawyerHomepage;