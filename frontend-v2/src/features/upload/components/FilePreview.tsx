/**
 * 文件预览组件
 */

import React, { useState } from 'react';

import type { UploadFile } from '../types';
import { isImageFile, formatFileSize, getFileExtension } from '../types';

/**
 * FilePreviewProps 接口
 */
export interface FilePreviewProps {
  /** 上传文件对象 */
  file: UploadFile;
  /** 是否可删除 */
  removable?: boolean;
  /** 删除回调 */
  onRemove?: (id: string) => void;
  /** 自定义类名 */
  className?: string;
}

/** 图片SVG图标 */
const ImageIcon = ({ size = 32, className = '' }: { size?: number; className?: string }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className={className}>
    <rect x="3" y="3" width="18" height="18" rx="2" ry="2" />
    <circle cx="8.5" cy="8.5" r="1.5" />
    <polyline points="21 15 16 10 5 21" />
  </svg>
);

/** 文件SVG图标 */
const FileIcon = ({ size = 32, className = '' }: { size?: number; className?: string }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className={className}>
    <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
    <polyline points="14 2 14 8 20 8" />
    <line x1="16" y1="13" x2="8" y2="13" />
    <line x1="16" y1="17" x2="8" y2="17" />
    <polyline points="10 9 9 9 8 9" />
  </svg>
);

/** 音乐SVG图标 */
const MusicIcon = ({ size = 32, className = '' }: { size?: number; className?: string }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className={className}>
    <path d="M9 18V5l12-2v13" />
    <circle cx="6" cy="18" r="3" />
    <circle cx="18" cy="16" r="3" />
  </svg>
);

/** 视频SVG图标 */
const VideoIcon = ({ size = 32, className = '' }: { size?: number; className?: string }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className={className}>
    <rect x="2" y="2" width="20" height="20" rx="2.18" ry="2.18" />
    <line x1="7" y1="2" x2="7" y2="22" />
    <line x1="17" y1="2" x2="17" y2="22" />
    <line x1="2" y1="12" x2="22" y2="12" />
    <line x1="2" y1="7" x2="7" y2="7" />
    <line x1="2" y1="17" x2="7" y2="17" />
    <line x1="17" y1="17" x2="22" y2="17" />
    <line x1="17" y1="7" x2="22" y2="7" />
  </svg>
);

/** 代码SVG图标 */
const CodeIcon = ({ size = 32, className = '' }: { size?: number; className?: string }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className={className}>
    <polyline points="16 18 22 12 16 6" />
    <polyline points="8 6 2 12 8 18" />
  </svg>
);

/** 关闭SVG图标 */
const CloseIcon = ({ size = 14 }: { size?: number }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3">
    <line x1="18" y1="6" x2="6" y2="18" />
    <line x1="6" y1="6" x2="18" y2="18" />
  </svg>
);

/** 放大SVG图标 */
const ZoomInIcon = ({ size = 20, className }: { size?: number; className?: string }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className={className}>
    <circle cx="11" cy="11" r="8" />
    <line x1="21" y1="21" x2="16.65" y2="16.65" />
    <line x1="11" y1="8" x2="11" y2="14" />
    <line x1="8" y1="11" x2="14" y2="11" />
  </svg>
);

/**
 * 文件预览组件
 */
export function FilePreview({
  file,
  removable = false,
  onRemove,
  className = '',
}: FilePreviewProps): React.ReactElement {
  const [imageLoaded, setImageLoaded] = useState(false);
  const [imageError, setImageError] = useState(false);

  // 判断是否为图片
  const isImage = isImageFile(file.file);

  // 获取文件图标
  const getFileIcon = () => {
    const ext = getFileExtension(file.name);
    const iconProps = { size: 32, className: 'text-gray-400' };

    if (isImage) return <ImageIcon {...iconProps} />;
    if (['mp3', 'wav', 'ogg', 'm4a'].includes(ext)) return <MusicIcon {...iconProps} />;
    if (['mp4', 'webm', 'ogg'].includes(ext)) return <VideoIcon {...iconProps} />;
    if (['js', 'ts', 'html', 'css', 'json', 'xml'].includes(ext)) return <CodeIcon {...iconProps} />;

    return <FileIcon {...iconProps} />;
  };

  // 处理图片加载完成
  const handleImageLoad = () => {
    setImageLoaded(true);
  };

  // 处理图片加载失败
  const handleImageError = () => {
    setImageError(true);
  };

  return (
    <div className={`relative group ${className}`}>
      {/* 图片预览 */}
      {isImage && file.previewUrl && !imageError ? (
        <div className="relative w-24 h-24 rounded-lg overflow-hidden bg-gray-100 border border-gray-200">
          <img
            src={file.previewUrl}
            alt={file.name}
            className={`w-full h-full object-cover transition-opacity duration-300 ${
              imageLoaded ? 'opacity-100' : 'opacity-0'
            }`}
            onLoad={handleImageLoad}
            onError={handleImageError}
          />
          {!imageLoaded && (
            <div className="absolute inset-0 flex items-center justify-center">
              <ImageIcon size={24} className="text-gray-400 animate-pulse" />
            </div>
          )}
          {/* 悬停遮罩 */}
          <div className="absolute inset-0 bg-black/0 group-hover:bg-black/40 transition-all duration-200 flex items-center justify-center opacity-0 group-hover:opacity-100">
            <ZoomInIcon size={20} className="text-white" />
          </div>
        </div>
      ) : (
        /* 文件图标预览 */
        <div className="w-24 h-24 rounded-lg bg-gray-50 border border-gray-200 flex flex-col items-center justify-center p-2">
          {getFileIcon()}
          <span className="text-xs text-gray-500 mt-1 text-center truncate w-full">
            {file.name.length > 12 ? `${file.name.slice(0, 12)}...` : file.name}
          </span>
          <span className="text-xs text-gray-400">{formatFileSize(file.size)}</span>
        </div>
      )}

      {/* 删除按钮 */}
      {removable && onRemove && (
        <button
          type="button"
          onClick={() => onRemove(file.id)}
          className="absolute -top-2 -right-2 w-6 h-6 bg-red-500 hover:bg-red-600 text-white rounded-full flex items-center justify-center shadow-md transition-colors duration-200 opacity-0 group-hover:opacity-100"
          aria-label="删除文件"
        >
          <CloseIcon size={14} />
        </button>
      )}

      {/* 状态指示器 */}
      {file.status === 'success' && (
        <div className="absolute -bottom-1 -right-1 w-5 h-5 bg-green-500 rounded-full flex items-center justify-center">
          <svg className="w-3 h-3 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" />
          </svg>
        </div>
      )}
      {file.status === 'error' && (
        <div className="absolute -bottom-1 -right-1 w-5 h-5 bg-red-500 rounded-full flex items-center justify-center">
          <svg className="w-3 h-3 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M6 18L18 6M6 6l12 12" />
          </svg>
        </div>
      )}
    </div>
  );
}

/**
 * 大图预览组件
 */
export interface ImagePreviewModalProps {
  /** 图片URL */
  src: string;
  /** 是否显示 */
  visible: boolean;
  /** 关闭回调 */
  onClose: () => void;
  /** 标题 */
  title?: string;
}

/**
 * 图片预览弹窗组件
 */
export function ImagePreviewModal({
  src,
  visible,
  onClose,
  title,
}: ImagePreviewModalProps): React.ReactElement | null {
  if (!visible) return null;

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm"
      onClick={onClose}
    >
      <div className="relative max-w-4xl max-h-[90vh] p-4" onClick={(e) => e.stopPropagation()}>
        {/* 关闭按钮 */}
        <button
          type="button"
          onClick={onClose}
          className="absolute top-2 right-2 w-10 h-10 bg-white/10 hover:bg-white/20 text-white rounded-full flex items-center justify-center transition-colors"
          aria-label="关闭预览"
        >
          <CloseIcon size={24} />
        </button>

        {/* 图片 */}
        <img
          src={src}
          alt={title || '预览'}
          className="max-w-full max-h-[80vh] object-contain rounded-lg"
        />

        {/* 标题 */}
        {title && <p className="text-white text-center mt-4 text-sm">{title}</p>}
      </div>
    </div>
  );
}

/**
 * 文件列表预览组件
 */
export interface FileListPreviewProps {
  /** 文件列表 */
  files: UploadFile[];
  /** 是否可删除 */
  removable?: boolean;
  /** 删除回调 */
  onRemove?: (id: string) => void;
  /** 自定义类名 */
  className?: string;
}

/**
 * 文件列表预览组件
 */
export function FileListPreview({
  files,
  removable = false,
  onRemove,
  className = '',
}: FileListPreviewProps): React.ReactElement {
  if (files.length === 0) {
    return <div className="text-gray-400 text-sm text-center py-4">暂无文件</div>;
  }

  return (
    <div className={`grid grid-cols-4 sm:grid-cols-6 md:grid-cols-8 gap-4 ${className}`}>
      {files.map((file) => (
        <FilePreview
          key={file.id}
          file={file}
          removable={removable}
          onRemove={onRemove}
        />
      ))}
    </div>
  );
}

export default FilePreview;