// ============================================
// 合同审查页面
// ============================================

import { useState } from 'react';

export function ContractReviewPage() {
  const [file, setFile] = useState<File | null>(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [result, setResult] = useState<{
    risk_level: string;
    risk_count: number;
    summary: string;
    suggestions: string[];
  } | null>(null);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0]);
    }
  };

  const handleAnalyze = async () => {
    if (!file) return;
    setIsAnalyzing(true);
    // Mock analysis
    await new Promise((resolve) => { setTimeout(resolve, 2000); });
    setResult({
      risk_level: 'medium',
      risk_count: 3,
      summary: '该劳动合同整体较为规范，但存在3处需要关注的风险点。',
      suggestions: [
        '试用期约定过长，建议不超过法定上限',
        '竞业限制条款补偿标准不明确',
        '加班工资计算基数约定不清晰',
      ],
    });
    setIsAnalyzing(false);
  };

  const getRiskLevelColor = (level: string) => {
    switch (level) {
      case 'high': return 'text-red-600 bg-red-50';
      case 'medium': return 'text-amber-600 bg-amber-50';
      case 'low': return 'text-green-600 bg-green-50';
      default: return 'text-gray-600 bg-gray-50';
    }
  };

  const getRiskLevelText = (level: string) => {
    switch (level) {
      case 'high': return '高风险';
      case 'medium': return '中风险';
      case 'low': return '低风险';
      default: return '未知';
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-4xl mx-auto px-4">
        <div className="mb-6">
          <h1 className="text-2xl font-bold text-gray-900">AI 合同审查</h1>
          <p className="text-gray-600 mt-1">上传合同文件，AI 智能识别风险条款</p>
        </div>

        {/* 上传区域 */}
        <div className="bg-white rounded-lg p-8 shadow-sm border border-gray-100 mb-6">
          <div className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center hover:border-blue-400 transition-colors">
            <svg className="w-12 h-12 text-gray-400 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
            <p className="text-gray-600 mb-4">支持 PDF、Word、TXT 格式，最大 10MB</p>
            <input
              type="file"
              accept=".pdf,.doc,.docx,.txt"
              onChange={handleFileChange}
              className="hidden"
              id="contract-file"
            />
            <label
              htmlFor="contract-file"
              className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors cursor-pointer inline-block"
            >
              选择文件
            </label>
            {file && (
              <p className="mt-4 text-sm text-gray-700">
                已选择：<span className="font-medium">{file.name}</span>
              </p>
            )}
          </div>

          {file && (
            <div className="mt-6 text-center">
              <button
                onClick={() => { void handleAnalyze(); }}
                disabled={isAnalyzing}
                className="px-8 py-3 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50 transition-colors flex items-center gap-2 mx-auto"
              >
                {isAnalyzing ? (
                  <>
                    <svg className="w-5 h-5 animate-spin" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                    </svg>
                    分析中...
                  </>
                ) : (
                  <>
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-3 7h3m-3 4h3m-6-4h.01M9 16h.01" />
                    </svg>
                    开始审查
                  </>
                )}
              </button>
            </div>
          )}
        </div>

        {/* 审查结果 */}
        {result && (
          <div className="bg-white rounded-lg p-6 shadow-sm border border-gray-100">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-xl font-bold text-gray-900">审查报告</h2>
              <span className={`px-4 py-2 rounded-full font-medium ${getRiskLevelColor(result.risk_level)}`}>
                {getRiskLevelText(result.risk_level)} · {result.risk_count} 项风险
              </span>
            </div>

            <div className="mb-6">
              <h3 className="font-semibold text-gray-900 mb-2">总体评估</h3>
              <p className="text-gray-600">{result.summary}</p>
            </div>

            <div>
              <h3 className="font-semibold text-gray-900 mb-3">修改建议</h3>
              <ul className="space-y-3">
                {result.suggestions.map((suggestion, index) => (
                  <li key={index} className="flex items-start gap-3 p-3 bg-amber-50 rounded-lg">
                    <span className="w-6 h-6 bg-amber-100 text-amber-600 rounded-full flex items-center justify-center text-sm font-medium flex-shrink-0">
                      {index + 1}
                    </span>
                    <span className="text-gray-700">{suggestion}</span>
                  </li>
                ))}
              </ul>
            </div>

            <div className="mt-6 pt-6 border-t border-gray-100 flex gap-3">
              <button className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors">
                下载完整报告
              </button>
              <button className="px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors">
                咨询律师
              </button>
            </div>
          </div>
        )}

        {/* 历史记录 */}
        <div className="mt-8">
          <h3 className="font-semibold text-gray-900 mb-4">审查历史</h3>
          <div className="bg-white rounded-lg shadow-sm border border-gray-100">
            <div className="divide-y divide-gray-100">
              {[
                { name: '劳动合同_v2.pdf', date: '2026-01-28', status: 'medium' },
                { name: '租房合同.pdf', date: '2026-01-20', status: 'low' },
              ].map((item, index) => (
                <div key={index} className="p-4 flex items-center justify-between hover:bg-gray-50">
                  <div className="flex items-center gap-3">
                    <svg className="w-8 h-8 text-red-500" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M4 4a2 2 0 012-2h4.586A2 2 0 0112 2.586L15.414 6A2 2 0 0116 7.414V16a2 2 0 01-2 2H6a2 2 0 01-2-2V4z" clipRule="evenodd" />
                    </svg>
                    <div>
                      <p className="font-medium text-gray-900">{item.name}</p>
                      <p className="text-sm text-gray-500">{item.date}</p>
                    </div>
                  </div>
                  <span className={`px-3 py-1 rounded-full text-xs font-medium ${
                    item.status === 'medium' ? 'bg-amber-100 text-amber-600' : 'bg-green-100 text-green-600'
                  }`}>
                    {item.status === 'medium' ? '中风险' : '低风险'}
                  </span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}