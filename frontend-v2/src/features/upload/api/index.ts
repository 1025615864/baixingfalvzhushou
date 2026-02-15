/**
 * 文件上传 API 层
 * 基于统一的 apiClient，对接后端 /api/v1/upload 端点
 */

import { apiClient } from "@/shared/lib/api/client";

import type {
  FileUploadRequest,
  ImageUploadRequest,
  BatchUploadRequest,
  UploadResponse,
} from '../types';

// API 基础路径
const API_BASE = '/upload';

/**
 * 上传文件
 * @param request - 文件上传请求
 * @returns 上传响应
 */
export async function apiUploadFile(request: FileUploadRequest): Promise<UploadResponse> {
  const { file, onProgress, signal } = request;

  const formData = new FormData();
  formData.append('file', file);

  const response = await apiClient.post<UploadResponse>(`${API_BASE}/file`, formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
    onUploadProgress: (progressEvent) => {
      if (onProgress && progressEvent.total) {
        const progress = Math.round((progressEvent.loaded * 100) / progressEvent.total);
        onProgress(progress);
      }
    },
    signal,
  });

  return response.data;
}

/**
 * 上传图片
 * @param request - 图片上传请求
 * @returns 上传响应
 */
export async function apiUploadImage(request: ImageUploadRequest): Promise<UploadResponse> {
  const { file, onProgress, signal, compress, quality, maxWidth, maxHeight } = request;

  let processedFile = file;

  // 如果需要压缩，先处理图片
  if (compress) {
    processedFile = await compressImage(file, {
      quality: quality ?? 0.8,
      maxWidth: maxWidth ?? 1920,
      maxHeight: maxHeight ?? 1080,
    });
  }

  const formData = new FormData();
  formData.append('file', processedFile);

  const response = await apiClient.post<UploadResponse>(`${API_BASE}/image`, formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
    onUploadProgress: (progressEvent) => {
      if (onProgress && progressEvent.total) {
        const progress = Math.round((progressEvent.loaded * 100) / progressEvent.total);
        onProgress(progress);
      }
    },
    signal,
  });

  return response.data;
}

/**
 * 上传头像
 * @param request - 头像上传请求
 * @returns 上传响应
 */
export async function apiUploadAvatar(request: FileUploadRequest): Promise<UploadResponse> {
  const { file, onProgress, signal } = request;

  const formData = new FormData();
  formData.append('file', file);

  const response = await apiClient.post<UploadResponse>(`${API_BASE}/avatar`, formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
    onUploadProgress: (progressEvent) => {
      if (onProgress && progressEvent.total) {
        const progress = Math.round((progressEvent.loaded * 100) / progressEvent.total);
        onProgress(progress);
      }
    },
    signal,
  });

  return response.data;
}

/**
 * 批量上传文件
 * @param request - 批量上传请求
 * @returns 上传响应数组
 */
export async function apiBatchUploadFiles(request: BatchUploadRequest): Promise<UploadResponse[]> {
  const { files, onProgress, onFileComplete, onFileError, signal } = request;

  const results: UploadResponse[] = [];
  const totalFiles = files.length;

  for (let i = 0; i < totalFiles; i++) {
    // 检查是否已取消
    if (signal?.aborted) {
      throw new Error('上传已取消');
    }

    const file = files[i];
    const fileProgress = { current: 0 };

    try {
      const response = await apiUploadFile({
        file,
        onProgress: (progress) => {
          fileProgress.current = progress;
          if (onProgress) {
            const totalProgress = Math.round(
              ((i * 100) + progress) / totalFiles
            );
            onProgress(totalProgress, i, progress);
          }
        },
        signal,
      });

      results.push(response);

      if (onFileComplete) {
        onFileComplete(file, response);
      }
    } catch (error) {
      if (onFileError) {
        onFileError(file, error as Error);
      }
      throw error;
    }
  }

  return results;
}

/**
 * 批量上传图片
 * @param request - 批量上传请求
 * @returns 上传响应数组
 */
export async function apiBatchUploadImages(request: BatchUploadRequest): Promise<UploadResponse[]> {
  const { files, onProgress, onFileComplete, onFileError, signal } = request;

  const results: UploadResponse[] = [];
  const totalFiles = files.length;

  for (let i = 0; i < totalFiles; i++) {
    // 检查是否已取消
    if (signal?.aborted) {
      throw new Error('上传已取消');
    }

    const file = files[i];
    const fileProgress = { current: 0 };

    try {
      const response = await apiUploadImage({
        file,
        onProgress: (progress) => {
          fileProgress.current = progress;
          if (onProgress) {
            const totalProgress = Math.round(
              ((i * 100) + progress) / totalFiles
            );
            onProgress(totalProgress, i, progress);
          }
        },
        signal,
      });

      results.push(response);

      if (onFileComplete) {
        onFileComplete(file, response);
      }
    } catch (error) {
      if (onFileError) {
        onFileError(file, error as Error);
      }
      throw error;
    }
  }

  return results;
}

/**
 * 压缩图片
 * @param file - 原图片文件
 * @param options - 压缩选项
 * @returns 压缩后的图片文件
 */
export async function compressImage(
  file: File,
  options: {
    quality?: number;
    maxWidth?: number;
    maxHeight?: number;
  } = {}
): Promise<File> {
  const { quality = 0.8, maxWidth = 1920, maxHeight = 1080 } = options;

  return new Promise((resolve, reject) => {
    const img = new Image();
    const url = URL.createObjectURL(file);

    img.onload = () => {
      URL.revokeObjectURL(url);

      // 计算压缩后的尺寸
      let { width, height } = img;
      const ratio = Math.min(maxWidth / width, maxHeight / height, 1);

      if (ratio < 1) {
        width *= ratio;
        height *= ratio;
      }

      // 创建 canvas
      const canvas = document.createElement('canvas');
      canvas.width = width;
      canvas.height = height;

      const ctx = canvas.getContext('2d');
      if (!ctx) {
        reject(new Error('无法创建 canvas 上下文'));
        return;
      }

      // 绘制图片
      ctx.drawImage(img, 0, 0, width, height);

      // 转换为 blob
      canvas.toBlob(
        (blob) => {
          if (!blob) {
            reject(new Error('图片压缩失败'));
            return;
          }

          // 创建新的文件对象
          const compressedFile = new File([blob], file.name, {
            type: file.type,
            lastModified: file.lastModified,
          });

          resolve(compressedFile);
        },
        file.type,
        quality
      );
    };

    img.onerror = () => {
      URL.revokeObjectURL(url);
      reject(new Error('图片加载失败'));
    };

    img.src = url;
  });
}

/**
 * 获取图片预览 URL
 * @param file - 图片文件
 * @returns 预览 URL
 */
export function getImagePreviewUrl(file: File): string {
  return URL.createObjectURL(file);
}

/**
 * 释放预览 URL
 * @param url - 预览 URL
 */
export function revokeImagePreviewUrl(url: string): void {
  URL.revokeObjectURL(url);
}

/**
 * 获取文件下载 URL
 * @param filename - 文件名
 * @returns 下载 URL
 */
export function getFileDownloadUrl(filename: string): string {
  return `${API_BASE}/files/${filename}`;
}

/**
 * 获取图片访问 URL
 * @param filename - 文件名
 * @returns 访问 URL
 */
export function getImageUrl(filename: string): string {
  return `${API_BASE}/images/${filename}`;
}

/**
 * 获取头像访问 URL
 * @param filename - 文件名
 * @returns 访问 URL
 */
export function getAvatarUrl(filename: string): string {
  return `${API_BASE}/avatars/${filename}`;
}