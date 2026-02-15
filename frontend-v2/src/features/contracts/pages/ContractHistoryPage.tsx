/**
 * ContractHistoryPage - 合同历史页面
 */

import { useState } from 'react';

import { ContractList } from '../components/ContractList';
import { useReviewDetail } from '../hooks/useContracts';

/**
 * 合同历史页面
 */
export function ContractHistoryPage(): JSX.Element {
  const [selectedReviewId, setSelectedReviewId] = useState<string | null>(null);
  
  const { data: reviewDetail, isLoading: isDetailLoading } = useReviewDetail(selectedReviewId);

  /** 处理查看详情 */
  const handleViewDetail = (reviewId: string): void => {
    setSelectedReviewId(reviewId);
  };

  /** 关闭详情弹窗 */
  const handleCloseDetail = (): void => {
    setSelectedReviewId(null);
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-6xl mx-auto px-4 py-8">
        {/* 页面标题 */}
        <div className="mb-6">
          <h1 className="text-2xl font-bold text-gray-900">合同审查历史</h1>
          <p className="text-gray-500 mt-1">查看和管理您的合同审查记录</p>
        </div>

        {/* 审查历史列表 */}
        <ContractList pageSize={10} onViewDetail={handleViewDetail} />
      </div>

      {/* 详情弹窗 */}
      {selectedReviewId && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black bg-opacity-50">
          <div className="bg-white rounded-xl shadow-xl w-full max-w-4xl max-h-[90vh] overflow-hidden">
            {/* 弹窗头部 */}
            <div className="flex items-center justify-between px-6 py-4 border-b border-gray-200">
              <h2 className="text-lg font-medium text-gray-900">审查详情</h2>
              <button
                onClick={handleCloseDetail}
                className="p-2 text-gray-400 hover:text-gray-600 rounded-lg hover:bg-gray-100"
              >
                <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            {/* 弹窗内容 */}
            <div className="p-6 overflow-y-auto max-h-[calc(90vh-80px)]">
              {isDetailLoading ? (
                <div className="flex items-center justify-center py-12">
                  <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
                  <span className="ml-3 text-gray-600">加载中...</span>
                </div>
              ) : reviewDetail ? (
                <div className="space-y-6">
                  {/* 基本信息 */}
                  <div className="bg-gray-50 rounded-lg p-4">
                    <h3 className="font-medium text-gray-900 mb-3">基本信息</h3>
                    <div className="grid grid-cols-2 gap-4 text-sm">
                      <div>
                        <span className="text-gray-500">文件名：</span>
                        <span className="text-gray-900">{reviewDetail.filename}</span>
                      </div>
                      <div>
                        <span className="text-gray-500">风险等级：</span>
                        <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${
                          reviewDetail.riskLevel === 'high'
                            ? 'bg-red-100 text-red-700'
                            : reviewDetail.riskLevel === 'medium'
                            ? 'bg-yellow-100 text-yellow-700'
                            : 'bg-green-100 text-green-700'
                        }`}>
                          {reviewDetail.riskLevel === 'high'
                            ? '高风险'
                            : reviewDetail.riskLevel === 'medium'
                            ? '中风险'
                            : '低风险'}
                          {reviewDetail.riskCount > 0 && ` (${reviewDetail.riskCount})`}
                        </span>
                      </div>
                      <div>
                        <span className="text-gray-500">文本长度：</span>
                        <span className="text-gray-900">{reviewDetail.textChars} 字符</span>
                      </div>
                      <div>
                        <span className="text-gray-500">请求ID：</span>
                        <span className="text-gray-900">{reviewDetail.requestId}</span>
                      </div>
                    </div>
                  </div>

                  {/* 文本预览 */}
                  <div>
                    <h3 className="font-medium text-gray-900 mb-3">文本预览</h3>
                    <div className="bg-gray-50 rounded-lg p-4 max-h-48 overflow-y-auto">
                      <pre className="text-sm text-gray-700 whitespace-pre-wrap font-mono">
                        {reviewDetail.textPreview}
                      </pre>
                    </div>
                  </div>

                  {/* 完整报告 */}
                  {reviewDetail.reportMarkdown && (
                    <div>
                      <h3 className="font-medium text-gray-900 mb-3">审查报告</h3>
                      <div className="prose prose-sm max-w-none bg-gray-50 rounded-lg p-4">
                        <div dangerouslySetInnerHTML={{ __html: reviewDetail.reportMarkdown }} />
                      </div>
                    </div>
                  )}

                  {/* 结构化风险数据 */}
                  {reviewDetail.reportJson.risks && reviewDetail.reportJson.risks.length > 0 && (
                    <div>
                      <h3 className="font-medium text-gray-900 mb-3">
                        风险点 ({reviewDetail.reportJson.risks.length})
                      </h3>
                      <div className="space-y-3">
                        {reviewDetail.reportJson.risks.map((risk) => (
                          <div
                            key={risk.id}
                            className="p-4 border border-gray-200 rounded-lg"
                          >
                            <div className="flex items-start justify-between mb-2">
                              <span className={`text-xs font-medium px-2 py-0.5 rounded ${
                                risk.severity === 'high'
                                  ? 'bg-red-100 text-red-700'
                                  : risk.severity === 'medium'
                                  ? 'bg-yellow-100 text-yellow-700'
                                  : 'bg-green-100 text-green-700'
                              }`}>
                                {risk.severity === 'high' ? '高风险' : risk.severity === 'medium' ? '中风险' : '低风险'}
                              </span>
                              <span className="text-xs text-gray-400">{risk.type}</span>
                            </div>
                            <p className="text-sm font-medium text-gray-900 mb-1">{risk.description}</p>
                            <p className="text-sm text-gray-600 mb-2">涉及条款：{risk.clause}</p>
                            <div className="bg-blue-50 p-3 rounded text-sm text-blue-800">
                              <span className="font-medium">建议：</span>
                              {risk.suggestion}
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              ) : (
                <div className="text-center py-12 text-gray-500">
                  未找到审查记录
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}