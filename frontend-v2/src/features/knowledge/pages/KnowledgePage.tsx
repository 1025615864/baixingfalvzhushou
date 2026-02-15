/**
 * 知识库页面
 * 展示法律知识列表，支持搜索、分类筛选和详情查看
 */

import { useState, useCallback } from 'react';

import { useKnowledge, useKnowledgeStats } from '../hooks/useKnowledge';
import { KnowledgeList } from '../components/KnowledgeList';
import { KnowledgeSearch } from '../components/KnowledgeSearch';
import { CategoryFilter } from '../components/CategoryFilter';
import { KnowledgeDetail } from '../components/KnowledgeDetail';

/**
 * 统计卡片组件
 */
function StatCard({
  title,
  value,
  color = 'blue',
}: {
  title: string;
  value: number;
  color?: 'blue' | 'green' | 'purple' | 'orange';
}): JSX.Element {
  const colorClasses = {
    blue: 'bg-blue-50 text-blue-700',
    green: 'bg-green-50 text-green-700',
    purple: 'bg-purple-50 text-purple-700',
    orange: 'bg-orange-50 text-orange-700',
  };

  return (
    <div className={`${colorClasses[color]} rounded-lg p-4`}>
      <p className="text-sm font-medium opacity-80">{title}</p>
      <p className="text-2xl font-bold mt-1">{value.toLocaleString()}</p>
    </div>
  );
}

/**
 * 知识库页面
 */
export function KnowledgePage(): JSX.Element {
  // 状态管理
  const [searchKeyword, setSearchKeyword] = useState('');
  const [selectedCategory, setSelectedCategory] = useState<string | null>(null);
  const [selectedArticleId, setSelectedArticleId] = useState<string | null>(null);
  const [currentPage, setCurrentPage] = useState(1);

  const pageSize = 10;

  // 获取知识列表
  const {
    data: knowledgeData,
    isLoading: isLoadingList,
    isError: isListError,
  } = useKnowledge({
    page: currentPage,
    pageSize,
    category: selectedCategory || undefined,
    keyword: searchKeyword || undefined,
  });

  // 获取统计信息
  const { data: stats, isLoading: isLoadingStats } = useKnowledgeStats();

  // 处理搜索
  const handleSearch = useCallback((keyword: string) => {
    setSearchKeyword(keyword);
    setCurrentPage(1); // 重置到第一页
  }, []);

  // 处理清空搜索
  const handleClearSearch = useCallback(() => {
    setSearchKeyword('');
    setCurrentPage(1);
  }, []);

  // 处理分类选择
  const handleSelectCategory = useCallback((category: string | null) => {
    setSelectedCategory(category);
    setCurrentPage(1);
  }, []);

  // 处理选择文章
  const handleSelectArticle = useCallback((id: string) => {
    setSelectedArticleId(id);
  }, []);

  // 处理关闭详情
  const handleCloseDetail = useCallback(() => {
    setSelectedArticleId(null);
  }, []);

  // 处理分页
  const handlePageChange = useCallback((page: number) => {
    setCurrentPage(page);
  }, []);

  // 如果正在查看详情，显示详情页
  if (selectedArticleId) {
    return (
      <div className="min-h-screen bg-gray-50">
        <div className="max-w-4xl mx-auto px-4 py-6">
          <KnowledgeDetail
            articleId={selectedArticleId}
            onClose={handleCloseDetail}
          />
        </div>
      </div>
    );
  }

  const totalPages = knowledgeData
    ? Math.ceil(knowledgeData.total / pageSize)
    : 0;

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-6xl mx-auto px-4 py-6">
        {/* 页面标题 */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">法律知识库</h1>
          <p className="text-gray-600">浏览和学习各类法律知识，保护您的合法权益</p>
        </div>

        {/* 统计卡片 */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
          {isLoadingStats ? (
            <>
              <div className="h-20 bg-gray-200 rounded-lg animate-pulse" />
              <div className="h-20 bg-gray-200 rounded-lg animate-pulse" />
              <div className="h-20 bg-gray-200 rounded-lg animate-pulse" />
              <div className="h-20 bg-gray-200 rounded-lg animate-pulse" />
            </>
          ) : stats ? (
            <>
              <StatCard
                title="法律条文"
                value={stats.totalLaws}
                color="blue"
              />
              <StatCard
                title="案例"
                value={stats.totalCases}
                color="green"
              />
              <StatCard
                title="法规"
                value={stats.totalRegulations}
                color="purple"
              />
              <StatCard
                title="司法解释"
                value={stats.totalInterpretations}
                color="orange"
              />
            </>
          ) : null}
        </div>

        {/* 搜索区域 */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4 mb-6">
          <KnowledgeSearch
            onSearch={handleSearch}
            onClear={handleClearSearch}
            initialValue={searchKeyword}
            loading={isLoadingList}
          />
        </div>

        {/* 分类筛选 */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4 mb-6">
          <h3 className="text-sm font-medium text-gray-700 mb-3">分类筛选</h3>
          <CategoryFilter
            selectedCategory={selectedCategory}
            onSelectCategory={handleSelectCategory}
          />
        </div>

        {/* 知识列表 */}
        <div className="mb-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-gray-900">
              {searchKeyword
                ? `"${searchKeyword}" 的搜索结果`
                : selectedCategory
                ? `${selectedCategory} 相关内容`
                : '全部法律知识'}
            </h2>
            {knowledgeData && (
              <span className="text-sm text-gray-500">
                共 {knowledgeData.total} 条
              </span>
            )}
          </div>

          {isListError ? (
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-8 text-center">
              <p className="text-red-600 mb-2">加载失败，请稍后重试</p>
              <button
                onClick={() => window.location.reload()}
                className="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors"
              >
                重新加载
              </button>
            </div>
          ) : (
            <KnowledgeList
              items={knowledgeData?.items || []}
              isLoading={isLoadingList}
              onSelect={handleSelectArticle}
            />
          )}
        </div>

        {/* 分页 */}
        {totalPages > 1 && (
          <div className="flex items-center justify-center gap-2">
            <button
              onClick={() => handlePageChange(currentPage - 1)}
              disabled={currentPage === 1}
              className="px-4 py-2 bg-white border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              上一页
            </button>

            <span className="px-4 py-2 text-sm text-gray-600">
              {currentPage} / {totalPages}
            </span>

            <button
              onClick={() => handlePageChange(currentPage + 1)}
              disabled={currentPage === totalPages}
              className="px-4 py-2 bg-white border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              下一页
            </button>
          </div>
        )}
      </div>
    </div>
  );
}