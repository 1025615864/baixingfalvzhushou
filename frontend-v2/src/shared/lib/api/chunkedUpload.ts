/**
 * 大文件分片上传模块 (FR-013, FR-014)
 * 
 * 功能：
 * - 文件分片逻辑（>100MB 自动分片，每片 5MB）
 * - 分片上传并发控制
 * - 分片失败重试
 * - 上传合并请求
 * - 断点续传支持
 * - 上传进度监听 (FR-012)
 * - 上传错误分类和处理 (FR-014)
 */

import { apiClient } from './client';

// ============================================
// 类型定义
// ============================================

/** 上传错误类型 */
export type UploadErrorType = 
  | 'NETWORK_ERROR'      // 网络错误
  | 'SERVER_ERROR'       // 服务器错误
  | 'FILE_ERROR'         // 文件错误
  | 'TIMEOUT_ERROR'      // 超时错误
  | 'ABORT_ERROR'        // 取消错误
  | 'VALIDATION_ERROR';  // 验证错误

/** 上传错误接口 */
export interface UploadError {
  /** 错误类型 */
  type: UploadErrorType;
  /** 错误消息 */
  message: string;
  /** 原始错误 */
  cause?: Error;
  /** HTTP 状态码 */
  statusCode?: number;
  /** 已上传的分片索引 */
  uploadedChunks?: number[];
}

/** 分片信息接口 */
export interface ChunkInfo {
  /** 分片索引 */
  index: number;
  /** 分片数据 */
  blob: Blob;
  /** 分片大小 */
  size: number;
  /** 分片起始位置 */
  start: number;
  /** 分片结束位置 */
  end: number;
}

/** 分片上传进度接口 */
export interface ChunkProgress {
  /** 分片索引 */
  index: number;
  /** 分片上传进度 (0-100) */
  progress: number;
  /** 已上传字节数 */
  loaded: number;
  /** 总分片字节数 */
  total: number;
}

/** 整体上传进度接口 */
export interface UploadProgress {
  /** 整体进度百分比 (0-100) */
  percentage: number;
  /** 已上传字节数 */
  loaded: number;
  /** 总字节数 */
  total: number;
  /** 已完成的分片数 */
  uploadedChunks: number;
  /** 总分片数 */
  totalChunks: number;
  /** 当前上传的分片索引 */
  currentChunk?: number;
  /** 当前分片进度 */
  chunkProgress?: ChunkProgress;
}

/** 分片上传请求接口 */
export interface ChunkedUploadRequest {
  /** 文件对象 */
  file: File;
  /** 上传进度回调 */
  onProgress?: (progress: UploadProgress) => void;
  /** 上传成功回调 */
  onSuccess?: (response: UploadResponse) => void;
  /** 上传失败回调 */
  onError?: (error: UploadError) => void;
  /** 取消信号 */
  signal?: AbortSignal;
  /** 分片大小（字节），默认 5MB */
  chunkSize?: number;
  /** 并发上传数量，默认 3 */
  concurrency?: number;
  /** 重试次数，默认 3 */
  maxRetries?: number;
  /** 上传超时时间（毫秒），默认 30000 */
  timeout?: number;
}

/** 上传响应接口 */
export interface UploadResponse {
  /** 上传后的 URL */
  url: string;
  /** 文件名 */
  filename: string;
  /** 原始文件名 */
  originalName?: string;
  /** 消息 */
  message?: string;
  /** 文件 ID */
  fileId?: string;
}

/** 分片上传状态接口 */
export interface UploadState {
  /** 上传 ID */
  uploadId: string;
  /** 文件哈希 */
  fileHash?: string;
  /** 已上传的分片索引 */
  uploadedChunks: Set<number>;
  /** 正在上传的分片索引 */
  uploadingChunks: Set<number>;
  /** 失败的分片索引 */
  failedChunks: Map<number, number>; // index -> retry count
  /** 总字节数 */
  totalBytes: number;
  /** 已上传字节数 */
  uploadedBytes: number;
  /** 是否已取消 */
  aborted: boolean;
}

// ============================================
// 常量定义
// ============================================

/** 默认分片大小：5MB */
export const DEFAULT_CHUNK_SIZE = 5 * 1024 * 1024;

/** 大文件阈值：100MB，超过此大小自动启用分片上传 */
export const LARGE_FILE_THRESHOLD = 100 * 1024 * 1024;

/** 默认并发数量 */
export const DEFAULT_CONCURRENCY = 3;

/** 最大并发数量 */
export const MAX_CONCURRENCY = 6;

/** 默认重试次数 */
export const DEFAULT_MAX_RETRIES = 3;

/** 默认超时时间（毫秒） */
export const DEFAULT_TIMEOUT = 30000;

// ============================================
// 工具函数
// ============================================

/**
 * 创建上传错误对象
 */
export function createUploadError(
  type: UploadErrorType,
  message: string,
  cause?: Error,
  statusCode?: number
): UploadError {
  return {
    type,
    message,
    cause,
    statusCode,
  };
}

/**
 * 格式化错误消息
 */
export function formatUploadError(error: UploadError): string {
  switch (error.type) {
    case 'NETWORK_ERROR':
      return `网络错误：${error.message}`;
    case 'SERVER_ERROR':
      return `服务器错误 (${error.statusCode || '未知'}): ${error.message}`;
    case 'FILE_ERROR':
      return `文件错误：${error.message}`;
    case 'TIMEOUT_ERROR':
      return `上传超时：${error.message}`;
    case 'ABORT_ERROR':
      return `上传已取消：${error.message}`;
    case 'VALIDATION_ERROR':
      return `验证失败：${error.message}`;
    default:
      return error.message;
  }
}

/**
 * 计算文件哈希（简化版，使用文件大小和最后修改时间）
 * 实际项目中可使用 spark-md5 等库计算精确哈希
 */
export function computeFileHash(file: File): Promise<string> {
  return new Promise((resolve) => {
    // 简化哈希：使用文件大小、名称和最后修改时间
    const hash = `${file.name}-${file.size}-${file.lastModified}`;
    resolve(btoa(hash).replace(/[^a-zA-Z0-9]/g, '').substring(0, 32));
  });
}

/**
 * 将文件分片
 */
export function chunkFile(file: File, chunkSize: number = DEFAULT_CHUNK_SIZE): ChunkInfo[] {
  const chunks: ChunkInfo[] = [];
  const totalChunks = Math.ceil(file.size / chunkSize);
  
  for (let i = 0; i < totalChunks; i++) {
    const start = i * chunkSize;
    const end = Math.min(start + chunkSize, file.size);
    const blob = file.slice(start, end);
    
    chunks.push({
      index: i,
      blob,
      size: blob.size,
      start,
      end,
    });
  }
  
  return chunks;
}

/**
 * 检查文件是否需要分片上传
 */
export function shouldUseChunkedUpload(file: File): boolean {
  return file.size > LARGE_FILE_THRESHOLD;
}

// ============================================
// 错误分类辅助函数
// ============================================

/**
 * 错误分类
 */
function classifyError(error: unknown): UploadError {
  // 取消错误
  if (error && typeof error === 'object' && 'name' in error) {
    const err = error as Error;
    if (err.name === 'AbortError' || err.name === 'CanceledError') {
      return createUploadError('ABORT_ERROR', err.message, err);
    }
  }

  // HTTP 错误
  if (error && typeof error === 'object' && 'response' in error) {
    const err = error as { response?: { status?: number }; message?: string };
    const status = err.response?.status;
    
    if (status) {
      if (status >= 500) {
        return createUploadError('SERVER_ERROR', `服务器错误 (${status})`, err as Error, status);
      }
      
      if (status === 408 || status === 504) {
        return createUploadError('TIMEOUT_ERROR', `请求超时 (${status})`, err as Error, status);
      }
      
      if (status >= 400 && status < 500) {
        return createUploadError('VALIDATION_ERROR', err.message || `客户端错误 (${status})`, err as Error, status);
      }
    }
  }

  // 网络错误
  if (error instanceof Error) {
    if (error.message?.includes('network') || error.message?.includes(' Network')) {
      return createUploadError('NETWORK_ERROR', error.message, error);
    }

    // 超时错误
    if (error.message?.includes('timeout')) {
      return createUploadError('TIMEOUT_ERROR', error.message, error);
    }
  }

  // 默认为服务器错误
  const err = error instanceof Error ? error : new Error(String(error));
  return createUploadError('SERVER_ERROR', err.message || '未知错误', err);
}

// ============================================
// 分片上传类
// ============================================

/**
 * 分片上传管理器
 */
export class ChunkedUploadManager {
  private state: UploadState;
  private chunks: ChunkInfo[] = [];
  private file: File;
  private options: Required<Omit<ChunkedUploadRequest, 'file' | 'onProgress' | 'onSuccess' | 'onError' | 'signal'>>;
  private signal?: AbortSignal;
  private onProgress?: (progress: UploadProgress) => void;
  private activeUploads = 0;

  constructor(request: ChunkedUploadRequest) {
    const {
      file,
      onProgress,
      signal,
      chunkSize = DEFAULT_CHUNK_SIZE,
      concurrency = DEFAULT_CONCURRENCY,
      maxRetries = DEFAULT_MAX_RETRIES,
      timeout = DEFAULT_TIMEOUT,
    } = request;

    this.file = file;
    this.signal = signal;
    this.onProgress = onProgress;
    
    this.options = {
      chunkSize: Math.min(chunkSize, DEFAULT_CHUNK_SIZE),
      concurrency: Math.min(concurrency, MAX_CONCURRENCY),
      maxRetries,
      timeout,
    };

    // 初始化上传状态
    this.state = {
      uploadId: this.generateUploadId(),
      uploadedChunks: new Set(),
      uploadingChunks: new Set(),
      failedChunks: new Map(),
      totalBytes: file.size,
      uploadedBytes: 0,
      aborted: false,
    };

    // 分片
    this.chunks = chunkFile(file, this.options.chunkSize);
  }

  /**
   * 生成上传 ID
   */
  private generateUploadId(): string {
    return `upload-${Date.now()}-${Math.random().toString(36).substring(2, 9)}`;
  }

  /**
   * 计算上传进度
   */
  private updateProgress(chunkProgress?: ChunkProgress): void {
    if (!this.onProgress) return;

    const percentage = Math.round((this.state.uploadedBytes / this.state.totalBytes) * 100);
    
    this.onProgress({
      percentage,
      loaded: this.state.uploadedBytes,
      total: this.state.totalBytes,
      uploadedChunks: this.state.uploadedChunks.size,
      totalChunks: this.chunks.length,
      currentChunk: chunkProgress?.index,
      chunkProgress,
    });
  }

  /**
   * 上传单个分片
   */
  private async uploadChunk(chunk: ChunkInfo): Promise<void> {
    // 检查是否已取消
    if (this.state.aborted || this.signal?.aborted) {
      throw createUploadError('ABORT_ERROR', '上传已取消');
    }

    // 检查是否已达到最大重试次数
    const currentRetries = this.state.failedChunks.get(chunk.index) || 0;
    if (currentRetries >= this.options.maxRetries) {
      throw createUploadError(
        'SERVER_ERROR',
        `分片 ${chunk.index} 上传失败，已达到最大重试次数`,
        undefined,
        500
      );
    }

    this.state.uploadingChunks.add(chunk.index);
    this.activeUploads++;

    const formData = new FormData();
    formData.append('chunk', chunk.blob);
    formData.append('index', String(chunk.index));
    formData.append('uploadId', this.state.uploadId);
    formData.append('filename', this.file.name);
    formData.append('totalChunks', String(this.chunks.length));
    formData.append('start', String(chunk.start));
    formData.append('end', String(chunk.end));

    try {
      const response = await apiClient.post<{
        success: boolean;
        chunkId?: string;
        uploadedChunks?: number[];
      }>('/upload/chunk', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
        onUploadProgress: (progressEvent) => {
          if (progressEvent.total) {
            const loaded = chunk.start + progressEvent.loaded;
            this.state.uploadedBytes = loaded;
            this.updateProgress({
              index: chunk.index,
              progress: Math.round((progressEvent.loaded * 100) / progressEvent.total),
              loaded: progressEvent.loaded,
              total: chunk.size,
            });
          }
        },
        timeout: this.options.timeout,
        signal: this.signal,
      });

      if (response.data.success) {
        this.state.uploadedChunks.add(chunk.index);
        this.state.failedChunks.delete(chunk.index);
      }
    } catch (error) {
      const uploadError = classifyError(error);
      
      // 如果是网络错误或超时，可以重试
      if (uploadError.type === 'NETWORK_ERROR' || uploadError.type === 'TIMEOUT_ERROR') {
        this.state.failedChunks.set(chunk.index, currentRetries + 1);
        throw uploadError; // 抛出错误以触发重试
      }
      
      throw uploadError;
    } finally {
      this.state.uploadingChunks.delete(chunk.index);
      this.activeUploads--;
    }
  }

  /**
   * 调度分片上传
   */
  private async scheduleChunks(): Promise<void> {
    const uploadNext = async (): Promise<void> => {
      // 检查是否完成
      if (this.state.uploadedChunks.size >= this.chunks.length) {
        return;
      }

      // 检查是否已取消
      if (this.state.aborted || this.signal?.aborted) {
        return;
      }

      // 获取下一个待上传的分片
      let chunkIndex = -1;
      for (const chunk of this.chunks) {
        if (
          !this.state.uploadedChunks.has(chunk.index) &&
          !this.state.uploadingChunks.has(chunk.index) &&
          this.activeUploads < this.options.concurrency
        ) {
          chunkIndex = chunk.index;
          break;
        }
      }

      if (chunkIndex === -1) {
        // 没有可上传的分片，等待
        await new Promise((resolve) => setTimeout(resolve, 100));
        return uploadNext();
      }

      const chunk = this.chunks[chunkIndex];

      // 有重试记录时，从失败队列中取出
      if (this.state.failedChunks.has(chunkIndex)) {
        // 重试前等待一小段时间
        await new Promise((resolve) => setTimeout(resolve, 1000 * Math.min(this.state.failedChunks.get(chunkIndex) || 1, 3)));
      }

      try {
        await this.uploadChunk(chunk);
      } catch (error) {
        const uploadError = error as UploadError;
        
        // 检查是否可以重试
        const retryCount = this.state.failedChunks.get(chunkIndex) || 0;
        if (
          retryCount < this.options.maxRetries &&
          (uploadError.type === 'NETWORK_ERROR' || uploadError.type === 'TIMEOUT_ERROR' || uploadError.type === 'SERVER_ERROR')
        ) {
          // 重新加入队列
        } else {
          // 重试失败，停止上传
          this.state.aborted = true;
          throw uploadError;
        }
      }

      // 继续上传下一个
      return uploadNext();
    };

    // 启动并发上传
    const workers = Array.from({ length: this.options.concurrency }, () => uploadNext());
    await Promise.all(workers);
  }

  /**
   * 合并分片
   */
  private async mergeChunks(): Promise<UploadResponse> {
    try {
      const response = await apiClient.post<{
        success: boolean;
        url: string;
        filename: string;
        original_name?: string;
        file_id?: string;
        message?: string;
      }>('/upload/merge', {
        uploadId: this.state.uploadId,
        filename: this.file.name,
        totalChunks: this.chunks.length,
        chunks: Array.from(this.state.uploadedChunks).sort((a, b) => a - b),
      });

      return {
        url: response.data.url,
        filename: response.data.filename,
        originalName: response.data.original_name,
        fileId: response.data.file_id,
        message: response.data.message,
      };
    } catch (error) {
      throw classifyError(error);
    }
  }

  /**
   * 开始上传
   */
  public async upload(): Promise<UploadResponse> {
    try {
      // 初始化进度
      this.updateProgress();

      // 如果是小文件，直接使用普通上传
      if (this.chunks.length <= 1) {
        return this.simpleUpload();
      }

      // 分片上传
      await this.scheduleChunks();

      // 检查是否已取消
      if (this.state.aborted || this.signal?.aborted) {
        throw createUploadError('ABORT_ERROR', '上传已取消');
      }

      // 合并分片
      return await this.mergeChunks();
    } catch (error) {
      throw classifyError(error);
    }
  }

  /**
   * 简单上传（小文件）
   */
  private async simpleUpload(): Promise<UploadResponse> {
    const formData = new FormData();
    formData.append('file', this.file);

    try {
      const response = await apiClient.post<{
        url: string;
        filename: string;
        original_name?: string;
        message?: string;
        file_id?: string;
      }>('/upload/file', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
        onUploadProgress: (progressEvent) => {
          if (progressEvent.total) {
            this.state.uploadedBytes = progressEvent.loaded;
            this.updateProgress();
          }
        },
        signal: this.signal,
      });

      return {
        url: response.data.url,
        filename: response.data.filename,
        originalName: response.data.original_name,
        fileId: response.data.file_id,
        message: response.data.message,
      };
    } catch (error) {
      throw classifyError(error);
    }
  }

  /**
   * 取消上传
   */
  public cancel(): void {
    this.state.aborted = true;
  }

  /**
   * 获取上传状态
   */
  public getState(): UploadState {
    return { ...this.state };
  }
}

// ============================================
// 便捷上传函数
// ============================================

/**
 * 分片上传入口函数
 */
export async function chunkedUpload(request: ChunkedUploadRequest): Promise<UploadResponse> {
  const manager = new ChunkedUploadManager(request);
  return manager.upload();
}

/**
 * 上传文件（自动选择分片或简单上传）
 */
export async function uploadFile(
  file: File,
  options: {
    onProgress?: (progress: UploadProgress) => void;
    signal?: AbortSignal;
    chunkSize?: number;
    concurrency?: number;
    maxRetries?: number;
    timeout?: number;
  } = {}
): Promise<UploadResponse> {
  return chunkedUpload({
    file,
    ...options,
  });
}
