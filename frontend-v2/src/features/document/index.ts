/**
 * 文档管理功能模块
 * 提供文档的创建、查看、编辑、删除、导出等功能
 */

// 类型定义
export type {
  Document,
  DocumentItem,
  DocumentListResponse,
  DocumentDetail,
  DocumentType,
  DocumentFileType,
  DocumentStatus,
  DocumentFilters,
  UploadDocumentDTO,
  GeneratedDocument,
  ExportFormat,
  CreateDocumentDTO,
  UpdateDocumentDTO,
  ExportDocumentDTO,
  GenerateDocumentDTO,
  DocumentGenerateResponse,
  DocumentQueryParams,
  DocumentTypeInfo,
} from './types';

// 类型工具函数
export {
  DOCUMENT_TYPE_LABELS,
  EXPORT_FORMAT_CONFIG,
  getDocumentTypeLabel,
  getDocumentTypeClass,
} from './types';

// API 函数
export {
  apiGetMyDocuments,
  apiGetDocument,
  apiCreateDocument,
  apiUpdateDocument,
  apiDeleteDocument,
  apiExportDocumentPdf,
  apiExportMyDocument,
  apiGenerateDocument,
  apiGetDocumentTypes,
} from './api';

// Query Keys
export { documentKeys } from './api/queryKeys';

// React Query Hooks (文档生成)
export {
  useMyDocuments,
  useDocument,
  useCreateDocument,
  useUpdateDocument,
  useDeleteDocument,
  useExportDocumentPdf,
  useExportMyDocument,
  useGenerateDocument,
  useDocumentTypes,
  useDocumentManager,
} from './hooks/useDocument';

// React Query Hooks (文件上传管理)
export {
  useDocuments,
  useUploadDocument,
} from './hooks/useDocuments';

// 组件（文档生成 - 使用 DocumentItem 类型）
export { DocumentCard } from './components/DocumentCard';
export { DocumentList } from './components/DocumentList';
export { DocumentForm } from './components/DocumentForm';
export { DocumentViewer } from './components/DocumentViewer';
export { DocumentExport } from './components/DocumentExport';
export { DocumentUpload } from './components/DocumentUpload';
export { DocumentActions, DocumentBatchActions } from './components/DocumentActions';

// 组件（文件上传管理 - 使用 Document 类型）
export { DocumentCard as DocumentFileCard } from './components/DocumentCard/index';
export { DocumentList as DocumentFileList } from './components/DocumentList/index';

// 页面
export { DocumentsPage } from './pages/DocumentsPage';