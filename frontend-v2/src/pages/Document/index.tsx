import { useState } from 'react';

import { DocumentFileCard, useDocuments } from '@/features/document';
import type { DocumentFileType, DocumentStatus, DocumentItem } from '@/features/document';

const types: { value: DocumentFileType | ''; label: string }[] = [
  { value: '', label: '全部类型' },
  { value: 'contract', label: '合同' },
  { value: 'agreement', label: '协议' },
  { value: 'certificate', label: '证件' },
  { value: 'evidence', label: '证据材料' },
  { value: 'other', label: '其他' },
];

const statuses: { value: DocumentStatus | ''; label: string }[] = [
  { value: '', label: '全部状态' },
  { value: 'draft', label: '草稿' },
  { value: 'pending', label: '审核中' },
  { value: 'approved', label: '已通过' },
  { value: 'rejected', label: '已驳回' },
];

export function DocumentPage(): JSX.Element {
  const [selectedType, setSelectedType] = useState<DocumentFileType | ''>('');
  const [selectedStatus, setSelectedStatus] = useState<DocumentStatus | ''>('');
  const [searchQuery, setSearchQuery] = useState('');
  const [, setIsUploadModalOpen] = useState(false);

  const { data: documents, isLoading } = useDocuments({
    type: selectedType || undefined,
    status: selectedStatus || undefined,
    searchQuery: searchQuery || undefined,
  });

  return (
    <div className="container mx-auto px-4 py-6 max-w-5xl">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">文档管理</h1>
          <p className="text-gray-600 mt-1">管理您的法律文档和证据材料</p>
        </div>
        <button
          onClick={(): void => setIsUploadModalOpen(true)}
          className="bg-primary-600 text-white px-4 py-2 rounded-lg hover:bg-primary-700 transition-colors flex items-center gap-2"
          type="button"
        >
          <span>+</span>
          上传文档
        </button>
      </div>

      {/* Filters */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4 mb-6">
        <div className="flex flex-col gap-4">
          {/* Search */}
          <input
            type="text"
            placeholder="搜索文档..."
            value={searchQuery}
            onChange={(e): void => setSearchQuery(e.target.value)}
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
          />
          
          {/* Filter Buttons */}
          <div className="flex flex-wrap gap-4">
            {/* Type Filter */}
            <div className="flex gap-2 flex-wrap">
              {types.map((t) => (
                <button
                  key={t.value}
                  onClick={(): void => setSelectedType(t.value)}
                  className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-colors ${
                    selectedType === t.value
                      ? 'bg-primary-600 text-white'
                      : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                  }`}
                  type="button"
                >
                  {t.label}
                </button>
              ))}
            </div>
            
            {/* Status Filter */}
            <div className="flex gap-2 flex-wrap">
              {statuses.map((s) => (
                <button
                  key={s.value}
                  onClick={(): void => setSelectedStatus(s.value)}
                  className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-colors ${
                    selectedStatus === s.value
                      ? 'bg-green-600 text-white'
                      : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                  }`}
                  type="button"
                >
                  {s.label}
                </button>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Stats */}
      <div className="flex items-center justify-between mb-4 text-sm text-gray-500">
        <span>
          {isLoading ? '加载中...' : `共 ${documents?.items?.length || 0} 个文档`}
        </span>
      </div>

      {/* Document List */}
      {isLoading ? (
        <div className="text-center py-8">加载中...</div>
      ) : documents?.items && documents.items.length > 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {documents.items.map((doc: DocumentItem) => (
            <DocumentFileCard
              key={doc.id}
              document={doc}
              onClick={(item): void => {
                // 类型守卫：只处理DocumentItem类型
                if ('documentType' in item) {
                  void (item as DocumentItem);
                }
              }}
            />
          ))}
        </div>
      ) : (
        <div className="text-center py-12 bg-gray-50 rounded-lg">
          <p className="text-gray-500">暂无文档</p>
          <p className="text-gray-400 text-sm mt-1">点击上方&ldquo;上传文档&rdquo;按钮添加</p>
        </div>
      )}
    </div>
  );
}