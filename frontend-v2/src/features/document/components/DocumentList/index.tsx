import type { DocumentItem } from '../../types';

interface DocumentListProps {
  documents?: DocumentItem[];
  isLoading?: boolean;
  currentPage?: number;
  pageSize?: number;
  total?: number;
  onDocumentClick?: (doc: DocumentItem) => void;
  onDocumentEdit?: (doc: DocumentItem) => void;
  onDocumentDelete?: (doc: DocumentItem) => void;
  onDocumentExport?: (doc: DocumentItem) => void;
  onPageChange?: (page: number) => void;
  onSearch?: (keyword: string) => void;
  searchKeyword?: string;
  emptyText?: string;
}

export function DocumentList({
  documents = [],
  isLoading,
  currentPage: _currentPage,
  pageSize: _pageSize,
  total: _total,
  onDocumentClick,
  onDocumentEdit,
  onDocumentDelete,
  onDocumentExport,
  onPageChange: _onPageChange,
  onSearch: _onSearch,
  searchKeyword: _searchKeyword,
  emptyText = '暂无文档',
}: DocumentListProps): JSX.Element {
  if (isLoading) {
    return (
      <div className="space-y-3">
        {Array.from({ length: 3 }, (_, index) => (
          <div
            key={index}
            className="bg-white rounded-lg shadow-sm border border-gray-200 p-4 animate-pulse"
          >
            <div className="flex items-start gap-4">
              <div className="w-12 h-12 bg-gray-200 rounded-lg flex-shrink-0" />
              <div className="flex-1 space-y-2">
                <div className="h-5 bg-gray-200 rounded w-1/3" />
                <div className="h-4 bg-gray-200 rounded w-full" />
                <div className="h-4 bg-gray-200 rounded w-1/2" />
              </div>
            </div>
          </div>
        ))}
      </div>
    );
  }

  if (!documents?.length) {
    return (
      <div className="text-center py-8 bg-white rounded-lg border border-gray-200">
        <p className="text-gray-500 mb-2">{emptyText}</p>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {documents.map((document: DocumentItem) => (
        <div
          key={document.id}
          className="bg-white rounded-lg shadow-sm border border-gray-200 p-4 hover:shadow-md transition-shadow cursor-pointer"
          onClick={(): void => onDocumentClick?.(document)}
        >
          <div className="flex items-start gap-4">
            <div className="w-12 h-12 bg-blue-100 rounded-lg flex-shrink-0 flex items-center justify-center">
              <span className="text-blue-600 font-semibold text-sm">
                {document.title?.charAt(0) || 'D'}
              </span>
            </div>
            <div className="flex-1 min-w-0">
              <h4 className="font-medium text-gray-900 truncate">{document.title}</h4>
              <p className="text-sm text-gray-500 mt-1">
                {document.documentType || '未分类'} • {document.createdAt || '未知日期'}
              </p>
              <div className="flex gap-2 mt-2">
                {onDocumentEdit && (
                  <button
                    onClick={(e): void => {
                      e.stopPropagation();
                      onDocumentEdit(document);
                    }}
                    className="text-sm text-blue-600 hover:text-blue-800"
                  >
                    编辑
                  </button>
                )}
                {onDocumentDelete && (
                  <button
                    onClick={(e): void => {
                      e.stopPropagation();
                      onDocumentDelete(document);
                    }}
                    className="text-sm text-red-600 hover:text-red-800"
                  >
                    删除
                  </button>
                )}
                {onDocumentExport && (
                  <button
                    onClick={(e): void => {
                      e.stopPropagation();
                      onDocumentExport(document);
                    }}
                    className="text-sm text-green-600 hover:text-green-800"
                  >
                    导出
                  </button>
                )}
              </div>
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}