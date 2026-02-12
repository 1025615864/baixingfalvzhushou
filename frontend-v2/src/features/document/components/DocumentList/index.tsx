import { useDocuments } from '../../hooks/useDocuments';
import { DocumentCard } from '../DocumentCard/index';
import type { DocumentItem } from '../../types';

interface DocumentListProps {
  onSelect?: (doc: DocumentItem) => void;
  onDownload?: (doc: DocumentItem) => void;
}

export function DocumentList({ onSelect, onDownload }: DocumentListProps): JSX.Element {
  const { data: documents, isLoading, isError } = useDocuments();

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

  if (isError) {
    return (
      <div className="text-center py-8">
        <p className="text-red-600">加载文档列表失败，请稍后重试</p>
      </div>
    );
  }

  if (!documents?.items?.length) {
    return (
      <div className="text-center py-8 bg-white rounded-lg border border-gray-200">
        <p className="text-gray-500 mb-2">暂无文档</p>
        <p className="text-sm text-gray-400">
          点击&ldquo;上传文档&rdquo;添加您的第一个文档
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {documents.items.map((document: DocumentItem) => (
        <DocumentCard
          key={document.id}
          document={document}
          onClick={(doc): void => {
            // DocumentList只处理DocumentItem类型，类型守卫确保安全
            if ('documentType' in doc) {
              onSelect?.(doc);
            }
          }}
          onDownload={(doc): void => {
            if ('documentType' in doc) {
              onDownload?.(doc);
            }
          }}
        />
      ))}
    </div>
  );
}