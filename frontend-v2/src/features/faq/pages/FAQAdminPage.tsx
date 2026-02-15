/**
 * FAQAdminPage - FAQ管理页面（管理端）
 */

import React, { useState, useCallback } from 'react';

import { FAQForm } from '../components/FAQForm';
import { FAQSearch } from '../components/FAQSearch';
import { useFAQAdminManager } from '../hooks/useFAQ';
import type { FAQItem, CreateFAQRequest, UpdateFAQRequest } from '../types';

/**
 * FAQ管理页面
 */
export const FAQAdminPage: React.FC = () => {
  const [showForm, setShowForm] = useState(false);
  const [editingFAQ, setEditingFAQ] = useState<FAQItem | null>(null);
  const [deleteConfirmId, setDeleteConfirmId] = useState<number | null>(null);

  const {
    faqs,
    categories,
    selectedFAQ,
    isLoading,
    isDeleting,
    filter,
    total,
    setFilter,
    refetch,
    selectFAQ,
    deleteFAQ,
    createFAQ,
    updateFAQ,
  } = useFAQAdminManager();

  // 处理创建
  const handleCreate = useCallback(() => {
    setEditingFAQ(null);
    setShowForm(true);
  }, []);

  // 处理编辑
  const handleEdit = useCallback((faq: FAQItem) => {
    setEditingFAQ(faq);
    setShowForm(true);
  }, []);

  // 处理删除
  const handleDelete = useCallback(async (id: number) => {
    if (deleteConfirmId === id) {
      await deleteFAQ(id);
      setDeleteConfirmId(null);
    } else {
      setDeleteConfirmId(id);
      // 3秒后自动取消确认
      setTimeout(() => setDeleteConfirmId((prev) => prev === id ? null : prev), 3000);
    }
  }, [deleteConfirmId, deleteFAQ]);

  // 处理表单提交
  const handleSubmit = useCallback(async (data: CreateFAQRequest | UpdateFAQRequest) => {
    try {
      if (editingFAQ) {
        await updateFAQ(editingFAQ.id, data as UpdateFAQRequest);
      } else {
        await createFAQ(data as CreateFAQRequest);
      }
      setShowForm(false);
      setEditingFAQ(null);
    } catch {
      // 错误已在hook中处理
    }
  }, [editingFAQ, createFAQ, updateFAQ]);

  // 处理取消
  const handleCancel = useCallback(() => {
    setShowForm(false);
    setEditingFAQ(null);
  }, []);

  // 处理搜索
  const handleSearch = useCallback((keyword: string) => {
    setFilter({ keyword, page: 1 });
  }, [setFilter]);

  // 处理分类切换
  const handleCategoryChange = useCallback((category: string) => {
    setFilter({ category, page: 1 });
  }, [setFilter]);

  // 处理页码切换
  const handlePageChange = useCallback((page: number) => {
    setFilter({ page });
  }, [setFilter]);

  return (
    <div className="min-h-screen bg-gray-50">
      {/* 页面头部 */}
      <div className="bg-white border-b border-gray-200">
        <div className="mx-auto max-w-7xl px-4 py-6 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">FAQ管理</h1>
              <p className="mt-1 text-sm text-gray-600">管理常见问题知识库</p>
            </div>
            <button
              onClick={handleCreate}
              disabled={showForm}
              className="rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50"
            >
              + 新建FAQ
            </button>
          </div>
        </div>
      </div>

      <div className="mx-auto max-w-7xl px-4 py-6 sm:px-6 lg:px-8">
        {/* 搜索区域 */}
        <div className="mb-6 rounded-lg bg-white p-4 shadow-sm">
          <FAQSearch
            keyword={filter.keyword}
            category={filter.category}
            categories={categories}
            onSearch={handleSearch}
            onCategoryChange={handleCategoryChange}
            placeholder="搜索问题或答案..."
          />
        </div>

        <div className="grid gap-6 lg:grid-cols-5">
          {/* 左侧：列表 */}
          <div className={`lg:col-span-3 ${showForm ? 'hidden lg:block' : ''}`}>
            <div className="rounded-lg bg-white p-4 shadow-sm">
              <div className="mb-4 flex items-center justify-between">
                <h2 className="text-lg font-semibold text-gray-900">
                  FAQ列表 ({total})
                </h2>
                <button
                  onClick={() => refetch()}
                  className="text-sm text-blue-600 hover:text-blue-700"
                >
                  刷新
                </button>
              </div>

              {isLoading ? (
                <div className="space-y-3">
                  {Array.from({ length: 5 }).map((_, i) => (
                    <div key={i} className="h-16 animate-pulse rounded bg-gray-100" />
                  ))}
                </div>
              ) : (
                <>
                  <div className="space-y-2">
                    {faqs.map((faq) => (
                      <div
                        key={faq.id}
                        className={`rounded-lg border p-4 ${
                          selectedFAQ?.id === faq.id
                            ? 'border-blue-500 bg-blue-50'
                            : 'border-gray-200 hover:border-gray-300'
                        }`}
                      >
                        <div className="flex items-start justify-between gap-4">
                          <div
                            className="min-w-0 flex-1 cursor-pointer"
                            onClick={() => selectFAQ(faq.id)}
                          >
                            <h3 className="font-medium text-gray-900">{faq.question}</h3>
                            <div className="mt-1 flex items-center gap-2 text-sm text-gray-500">
                              {faq.category && (
                                <span className="rounded bg-gray-100 px-1.5 py-0.5 text-xs">
                                  {faq.category}
                                </span>
                              )}
                              <span>浏览: {faq.viewCount}</span>
                              {!faq.isActive && (
                                <span className="rounded bg-gray-200 px-1.5 py-0.5 text-xs text-gray-600">
                                  未激活
                                </span>
                              )}
                            </div>
                          </div>
                          <div className="flex items-center gap-2">
                            <button
                              onClick={() => handleEdit(faq)}
                              className="rounded px-2 py-1 text-sm text-blue-600 hover:bg-blue-50"
                            >
                              编辑
                            </button>
                            <button
                              onClick={() => void handleDelete(faq.id)}
                              disabled={isDeleting}
                              className={`rounded px-2 py-1 text-sm ${
                                deleteConfirmId === faq.id
                                  ? 'bg-red-100 text-red-700'
                                  : 'text-red-600 hover:bg-red-50'
                              }`}
                            >
                              {deleteConfirmId === faq.id ? '确认删除?' : '删除'}
                            </button>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>

                  {/* 分页 */}
                  {total > filter.pageSize && (
                    <div className="mt-4 flex items-center justify-center gap-2">
                      <button
                        onClick={() => handlePageChange(filter.page - 1)}
                        disabled={filter.page <= 1}
                        className="rounded-md border border-gray-300 bg-white px-3 py-1.5 text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-50"
                      >
                        上一页
                      </button>
                      <span className="text-sm text-gray-600">
                        第 {filter.page} 页 / 共 {Math.ceil(total / filter.pageSize)} 页
                      </span>
                      <button
                        onClick={() => handlePageChange(filter.page + 1)}
                        disabled={filter.page >= Math.ceil(total / filter.pageSize)}
                        className="rounded-md border border-gray-300 bg-white px-3 py-1.5 text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-50"
                      >
                        下一页
                      </button>
                    </div>
                  )}
                </>
              )}
            </div>
          </div>

          {/* 右侧：表单或详情 */}
          <div className={`${showForm ? 'lg:col-span-5' : 'lg:col-span-2'}`}>
            {showForm ? (
              <div className="rounded-lg bg-white p-6 shadow-sm">
                <h2 className="mb-4 text-lg font-semibold text-gray-900">
                  {editingFAQ ? '编辑FAQ' : '新建FAQ'}
                </h2>
                <FAQForm
                  initialData={editingFAQ || undefined}
                  categories={categories}
                  onSubmit={(data) => void handleSubmit(data)}
                  onCancel={handleCancel}
                  loading={false}
                />
              </div>
            ) : selectedFAQ ? (
              <div className="rounded-lg bg-white p-4 shadow-sm">
                <div className="mb-4 flex items-center justify-between">
                  <h2 className="text-lg font-semibold text-gray-900">FAQ详情</h2>
                  <div className="flex gap-2">
                    <button
                      onClick={() => handleEdit(selectedFAQ)}
                      className="rounded px-3 py-1 text-sm bg-blue-600 text-white hover:bg-blue-700"
                    >
                      编辑
                    </button>
                  </div>
                </div>
                <div className="space-y-4">
                  <div>
                    <span className="text-xs text-gray-500">问题</span>
                    <p className="font-medium text-gray-900">{selectedFAQ.question}</p>
                  </div>
                  <div>
                    <span className="text-xs text-gray-500">答案</span>
                    <p className="whitespace-pre-wrap text-gray-700">{selectedFAQ.answer}</p>
                  </div>
                  {selectedFAQ.category && (
                    <div>
                      <span className="text-xs text-gray-500">分类</span>
                      <p className="text-gray-700">{selectedFAQ.category}</p>
                    </div>
                  )}
                  {selectedFAQ.tags && selectedFAQ.tags.length > 0 && (
                    <div>
                      <span className="text-xs text-gray-500">标签</span>
                      <div className="mt-1 flex flex-wrap gap-1">
                        {selectedFAQ.tags.map((tag) => (
                          <span
                            key={tag}
                            className="rounded bg-gray-100 px-2 py-0.5 text-xs text-gray-600"
                          >
                            {tag}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}
                  <div className="grid grid-cols-2 gap-4 pt-4 border-t border-gray-100 text-sm">
                    <div>
                      <span className="text-xs text-gray-500">浏览次数</span>
                      <p className="text-gray-700">{selectedFAQ.viewCount}</p>
                    </div>
                    <div>
                      <span className="text-xs text-gray-500">优先级</span>
                      <p className="text-gray-700">{selectedFAQ.priority}</p>
                    </div>
                    <div>
                      <span className="text-xs text-gray-500">状态</span>
                      <p className={selectedFAQ.isActive ? 'text-green-600' : 'text-gray-500'}>
                        {selectedFAQ.isActive ? '激活' : '未激活'}
                      </p>
                    </div>
                    <div>
                      <span className="text-xs text-gray-500">ID</span>
                      <p className="text-gray-700">{selectedFAQ.id}</p>
                    </div>
                  </div>
                </div>
              </div>
            ) : (
              <div className="rounded-lg bg-gray-50 p-8 text-center text-gray-500">
                请选择一个FAQ查看详情或点击&quot;新建FAQ&quot;创建
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

FAQAdminPage.displayName = 'FAQAdminPage';