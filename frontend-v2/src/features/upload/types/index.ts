/**
 * 文件上传类型定义
 */

/** 上传状态 */
export type UploadStatus = 'pending' | 'uploading' | 'success' | 'error' | 'cancelled';

/** 上传文件项 */
export interface UploadFile {
  /** 唯一ID */
  id: string;
  /** 原始文件 */
  file: File;
  /** 文件名 */
  name: string;
  /** 文件大小（字节） */
  size: number;
  /** 文件类型 */
  type: string;
  /** 上传进度（0-100） */
  progress: number;
  /** 上传状态 */
  status: UploadStatus;
  /** 错误信息 */
  error?: string;
  /** 上传后的URL */
  url?: string;
  /** 上传后的文件名 */
  filename?: string;
  /** 原始文件名 */
  originalName?: string;
  /** 预览URL（如果是图片） */
  previewUrl?: string;
}

/** 文件上传配置 */
export interface UploadConfig {
  /** 接受的文件类型 */
  accept?: string;
  /** 最大文件大小（字节） */
  maxSize?: number;
  /** 是否允许多选 */
  multiple?: boolean;
  /** 最大文件数量 */
  maxCount?: number;
  /** 是否禁用 */
  disabled?: boolean;
  /** 是否显示上传列表 */
  showUploadList?: boolean;
  /** 是否在选中后立即上传 */
  autoUpload?: boolean;
  /** 自定义上传请求 */
  customRequest?: (file: UploadFile, onProgress: (progress: number) => void) => Promise<UploadResponse>;
  /** 自定义类名 */
  className?: string;
}

/** 图片上传配置 */
export interface ImageUploadConfig extends UploadConfig {
  /** 是否允许裁剪 */
  allowCrop?: boolean;
  /** 裁剪比例 */
  cropAspectRatio?: number;
  /** 是否压缩 */
  compress?: boolean;
  /** 压缩质量（0-1） */
  compressQuality?: number;
  /** 最大宽度 */
  maxWidth?: number;
  /** 最大高度 */
  maxHeight?: number;
}

/** 拖拽上传配置 */
export interface DropzoneConfig extends UploadConfig {
  /** 是否支持点击上传 */
  clickable?: boolean;
  /** 自定义提示文本 */
  promptText?: string;
  /** 自定义提示图标 */
  promptIcon?: React.ReactNode;
}

/** 上传响应 */
export interface UploadResponse {
  /** 上传后的URL */
  url: string;
  /** 文件名 */
  filename: string;
  /** 原始文件名 */
  original_name?: string;
  /** 消息 */
  message?: string;
}

/** 文件上传请求 */
export interface FileUploadRequest {
  /** 文件 */
  file: File;
  /** 上传进度回调 */
  onProgress?: (progress: number) => void;
  /** 取消信号 */
  signal?: AbortSignal;
}

/** 图片上传请求 */
export interface ImageUploadRequest extends FileUploadRequest {
  /** 是否压缩 */
  compress?: boolean;
  /** 压缩质量 */
  quality?: number;
  /** 最大宽度 */
  maxWidth?: number;
  /** 最大高度 */
  maxHeight?: number;
}

/** 批量上传请求 */
export interface BatchUploadRequest {
  /** 文件列表 */
  files: File[];
  /** 上传进度回调（返回总进度和当前文件索引） */
  onProgress?: (totalProgress: number, currentIndex: number, fileProgress: number) => void;
  /** 单个文件上传完成回调 */
  onFileComplete?: (file: File, response: UploadResponse) => void;
  /** 单个文件上传失败回调 */
  onFileError?: (file: File, error: Error) => void;
  /** 取消信号 */
  signal?: AbortSignal;
}

/** 文件校验结果 */
export interface FileValidationResult {
  /** 是否有效 */
  valid: boolean;
  /** 错误信息 */
  error?: string;
}

/** 文件类型定义 */
export const ALLOWED_IMAGE_TYPES = [
  'image/jpeg',
  'image/png',
  'image/gif',
  'image/webp',
] as const;

export const ALLOWED_FILE_TYPES = [
  // 文档
  'application/pdf',
  'text/plain',
  'text/markdown',
  'text/csv',
  'application/json',
  // 压缩包
  'application/zip',
  'application/x-zip-compressed',
  'application/x-7z-compressed',
  'application/x-rar-compressed',
  'application/vnd.rar',
  'application/x-tar',
  'application/gzip',
  'application/x-gzip',
  // Office文档
  'application/msword',
  'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
  'application/vnd.ms-excel',
  'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
  'application/vnd.ms-powerpoint',
  'application/vnd.openxmlformats-officedocument.presentationml.presentation',
  // 图片
  'image/jpeg',
  'image/png',
  'image/gif',
  'image/webp',
  // 音频
  'audio/mpeg',
  'audio/wav',
  'audio/ogg',
  'audio/mp4',
  // 视频
  'video/mp4',
  'video/webm',
  'video/ogg',
] as const;

/** 文件大小限制 */
export const FILE_SIZE_LIMITS = {
  /** 图片最大2MB */
  IMAGE_MAX_SIZE: 2 * 1024 * 1024,
  /** 附件最大10MB */
  FILE_MAX_SIZE: 10 * 1024 * 1024,
} as const;

/** 生成唯一ID */
export function generateUploadId(): string {
  return `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
}

/** 格式化文件大小 */
export function formatFileSize(bytes: number): string {
  if (bytes === 0) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return `${parseFloat((bytes / k ** i).toFixed(2))} ${sizes[i]}`;
}

/** 获取文件扩展名 */
export function getFileExtension(filename: string): string {
  return filename.slice(((filename.lastIndexOf('.') - 1) >>> 0) + 2).toLowerCase();
}

/** 检查是否为图片 */
export function isImageFile(file: File): boolean {
  return ALLOWED_IMAGE_TYPES.includes(file.type as typeof ALLOWED_IMAGE_TYPES[number]);
}

/** 验证文件类型 */
export function validateFileType(file: File, allowedTypes?: string[]): FileValidationResult {
  if (allowedTypes && !allowedTypes.includes(file.type)) {
    return {
      valid: false,
      error: `不支持的文件类型: ${file.type}`,
    };
  }
  return { valid: true };
}

/** 验证文件大小 */
export function validateFileSize(file: File, maxSize?: number): FileValidationResult {
  if (maxSize && file.size > maxSize) {
    return {
      valid: false,
      error: `文件大小超过限制，最大允许 ${formatFileSize(maxSize)}`,
    };
  }
  return { valid: true };
}

/** 验证图片文件 */
export function validateImageFile(file: File, maxSize = FILE_SIZE_LIMITS.IMAGE_MAX_SIZE): FileValidationResult {
  if (!isImageFile(file)) {
    return {
      valid: false,
      error: '请上传 jpg/png/gif/webp 格式的图片',
    };
  }
  return validateFileSize(file, maxSize);
}

/** 验证普通文件 */
export function validateAttachmentFile(file: File, maxSize = FILE_SIZE_LIMITS.FILE_MAX_SIZE): FileValidationResult {
  const result = validateFileType(file, [...ALLOWED_FILE_TYPES]);
  if (!result.valid) {
    return result;
  }
  return validateFileSize(file, maxSize);
}