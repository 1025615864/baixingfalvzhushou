/**
 * 文档管理页面
 * 文档列表、创建、编辑、查看、导出等功能
 */

import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';

import type {
  DocumentItem,
  CreateDocumentDTO,
  UpdateDocumentDTO,
  ExportDocumentDTO
} from '../types';
import {
  useMyDocuments,
  useDocument,
  useCreateDocument,
  useUpdateDocument,
  useDeleteDocument,
  useExportDocumentPdf,
  useExportMyDocument,
  useDocumentTypes,
} from '../hooks/useDocument';
import { DocumentList } from '../components/DocumentList';
import { DocumentForm } from '../components/DocumentForm';
import { DocumentViewer } from '../components/DocumentViewer';
import { DocumentExport } from '../components/DocumentExport';

/**
 * 文档管理页面
 */
export function DocumentsPage(): React.ReactElement {
  const navigate = useNavigate();

  // 页面状态
  const [currentPage, setCurrentPage] = useState(1);
  const [selectedDocId, setSelectedDocId] = useState<number | null>(null);
  const [viewMode, setViewMode] = useState<'list' | 'create' | 'edit' | 'view' | 'export'>('list');
  const [searchKeyword, setSearchKeyword] = useState('');

  // 数据获取
  const { 
    data: documentsData, 
    isLoading: isDocumentsLoading,
    refetch: refetchDocuments 
  } = useMyDocuments({ page: currentPage, pageSize: 10 });

  const { 
    data: documentDetail, 
    isLoading: isDetailLoading 
  } = useDocument(selectedDocId || 0);

  const {
    data: documentTypes,
  } = useDocumentTypes();

  // Mutations
  const createMutation = useCreateDocument();
  const updateMutation = useUpdateDocument();
  const deleteMutation = useDeleteDocument();
  const exportPdfMutation = useExportDocumentPdf();
  const exportMyMutation = useExportMyDocument();

  // 处理创建文档
  const handleCreate = () => {
    setViewMode('create');
    setSelectedDocId(null);
  };

  // 处理查看文档
  const handleView = (doc: DocumentItem) => {
    setSelectedDocId(doc.id);
    setViewMode('view');
  };

  // 处理编辑文档
  const handleEdit = (doc: DocumentItem) => {
    setSelectedDocId(doc.id);
    setViewMode('edit');
  };

  // 处理删除文档
  const handleDelete = async (doc: DocumentItem) => {
    if (!window.confirm(`确定要删除文档"${doc.title}"吗？`)) {
      return;
    }

    try {
      await deleteMutation.mutateAsync(doc.id);
      // 如果删除的是当前查看的文档，返回列表
      if (selectedDocId === doc.id) {
        setViewMode('list');
        setSelectedDocId(null);
      }
    } catch (error) {
      console.error('删除文档失败:', error);
      alert('删除失败，请重试');
    }
  };

  // 处理导出文档
  const handleExport = (doc: DocumentItem) => {
    setSelectedDocId(doc.id);
    setViewMode('export');
  };

  // 处理导出提交
  const handleExportSubmit = async (data: ExportDocumentDTO) => {
    try {
      if (selectedDocId) {
        await exportMyMutation.mutateAsync({ 
          docId: selectedDocId, 
          filename: data.title 
        });
      } else {
        await exportPdfMutation.mutateAsync(data);
      }
      setViewMode('list');
      setSelectedDocId(null);
    } catch (error) {
      console.error('导出失败:', error);
      alert('导出失败，请重试');
    }
  };

  // 处理创建提交
  const handleCreateSubmit = async (data: CreateDocumentDTO) => {
    try {
      await createMutation.mutateAsync(data);
      setViewMode('list');
      setSearchKeyword('');
      void refetchDocuments();
    } catch (error) {
      console.error('创建文档失败:', error);
      alert('创建失败，请重试');
    }
  };

  // 处理更新提交
  const handleUpdateSubmit = async (data: UpdateDocumentDTO) => {
    if (!selectedDocId) return;

    try {
      await updateMutation.mutateAsync({ docId: selectedDocId, data });
      setViewMode('list');
      setSelectedDocId(null);
      void refetchDocuments();
    } catch (error) {
      console.error('更新文档失败:', error);
      alert('更新失败，请重试');
    }
  };

  // 返回列表
  const handleBackToList = () => {
    setViewMode('list');
    setSelectedDocId(null);
  };

  // 渲染头部
  const renderHeader = () => (
    <div className="flex items-center justify-between mb-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">我的文档</h1>
        <p className="text-gray-500 mt-1">管理和导出您的法律文书</p>
      </div>
      <div className="flex items-center gap-3">
        {viewMode === 'list' ? (
          <button
            onClick={handleCreate}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors flex items-center gap-2"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
            </svg>
            新建文档
          </button>
        ) : (
          <button
            onClick={handleBackToList}
            className="px-4 py-2 text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200 transition-colors flex items-center gap-2"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
            </svg>
            返回列表
          </button>
        )}
      </div>
    </div>
  );

  // 渲染内容
  const renderContent = () => {
    switch (viewMode) {
      case 'create':
        return (
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-6">创建新文档</h2>
            <DocumentForm
              mode="create"
              onSubmit={(data) => {
                void handleCreateSubmit(data as CreateDocumentDTO);
              }}
              onCancel={handleBackToList}
              isSubmitting={createMutation.isPending}
            />
          </div>
        );

      case 'edit':
        return (
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-6">编辑文档</h2>
            <DocumentForm
              mode="edit"
              initialData={documentDetail || undefined}
              onSubmit={(data) => {
                void handleUpdateSubmit(data as UpdateDocumentDTO);
              }}
              onCancel={handleBackToList}
              isSubmitting={updateMutation.isPending}
            />
          </div>
        );

      case 'view':
        return (
          <DocumentViewer
            document={documentDetail || null}
            isLoading={isDetailLoading}
            onClose={handleBackToList}
            onEdit={() => setViewMode('edit')}
            onExport={() => setViewMode('export')}
            onDelete={() => {
              if (documentDetail) {
                void handleDelete(documentDetail as unknown as DocumentItem);
              }
            }}
          />
        );

      case 'export': {
        const exportDoc = documentDetail || { title: '', content: '' };
        return (
          <div className="max-w-2xl mx-auto">
            <DocumentExport
              title={exportDoc.title}
              content={exportDoc.content}
              onExport={(data) => {
                void handleExportSubmit(data);
              }}
              onCancel={handleBackToList}
              isExporting={exportPdfMutation.isPending || exportMyMutation.isPending}
            />
          </div>
        );
      }

      case 'list':
      default:
        return (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* 左侧：文档列表 */}
            <div className="lg:col-span-2">
              <DocumentList
                documents={documentsData?.items || []}
                isLoading={isDocumentsLoading}
                currentPage={currentPage}
                pageSize={10}
                total={documentsData?.total || 0}
                onDocumentClick={handleView}
                onDocumentEdit={handleEdit}
                onDocumentDelete={(doc) => {
                  void handleDelete(doc);
                }}
                onDocumentExport={handleExport}
                onPageChange={setCurrentPage}
                onSearch={setSearchKeyword}
                searchKeyword={searchKeyword}
                emptyText="暂无文档，点击右上角创建"
              />
            </div>

            {/* 右侧：快捷操作和统计 */}
            <div className="space-y-6">
              {/* 快速统计 */}
              <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
                <h3 className="text-sm font-semibold text-gray-900 mb-4">文档统计</h3>
                <div className="grid grid-cols-2 gap-4">
                  <div className="text-center p-4 bg-blue-50 rounded-lg">
                    <div className="text-2xl font-bold text-blue-600">
                      {documentsData?.total || 0}
                    </div>
                    <div className="text-xs text-gray-600 mt-1">总文档数</div>
                  </div>
                  <div className="text-center p-4 bg-green-50 rounded-lg">
                    <div className="text-2xl font-bold text-green-600">
                      {documentTypes?.length || 0}
                    </div>
                    <div className="text-xs text-gray-600 mt-1">可用模板</div>
                  </div>
                </div>
              </div>

              {/* 快捷操作 */}
              <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
                <h3 className="text-sm font-semibold text-gray-900 mb-4">快捷操作</h3>
                <div className="space-y-2">
                  <button
                    onClick={handleCreate}
                    className="w-full px-4 py-3 text-left text-gray-700 hover:bg-gray-50 rounded-lg transition-colors flex items-center gap-3"
                  >
                    <div className="w-8 h-8 bg-blue-100 rounded-lg flex items-center justify-center">
                      <svg className="w-4 h-4 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                      </svg>
                    </div>
                    <div>
                      <div className="font-medium">创建空白文档</div>
                      <div className="text-xs text-gray-500">从零开始编写</div>
                    </div>
                  </button>
                  
                  <button
                    onClick={() => navigate('/ai/document-generate')}
                    className="w-full px-4 py-3 text-left text-gray-700 hover:bg-gray-50 rounded-lg transition-colors flex items-center gap-3"
                  >
                    <div className="w-8 h-8 bg-purple-100 rounded-lg flex items-center justify-center">
                      <svg className="w-4 h-4 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                      </svg>
                    </div>
                    <div>
                      <div className="font-medium">AI生成文书</div>
                      <div className="text-xs text-gray-500">智能生成法律文书</div>
                    </div>
                  </button>
                </div>
              </div>

              {/* 提示信息 */}
              <div className="bg-yellow-50 border border-yellow-200 rounded-xl p-4">
                <div className="flex items-start gap-2">
                  <svg className="w-5 h-5 text-yellow-600 flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  <div className="text-sm text-yellow-800">
                    <p className="font-medium mb-1">提示</p>
                    <p className="text-xs">您可以导出文档为PDF格式用于打印，或导出为Word格式进行编辑。</p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        );
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {renderHeader()}
        {renderContent()}
      </div>
    </div>
  );
}