/**
 * 文档导出组件
 * 提供导出文档为PDF/Word的功能
 */

import React, { useState } from 'react';

import type { ExportFormat, ExportDocumentDTO } from '../types';
import { EXPORT_FORMAT_CONFIG } from '../types';

export interface DocumentExportProps {
  /** 文档标题 */
  title: string;
  /** 文档内容 */
  content: string;
  /** 导出回调 */
  onExport: (data: ExportDocumentDTO) => void;
  /** 是否导出中 */
  isExporting?: boolean;
  /** 取消回调 */
  onCancel?: () => void;
  /** 额外样式类 */
  className?: string;
}

/**
 * 文档导出组件
 */
export function DocumentExport({
  title,
  content,
  onExport,
  isExporting = false,
  onCancel,
  className = '',
}: DocumentExportProps): React.ReactElement {
  const [selectedFormat, setSelectedFormat] = useState<ExportFormat>('pdf');
  const [customFilename, setCustomFilename] = useState('');

  // 处理导出
  const handleExport = () => {
    const filename = customFilename.trim() || title || '未命名文档';
    onExport({
      title: filename,
      content,
      format: selectedFormat,
    });
  };

  // 导出格式选项
  const formatOptions: { value: ExportFormat; label: string; description: string }[] = [
    {
      value: 'pdf',
      label: 'PDF 格式',
      description: '适合打印和分享的固定版式文档',
    },
    {
      value: 'word',
      label: 'Word 格式',
      description: '可编辑的文档格式，便于后续修改',
    },
  ];

  return (
    <div className={`bg-white rounded-xl border border-gray-200 p-6 ${className}`}>
      <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
        <svg className="w-5 h-5 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
        </svg>
        导出文档
      </h3>

      {/* 导出格式选择 */}
      <div className="space-y-3 mb-6">
        <label className="block text-sm font-medium text-gray-700">
          选择导出格式
        </label>
        {formatOptions.map((option) => (
          <label
            key={option.value}
            className={`
              flex items-start gap-3 p-4 rounded-lg border-2 cursor-pointer transition-all
              ${selectedFormat === option.value 
                ? 'border-blue-500 bg-blue-50' 
                : 'border-gray-200 hover:border-gray-300'}
            `}
          >
            <input
              type="radio"
              name="exportFormat"
              value={option.value}
              checked={selectedFormat === option.value}
              onChange={() => setSelectedFormat(option.value)}
              className="mt-1 w-4 h-4 text-blue-600 border-gray-300 focus:ring-blue-500"
            />
            <div>
              <span className="font-medium text-gray-900 block">{option.label}</span>
              <span className="text-sm text-gray-500">{option.description}</span>
            </div>
          </label>
        ))}
      </div>

      {/* 文件名设置 */}
      <div className="mb-6">
        <label className="block text-sm font-medium text-gray-700 mb-2">
          文件名（可选）
        </label>
        <div className="flex items-center gap-2">
          <input
            type="text"
            value={customFilename}
            onChange={(e) => setCustomFilename(e.target.value)}
            placeholder={title || '未命名文档'}
            className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none"
          />
          <span className="text-gray-500 text-sm">
            {EXPORT_FORMAT_CONFIG[selectedFormat].extension}
          </span>
        </div>
        <p className="mt-1 text-xs text-gray-500">
          留空将使用文档原标题
        </p>
      </div>

      {/* 导出预览信息 */}
      <div className="bg-gray-50 rounded-lg p-4 mb-6">
        <h4 className="text-sm font-medium text-gray-700 mb-2">导出预览</h4>
        <div className="text-sm text-gray-600 space-y-1">
          <p>文件名：{(customFilename.trim() || title || '未命名文档') + EXPORT_FORMAT_CONFIG[selectedFormat].extension}</p>
          <p>格式：{EXPORT_FORMAT_CONFIG[selectedFormat].label}</p>
          <p>内容长度：{content.length} 字符</p>
        </div>
      </div>

      {/* 操作按钮 */}
      <div className="flex items-center justify-end gap-3">
        {onCancel && (
          <button
            onClick={onCancel}
            disabled={isExporting}
            className="px-6 py-2 text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200 transition-colors disabled:opacity-50"
          >
            取消
          </button>
        )}
        <button
          onClick={handleExport}
          disabled={isExporting}
          className="px-6 py-2 text-white bg-blue-600 rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50 flex items-center gap-2"
        >
          {isExporting ? (
            <>
              <svg className="animate-spin h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              导出中...
            </>
          ) : (
            <>
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
              </svg>
              确认导出
            </>
          )}
        </button>
      </div>
    </div>
  );
}