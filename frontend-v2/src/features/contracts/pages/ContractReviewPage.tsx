/**
 * ContractReviewPage - 合同审查页面
 */

import { useState } from 'react';

import { ContractReviewer } from '../components/ContractReviewer';
import { ContractGenerator } from '../components/ContractGenerator';
import { ContractCompare } from '../components/ContractCompare';

type TabType = 'review' | 'generate' | 'compare' | 'history';

/**
 * 合同审查页面
 */
export function ContractReviewPage(): JSX.Element {
  const [activeTab, setActiveTab] = useState<TabType>('review');
  const [, setGeneratedContract] = useState<{ title: string; content: string } | null>(null);

  /** 处理合同生成成功 */
  const handleGenerateSuccess = (contract: { title: string; content: string }): void => {
    setGeneratedContract(contract);
  };

  /** 渲染标签按钮 */
  const renderTabButton = (tab: TabType, label: string, icon: JSX.Element): JSX.Element => (
    <button
      onClick={() => setActiveTab(tab)}
      className={`
        flex items-center gap-2 px-4 py-3 text-sm font-medium transition-all
        ${activeTab === tab
          ? 'text-blue-600 border-b-2 border-blue-600 bg-blue-50'
          : 'text-gray-600 hover:text-gray-900 hover:bg-gray-50'
        }
      `}
    >
      {icon}
      {label}
    </button>
  );

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-6xl mx-auto px-4 py-8">
        {/* 页面标题 */}
        <div className="mb-6">
          <h1 className="text-2xl font-bold text-gray-900">合同助手</h1>
          <p className="text-gray-500 mt-1">AI 智能审查、生成、对比合同</p>
        </div>

        {/* 标签页导航 */}
        <div className="bg-white rounded-t-xl border-b border-gray-200">
          <div className="flex">
            {renderTabButton('review', '合同审查', (
              <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            ))}
            {renderTabButton('generate', '合同生成', (
              <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 13h6m-3-3v6m5 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
            ))}
            {renderTabButton('compare', '版本对比', (
              <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M8 7h12m0 0l-4-4m4 4l-4 4m0 6H4m0 0l4 4m-4-4l4-4" />
              </svg>
            ))}
            {renderTabButton('history', '历史记录', (
              <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            ))}
          </div>
        </div>

        {/* 标签页内容 */}
        <div className="bg-white rounded-b-xl shadow-sm p-6">
          {/* 合同审查 */}
          {activeTab === 'review' && (
            <div className="max-w-3xl mx-auto">
              <div className="text-center mb-8">
                <h2 className="text-xl font-semibold text-gray-900">AI 合同审查</h2>
                <p className="text-gray-500 mt-2">
                  上传您的合同文件，AI 将自动分析风险点、缺失条款，并提供修改建议
                </p>
              </div>
              <ContractReviewer onReviewSuccess={() => {
                // 审查成功后的回调，可以刷新历史记录等
              }} />
            </div>
          )}

          {/* 合同生成 */}
          {activeTab === 'generate' && (
            <div className="max-w-4xl mx-auto">
              <div className="text-center mb-8">
                <h2 className="text-xl font-semibold text-gray-900">智能合同生成</h2>
                <p className="text-gray-500 mt-2">
                  选择模板并填写信息，快速生成专业合同
                </p>
              </div>
              <ContractGenerator onGenerateSuccess={handleGenerateSuccess} />
            </div>
          )}

          {/* 版本对比 */}
          {activeTab === 'compare' && (
            <div className="max-w-3xl mx-auto">
              <div className="text-center mb-8">
                <h2 className="text-xl font-semibold text-gray-900">合同版本对比</h2>
                <p className="text-gray-500 mt-2">
                  上传两个版本的合同文件，快速识别差异
                </p>
              </div>
              <ContractCompare onCompareComplete={() => {
                // 对比完成后的回调
              }} />
            </div>
          )}

          {/* 历史记录 - 跳转到历史页面 */}
          {activeTab === 'history' && (
            <div className="text-center py-12">
              <svg
                className="mx-auto h-12 w-12 text-gray-400 mb-4"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={1.5}
                  d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"
                />
              </svg>
              <h3 className="text-lg font-medium text-gray-900 mb-2">查看完整历史记录</h3>
              <p className="text-gray-500 mb-6">前往历史记录页面查看所有审查详情</p>
              <a
                href="/contracts/history"
                className="inline-flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
              >
                前往历史记录
                <svg className="ml-2 w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                </svg>
              </a>
            </div>
          )}
        </div>

        {/* 功能说明 */}
        <div className="mt-8 grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="bg-white rounded-xl p-6 shadow-sm">
            <div className="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center mb-4">
              <svg className="w-6 h-6 text-blue-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            <h3 className="font-medium text-gray-900 mb-2">AI 智能审查</h3>
            <p className="text-sm text-gray-500">
              基于法律知识库和大模型，自动识别合同风险点、缺失条款，提供专业修改建议
            </p>
          </div>
          
          <div className="bg-white rounded-xl p-6 shadow-sm">
            <div className="w-10 h-10 bg-green-100 rounded-lg flex items-center justify-center mb-4">
              <svg className="w-6 h-6 text-green-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 13h6m-3-3v6m5 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
            </div>
            <h3 className="font-medium text-gray-900 mb-2">智能合同生成</h3>
            <p className="text-sm text-gray-500">
              内置多种常用合同模板，填写关键信息即可快速生成规范合同文本
            </p>
          </div>
          
          <div className="bg-white rounded-xl p-6 shadow-sm">
            <div className="w-10 h-10 bg-purple-100 rounded-lg flex items-center justify-center mb-4">
              <svg className="w-6 h-6 text-purple-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M8 7h12m0 0l-4-4m4 4l-4 4m0 6H4m0 0l4 4m-4-4l4-4" />
              </svg>
            </div>
            <h3 className="font-medium text-gray-900 mb-2">版本对比分析</h3>
            <p className="text-sm text-gray-500">
              快速对比合同版本差异，清晰标注新增、删除、修改内容，避免遗漏重要变更
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}