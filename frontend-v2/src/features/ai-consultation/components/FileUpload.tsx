/**
 * 文件上传组件
 * 
 * 支持多种文件格式（PDF、Word、图片等）上传并进行AI分析
 */

import { useCallback, useState, useRef } from 'react';

import {
  useAnalysis,
  formatFileSize,
  getFileTypeDisplayName,
  getFileIconType,
  isImageFile,
  readFileAsDataURL,
  MAX_FILE_SIZE,
} from '../hooks/useAnalysis';

/** 文件上传组件Props */
interface FileUploadProps {
  /** 分析完成回调 */
  onAnalysisComplete: (result: { text: string; summary: string }) => void;
  /** 取消回调 */
  onCancel: () => void;
}

/**
 * 文件上传组件
 */
export function FileUpload({ onAnalysisComplete, onCancel }: FileUploadProps): JSX.Element {
  const { state, analyzeFile, reset, validateFile } = useAnalysis();
  const [dragActive, setDragActive] = useState(false);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  // 处理文件选择
  const handleFile = useCallback(
    async (file: File) => {
      const validation = validateFile(file);
      if (!validation.valid) {
        return;
      }

      // 如果是图片，生成预览
      if (isImageFile(file)) {
        try {
          const dataUrl = await readFileAsDataURL(file);
          setPreviewUrl(dataUrl);
        } catch {
          setPreviewUrl(null);
        }
      } else {
        setPreviewUrl(null);
      }

      try {
        const result = await analyzeFile(file);
        onAnalysisComplete({
          text: result.textPreview,
          summary: result.summary,
        });
      } catch {
        // 错误已在hook中处理
      }
    },
    [analyzeFile, onAnalysisComplete, validateFile]
  );

  // 处理文件选择
  const handleChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const file = e.target.files?.[0];
      if (file) {
        void handleFile(file);
      }
    },
    [handleFile]
  );

  // 拖拽处理
  const handleDrag = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  }, []);

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      e.stopPropagation();
      setDragActive(false);

      const file = e.dataTransfer.files?.[0];
      if (file) {
        void handleFile(file);
      }
    },
    [handleFile]
  );

  // 重新上传
  const handleRetry = useCallback(() => {
    reset();
    setPreviewUrl(null);
    if (inputRef.current) {
      inputRef.current.value = '';
    }
  }, [reset]);

  // 使用结果
  const handleUseResult = useCallback(() => {
    if (state.result) {
      onAnalysisComplete({
        text: state.result.textPreview,
        summary: state.result.summary,
      });
      handleRetry();
    }
  }, [state.result, onAnalysisComplete, handleRetry]);

  // 获取文件图标
  const getFileIcon = (_filename: string): JSX.Element => {
    const iconType = getFileIconType(state.result?.contentType || '');

    switch (iconType) {
      case 'pdf':
        return (
          <div className="w-12 h-12 bg-red-100 rounded-lg flex items-center justify-center">
            <svg className="w-6 h-6 text-red-600" fill="currentColor" viewBox="0 0 24 24">
              <path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8l-6-6z" />
              <path d="M14 3v5h5M16 13H8M16 17H8M10 9H8" stroke="white" strokeWidth="2" strokeLinecap="round" />
            </svg>
          </div>
        );
      case 'word':
        return (
          <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center">
            <svg className="w-6 h-6 text-blue-600" fill="currentColor" viewBox="0 0 24 24">
              <path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8l-6-6z" />
              <path d="M14 3v5h5M16 13H8M16 17H8M10 9H8" stroke="white" strokeWidth="2" strokeLinecap="round" />
            </svg>
          </div>
        );
      case 'text':
        return (
          <div className="w-12 h-12 bg-gray-100 rounded-lg flex items-center justify-center">
            <svg className="w-6 h-6 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
          </div>
        );
      case 'image':
        return previewUrl ? (
          <img src={previewUrl} alt="预览" className="w-12 h-12 object-cover rounded-lg" />
        ) : (
          <div className="w-12 h-12 bg-purple-100 rounded-lg flex items-center justify-center">
            <svg className="w-6 h-6 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
            </svg>
          </div>
        );
      default:
        return (
          <div className="w-12 h-12 bg-gray-100 rounded-lg flex items-center justify-center">
            <svg className="w-6 h-6 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
            </svg>
          </div>
        );
    }
  };

  return (
    <div className="bg-white border border-gray-200 rounded-xl overflow-hidden">
      {/* 上传区域 */}
      {state.uploadStatus === 'idle' && (
        <div
          className={`p-8 text-center border-2 border-dashed rounded-xl m-4 transition-colors
            ${dragActive ? 'border-blue-500 bg-blue-50' : 'border-gray-300 hover:border-gray-400'}`}
          onDragEnter={handleDrag}
          onDragLeave={handleDrag}
          onDragOver={handleDrag}
          onDrop={handleDrop}
        >
          <div className="w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <svg className="w-8 h-8 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
            </svg>
          </div>
          <p className="text-gray-700 font-medium mb-1">点击或拖拽文件到此处</p>
          <p className="text-sm text-gray-400 mb-4">支持 PDF、Word、TXT、图片等格式</p>
          <input
            ref={inputRef}
            type="file"
            accept=".pdf,.doc,.docx,.txt,.jpg,.jpeg,.png,.gif,.webp"
            onChange={handleChange}
            className="hidden"
          />
          <button
            onClick={() => inputRef.current?.click()}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors text-sm font-medium"
          >
            选择文件
          </button>
          <p className="text-xs text-gray-400 mt-3">最大支持 {formatFileSize(MAX_FILE_SIZE)}</p>
        </div>
      )}

      {/* 上传中/处理中 */}
      {(state.uploadStatus === 'uploading' || state.uploadStatus === 'processing') && (
        <div className="p-8 text-center">
          <div className="w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <svg className="w-8 h-8 text-blue-600 animate-spin" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
            </svg>
          </div>
          <p className="text-gray-700 font-medium mb-2">
            {state.uploadStatus === 'uploading' ? '正在上传...' : '正在分析...'}
          </p>
          {/* 进度条 */}
          <div className="w-full max-w-xs h-2 bg-gray-200 rounded-full mx-auto overflow-hidden">
            <div
              className="h-full bg-blue-600 transition-all duration-300"
              style={{ width: `${state.progress}%` }}
            />
          </div>
          <p className="text-sm text-gray-400 mt-2">{state.progress}%</p>
        </div>
      )}

      {/* 完成 */}
      {state.uploadStatus === 'completed' && state.result && (
        <div className="p-6">
          <div className="flex items-center gap-4 mb-4">
            {getFileIcon(state.result.filename)}
            <div className="flex-1 min-w-0">
              <p className="font-medium text-gray-900 truncate">{state.result.filename}</p>
              <p className="text-sm text-gray-500">
                {getFileTypeDisplayName(state.result.contentType || '')} · {state.result.textChars} 字符
              </p>
            </div>
            <div className="flex items-center gap-1 text-green-600">
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <span className="text-sm font-medium">分析完成</span>
            </div>
          </div>

          {/* 分析摘要 */}
          <div className="bg-gray-50 rounded-xl p-4 mb-4">
            <h4 className="text-sm font-medium text-gray-700 mb-2">分析摘要</h4>
            <p className="text-sm text-gray-600 leading-relaxed">{state.result.summary}</p>
          </div>

          {/* 文本预览 */}
          {state.result.textPreview && (
            <div className="bg-gray-50 rounded-xl p-4">
              <h4 className="text-sm font-medium text-gray-700 mb-2">内容预览</h4>
              <p className="text-sm text-gray-600 leading-relaxed line-clamp-6">
                {state.result.textPreview}
              </p>
            </div>
          )}
        </div>
      )}

      {/* 错误 */}
      {state.uploadStatus === 'error' && (
        <div className="p-8 text-center">
          <div className="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <svg className="w-8 h-8 text-red-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
          <p className="text-red-600 font-medium mb-1">上传失败</p>
          <p className="text-sm text-gray-500 mb-4">{state.error || '请重试'}</p>
          <button
            onClick={handleRetry}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors text-sm font-medium"
          >
            重新上传
          </button>
        </div>
      )}

      {/* 操作按钮 */}
      <div className="flex items-center justify-between px-6 py-4 bg-gray-50 border-t border-gray-200">
        <button
          onClick={() => {
            handleRetry();
            onCancel();
          }}
          className="px-4 py-2 text-gray-600 hover:text-gray-800 hover:bg-gray-200 rounded-lg transition-colors text-sm font-medium"
        >
          关闭
        </button>

        {state.uploadStatus === 'completed' && (
          <div className="flex items-center gap-2">
            <button
              onClick={handleRetry}
              className="px-4 py-2 text-gray-600 hover:text-gray-800 hover:bg-gray-200 rounded-lg transition-colors text-sm font-medium"
            >
              重新上传
            </button>
            <button
              onClick={handleUseResult}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors text-sm font-medium"
            >
              使用分析结果
            </button>
          </div>
        )}
      </div>
    </div>
  );
}

/** 文件上传按钮组件 */
interface FileUploadButtonProps {
  /** 点击回调 */
  onClick: () => void;
  /** 是否禁用 */
  disabled?: boolean;
}

/**
 * 文件上传按钮组件
 */
export function FileUploadButton({ onClick, disabled }: FileUploadButtonProps): JSX.Element {
  return (
    <button
      onClick={onClick}
      disabled={disabled}
      className="p-2.5 text-gray-400 hover:text-gray-600 hover:bg-gray-100 
               rounded-xl transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
      title="上传文件"
    >
      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15.172 7l-6.586 6.586a2 2 0 102.828 2.828l6.414-6.586a4 4 0 00-5.656-5.656l-6.415 6.585a6 6 0 108.486 8.486L20.5 13" />
      </svg>
    </button>
  );
}