/**
 * KnowledgeAdminPage - 知识库管理页面
 */

import { useState } from 'react';

import type {
  KnowledgeArticle,
  KnowledgeArticleListItem,
  CreateArticleRequest,
  UpdateArticleRequest,
} from '../types';
import {
  useArticles,
  useArticle,
  useCategories,
  useKnowledgeStats,
  useCreateArticle,
  useUpdateArticle,
  useDeleteArticle,
  useCreateCategory,
  useImportSample,
} from '../hooks/useKnowledgeAdmin';
import { ArticleList } from '../components/ArticleList';
import { ArticleEditor } from '../components/ArticleEditor';
import { CategoryManager } from '../components/CategoryManager';
import { KnowledgeStatsComponent } from '../components/KnowledgeStats';

type TabType = 'articles' | 'categories' | 'stats';

/**
 * 知识库管理页面
 */
export function KnowledgeAdminPage(): JSX.Element {
  // 当前选中的标签页
  const [activeTab, setActiveTab] = useState<TabType>('articles');

  // 列表查询参数
  const [page, setPage] = useState<number>(1);
  const [pageSize] = useState<number>(10);
  const [category, setCategory] = useState<string | undefined>(undefined);
  const [keyword, setKeyword] = useState<string>('');
  const [_knowledgeType, _setKnowledgeType] = useState<string | undefined>(undefined);

  // 编辑状态
  const [isEditing, setIsEditing] = useState<boolean>(false);
  const [editingArticle, setEditingArticle] = useState<KnowledgeArticleListItem | KnowledgeArticle | null>(null);

  // 查看详情状态
  const [viewingArticleId, setViewingArticleId] = useState<number | null>(null);

  // 数据查询
  const { data: articlesData, isLoading: isLoadingArticles, refetch: refetchArticles } = useArticles({
    page,
    pageSize,
    category,
    keyword: keyword || undefined,
  });

  const { data: categories, isLoading: isLoadingCategories, refetch: refetchCategories } = useCategories(true);
  const { data: stats, isLoading: isLoadingStats, refetch: refetchStats } = useKnowledgeStats();
  const { data: viewingArticle } = useArticle(viewingArticleId);

  // Mutations
  const createMutation = useCreateArticle();
  const updateMutation = useUpdateArticle();
  const deleteMutation = useDeleteArticle();
  const createCategoryMutation = useCreateCategory();
  const importSampleMutation = useImportSample();

  // 提取分类名称列表
  const categoryNames = categories?.map((c) => c.name) ?? [];

  // 处理新建文章
  const handleCreate = (): void => {
    setEditingArticle(null);
    setIsEditing(true);
  };

  // 处理编辑文章
  const handleEdit = (article: KnowledgeArticleListItem): void => {
    setEditingArticle(article);
    setIsEditing(true);
  };

  // 处理查看文章
  const handleView = (article: KnowledgeArticleListItem): void => {
    setViewingArticleId(article.id);
  };

  // 处理删除文章
  const handleDelete = (article: KnowledgeArticleListItem): void => {
    if (window.confirm(`确定要删除文章"${article.title}"吗？此操作不可恢复。`)) {
      deleteMutation.mutate(article.id);
    }
  };

  // 处理保存文章
  const handleSaveArticle = (data: CreateArticleRequest | UpdateArticleRequest): void => {
    if (editingArticle) {
      // 更新
      updateMutation.mutate(
        { articleId: editingArticle.id, request: data as UpdateArticleRequest },
        {
          onSuccess: () => {
            setIsEditing(false);
            setEditingArticle(null);
          },
        }
      );
    } else {
      // 创建
      createMutation.mutate(data as CreateArticleRequest, {
        onSuccess: () => {
          setIsEditing(false);
        },
      });
    }
  };

  // 处理创建分类
  const handleCreateCategory = (name: string, description?: string): void => {
    createCategoryMutation.mutate(
      { name, description },
      {
        onSuccess: () => {
          void refetchCategories();
        },
      }
    );
  };

  // 处理导入示例数据
  const handleImportSample = (): void => {
    if (window.confirm('确定要导入示例数据吗？这将添加多条法律知识到知识库中。')) {
      importSampleMutation.mutate(undefined, {
        onSuccess: (result) => {
          alert(result.message);
          void refetchArticles();
          void refetchStats();
          void refetchCategories();
        },
      });
    }
  };

  // 刷新所有数据
  const handleRefreshAll = (): void => {
    void refetchArticles();
    void refetchCategories();
    void refetchStats();
  };

  // 渲染标签页按钮
  const renderTabButton = (tab: TabType, label: string, count?: number): JSX.Element => (
    <button
      onClick={() => setActiveTab(tab)}
      className={`whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm ${
        activeTab === tab
          ? 'border-blue-500 text-blue-600'
          : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
      }`}
    >
      {label}
      {count !== undefined && count > 0 && (
        <span className="ml-2 px-2 py-0.5 text-xs bg-blue-100 text-blue-600 rounded-full">
          {count}
        </span>
      )}
    </button>
  );

  // 渲染内容区域
  const renderContent = (): JSX.Element => {
    if (isEditing) {
      return (
        <div className="max-w-5xl mx-auto">
          <div className="mb-6 flex items-center space-x-2 text-sm text-gray-500">
            <button
              onClick={() => {
                setIsEditing(false);
                setEditingArticle(null);
              }}
              className="hover:text-blue-600 transition-colors"
            >
              ← 返回列表
            </button>
            <span>/</span>
            <span>{editingArticle ? '编辑文章' : '新建文章'}</span>
          </div>
          <ArticleEditor
            article={editingArticle}
            categories={categoryNames}
            onSave={handleSaveArticle}
            onCancel={() => {
              setIsEditing(false);
              setEditingArticle(null);
            }}
            isLoading={createMutation.isPending || updateMutation.isPending}
          />
        </div>
      );
    }

    if (viewingArticleId && viewingArticle) {
      return (
        <div className="max-w-5xl mx-auto">
          <div className="mb-6 flex items-center space-x-2 text-sm text-gray-500">
            <button
              onClick={() => setViewingArticleId(null)}
              className="hover:text-blue-600 transition-colors"
            >
              ← 返回列表
            </button>
            <span>/</span>
            <span>文章详情</span>
          </div>
          <div className="bg-white rounded-lg shadow p-8">
            <div className="flex items-center gap-3 mb-4">
              <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                viewingArticle.knowledgeType === 'law' ? 'bg-blue-100 text-blue-800' :
                viewingArticle.knowledgeType === 'case' ? 'bg-green-100 text-green-800' :
                viewingArticle.knowledgeType === 'regulation' ? 'bg-purple-100 text-purple-800' :
                'bg-orange-100 text-orange-800'
              }`}>
                {viewingArticle.knowledgeType === 'law' ? '法律法规' :
                 viewingArticle.knowledgeType === 'case' ? '典型案例' :
                 viewingArticle.knowledgeType === 'regulation' ? '规章制度' : '司法解释'}
              </span>
              <span className="text-sm text-gray-500">{viewingArticle.category}</span>
              {viewingArticle.isVectorized && (
                <span className="inline-flex items-center px-2 py-0.5 rounded text-xs bg-green-50 text-green-700 border border-green-200">
                  已向量化
                </span>
              )}
            </div>
            <h1 className="text-2xl font-bold text-gray-900 mb-4">{viewingArticle.title}</h1>
            {viewingArticle.articleNumber && (
              <p className="text-sm text-gray-500 mb-4">编号: {viewingArticle.articleNumber}</p>
            )}
            <div className="prose max-w-none mb-8 whitespace-pre-wrap">{viewingArticle.content}</div>
            {viewingArticle.summary && (
              <div className="bg-gray-50 p-4 rounded-lg mb-4">
                <h3 className="text-sm font-medium text-gray-700 mb-2">摘要</h3>
                <p className="text-sm text-gray-600">{viewingArticle.summary}</p>
              </div>
            )}
            {viewingArticle.keywords && (
              <div className="mb-4">
                <h3 className="text-sm font-medium text-gray-700 mb-2">关键词</h3>
                <div className="flex flex-wrap gap-2">
                  {viewingArticle.keywords.split(',').map((k, i) => (
                    <span key={i} className="px-2 py-1 bg-blue-50 text-blue-700 text-xs rounded">
                      {k.trim()}
                    </span>
                  ))}
                </div>
              </div>
            )}
            <div className="border-t border-gray-200 pt-4 text-sm text-gray-500">
              {viewingArticle.source && <p>来源: {viewingArticle.source}</p>}
              {viewingArticle.sourceVersion && <p>版本: {viewingArticle.sourceVersion}</p>}
              {viewingArticle.effectiveDate && <p>生效日期: {viewingArticle.effectiveDate}</p>}
              <p className="mt-2">创建时间: {new Date(viewingArticle.createdAt).toLocaleString('zh-CN')}</p>
            </div>
          </div>
        </div>
      );
    }

    switch (activeTab) {
      case 'articles':
        return (
          <ArticleList
            articles={articlesData?.items ?? []}
            total={articlesData?.total ?? 0}
            page={page}
            pageSize={pageSize}
            onPageChange={setPage}
            onEdit={handleEdit}
            onDelete={handleDelete}
            onView={handleView}
            isLoading={isLoadingArticles}
            categories={categoryNames}
            onCategoryChange={setCategory}
            selectedCategory={category}
            onKeywordChange={setKeyword}
            keyword={keyword}
          />
        );
      case 'categories':
        return (
          <CategoryManager
            categories={categories ?? []}
            onCreateCategory={handleCreateCategory}
            isLoading={isLoadingCategories}
          />
        );
      case 'stats':
        return (
          <KnowledgeStatsComponent
            stats={stats}
            isLoading={isLoadingStats}
          />
        );
      default:
        return <div />;
    }
  };

  return (
    <div className="min-h-screen bg-gray-100">
      {/* 页面头部 */}
      <div className="bg-white shadow">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">知识库管理</h1>
              <p className="mt-1 text-sm text-gray-500">管理法律知识、案例、法规等内容</p>
            </div>
            <div className="flex items-center space-x-3">
              {!isEditing && !viewingArticleId && (
                <>
                  <button
                    onClick={handleRefreshAll}
                    className="inline-flex items-center px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                  >
                    <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                    </svg>
                    刷新
                  </button>
                  <button
                    onClick={handleImportSample}
                    disabled={importSampleMutation.isPending}
                    className="inline-flex items-center px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50"
                  >
                    {importSampleMutation.isPending ? '导入中...' : '导入示例'}
                  </button>
                  <button
                    onClick={handleCreate}
                    className="inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                  >
                    <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                    </svg>
                    新建文章
                  </button>
                </>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* 标签页导航 */}
      {!isEditing && !viewingArticleId && (
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 mt-6">
          <div className="border-b border-gray-200">
            <nav className="-mb-px flex space-x-8">
              {renderTabButton('articles', '文章列表', articlesData?.total)}
              {renderTabButton('categories', '分类管理', categories?.length)}
              {renderTabButton('stats', '数据统计')}
            </nav>
          </div>
        </div>
      )}

      {/* 内容区域 */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        {renderContent()}
      </div>
    </div>
  );
}