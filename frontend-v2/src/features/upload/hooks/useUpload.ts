/**
 * 文件上传 React Query Hooks
 */

import { useState, useCallback, useRef } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';

import type {
  UploadFile,
  UploadResponse,
  FileUploadRequest,
} from '../types';
import { generateUploadId } from '../types';
import {
  apiUploadFile,
  apiUploadImage,
  apiUploadAvatar,
  apiBatchUploadFiles,
  apiBatchUploadImages,
  getImagePreviewUrl,
  revokeImagePreviewUrl,
} from '../api';

// 查询键常量
export const uploadQueryKeys = {
  all: ['upload'] as const,
  files: () => [...uploadQueryKeys.all, 'files'] as const,
  images: () => [...uploadQueryKeys.all, 'images'] as const,
  avatars: () => [...uploadQueryKeys.all, 'avatars'] as const,
};

/**
 * 单文件上传 Hook
 */
export function useUploadFile() {
  return useMutation({
    mutationFn: apiUploadFile,
  });
}

/**
 * 单图片上传 Hook
 */
export function useUploadImage() {
  return useMutation({
    mutationFn: apiUploadImage,
  });
}

/**
 * 头像上传 Hook
 */
export function useUploadAvatar() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: apiUploadAvatar,
    onSuccess: () => {
      // 上传成功后，刷新用户相关信息
      void queryClient.invalidateQueries({ queryKey: ['user'] });
    },
  });
}

/**
 * 批量文件上传 Hook
 */
export function useBatchUploadFiles() {
  return useMutation({
    mutationFn: apiBatchUploadFiles,
  });
}

/**
 * 批量图片上传 Hook
 */
export function useBatchUploadImages() {
  return useMutation({
    mutationFn: apiBatchUploadImages,
  });
}

/**
 * 管理上传文件列表的 Hook
 */
export function useUploadFileList() {
  const [uploadFiles, setUploadFiles] = useState<UploadFile[]>([]);
  const abortControllersRef = useRef<Map<string, AbortController>>(new Map());

  /**
   * 添加文件到上传列表
   */
  const addFiles = useCallback((files: File[]) => {
    const newUploadFiles: UploadFile[] = files.map((file) => {
      const uploadId = generateUploadId();
      const previewUrl = file.type.startsWith('image/')
        ? getImagePreviewUrl(file)
        : undefined;

      return {
        id: uploadId,
        file,
        name: file.name,
        size: file.size,
        type: file.type,
        progress: 0,
        status: 'pending',
        previewUrl,
      };
    });

    setUploadFiles((prev) => [...prev, ...newUploadFiles]);
    return newUploadFiles.map((f) => f.id);
  }, []);

  /**
   * 从上传列表中移除文件
   */
  const removeFile = useCallback((uploadId: string) => {
    setUploadFiles((prev) => {
      const file = prev.find((f) => f.id === uploadId);
      if (file?.previewUrl) {
        revokeImagePreviewUrl(file.previewUrl);
      }
      return prev.filter((f) => f.id !== uploadId);
    });

    // 取消正在上传的请求
    const controller = abortControllersRef.current.get(uploadId);
    if (controller) {
      controller.abort();
      abortControllersRef.current.delete(uploadId);
    }
  }, []);

  /**
   * 清空上传列表
   */
  const clearFiles = useCallback(() => {
    uploadFiles.forEach((file) => {
      if (file.previewUrl) {
        revokeImagePreviewUrl(file.previewUrl);
      }
    });

    // 取消所有正在上传的请求
    abortControllersRef.current.forEach((controller) => {
      controller.abort();
    });
    abortControllersRef.current.clear();

    setUploadFiles([]);
  }, [uploadFiles]);

  /**
   * 更新文件状态
   */
  const updateFileStatus = useCallback(
    (uploadId: string, updates: Partial<UploadFile>) => {
      setUploadFiles((prev) =>
        prev.map((f) => (f.id === uploadId ? { ...f, ...updates } : f))
      );
    },
    []
  );

  /**
   * 上传单个文件
   */
  const uploadSingleFile = useCallback(
    async (
      uploadId: string,
      uploadFn: (request: FileUploadRequest) => Promise<UploadResponse>,
      options?: {
        onSuccess?: (response: UploadResponse) => void;
        onError?: (error: Error) => void;
      }
    ) => {
      const file = uploadFiles.find((f) => f.id === uploadId);
      if (!file) {
        options?.onError?.(new Error('文件不存在'));
        return;
      }

      // 创建 AbortController
      const controller = new AbortController();
      abortControllersRef.current.set(uploadId, controller);

      try {
        updateFileStatus(uploadId, { status: 'uploading', progress: 0 });

        const response = await uploadFn({
          file: file.file,
          onProgress: (progress) => {
            updateFileStatus(uploadId, { progress });
          },
          signal: controller.signal,
        });

        updateFileStatus(uploadId, {
          status: 'success',
          progress: 100,
          url: response.url,
          filename: response.filename,
          originalName: response.original_name,
        });

        options?.onSuccess?.(response);
        return response;
      } catch (error) {
        const errorMessage =
          error instanceof Error ? error.message : '上传失败';

        // 检查是否是取消错误
        if (error instanceof Error && error.name === 'AbortError') {
          updateFileStatus(uploadId, {
            status: 'cancelled',
            error: '已取消上传',
          });
        } else {
          updateFileStatus(uploadId, {
            status: 'error',
            error: errorMessage,
          });
        }

        options?.onError?.(error instanceof Error ? error : new Error(errorMessage));
        throw error;
      } finally {
        abortControllersRef.current.delete(uploadId);
      }
    },
    [uploadFiles, updateFileStatus]
  );

  /**
   * 取消文件上传
   */
  const cancelUpload = useCallback((uploadId: string) => {
    const controller = abortControllersRef.current.get(uploadId);
    if (controller) {
      controller.abort();
      abortControllersRef.current.delete(uploadId);
    }
  }, []);

  return {
    uploadFiles,
    addFiles,
    removeFile,
    clearFiles,
    updateFileStatus,
    uploadSingleFile,
    cancelUpload,
  };
}

/**
 * 图片上传管理 Hook
 */
export function useImageUploader() {
  const {
    uploadFiles,
    addFiles,
    removeFile,
    clearFiles,
    updateFileStatus,
    uploadSingleFile,
    cancelUpload,
  } = useUploadFileList();

  /**
   * 上传图片
   */
  const handleUpload = useCallback(
    async (
      uploadId: string,
      options?: {
        compress?: boolean;
        quality?: number;
        maxWidth?: number;
        maxHeight?: number;
        onSuccess?: (response: UploadResponse) => void;
        onError?: (error: Error) => void;
      }
    ) => {
      const uploadImageFunc = async (request: FileUploadRequest) => {
        const { apiUploadImage } = await import('../api');
        return apiUploadImage({
          ...request,
          compress: options?.compress,
          quality: options?.quality,
          maxWidth: options?.maxWidth,
          maxHeight: options?.maxHeight,
        });
      };

      await uploadSingleFile(uploadId, uploadImageFunc, options);
    },
    [uploadSingleFile]
  );

  return {
    uploadFiles,
    addFiles,
    removeFile,
    clearFiles,
    updateFileStatus,
    handleUpload,
    cancelUpload,
  };
}

/**
 * 文件上传管理 Hook
 */
export function useFileUploader() {
  const {
    uploadFiles,
    addFiles,
    removeFile,
    clearFiles,
    updateFileStatus,
    uploadSingleFile,
    cancelUpload,
  } = useUploadFileList();

  /**
   * 上传文件
   */
  const handleUpload = useCallback(
    async (
      uploadId: string,
      options?: {
        onSuccess?: (response: UploadResponse) => void;
        onError?: (error: Error) => void;
      }
    ) => {
      const { apiUploadFile } = await import('../api');
      await uploadSingleFile(uploadId, apiUploadFile, options);
    },
    [uploadSingleFile]
  );

  return {
    uploadFiles,
    addFiles,
    removeFile,
    clearFiles,
    updateFileStatus,
    handleUpload,
    cancelUpload,
  };
}