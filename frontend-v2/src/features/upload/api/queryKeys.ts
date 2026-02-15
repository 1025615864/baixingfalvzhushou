/**
 * Upload（文件上传）Query Keys
 * 用于 React Query 的缓存管理
 */

/**
 * 文件上传模块的基础 query key
 */
export const uploadKeys = {
  all: ['upload'] as const,

  /** 上传文件列表 */
  lists: () => [...uploadKeys.all, 'list'] as const,
  list: (filters: {
    status?: 'pending' | 'uploading' | 'success' | 'error';
    type?: 'image' | 'file' | 'avatar';
  } = {}) => [...uploadKeys.lists(), filters] as const,

  /** 单个上传文件 */
  details: () => [...uploadKeys.all, 'detail'] as const,
  detail: (fileId: string) => [...uploadKeys.details(), fileId] as const,

  /** 上传进度 */
  progress: (fileId: string) => [...uploadKeys.all, 'progress', fileId] as const,

  /** 图片处理 */
  imageProcessing: () => [...uploadKeys.all, 'image-processing'] as const,

  /** 批量上传 */
  batch: () => [...uploadKeys.all, 'batch'] as const,
} as const;

export default uploadKeys;