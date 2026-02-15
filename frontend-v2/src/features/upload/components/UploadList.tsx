/**
 * 上传文件列表组件
 */

import React from 'react';

import type { UploadFile } from '../types';
import { formatFileSize, isImageFile } from '../types';

import { UploadProgress } from './UploadProgress';

/**
 * UploadListProps 接口
 */
export interface UploadListProps {
  /** 上传文件列表 */
  files: UploadFile[];
  /** 是否显示文件列表 */
  showRemove?: boolean;
  /** 删除回调 */
  onRemove?: (id: string) => void;
  /** 自定义类名 */
  className?: string;
}

/** 文件图标SVG */
const FileIcon = ({ className = '' }: { className?: string }) => (
  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className={className}>
    <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
    <polyline points="14 2 14 8 20 8" />
  </svg>
);

/** 图片图标SVG */
const ImageIcon = ({ className = '' }: { className?: string }) => (
  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className={className}>
    <rect x="3" y="3" width="18" height="18" rx="2" ry="2" />
    <circle cx="8.5" cy="8.5" r="1.5" />
    <polyline points="21 15 16 10 5 21" />
  </svg>
);

/** 成功图标SVG */
const SuccessIcon = ({ className = '' }: { className?: string }) => (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" className={className}>
    <polyline points="20 6 9 17 4 12" />
  </svg>
);

/** 错误图标SVG */
const ErrorIcon = ({ className = '' }: { className?: string }) => (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" className={className}>
    <line x1="18" y1="6" x2="6" y2="18" />
    <line x1="6" y1="6" x2="18" y2="18" />
  </svg>
);

/** 删除图标SVG */
const DeleteIcon = ({ className = '' }: { className?: string }) => (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className={className}>
    <polyline points="3 6 5 6 21 6" />
    <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2" />
  </svg>
);

/**
 * 上传文件列表组件
 */
export function UploadList({
  files,
  showRemove = true,
  onRemove,
  className = '',
}: UploadListProps): React.ReactElement {
  if (files.length === 0) {
    return <div className="hidden" />;
  }

  return (
    <div className={`space-y-3 ${className}`}>
      {files.map((file) => (
        <div
          key={file.id}
          className="flex items-start space-x-3 p-3 bg-gray-50 rounded-lg border border-gray-100"
        >
          {/* 文件图标或图片缩略图 */}
          <div className="flex-shrink-0">
            {file.previewUrl && isImageFile(file.file) ? (
              <img
                src={file.previewUrl}
                alt={file.name}
                className="w-12 h-12 object-cover rounded"
              />
            ) : (
              <div className="w-12 h-12 flex items-center justify-center bg-gray-200 rounded">
                {isImageFile(file.file) ? (
                  <ImageIcon className="text-gray-500" />
                ) : (
                  <FileIcon className="text-gray-500" />
                )}
              </div>
            )}
          </div>

          {/* 文件信息和进度 */}
          <div className="flex-1 min-w-0">
            <UploadProgress
              file={file}
              showName={true}
              showSize={true}
            />
          </div>

          {/* 状态图标和删除按钮 */}
          <div className="flex items-center space-x-2">
            {/* 状态图标 */}
            {file.status === 'success' && (
              <SuccessIcon className="text-green-500" />
            )}
            {file.status === 'error' && (
              <ErrorIcon className="text-red-500" />
            )}

            {/* 删除按钮 */}
            {showRemove && onRemove && (
              <button
                type="button"
                onClick={() => onRemove(file.id)}
                className="p-1 text-gray-400 hover:text-red-500 transition-colors"
                aria-label="删除文件"
              >
                <DeleteIcon />
              </button>
            )}
          </div>
        </div>
      ))}
    </div>
  );
}

/**
 * 简洁版上传列表组件
 */
export interface CompactUploadListProps {
  /** 上传文件列表 */
  files: UploadFile[];
  /** 是否显示文件列表 */
  showRemove?: boolean;
  /** 删除回调 */
  onRemove?: (id: string) => void;
  /** 自定义类名 */
  className?: string;
}

/**
 * 简洁版上传列表组件
 */
export function CompactUploadList({
  files,
  showRemove = true,
  onRemove,
  className = '',
}: CompactUploadListProps): React.ReactElement {
  if (files.length === 0) {
    return <div className="hidden" />;
  }

  return (
    <div className={`space-y-2 ${className}`}>
      {files.map((file) => (
        <div
          key={file.id}
          className="flex items-center justify-between p-2 bg-gray-50 rounded border border-gray-100"
        >
          <div className="flex items-center space-x-2 flex-1 min-w-0">
            {/* 文件类型图标 */}
            {isImageFile(file.file) ? (
              <ImageIcon className="text-gray-400 flex-shrink-0" />
            ) : (
              <FileIcon className="text-gray-400 flex-shrink-0" />
            )}

            {/* 文件名 */}
            <span className="text-sm text-gray-700 truncate" title={file.name}>
              {file.name}
            </span>

            {/* 文件大小 */}
            <span className="text-xs text-gray-400 whitespace-nowrap">
              ({formatFileSize(file.size)})
            </span>
          </div>

          {/* 右侧内容 */}
          <div className="flex items-center space-x-2 flex-shrink-0">
            {/* 进度或状态 */}
            {file.status === 'uploading' && (
              <span className="text-xs text-blue-500">{file.progress}%</span>
            )}
            {file.status === 'success' && (
              <SuccessIcon className="text-green-500" />
            )}
            {file.status === 'error' && (
              <span className="text-xs text-red-500" title={file.error}>失败</span>
            )}

            {/* 删除按钮 */}
            {showRemove && onRemove && (
              <button
                type="button"
                onClick={() => onRemove(file.id)}
                className="p-1 text-gray-400 hover:text-red-500 transition-colors"
                aria-label="删除文件"
              >
                <DeleteIcon />
              </button>
            )}
          </div>
        </div>
      ))}
    </div>
  );
}

export default UploadList;