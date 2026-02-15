/**
 * 文档上传组件
 * 支持上传本地文档文件
 */

import React, { useRef, useState } from 'react';

export interface DocumentUploadProps {
  /** 上传成功回调 */
  onUpload?: (file: File, content: string) => void;
  /** 接受文件类型 */
  accept?: string;
  /** 最大文件大小（MB） */
  maxSize?: number;
  /** 是否上传中 */
  isUploading?: boolean;
  /** 额外样式类 */
  className?: string;
}

/**
 * 文档上传组件
 */
export function DocumentUpload({
  onUpload,
  accept = '.txt,.doc,.docx,.pdf,.md',
  maxSize = 10,
  isUploading = false,
  className = '',
}: DocumentUploadProps): React.ReactElement {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [dragActive, setDragActive] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // 验证文件
  const validateFile = (file: File): boolean => {
    setError(null);

    // 检查文件大小
    if (file.size > maxSize * 1024 * 1024) {
      setError(`文件大小不能超过 ${maxSize}MB`);
      return false;
    }

    // 检查文件类型
    const allowedTypes = accept.split(',').map(t => t.trim().toLowerCase());
    const fileExtension = `.${file.name.split('.').pop()?.toLowerCase()}`;
    
    if (!allowedTypes.includes(fileExtension)) {
      setError(`不支持的文件格式，请上传 ${accept} 格式的文件`);
      return false;
    }

    return true;
  };

  // 读取文件内容
  const readFileContent = (file: File): Promise<string> => {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      
      reader.onload = (e) => {
        const content = e.target?.result as string;
        resolve(content);
      };
      
      reader.onerror = () => {
        reject(new Error('读取文件失败'));
      };

      // 对于文本文件直接读取
      if (file.type.includes('text') || file.name.endsWith('.md') || file.name.endsWith('.txt')) {
        reader.readAsText(file);
      } else {
        // 对于其他文件类型，只返回文件名信息
        resolve(`[文件: ${file.name}, 大小: ${(file.size / 1024).toFixed(2)}KB]`);
      }
    });
  };

  // 处理文件选择
  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    if (!validateFile(file)) {
      return;
    }

    void (async () => {
      try {
        const content = await readFileContent(file);
        onUpload?.(file, content);
      } catch {
        setError('读取文件内容失败');
      }

      // 重置 input
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    })();
  };

  // 处理拖拽事件
  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  // 处理拖放
  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);

    const file = e.dataTransfer.files?.[0];
    if (!file) return;

    if (!validateFile(file)) {
      return;
    }

    void (async () => {
      try {
        const content = await readFileContent(file);
        onUpload?.(file, content);
      } catch {
        setError('读取文件内容失败');
      }
    })();
  };

  // 点击上传区域
  const handleClick = () => {
    fileInputRef.current?.click();
  };

  return (
    <div className={className}>
      {/* 上传区域 */}
      <div
        onClick={handleClick}
        onDragEnter={handleDrag}
        onDragLeave={handleDrag}
        onDragOver={handleDrag}
        onDrop={handleDrop}
        className={`
          relative border-2 border-dashed rounded-xl p-8 text-center cursor-pointer
          transition-all duration-200
          ${dragActive 
            ? 'border-blue-500 bg-blue-50' 
            : 'border-gray-300 hover:border-gray-400 hover:bg-gray-50'}
          ${isUploading ? 'opacity-50 cursor-not-allowed' : ''}
        `}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept={accept}
          onChange={handleFileChange}
          disabled={isUploading}
          className="hidden"
        />

        {/* 上传图标 */}
        <div className="mb-4">
          {isUploading ? (
            <div className="inline-flex items-center justify-center w-16 h-16 bg-blue-100 rounded-full">
              <svg className="animate-spin w-8 h-8 text-blue-600" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
            </div>
          ) : (
            <div className="inline-flex items-center justify-center w-16 h-16 bg-gray-100 rounded-full">
              <svg className="w-8 h-8 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
              </svg>
            </div>
          )}
        </div>

        {/* 提示文字 */}
        <div className="space-y-1">
          <p className="text-base font-medium text-gray-900">
            {isUploading ? '上传中...' : '点击或拖拽文件到此处上传'}
          </p>
          <p className="text-sm text-gray-500">
            支持 {accept} 格式，单个文件不超过 {maxSize}MB
          </p>
        </div>
      </div>

      {/* 错误提示 */}
      {error && (
        <div className="mt-3 p-3 bg-red-50 border border-red-200 rounded-lg flex items-center gap-2 text-sm text-red-600">
          <svg className="w-4 h-4 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          {error}
        </div>
      )}
    </div>
  );
}