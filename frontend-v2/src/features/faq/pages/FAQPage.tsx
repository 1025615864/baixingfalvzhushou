/**
 * FAQPage - FAQ中心页面（用户端）
 */

import React, { useState, useCallback } from 'react';

import { FAQList } from '../components/FAQList';
import { FAQDetail } from '../components/FAQDetail';
import { FAQSearch } from '../components/FAQSearch';
import { useFAQManager } from '../hooks/useFAQ';

/**
 * FAQ中心页面
 */
export const FAQPage: React.FC = () => {
  const [showDetail, setShowDetail] = useState(false);
  
  const {
    faqs,
    categories,
    selectedFAQ,
    isLoading,
    filter,
    total,
    setFilter,
    selectFAQ,
  } = useFAQManager();

  // 处理搜索
  const handleSearch = useCallback((keyword: string) => {
    setFilter({ keyword, page: 1 });
    setShowDetail(false);
  }, [setFilter]);

  // 处理分类切换
  const handleCategoryChange = useCallback((category: string) => {
    setFilter({ category, page: 1 });
    setShowDetail(false);
  }, [setFilter]);

  // 处理选择FAQ
  const handleSelectFAQ = useCallback((faq: typeof selectedFAQ) => {
    if (faq) {
      selectFAQ(faq.id);
      setShowDetail(true);
    }
  }, [selectFAQ]);

  // 处理返回列表
  const handleBackToList = useCallback(() => {
    setShowDetail(false);
    selectFAQ(null);
  }, [selectFAQ]);

  // 处理页码切换
  const handlePageChange = useCallback((page: number) => {
    setFilter({ page });
  }, [setFilter]);

  return (
    <div className="min-h-screen bg-gray-50">
      {/* 页面头部 */}
      <div className="bg-white border-b border-gray-200">
        <div className="mx-auto max-w-5xl px-4 py-8 sm:px-6 lg:px-8">
          <h1 className="text-3xl font-bold text-gray-900">帮助中心</h1>
          <p className="mt-2 text-gray-600">查找常见问题的解答</p>
        </div>
      </div>

      <div className="mx-auto max-w-5xl px-4 py-8 sm:px-6 lg:px-8">
        {/* 搜索区域 */}
        <div className="mb-8 rounded-xl bg-white p-6 shadow-sm">
          <FAQSearch
            keyword={filter.keyword}
            category={filter.category}
            categories={categories}
            onSearch={handleSearch}
            onCategoryChange={handleCategoryChange}
            placeholder="搜索问题，例如：如何修改密码？"
          />
        </div>

        {/* 内容区域 */}
        <div className="grid gap-8 lg:grid-cols-3">
          {/* 左侧：FAQ列表 */}
          <div className={`lg:col-span-2 ${showDetail ? 'hidden lg:block' : ''}`}>
            <div className="rounded-xl bg-white p-6 shadow-sm">
              <h2 className="mb-4 text-lg font-semibold text-gray-900">
                {filter.keyword ? `搜索结果 (${total})` : '常见问题'}
              </h2>
              
              <FAQList
                items={faqs}
                loading={isLoading}
                onItemClick={handleSelectFAQ}
                emptyText={filter.keyword ? '没有找到相关FAQ' : '暂无FAQ'}
              />

              {/* 分页 */}
              {!isLoading && total > filter.pageSize && (
                <div className="mt-6 flex items-center justify-center gap-2">
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
            </div>
          </div>

          {/* 右侧：详情或热门 */}
          <div className={`${showDetail ? 'lg:col-span-3' : 'hidden lg:block lg:col-span-1'}`}>
            {showDetail && selectedFAQ ? (
              <div className="rounded-xl bg-white p-6 shadow-sm">
                <FAQDetail
                  item={selectedFAQ}
                  onBack={handleBackToList}
                />
              </div>
            ) : (
              <div className="rounded-xl bg-white p-6 shadow-sm">
                <h3 className="mb-4 text-lg font-semibold text-gray-900">暂无热门问题</h3>
              </div>
            )}
          </div>
        </div>

        {/* 移动端详情视图 */}
        {showDetail && selectedFAQ && (
          <div className="fixed inset-0 z-50 bg-white lg:hidden">
            <div className="h-full overflow-auto p-4">
              <FAQDetail
                item={selectedFAQ}
                onBack={handleBackToList}
              />
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

FAQPage.displayName = 'FAQPage';