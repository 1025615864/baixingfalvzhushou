import { typeNames, statusConfig } from '../../hooks/useDocuments';
import type { Document, DocumentItem, DocumentFileType, DocumentStatus } from '../../types';

interface DocumentCardProps {
  document: Document | DocumentItem;
  onClick?: (doc: Document | DocumentItem) => void;
  onDownload?: (doc: Document | DocumentItem) => void;
}

function formatFileSize(bytes: number): string {
  if (bytes === 0) return '0 Bytes';
  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

function getFileIcon(fileType: string): string {
  if (fileType?.includes('pdf')) return '📄';
  if (fileType?.includes('word') || fileType?.includes('document')) return '📝';
  if (fileType?.includes('excel') || fileType?.includes('sheet')) return '📊';
  if (fileType?.includes('image')) return '🖼️';
  return '📁';
}

export function DocumentCard({ document, onClick, onDownload }: DocumentCardProps): JSX.Element {
  // 类型守卫：检查是否为完整Document类型
  const isFullDocument = (doc: Document | DocumentItem): doc is Document => {
    return 'fileName' in doc && 'fileUrl' in doc;
  };

  const docStatus: DocumentStatus = isFullDocument(document) ? document.status : 'draft';
  const docType: DocumentFileType = isFullDocument(document) ? document.type : (document.type ?? 'other');
  const status = statusConfig[docStatus];
  const typeLabel = isFullDocument(document)
    ? typeNames[docType] ?? docType
    : document.documentType;

  const handleClick = (): void => {
    onClick?.(document);
  };

  const handleDownload = (e: React.MouseEvent): void => {
    e.stopPropagation();
    onDownload?.(document);
  };

  return (
    <article
      className="bg-white rounded-lg shadow-sm border border-gray-200 p-4 cursor-pointer hover:shadow-md transition-shadow"
      onClick={handleClick}
      role="button"
      tabIndex={0}
      onKeyDown={(e): void => {
        if (e.key === 'Enter' || e.key === ' ') {
          handleClick();
        }
      }}
    >
      <div className="flex items-start gap-4">
        {/* File Icon */}
        <div className="flex-shrink-0 w-12 h-12 bg-gray-100 rounded-lg flex items-center justify-center text-2xl">
          {getFileIcon(isFullDocument(document) ? document.fileType : (document.fileType ?? 'folder'))}
        </div>

        {/* Content */}
        <div className="flex-1 min-w-0">
          <div className="flex items-start justify-between gap-2 mb-1">
            <h3 className="font-semibold text-gray-900 line-clamp-1" title={document.title}>
              {document.title}
            </h3>
            <span className={`flex-shrink-0 px-2 py-0.5 text-xs font-medium rounded ${status.color}`}>
              {status.label}
            </span>
          </div>

          <p className="text-sm text-gray-500 line-clamp-1 mb-2">
            {isFullDocument(document) ? (document.description || document.fileName) : (document.description || document.title)}
          </p>

          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3 text-xs text-gray-400">
              <span className="px-2 py-0.5 bg-gray-100 rounded">{typeLabel}</span>
              {isFullDocument(document) && (
                <span>{formatFileSize(document.fileSize)}</span>
              )}
              <time dateTime={document.createdAt}>
                {new Date(document.createdAt).toLocaleDateString('zh-CN')}
              </time>
            </div>

            {isFullDocument(document) && (
              <button
                onClick={handleDownload}
                className="text-primary-600 hover:text-primary-700 text-sm font-medium"
                type="button"
              >
                下载
              </button>
            )}
          </div>

          {document.tags && document.tags.length > 0 && (
            <div className="flex flex-wrap gap-1 mt-2">
              {document.tags.map((tag: string) => (
                <span
                  key={tag}
                  className="px-1.5 py-0.5 bg-blue-50 text-blue-600 text-xs rounded"
                >
                  #{tag}
                </span>
              ))}
            </div>
          )}
        </div>
      </div>
    </article>
  );
}