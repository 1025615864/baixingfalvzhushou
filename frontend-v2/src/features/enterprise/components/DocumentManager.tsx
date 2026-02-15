/**
 * DocumentManager - 文档管理组件
 */

import { useState } from 'react';

interface Document {
  id: string;
  name: string;
  type: string;
  size: number;
  createdAt: string;
  updatedAt: string;
  status: 'active' | 'archived' | 'pending';
}

interface DocumentManagerProps {
  documents?: Document[];
  isLoading?: boolean;
  onUpload?: (file: File) => void;
  onDelete?: (id: string) => void;
  onDownload?: (id: string) => void;
  className?: string;
}

const statusLabels: Record<Document['status'], string> = {
  active: '正常',
  archived: '已归档',
  pending: '待审核',
};

const statusColors: Record<Document['status'], string> = {
  active: 'bg-green-100 text-green-800',
  archived: 'bg-gray-100 text-gray-800',
  pending: 'bg-yellow-100 text-yellow-800',
};

/**
 * 格式化文件大小
 */
function formatFileSize(bytes: number): string {
  if (bytes === 0) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

/**
 * 获取文件图标
 */
function getFileIcon(type: string): JSX.Element {
  const iconClass = 'w-8 h-8 text-gray-400';
  
  if (type.includes('pdf')) {
    return (
      <svg className={iconClass} fill="currentColor" viewBox="0 0 24 24">
        <path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8l-6-6z" />
      </svg>
    );
  }
  if (type.includes('word') || type.includes('doc')) {
    return (
      <svg className={iconClass} fill="currentColor" viewBox="0 0 24 24">
        <path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8l-6-6z" />
      </svg>
    );
  }
  return (
    <svg className={iconClass} fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
    </svg>
  );
}

/**
 * 文档管理组件
 */
export function DocumentManager({
  documents = [],
  isLoading = false,
  onUpload,
  onDelete,
  onDownload,
  className = '',
}: DocumentManagerProps): JSX.Element {
  const [filter, setFilter] = useState<string>('all');

  const filteredDocs =
    filter === 'all' ? documents : documents.filter((d) => d.status === filter);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>): void => {
    const file = e.target.files?.[0];
    if (file && onUpload) {
      onUpload(file);
    }
  };

  if (isLoading) {
    return (
      <div className={`bg-white rounded-xl shadow-sm p-6 ${className}`}>
        <div className="animate-pulse space-y-4">
          <div className="h-4 bg-gray-200 rounded w-1/3" />
          <div className="space-y-2">
            {[1, 2, 3].map((i) => (
              <div key={i} className="h-16 bg-gray-200 rounded" />
            ))}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className={`bg-white rounded-xl shadow-sm p-6 ${className}`}>
      <div className="flex items-center justify-between mb-6">
        <div>
          <h3 className="text-lg font-semibold text-gray-900">文档管理</h3>
          <p className="text-sm text-gray-500">共 {documents.length} 个文档</p>
        </div>
        <div className="flex items-center gap-3">
          <select
            value={filter}
            onChange={(e) => setFilter(e.target.value)}
            className="px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="all">全部</option>
            <option value="active">正常</option>
            <option value="archived">已归档</option>
            <option value="pending">待审核</option>
          </select>
          <label className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 cursor-pointer transition-colors">
            上传文档
            <input type="file" className="hidden" onChange={handleFileChange} />
          </label>
        </div>
      </div>

      {filteredDocs.length > 0 ? (
        <div className="space-y-3">
          {filteredDocs.map((doc) => (
            <div
              key={doc.id}
              className="flex items-center justify-between p-4 border border-gray-200 rounded-lg hover:border-blue-300 transition-colors"
            >
              <div className="flex items-center gap-4">
                {getFileIcon(doc.type)}
                <div>
                  <h4 className="font-medium text-gray-900">{doc.name}</h4>
                  <div className="flex items-center gap-3 text-sm text-gray-500">
                    <span>{formatFileSize(doc.size)}</span>
                    <span>{new Date(doc.updatedAt).toLocaleDateString('zh-CN')}</span>
                  </div>
                </div>
              </div>
              <div className="flex items-center gap-3">
                <span
                  className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${statusColors[doc.status]}`}
                >
                  {statusLabels[doc.status]}
                </span>
                <button
                  onClick={() => onDownload?.(doc.id)}
                  className="p-2 text-gray-500 hover:text-blue-600 hover:bg-blue-50 rounded-lg transition-colors"
                  title="下载"
                >
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                  </svg>
                </button>
                <button
                  onClick={() => onDelete?.(doc.id)}
                  className="p-2 text-gray-500 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors"
                  title="删除"
                >
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                  </svg>
                </button>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="text-center py-12">
          <div className="w-16 h-16 mx-auto mb-4 bg-gray-100 rounded-full flex items-center justify-center">
            <svg className="w-8 h-8 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
          </div>
          <p className="text-gray-500">暂无文档</p>
          <label className="mt-4 inline-block px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 cursor-pointer transition-colors">
            上传第一个文档
            <input type="file" className="hidden" onChange={handleFileChange} />
          </label>
        </div>
      )}
    </div>
  );
}