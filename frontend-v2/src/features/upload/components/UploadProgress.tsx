/**
 * 上传进度条组件
 */

import React from 'react';

import type { UploadFile } from '../types';
import { formatFileSize } from '../types';

/**
 * UploadProgressProps 接口
 */
export interface UploadProgressProps {
  /** 上传文件对象 */
  file: UploadFile;
  /** 是否显示文件名 */
  showName?: boolean;
  /** 是否显示文件大小 */
  showSize?: boolean;
  /** 自定义类名 */
  className?: string;
}

/**
 * 上传进度条组件
 */
export function UploadProgress({
  file,
  showName = true,
  showSize = false,
  className = '',
}: UploadProgressProps): React.ReactElement {
  const { status, progress, name, size, error } = file;

  // 根据状态获取颜色
  const getStatusColor = () => {
    switch (status) {
      case 'success':
        return 'bg-green-500';
      case 'error':
        return 'bg-red-500';
      case 'cancelled':
        return 'bg-gray-400';
      case 'uploading':
        return 'bg-blue-500';
      default:
        return 'bg-gray-300';
    }
  };

  // 根据状态获取文本
  const getStatusText = () => {
    switch (status) {
      case 'success':
        return '上传成功';
      case 'error':
        return error || '上传失败';
      case 'cancelled':
        return '已取消';
      case 'uploading':
        return `上传中 ${progress}%`;
      default:
        return '等待上传';
    }
  };

  return (
    <div className={`w-full ${className}`}>
      {/* 文件信息 */}
      {(showName || showSize) && (
        <div className="flex justify-between items-center mb-1">
          {showName && (
            <span className="text-sm text-gray-700 truncate flex-1 mr-2" title={name}>
              {name}
            </span>
          )}
          {showSize && (
            <span className="text-xs text-gray-500 whitespace-nowrap">
              {formatFileSize(size)}
            </span>
          )}
        </div>
      )}

      {/* 进度条 */}
      <div className="relative w-full h-2 bg-gray-200 rounded-full overflow-hidden">
        <div
          className={`absolute left-0 top-0 h-full transition-all duration-300 ease-out ${getStatusColor()}`}
          style={{ width: `${progress}%` }}
        />
      </div>

      {/* 状态文本 */}
      <div className="flex justify-between items-center mt-1">
        <span
          className={`text-xs ${
            status === 'error'
              ? 'text-red-500'
              : status === 'success'
              ? 'text-green-500'
              : 'text-gray-500'
          }`}
        >
          {getStatusText()}
        </span>
        <span className="text-xs text-gray-400">{progress}%</span>
      </div>
    </div>
  );
}

/**
 * 圆形进度条组件
 */
export interface CircularProgressProps {
  /** 进度值 0-100 */
  progress: number;
  /** 大小 */
  size?: number;
  /** 线条宽度 */
  strokeWidth?: number;
  /** 自定义类名 */
  className?: string;
}

/**
 * 圆形进度条组件
 */
export function CircularProgress({
  progress,
  size = 40,
  strokeWidth = 4,
  className = '',
}: CircularProgressProps): React.ReactElement {
  const radius = (size - strokeWidth) / 2;
  const circumference = radius * 2 * Math.PI;
  const offset = circumference - (progress / 100) * circumference;

  return (
    <div className={`relative inline-flex items-center justify-center ${className}`}>
      <svg width={size} height={size} className="transform -rotate-90">
        {/* 背景圆环 */}
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke="#e5e7eb"
          strokeWidth={strokeWidth}
        />
        {/* 进度圆环 */}
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke="#3b82f6"
          strokeWidth={strokeWidth}
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          className="transition-all duration-300 ease-out"
        />
      </svg>
      {/* 进度文本 */}
      <span className="absolute text-xs font-medium text-gray-700">{Math.round(progress)}%</span>
    </div>
  );
}

/**
 * 批量上传总进度组件
 */
export interface BatchUploadProgressProps {
  /** 上传文件列表 */
  files: UploadFile[];
  /** 自定义类名 */
  className?: string;
}

/**
 * 批量上传总进度组件
 */
export function BatchUploadProgress({
  files,
  className = '',
}: BatchUploadProgressProps): React.ReactElement {
  const totalFiles = files.length;
  const completedFiles = files.filter(
    (f) => f.status === 'success' || f.status === 'error' || f.status === 'cancelled'
  ).length;
  const uploadingFiles = files.filter((f) => f.status === 'uploading').length;

  // 计算总进度
  const totalProgress =
    totalFiles > 0
      ? files.reduce((sum, file) => sum + file.progress, 0) / totalFiles
      : 0;

  return (
    <div className={`w-full ${className}`}>
      {/* 统计信息 */}
      <div className="flex justify-between items-center mb-2">
        <span className="text-sm text-gray-700">
          总进度 ({completedFiles}/{totalFiles})
        </span>
        <span className="text-xs text-gray-500">
          {uploadingFiles > 0 ? `${uploadingFiles} 个文件上传中` : ''}
        </span>
      </div>

      {/* 总进度条 */}
      <div className="relative w-full h-3 bg-gray-200 rounded-full overflow-hidden">
        <div
          className="absolute left-0 top-0 h-full bg-blue-500 transition-all duration-300 ease-out"
          style={{ width: `${totalProgress}%` }}
        />
      </div>

      {/* 进度百分比 */}
      <div className="text-right mt-1">
        <span className="text-xs text-gray-500">{Math.round(totalProgress)}%</span>
      </div>
    </div>
  );
}

export default UploadProgress;