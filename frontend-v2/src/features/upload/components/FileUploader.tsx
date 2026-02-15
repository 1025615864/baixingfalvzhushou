/**
 * 文件上传组件
 */

import React, { useCallback, useState } from 'react';

import type { UploadConfig, UploadResponse } from '../types';
import {
  validateAttachmentFile,
  FILE_SIZE_LIMITS,
  ALLOWED_FILE_TYPES,
} from '../types';
import { useFileUploader } from '../hooks/useUpload';

import { UploadDropzone } from './UploadDropzone';
import { UploadList } from './UploadList';

/**
 * FileUploaderProps 接口
 */
export interface FileUploaderProps extends UploadConfig {
  /** 值（已上传文件URL列表） */
  value?: string[];
  /** 默认值 */
  defaultValue?: string[];
  /** 文件选择回调 */
  onChange?: (urls: string[]) => void;
  /** 上传成功回调 */
  onSuccess?: (response: UploadResponse) => void;
  /** 上传失败回调 */
  onError?: (error: Error) => void;
  /** 自定义类名 */
  className?: string;
  /** 提示文本 */
  placeholder?: string;
}

/**
 * 文件上传组件
 */
export function FileUploader({
  accept,
  maxSize = FILE_SIZE_LIMITS.FILE_MAX_SIZE,
  multiple = false,
  maxCount = 10,
  disabled = false,
  showUploadList = true,
  autoUpload = true,
  value,
  defaultValue,
  onChange,
  onSuccess,
  onError,
  className = '',
  placeholder = '点击或拖拽文件到此处上传',
}: FileUploaderProps): React.ReactElement {
  const {
    uploadFiles,
    addFiles,
    removeFile,
    handleUpload,
  } = useFileUploader();

  const [uploadedUrls, setUploadedUrls] = useState<string[]>(value || defaultValue || []);

  // 同步外部value
  React.useEffect(() => {
    if (value !== undefined) {
      setUploadedUrls(value);
    }
  }, [value]);

  /**
   * 处理文件选择
   */
  const handleFilesSelected = useCallback(
    (files: File[]) => {
      // 验证文件
      const validFiles = files.filter((file) => {
        const result = validateAttachmentFile(file, maxSize);
        if (!result.valid) {
          onError?.(new Error(result.error || '文件验证失败'));
          return false;
        }
        return true;
      });

      if (validFiles.length === 0) return;

      // 检查文件数量限制
      const currentCount = uploadFiles.length + uploadedUrls.length;
      if (maxCount && currentCount + validFiles.length > maxCount) {
        onError?.(new Error(`最多只能上传 ${maxCount} 个文件`));
        return;
      }

      // 添加到上传列表
      const newUploadIds = addFiles(validFiles);

      // 自动上传
      if (autoUpload) {
        newUploadIds.forEach((uploadId) => {
          void handleUpload(uploadId, {
            onSuccess: (response: UploadResponse) => {
              const newUrls = [...uploadedUrls, response.url];
              setUploadedUrls(newUrls);
              onChange?.(newUrls);
              onSuccess?.(response);
            },
            onError: (error: Error) => {
              onError?.(error);
            },
          });
        });
      }
    },
    [addFiles, autoUpload, maxSize, maxCount, uploadFiles.length, uploadedUrls, onError, handleUpload, onChange, onSuccess]
  );

  /**
   * 处理文件删除
   */
  const handleRemove = useCallback(
    (uploadId: string) => {
      const file = uploadFiles.find((f) => f.id === uploadId);
      if (file?.url) {
        // 已上传的文件，从URL列表中移除
        const newUrls = uploadedUrls.filter((url) => url !== file.url);
        setUploadedUrls(newUrls);
        onChange?.(newUrls);
      }
      removeFile(uploadId);
    },
    [uploadFiles, uploadedUrls, removeFile, onChange]
  );

  /**
   * 格式化accept属性
   */
  const formatAccept = useCallback(() => {
    if (accept) return accept;
    // 默认允许所有支持的文件类型
    return ALLOWED_FILE_TYPES.join(',');
  }, [accept]);

  return (
    <div className={`space-y-4 ${className}`}>
      {/* 拖拽上传区域 */}
      <UploadDropzone
        accept={formatAccept()}
        maxSize={maxSize}
        multiple={multiple}
        maxCount={maxCount ? maxCount - uploadFiles.length - uploadedUrls.length : undefined}
        disabled={disabled}
        onFilesSelected={handleFilesSelected}
        promptText={placeholder}
      />

      {/* 上传列表 */}
      {showUploadList && uploadFiles.length > 0 && (
        <UploadList files={uploadFiles} onRemove={handleRemove} showRemove={!disabled} />
      )}

      {/* 已上传文件列表 */}
      {showUploadList && uploadedUrls.length > 0 && (
        <div className="space-y-2">
          <h4 className="text-sm font-medium text-gray-700">已上传文件</h4>
          <div className="space-y-2">
            {uploadedUrls.map((url, index) => (
              <div
                key={`${url}-${index}`}
                className="flex items-center justify-between p-2 bg-gray-50 rounded border border-gray-100"
              >
                <a
                  href={url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-sm text-blue-500 hover:text-blue-600 truncate flex-1"
                >
                  {url.split('/').pop() || url}
                </a>
                {!disabled && (
                  <button
                    type="button"
                    onClick={() => {
                      const newUrls = uploadedUrls.filter((_, i) => i !== index);
                      setUploadedUrls(newUrls);
                      onChange?.(newUrls);
                    }}
                    className="ml-2 text-gray-400 hover:text-red-500 transition-colors"
                  >
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <line x1="18" y1="6" x2="6" y2="18" />
                      <line x1="6" y1="6" x2="18" y2="18" />
                    </svg>
                  </button>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

export default FileUploader;