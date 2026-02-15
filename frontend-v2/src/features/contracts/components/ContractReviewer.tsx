/**
 * ContractReviewer - 合同审查组件
 */

import { useState, useCallback } from 'react';

import type { RiskLevel } from '../types';
import { useReviewContract } from '../hooks/useContracts';

/** 风险等级配置 */
const RISK_CONFIG: Record<RiskLevel, { label: string; color: string; bg: string; border: string }> = {
  low: {
    label: '低风险',
    color: 'text-green-700',
    bg: 'bg-green-50',
    border: 'border-green-200',
  },
  medium: {
    label: '中风险',
    color: 'text-yellow-700',
    bg: 'bg-yellow-50',
    border: 'border-yellow-200',
  },
  high: {
    label: '高风险',
    color: 'text-red-700',
    bg: 'bg-red-50',
    border: 'border-red-200',
  },
};

/** 支持的文件类型 */
const SUPPORTED_TYPES = [
  'application/pdf',
  'application/msword',
  'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
  'text/plain',
];

/** 最大文件大小 (10MB) */
const MAX_FILE_SIZE = 10 * 1024 * 1024;

interface ContractReviewerProps {
  /** 审查成功回调 */
  onReviewSuccess?: () => void;
}

/**
 * 合同审查组件
 */
export function ContractReviewer({ onReviewSuccess }: ContractReviewerProps): JSX.Element {
  const [dragActive, setDragActive] = useState<boolean>(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [error, setError] = useState<string | null>(null);

  const reviewMutation = useReviewContract();

  /** 验证文件 */
  const validateFile = (file: File): string | null => {
    if (!SUPPORTED_TYPES.includes(file.type)) {
      return '不支持的文件类型，请上传 PDF、Word 或 TXT 文件';
    }
    if (file.size > MAX_FILE_SIZE) {
      return '文件大小超过 10MB 限制';
    }
    return null;
  };

  /** 处理文件选择 */
  const handleFileSelect = useCallback((file: File): void => {
    const validationError = validateFile(file);
    if (validationError) {
      setError(validationError);
      setSelectedFile(null);
      return;
    }
    setError(null);
    setSelectedFile(file);
  }, []);

  /** 处理输入变化 */
  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>): void => {
    const file = e.target.files?.[0];
    if (file) {
      handleFileSelect(file);
    }
  };

  /** 处理拖拽 */
  const handleDrag = (e: React.DragEvent<HTMLDivElement>): void => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  /** 处理拖放 */
  const handleDrop = (e: React.DragEvent<HTMLDivElement>): void => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);

    const file = e.dataTransfer.files?.[0];
    if (file) {
      handleFileSelect(file);
    }
  };

  /** 开始审查 */
  const handleReview = async (): Promise<void> => {
    if (!selectedFile) return;

    try {
      await reviewMutation.mutateAsync(selectedFile);
      setSelectedFile(null);
      if (onReviewSuccess) {
        onReviewSuccess();
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : '审查失败，请重试');
    }
  };

  /** 清除选择 */
  const handleClear = (): void => {
    setSelectedFile(null);
    setError(null);
  };

  /** 渲染上传区域 */
  const renderUploadArea = (): JSX.Element => (
    <div
      onDragEnter={handleDrag}
      onDragLeave={handleDrag}
      onDragOver={handleDrag}
      onDrop={handleDrop}
      className={`
        relative border-2 border-dashed rounded-xl p-8 text-center transition-all
        ${dragActive
          ? 'border-blue-500 bg-blue-50'
          : 'border-gray-300 hover:border-gray-400 bg-gray-50'
        }
      `}
    >
      <input
        type="file"
        accept=".pdf,.doc,.docx,.txt"
        onChange={handleInputChange}
        className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
      />
      <div className="space-y-3">
        <div className="mx-auto w-16 h-16 bg-white rounded-full flex items-center justify-center shadow-sm">
          <svg
            className="w-8 h-8 text-gray-400"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={1.5}
              d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"
            />
          </svg>
        </div>
        <div>
          <p className="text-base font-medium text-gray-900">
            点击或拖拽上传合同文件
          </p>
          <p className="text-sm text-gray-500 mt-1">
            支持 PDF、Word、TXT 格式，最大 10MB
          </p>
        </div>
      </div>
    </div>
  );

  /** 渲染文件预览 */
  const renderFilePreview = (): JSX.Element => {
    if (!selectedFile) return <></>;

    return (
      <div className="bg-white border border-gray-200 rounded-xl p-6">
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-4">
            <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center">
              <svg
                className="w-6 h-6 text-blue-600"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={1.5}
                  d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
                />
              </svg>
            </div>
            <div>
              <p className="font-medium text-gray-900">{selectedFile.name}</p>
              <p className="text-sm text-gray-500">
                {(selectedFile.size / 1024).toFixed(1)} KB
              </p>
            </div>
          </div>
          <button
            onClick={handleClear}
            className="p-2 text-gray-400 hover:text-red-500 transition-colors"
          >
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M6 18L18 6M6 6l12 12"
              />
            </svg>
          </button>
        </div>

        {error && (
          <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded-lg text-sm text-red-600">
            {error}
          </div>
        )}

        <button
          onClick={() => { void handleReview(); }}
          disabled={reviewMutation.isPending || !!error}
          className={`
            w-full mt-4 py-3 px-4 rounded-lg font-medium text-white transition-all
            ${reviewMutation.isPending || !!error
              ? 'bg-gray-400 cursor-not-allowed'
              : 'bg-blue-600 hover:bg-blue-700 shadow-sm hover:shadow'
            }
          `}
        >
          {reviewMutation.isPending ? (
            <span className="flex items-center justify-center gap-2">
              <svg
                className="animate-spin h-5 w-5"
                fill="none"
                viewBox="0 0 24 24"
              >
                <circle
                  className="opacity-25"
                  cx="12"
                  cy="12"
                  r="10"
                  stroke="currentColor"
                  strokeWidth="4"
                />
                <path
                  className="opacity-75"
                  fill="currentColor"
                  d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                />
              </svg>
              AI 审查中...
            </span>
          ) : (
            '开始审查'
          )}
        </button>
      </div>
    );
  };

  /** 渲染审查结果 */
  const renderReviewResult = (): JSX.Element | null => {
    if (!reviewMutation.isSuccess || !reviewMutation.data) return null;

    const result = reviewMutation.data;
    const riskConfig = RISK_CONFIG[result.riskLevel];

    return (
      <div className="mt-6 bg-white border border-gray-200 rounded-xl overflow-hidden">
        {/* 结果头部 */}
        <div className={`${riskConfig.bg} ${riskConfig.border} border-b px-6 py-4`}>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <span className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-semibold ${riskConfig.bg} ${riskConfig.color} border ${riskConfig.border}`}>
                {riskConfig.label}
              </span>
              <span className="text-gray-600">
                发现 {result.riskCount} 个风险点
              </span>
            </div>
            <span className="text-sm text-gray-400">ID: {result.requestId}</span>
          </div>
        </div>

        {/* 报告内容 */}
        <div className="p-6">
          {/* 合同信息 */}
          <div className="mb-6 p-4 bg-gray-50 rounded-lg">
            <h4 className="font-medium text-gray-900 mb-2">合同信息</h4>
            <div className="grid grid-cols-2 gap-4 text-sm">
              <div>
                <span className="text-gray-500">文件名：</span>
                <span className="text-gray-900">{result.filename}</span>
              </div>
              <div>
                <span className="text-gray-500">文本长度：</span>
                <span className="text-gray-900">{result.textChars} 字符</span>
              </div>
              {result.contractType && (
                <div>
                  <span className="text-gray-500">合同类型：</span>
                  <span className="text-gray-900">{result.contractType}</span>
                </div>
              )}
            </div>
          </div>

          {/* 风险摘要 */}
          {result.reportJson.summary && (
            <div className="mb-6">
              <h4 className="font-medium text-gray-900 mb-2">审查摘要</h4>
              <p className="text-sm text-gray-600 leading-relaxed">
                {result.reportJson.summary}
              </p>
            </div>
          )}

          {/* 风险列表 */}
          {result.reportJson.risks && result.reportJson.risks.length > 0 && (
            <div className="mb-6">
              <h4 className="font-medium text-gray-900 mb-3">
                风险点 ({result.reportJson.risks.length})
              </h4>
              <div className="space-y-3">
                {result.reportJson.risks.map((risk) => (
                  <div
                    key={risk.id}
                    className="p-4 border border-gray-200 rounded-lg hover:border-gray-300 transition-colors"
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

          {/* 缺失条款 */}
          {result.reportJson.missingClauses && result.reportJson.missingClauses.length > 0 && (
            <div className="mb-6">
              <h4 className="font-medium text-gray-900 mb-3">
                缺失条款 ({result.reportJson.missingClauses.length})
              </h4>
              <div className="space-y-2">
                {result.reportJson.missingClauses.map((clause, index) => (
                  <div
                    key={index}
                    className="flex items-start gap-3 p-3 bg-orange-50 border border-orange-200 rounded-lg"
                  >
                    <span className="flex-shrink-0 w-6 h-6 bg-orange-100 text-orange-600 rounded-full flex items-center justify-center text-xs font-medium">
                      {index + 1}
                    </span>
                    <div>
                      <p className="text-sm font-medium text-gray-900">{clause.clause}</p>
                      <p className="text-sm text-gray-600 mt-0.5">{clause.suggestion}</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* 建议修改 */}
          {result.reportJson.suggestedEdits && result.reportJson.suggestedEdits.length > 0 && (
            <div className="mb-6">
              <h4 className="font-medium text-gray-900 mb-3">建议修改</h4>
              <div className="space-y-3">
                {result.reportJson.suggestedEdits.map((edit, index) => (
                  <div key={index} className="p-4 bg-gray-50 rounded-lg">
                    <div className="mb-2">
                      <span className="text-xs font-medium text-red-600">原文：</span>
                      <p className="text-sm text-gray-700 mt-1">{edit.original}</p>
                    </div>
                    <div className="mb-2">
                      <span className="text-xs font-medium text-green-600">建议：</span>
                      <p className="text-sm text-gray-700 mt-1">{edit.suggested}</p>
                    </div>
                    <p className="text-xs text-gray-500">{edit.reason}</p>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* 法律依据 */}
          {result.reportJson.legalBasis && result.reportJson.legalBasis.length > 0 && (
            <div>
              <h4 className="font-medium text-gray-900 mb-2">法律依据</h4>
              <ul className="list-disc list-inside text-sm text-gray-600 space-y-1">
                {result.reportJson.legalBasis.map((basis, index) => (
                  <li key={index}>{basis}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      </div>
    );
  };

  return (
    <div className="w-full">
      {!selectedFile ? renderUploadArea() : renderFilePreview()}
      {renderReviewResult()}
    </div>
  );
}