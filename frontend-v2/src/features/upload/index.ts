/**
 * 文件上传功能模块
 */

// 类型定义
export type {
  UploadFile,
  UploadStatus,
  UploadConfig,
  ImageUploadConfig,
  DropzoneConfig,
  UploadResponse,
  FileUploadRequest,
  ImageUploadRequest,
  BatchUploadRequest,
  FileValidationResult,
} from './types';

export {
  ALLOWED_IMAGE_TYPES,
  ALLOWED_FILE_TYPES,
  FILE_SIZE_LIMITS,
  generateUploadId,
  formatFileSize,
  getFileExtension,
  isImageFile,
  validateFileType,
  validateFileSize,
  validateImageFile,
  validateAttachmentFile,
} from './types';

// API
export {
  apiUploadFile,
  apiUploadImage,
  apiUploadAvatar,
  apiBatchUploadFiles,
  apiBatchUploadImages,
  compressImage,
  getImagePreviewUrl,
  revokeImagePreviewUrl,
  getFileDownloadUrl,
  getImageUrl,
  getAvatarUrl,
} from './api';

// Hooks
export {
  uploadQueryKeys,
  useUploadFile,
  useUploadImage,
  useUploadAvatar,
  useBatchUploadFiles,
  useBatchUploadImages,
  useUploadFileList,
  useImageUploader,
  useFileUploader,
} from './hooks/useUpload';

// 组件
export {
  FilePreview,
  FileListPreview,
  ImagePreviewModal,
} from './components/FilePreview';
export type {
  FilePreviewProps,
  FileListPreviewProps,
  ImagePreviewModalProps,
} from './components/FilePreview';

export {
  UploadProgress,
  CircularProgress,
  BatchUploadProgress,
} from './components/UploadProgress';
export type {
  UploadProgressProps,
  CircularProgressProps,
  BatchUploadProgressProps,
} from './components/UploadProgress';

export {
  UploadDropzone,
} from './components/UploadDropzone';
export type {
  UploadDropzoneProps,
} from './components/UploadDropzone';

export {
  UploadList,
  CompactUploadList,
} from './components/UploadList';
export type {
  UploadListProps,
  CompactUploadListProps,
} from './components/UploadList';

export {
  FileUploader,
} from './components/FileUploader';
export type {
  FileUploaderProps,
} from './components/FileUploader';

export {
  ImageUploader,
} from './components/ImageUploader';
export type {
  ImageUploaderProps,
} from './components/ImageUploader';