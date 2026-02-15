/**
 * 图片上传组件
 */

import React, { useCallback, useState } from 'react';

import type { ImageUploadConfig, UploadResponse } from '../types';
import {
  validateImageFile,
  FILE_SIZE_LIMITS,
  ALLOWED_IMAGE_TYPES,
} from '../types';
import { useImageUploader } from '../hooks/useUpload';

import { UploadDropzone } from './UploadDropzone';
import { UploadProgress } from './UploadProgress';
import { FilePreview } from './FilePreview';

/**
 * ImageUploaderProps 接口
 */
export interface ImageUploaderProps extends ImageUploadConfig {
  /** 值（已上传图片URL列表） */
  value?: string[];
  /** 默认值 */
  defaultValue?: string[];
  /** 图片选择回调 */
  onChange?: (urls: string[]) => void;
  /** 上传成功回调 */
  onSuccess?: (response: UploadResponse) => void;
  /** 上传失败回调 */
  onError?: (error: Error) => void;
  /** 自定义类名 */
  className?: string;
  /** 提示文本 */
  placeholder?: string;
  /** 是否显示预览 */
  showPreview?: boolean;
  /** 预览图片宽度 */
  previewWidth?: number;
  /** 预览图片高度 */
  previewHeight?: number;
}

/**
 * 图片上传组件
 */
export function ImageUploader({
  maxSize = FILE_SIZE_LIMITS.IMAGE_MAX_SIZE,
  multiple = false,
  maxCount = 9,
  disabled = false,
  showUploadList = true,
  autoUpload = true,
  compress = false,
  compressQuality = 0.8,
  maxWidth = 1920,
  maxHeight = 1080,
  value,
  defaultValue,
  onChange,
  onSuccess,
  onError,
  className = '',
  placeholder = '点击或拖拽图片到此处上传',
  showPreview = true,
  previewWidth = 100,
  previewHeight = 100,
}: ImageUploaderProps): React.ReactElement {
  const {
    uploadFiles,
    addFiles,
    removeFile,
    handleUpload,
  } = useImageUploader();

  const [uploadedUrls, setUploadedUrls] = useState<string[]>(value || defaultValue || []);

  // 同步外部value
  React.useEffect(() => {
    if (value !== undefined) {
      setUploadedUrls(value);
    }
  }, [value]);

  /**
   * 处理图片选择
   */
  const handleFilesSelected = useCallback(
    (files: File[]) => {
      // 验证文件
      const validFiles = files.filter((file) => {
        const result = validateImageFile(file, maxSize);
        if (!result.valid) {
          onError?.(new Error(result.error || '图片验证失败'));
          return false;
        }
        return true;
      });

      if (validFiles.length === 0) return;

      // 检查文件数量限制
      const currentCount = uploadFiles.length + uploadedUrls.length;
      if (maxCount && currentCount + validFiles.length > maxCount) {
        onError?.(new Error(`最多只能上传 ${maxCount} 张图片`));
        return;
      }

      // 添加到上传列表
      const newUploadIds = addFiles(validFiles);

      // 自动上传
      if (autoUpload) {
        newUploadIds.forEach((uploadId) => {
          void handleUpload(uploadId, {
            compress,
            quality: compressQuality,
            maxWidth,
            maxHeight,
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
    [addFiles, autoUpload, maxSize, maxCount, uploadFiles.length, uploadedUrls, onError, handleUpload, compress, compressQuality, maxWidth, maxHeight, onChange, onSuccess]
  );

  /**
   * 处理图片删除
   */
  const handleRemove = useCallback(
    (uploadId: string) => {
      const file = uploadFiles.find((f) => f.id === uploadId);
      if (file?.url) {
        // 已上传的图片，从URL列表中移除
        const newUrls = uploadedUrls.filter((url) => url !== file.url);
        setUploadedUrls(newUrls);
        onChange?.(newUrls);
      }
      removeFile(uploadId);
    },
    [uploadFiles, uploadedUrls, removeFile, onChange]
  );

  return (
    <div className={`space-y-4 ${className}`}>
      {/* 拖拽上传区域 */}
      <UploadDropzone
        accept={ALLOWED_IMAGE_TYPES.join(',')}
        maxSize={maxSize}
        multiple={multiple}
        maxCount={maxCount ? maxCount - uploadFiles.length - uploadedUrls.length : undefined}
        disabled={disabled}
        onFilesSelected={handleFilesSelected}
        promptText={placeholder}
      />

      {/* 上传列表和预览 */}
      {showUploadList && (uploadFiles.length > 0 || uploadedUrls.length > 0) && (
        <div className="space-y-4">
          {/* 正在上传的图片预览 */}
          {showPreview && uploadFiles.length > 0 && (
            <div>
              <h4 className="text-sm font-medium text-gray-700 mb-2">正在上传</h4>
              <div className="flex flex-wrap gap-4">
                {uploadFiles.map((file) => (
                  <div key={file.id} className="space-y-2">
                    <FilePreview
                      file={file}
                      removable={!disabled}
                      onRemove={handleRemove}
                    />
                    {file.status === 'uploading' && (
                      <UploadProgress file={file} showName={false} showSize={false} />
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* 已上传图片预览 */}
          {showPreview && uploadedUrls.length > 0 && (
            <div>
              <h4 className="text-sm font-medium text-gray-700 mb-2">已上传</h4>
              <div className="flex flex-wrap gap-4">
                {uploadedUrls.map((url, index) => (
                  <div
                    key={`${url}-${index}`}
                    className="relative group"
                    style={{ width: previewWidth, height: previewHeight }}
                  >
                    <img
                      src={url}
                      alt={`已上传图片 ${index + 1}`}
                      className="w-full h-full object-cover rounded-lg border border-gray-200"
                    />
                    {/* 悬停遮罩 */}
                    <div className="absolute inset-0 bg-black/0 group-hover:bg-black/40 transition-all duration-200 flex items-center justify-center opacity-0 group-hover:opacity-100 rounded-lg">
                      <div className="flex space-x-2">
                        {/* 查看按钮 */}
                        <a
                          href={url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="p-2 bg-white rounded-full hover:bg-gray-100 transition-colors"
                          title="查看原图"
                        >
                          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                            <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z" />
                            <circle cx="12" cy="12" r="3" />
                          </svg>
                        </a>
                        {/* 删除按钮 */}
                        {!disabled && (
                          <button
                            type="button"
                            onClick={() => {
                              const newUrls = uploadedUrls.filter((_, i) => i !== index);
                              setUploadedUrls(newUrls);
                              onChange?.(newUrls);
                            }}
                            className="p-2 bg-white rounded-full hover:bg-red-50 text-gray-600 hover:text-red-500 transition-colors"
                            title="删除"
                          >
                            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                              <polyline points="3 6 5 6 21 6" />
                              <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2" />
                            </svg>
                          </button>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* 简洁列表视图（非预览模式） */}
          {!showPreview && uploadFiles.length > 0 && (
            <div className="space-y-2">
              {uploadFiles.map((file) => (
                <UploadProgress key={file.id} file={file} showName={true} showSize={true} />
              ))}
            </div>
          )}

          {/* 简洁列表视图（已上传） */}
          {!showPreview && uploadedUrls.length > 0 && (
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
          )}
        </div>
      )}
    </div>
  );
}

export default ImageUploader;