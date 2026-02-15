/**
 * ContractCompare - 合同版本对比组件
 */

import { useState } from 'react';

import type { DiffType } from '../types';
import { useCompareContracts } from '../hooks/useContracts';

/** 差异类型配置 */
const DIFF_CONFIG: Record<DiffType, { label: string; color: string; bg: string; icon: string }> = {
  add: {
    label: '新增',
    color: 'text-green-700',
    bg: 'bg-green-50',
    icon: '+',
  },
  remove: {
    label: '删除',
    color: 'text-red-700',
    bg: 'bg-red-50',
    icon: '-',
  },
  modify: {
    label: '修改',
    color: 'text-yellow-700',
    bg: 'bg-yellow-50',
    icon: '~',
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

interface ContractCompareProps {
  /** 对比完成回调 */
  onCompareComplete?: () => void;
}

/**
 * 合同版本对比组件
 */
export function ContractCompare({ onCompareComplete }: ContractCompareProps): JSX.Element {
  const [originalFile, setOriginalFile] = useState<File | null>(null);
  const [newFile, setNewFile] = useState<File | null>(null);
  const [errors, setErrors] = useState<{ original?: string; new?: string }>({});

  const compareMutation = useCompareContracts();

  /** 验证文件 */
  const validateFile = (file: File): string | null => {
    if (!SUPPORTED_TYPES.includes(file.type)) {
      return '不支持的文件类型';
    }
    if (file.size > MAX_FILE_SIZE) {
      return '文件大小超过 10MB';
    }
    return null;
  };

  /** 处理原文件选择 */
  const handleOriginalFileSelect = (e: React.ChangeEvent<HTMLInputElement>): void => {
    const file = e.target.files?.[0];
    if (file) {
      const error = validateFile(file);
      if (error) {
        setErrors(prev => ({ ...prev, original: error }));
        setOriginalFile(null);
      } else {
        setErrors(prev => ({ ...prev, original: undefined }));
        setOriginalFile(file);
      }
    }
  };

  /** 处理新文件选择 */
  const handleNewFileSelect = (e: React.ChangeEvent<HTMLInputElement>): void => {
    const file = e.target.files?.[0];
    if (file) {
      const error = validateFile(file);
      if (error) {
        setErrors(prev => ({ ...prev, new: error }));
        setNewFile(null);
      } else {
        setErrors(prev => ({ ...prev, new: undefined }));
        setNewFile(file);
      }
    }
  };

  /** 开始对比 */
  const handleCompare = async (): Promise<void> => {
    if (!originalFile || !newFile) return;

    try {
      await compareMutation.mutateAsync({ originalFile, newFile });
      if (onCompareComplete) {
        onCompareComplete();
      }
    } catch (err) {
      // 错误已由 mutation 处理
    }
  };

  /** 清除选择 */
  const handleClear = (): void => {
    setOriginalFile(null);
    setNewFile(null);
    setErrors({});
    compareMutation.reset();
  };

  /** 渲染文件选择卡片 */
  const renderFileCard = (
    type: 'original' | 'new',
    file: File | null,
    onChange: (e: React.ChangeEvent<HTMLInputElement>) => void,
    error?: string
  ): JSX.Element => {
    const isOriginal = type === 'original';
    const title = isOriginal ? '原版本' : '新版本';
    const colorClass = isOriginal ? 'border-blue-300 bg-blue-50' : 'border-green-300 bg-green-50';

    return (
      <div className={`border-2 border-dashed rounded-xl p-6 ${file ? 'bg-white' : colorClass}`}>
        <h4 className="text-sm font-medium text-gray-700 mb-3">{title}</h4>
        
        {!file ? (
          <div className="relative">
            <input
              type="file"
              accept=".pdf,.doc,.docx,.txt"
              onChange={onChange}
              className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
            />
            <div className="text-center py-8">
              <svg
                className="mx-auto h-10 w-10 text-gray-400 mb-2"
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
              <p className="text-sm text-gray-600">点击选择文件</p>
              <p className="text-xs text-gray-400 mt-1">支持 PDF、Word、TXT</p>
            </div>
          </div>
        ) : (
          <div className="flex items-center gap-3 p-3 bg-gray-50 rounded-lg">
            <div className="w-10 h-10 bg-white rounded-lg flex items-center justify-center shadow-sm">
              <svg
                className="w-5 h-5 text-gray-400"
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
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-gray-900 truncate">{file.name}</p>
              <p className="text-xs text-gray-500">{(file.size / 1024).toFixed(1)} KB</p>
            </div>
            <button
              onClick={() => isOriginal ? setOriginalFile(null) : setNewFile(null)}
              className="p-1 text-gray-400 hover:text-red-500"
            >
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        )}
        
        {error && (
          <p className="mt-2 text-xs text-red-600">{error}</p>
        )}
      </div>
    );
  };

  /** 渲染对比结果 */
  const renderCompareResult = (): JSX.Element | null => {
    if (!compareMutation.isSuccess || !compareMutation.data) return null;

    const result = compareMutation.data;

    return (
      <div className="mt-6 bg-white border border-gray-200 rounded-xl overflow-hidden">
        {/* 结果头部 */}
        <div className="px-6 py-4 border-b border-gray-200 bg-gray-50">
          <div className="flex items-center justify-between">
            <h3 className="font-medium text-gray-900">对比结果</h3>
            <span className="text-sm text-gray-500">ID: {result.requestId}</span>
          </div>
          <div className="mt-2 flex items-center gap-4 text-sm">
            <span className="text-gray-600">原文件: {result.originalFilename}</span>
            <span className="text-gray-400">→</span>
            <span className="text-gray-600">新文件: {result.newFilename}</span>
          </div>
        </div>

        {/* 统计信息 */}
        <div className="px-6 py-4 border-b border-gray-200">
          <div className="grid grid-cols-3 gap-4">
            <div className="text-center p-3 bg-green-50 rounded-lg">
              <p className="text-2xl font-bold text-green-700">{result.summary.added}</p>
              <p className="text-sm text-green-600">新增</p>
            </div>
            <div className="text-center p-3 bg-red-50 rounded-lg">
              <p className="text-2xl font-bold text-red-700">{result.summary.removed}</p>
              <p className="text-sm text-red-600">删除</p>
            </div>
            <div className="text-center p-3 bg-yellow-50 rounded-lg">
              <p className="text-2xl font-bold text-yellow-700">{result.summary.modified}</p>
              <p className="text-sm text-yellow-600">修改</p>
            </div>
          </div>
        </div>

        {/* 差异列表 */}
        <div className="p-6">
          <h4 className="font-medium text-gray-900 mb-4">
            差异详情 ({result.differences.length})
          </h4>
          
          {result.differences.length === 0 ? (
            <div className="text-center py-8 text-gray-500">
              <p>两个文件内容相同，未发现差异</p>
            </div>
          ) : (
            <div className="space-y-3 max-h-96 overflow-y-auto">
              {result.differences.map((diff, index) => {
                const config = DIFF_CONFIG[diff.type];
                
                return (
                  <div
                    key={index}
                    className={`p-4 rounded-lg border ${config.bg} ${config.color.replace('text-', 'border-').replace('700', '200')}`}
                  >
                    <div className="flex items-start gap-3">
                      <span className={`
                        flex-shrink-0 w-6 h-6 rounded-full flex items-center justify-center text-sm font-bold
                        ${config.color} bg-white bg-opacity-50
                      `}>
                        {config.icon}
                      </span>
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-1">
                          <span className={`text-xs font-medium ${config.color}`}>
                            {config.label}
                          </span>
                          <span className="text-xs text-gray-400">
                            第 {diff.position.page} 页，第 {diff.position.line} 行
                          </span>
                        </div>
                        <p className="text-sm text-gray-700 whitespace-pre-wrap">
                          {diff.content}
                        </p>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </div>
    );
  };

  const canCompare = originalFile && newFile && !errors.original && !errors.new;

  return (
    <div className="w-full">
      {/* 文件选择区域 */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {renderFileCard('original', originalFile, handleOriginalFileSelect, errors.original)}
        {renderFileCard('new', newFile, handleNewFileSelect, errors.new)}
      </div>

      {/* 操作按钮 */}
      <div className="mt-4 flex items-center gap-3">
        <button
          onClick={() => void handleCompare()}
          disabled={!canCompare || compareMutation.isPending}
          className={`
            flex-1 py-3 px-4 rounded-lg font-medium text-white transition-all
            ${!canCompare || compareMutation.isPending
              ? 'bg-gray-400 cursor-not-allowed'
              : 'bg-blue-600 hover:bg-blue-700 shadow-sm hover:shadow'
            }
          `}
        >
          {compareMutation.isPending ? (
            <span className="flex items-center justify-center gap-2">
              <svg className="animate-spin h-5 w-5" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
              </svg>
              对比中...
            </span>
          ) : (
            '开始对比'
          )}
        </button>
        
        {(originalFile || newFile || compareMutation.data) && (
          <button
            onClick={handleClear}
            className="px-4 py-3 text-gray-600 hover:text-gray-800 hover:bg-gray-100 rounded-lg transition-colors"
          >
            重置
          </button>
        )}
      </div>

      {/* 错误提示 */}
      {compareMutation.isError && (
        <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded-lg text-sm text-red-600">
          {compareMutation.error?.message || '对比失败，请重试'}
        </div>
      )}

      {/* 对比结果 */}
      {renderCompareResult()}
    </div>
  );
}