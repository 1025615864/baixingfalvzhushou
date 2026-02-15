/**
 * AI咨询文件分析功能Hook
 */

import { useState, useCallback } from 'react';
import { useMutation } from '@tanstack/react-query';

import type {
  FileAnalysisResponse,
  FileUploadRequest,
  FileAnalysisState,
} from '../types';
import { apiAnalyzeFile } from '../api';

// ==================== 常量 ====================

/** 最大文件大小（10MB） */
export const MAX_FILE_SIZE = 10 * 1024 * 1024;

/** 支持的文件类型 */
export const SUPPORTED_FILE_TYPES: Record<string, string> = {
  'application/pdf': 'PDF',
  'application/msword': 'Word',
  'application/vnd.openxmlformats-officedocument.wordprocessingml.document': 'Word',
  'text/plain': '文本',
  'image/jpeg': '图片',
  'image/png': '图片',
  'image/gif': '图片',
  'image/webp': '图片',
};

/** 支持的MIME类型列表 */
const SUPPORTED_MIME_TYPES = Object.keys(SUPPORTED_FILE_TYPES);

// ==================== Hook 返回类型 ====================

/** 文件分析Hook返回类型 */
interface UseAnalysisReturn {
  /** 分析状态 */
  state: FileAnalysisState;
  /** 上传并分析文件 */
  analyzeFile: (file: File) => Promise<FileAnalysisResponse>;
  /** 重置状态 */
  reset: () => void;
  /** 验证文件 */
  validateFile: (file: File) => { valid: boolean; error: string | null };
}

// ==================== Hook ====================

/**
 * 文件分析Hook
 */
export function useAnalysis(): UseAnalysisReturn {
  const [state, setState] = useState<FileAnalysisState>({
    uploadStatus: 'idle',
    result: null,
    error: null,
    progress: 0,
  });

  // 文件分析mutation
  const analyzeMutation = useMutation<FileAnalysisResponse, Error, FileUploadRequest>({
    mutationFn: apiAnalyzeFile,
    onMutate: () => {
      setState(prev => ({
        ...prev,
        uploadStatus: 'uploading',
        progress: 0,
        error: null,
      }));
    },
  });

  /** 验证文件 */
  const validateFile = useCallback((file: File): { valid: boolean; error: string | null } => {
    // 检查文件大小
    if (file.size === 0) {
      return { valid: false, error: '文件不能为空' };
    }

    if (file.size > MAX_FILE_SIZE) {
      return { valid: false, error: `文件大小不能超过${formatFileSize(MAX_FILE_SIZE)}` };
    }

    // 检查文件类型
    if (!SUPPORTED_MIME_TYPES.includes(file.type)) {
      return {
        valid: false,
        error: `不支持的文件类型: ${file.type || '未知'}。支持的格式：PDF、Word、TXT、图片(JPG/PNG/GIF/WebP)`,
      };
    }

    return { valid: true, error: null };
  }, []);

  /** 上传并分析文件 */
  const analyzeFile = useCallback(
    async (file: File): Promise<FileAnalysisResponse> => {
      const validation = validateFile(file);
      if (!validation.valid) {
        setState(prev => ({
          ...prev,
          uploadStatus: 'error',
          error: validation.error,
        }));
        throw new Error(validation.error || '文件验证失败');
      }

      try {
        // 模拟进度更新
        const progressInterval = setInterval(() => {
          setState(prev => ({
            ...prev,
            progress: Math.min(prev.progress + 10, 90),
          }));
        }, 200);

        setState(prev => ({
          ...prev,
          uploadStatus: 'processing',
        }));

        const result = await analyzeMutation.mutateAsync({ file });

        clearInterval(progressInterval);

        setState({
          uploadStatus: 'completed',
          result,
          error: null,
          progress: 100,
        });

        return result;
      } catch (error) {
        setState(prev => ({
          ...prev,
          uploadStatus: 'error',
          error: error instanceof Error ? error.message : '文件分析失败',
          progress: 0,
        }));
        throw error;
      }
    },
    [analyzeMutation, validateFile]
  );

  /** 重置状态 */
  const reset = useCallback((): void => {
    setState({
      uploadStatus: 'idle',
      result: null,
      error: null,
      progress: 0,
    });
    analyzeMutation.reset();
  }, [analyzeMutation]);

  return {
    state,
    analyzeFile,
    reset,
    validateFile,
  };
}

// ==================== 辅助函数 ====================

/**
 * 格式化文件大小显示
 */
export function formatFileSize(bytes: number): string {
  if (bytes === 0) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(2))} ${sizes[i]}`;
}

/**
 * 检查是否为支持的文件类型
 */
export function isSupportedFileType(file: File): boolean {
  return SUPPORTED_MIME_TYPES.includes(file.type);
}

/**
 * 获取文件类型显示名称
 */
export function getFileTypeDisplayName(mimeType: string): string {
  return SUPPORTED_FILE_TYPES[mimeType] || '文件';
}

/**
 * 获取文件图标类型
 */
export function getFileIconType(mimeType: string): 'pdf' | 'word' | 'text' | 'image' | 'unknown' {
  if (mimeType === 'application/pdf') {
    return 'pdf';
  }
  if (
    mimeType === 'application/msword' ||
    mimeType === 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
  ) {
    return 'word';
  }
  if (mimeType === 'text/plain') {
    return 'text';
  }
  if (mimeType.startsWith('image/')) {
    return 'image';
  }
  return 'unknown';
}

/**
 * 从文件名获取扩展名
 */
export function getFileExtension(filename: string): string {
  const parts = filename.split('.');
  return parts.length > 1 ? (parts.pop() ?? '').toLowerCase() : '';
}

/**
 * 检查文件是否为图片
 */
export function isImageFile(file: File): boolean {
  return file.type.startsWith('image/');
}

/**
 * 读取文件为Data URL（用于图片预览）
 */
export function readFileAsDataURL(file: File): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(reader.result as string);
    reader.onerror = reject;
    reader.readAsDataURL(file);
  });
}

/**
 * 读取文件为文本
 */
export function readFileAsText(file: File): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(reader.result as string);
    reader.onerror = reject;
    reader.readAsText(file);
  });
}