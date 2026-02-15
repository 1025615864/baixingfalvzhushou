/**
 * 拖拽上传区域组件
 */

import React, { useState, useCallback, useRef } from 'react';

import type { DropzoneConfig } from '../types';
import { validateFileType, validateFileSize, formatFileSize } from '../types';

/** 上传SVG图标 */
const UploadIcon = ({ size = 48, className = '' }: { size?: number; className?: string }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" className={className}>
    <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
    <polyline points="17 8 12 3 7 8" />
    <line x1="12" y1="3" x2="12" y2="15" />
  </svg>
);

/** 成功SVG图标 */
const CheckIcon = ({ size = 24, className = '' }: { size?: number; className?: string }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className={className}>
    <polyline points="20 6 9 17 4 12" />
  </svg>
);

/**
 * UploadDropzoneProps 接口
 */
export interface UploadDropzoneProps extends DropzoneConfig {
  /** 文件选择回调 */
  onFilesSelected: (files: File[]) => void;
  /** 自定义提示文本 */
  promptText?: string;
  /** 子元素 */
  children?: React.ReactNode;
}

/**
 * 拖拽上传区域组件
 */
export function UploadDropzone({
  accept,
  maxSize,
  multiple = false,
  maxCount,
  disabled = false,
  clickable = true,
  promptText,
  children,
  onFilesSelected,
  className = '',
}: UploadDropzoneProps): React.ReactElement {
  const [isDragging, setIsDragging] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  /**
   * 处理拖拽进入
   */
  const handleDragEnter = useCallback((e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    if (!disabled) {
      setIsDragging(true);
    }
  }, [disabled]);

  /**
   * 处理拖拽离开
   */
  const handleDragLeave = useCallback((e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
  }, []);

  /**
   * 处理拖拽悬停
   */
  const handleDragOver = useCallback((e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
  }, []);

  /**
   * 验证文件
   */
  const validateFiles = useCallback((files: FileList | null): File[] => {
    setError(null);

    if (!files || files.length === 0) {
      return [];
    }

    const validFiles: File[] = [];
    const fileArray = Array.from(files);

    // 检查文件数量
    if (maxCount && fileArray.length > maxCount) {
      setError(`最多只能选择 ${maxCount} 个文件`);
      return [];
    }

    for (const file of fileArray) {
      // 验证文件类型
      if (accept) {
        const acceptTypes = accept.split(',').map(t => t.trim());
        const typeResult = validateFileType(file, acceptTypes);
        if (!typeResult.valid) {
          setError(typeResult.error || '文件类型不支持');
          continue;
        }
      }

      // 验证文件大小
      if (maxSize) {
        const sizeResult = validateFileSize(file, maxSize);
        if (!sizeResult.valid) {
          setError(sizeResult.error || '文件大小超出限制');
          continue;
        }
      }

      validFiles.push(file);
    }

    return validFiles;
  }, [accept, maxSize, maxCount]);

  /**
   * 处理文件拖放
   */
  const handleDrop = useCallback((e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);

    if (disabled) return;

    const files = e.dataTransfer.files;
    const validFiles = validateFiles(files);

    if (validFiles.length > 0) {
      onFilesSelected(validFiles);
    }
  }, [disabled, validateFiles, onFilesSelected]);

  /**
   * 处理文件选择
   */
  const handleFileInput = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    const validFiles = validateFiles(files);

    if (validFiles.length > 0) {
      onFilesSelected(validFiles);
    }

    // 清空input，允许重复选择相同文件
    if (inputRef.current) {
      inputRef.current.value = '';
    }
  }, [validateFiles, onFilesSelected]);

  /**
   * 点击上传区域
   */
  const handleClick = useCallback(() => {
    if (clickable && !disabled && inputRef.current) {
      inputRef.current.click();
    }
  }, [clickable, disabled]);

  // 计算容器样式
  const containerClasses = [
    'relative border-2 border-dashed rounded-lg p-8 text-center transition-all duration-200',
    isDragging
      ? 'border-blue-500 bg-blue-50'
      : 'border-gray-300 bg-white hover:border-gray-400',
    clickable && !disabled ? 'cursor-pointer' : 'cursor-not-allowed opacity-60',
    error ? 'border-red-300 bg-red-50' : '',
    className,
  ].join(' ');

  // 默认提示文本
  const defaultPromptText = multiple
    ? `点击或拖拽文件到此处上传${maxCount ? `（最多 ${maxCount} 个）` : ''}`
    : '点击或拖拽文件到此处上传';

  // 文件大小提示
  const sizeHint = maxSize ? `单个文件不超过 ${formatFileSize(maxSize)}` : null;

  return (
    <div
      className={containerClasses}
      onDragEnter={handleDragEnter}
      onDragLeave={handleDragLeave}
      onDragOver={handleDragOver}
      onDrop={handleDrop}
      onClick={handleClick}
      role="button"
      tabIndex={clickable && !disabled ? 0 : -1}
      aria-disabled={disabled}
    >
      {/* 隐藏的文件输入 */}
      <input
        ref={inputRef}
        type="file"
        accept={accept}
        multiple={multiple}
        disabled={disabled}
        onChange={handleFileInput}
        className="hidden"
        aria-label="文件上传"
      />

      {/* 内容区域 */}
      <div className="flex flex-col items-center justify-center space-y-4">
        {children || (
          <>
            {/* 图标 */}
            <div className={`transition-colors duration-200 ${isDragging ? 'text-blue-500' : 'text-gray-400'}`}>
              <UploadIcon size={48} className={isDragging ? 'animate-bounce' : ''} />
            </div>

            {/* 提示文本 */}
            <div className="space-y-2">
              <p className="text-gray-600 font-medium">
                {promptText || defaultPromptText}
              </p>
              {sizeHint && (
                <p className="text-sm text-gray-400">{sizeHint}</p>
              )}
              {accept && (
                <p className="text-xs text-gray-400">
                  支持格式：{accept.replace(/\./g, ' ').toUpperCase()}
                </p>
              )}
            </div>

            {/* 错误提示 */}
            {error && (
              <div className="flex items-center text-red-500 text-sm">
                <span className="mr-1">!</span>
                {error}
              </div>
            )}

            {/* 拖拽中提示 */}
            {isDragging && !error && (
              <div className="flex items-center text-blue-500 text-sm animate-pulse">
                <CheckIcon size={16} className="mr-1" />
                松开以上传文件
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}

export default UploadDropzone;