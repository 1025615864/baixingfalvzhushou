/**
 * NewsAdminPage - 新闻管理页面
 */

import { lazy, Suspense, useState } from 'react';

const LazyNewsArticlesPanel = lazy(() =>
  import('../components/NewsArticlesPanel').then((module) => ({
    default: module.NewsArticlesPanel,
  }))
);

const LazyArticleEditor = lazy(() =>
  import('../components/ArticleEditor').then((module) => ({
    default: module.ArticleEditor,
  }))
);

const LazyArticleReview = lazy(() =>
  import('../components/ArticleReview').then((module) => ({
    default: module.ArticleReview,
  }))
);

const LazyCategoryManager = lazy(() =>
  import('../components/CategoryManager').then((module) => ({
    default: module.CategoryManager,
  }))
);
import type { NewsArticle, NewsAdminListItem, CreateNewsRequest, UpdateNewsRequest, ReviewNewsRequest, CategoryCount, NewsStats } from '../types';
import {
  useNewsList,
  useCreateNews,
  useUpdateNews,
  useDeleteNews,
  useReviewNews,
  useCategoryStats,
  useNewsStats,
} from '../hooks/useNewsAdmin';

type TabType = 'articles' | 'categories';

function NewsAdminSectionSkeleton({ rows = 3 }: { rows?: number }): JSX.Element {
  return (
    <div className="space-y-4">
      {Array.from({ length: rows }).map((_, index) => (
        <div key={index} className="h-24 animate-pulse rounded-lg bg-slate-100" />
      ))}
    </div>
  );
}

/**
 * 新闻管理页面
 */
export function NewsAdminPage(): JSX.Element {
  // 当前选中的标签页
  const [activeTab, setActiveTab] = useState<TabType>('articles');

  // 列表查询参数
  const [page, setPage] = useState<number>(1);
  const [pageSize] = useState<number>(10);
  const [category, setCategory] = useState<string | undefined>(undefined);
  const [keyword, setKeyword] = useState<string>('');
  const [reviewStatus, setReviewStatus] = useState<'pending' | 'approved' | 'rejected' | undefined>(undefined);

  // 弹窗状态
  const [editorOpen, setEditorOpen] = useState<boolean>(false);
  const [reviewOpen, setReviewOpen] = useState<boolean>(false);
  const [editingArticle, setEditingArticle] = useState<NewsAdminListItem | null>(null);
  const [reviewingArticle, setReviewingArticle] = useState<NewsAdminListItem | null>(null);

  // 数据查询
  const shouldLoadArticles = activeTab === 'articles';
  const shouldLoadCategories = activeTab === 'categories';

  const { data: newsData, isLoading: isLoadingNews } = useNewsList(
    {
      page,
      pageSize,
      category,
      keyword: keyword || undefined,
      reviewStatus,
    },
    shouldLoadArticles
  );

  const {
    data: categoriesData,
    isLoading: isLoadingCategories,
    refetch: refetchCategories
  } = useCategoryStats(shouldLoadCategories) as { data: CategoryCount[] | undefined; isLoading: boolean; refetch: () => Promise<unknown> };
  const {
    data: newsStats,
    isLoading: isLoadingStats,
    refetch: refetchStats
  } = useNewsStats(shouldLoadArticles || shouldLoadCategories) as { data: NewsStats | undefined; isLoading: boolean; refetch: () => Promise<unknown> };
  
  // 分类数据本身就是数组
  const categories = categoriesData ?? [];

  // Mutations
  const createMutation = useCreateNews();
  const updateMutation = useUpdateNews();
  const deleteMutation = useDeleteNews();
  const reviewMutation = useReviewNews();

  // 处理新建文章
  const handleCreate = (): void => {
    setEditingArticle(null);
    setEditorOpen(true);
  };

  // 处理编辑文章
  const handleEdit = (article: NewsAdminListItem): void => {
    setEditingArticle(article);
    setEditorOpen(true);
  };

  // 处理删除文章
  const handleDelete = (article: NewsAdminListItem): void => {
    if (window.confirm(`确定要删除文章"${article.title}"吗？此操作不可恢复。`)) {
      deleteMutation.mutate(article.id);
    }
  };

  // 处理审核文章
  const handleReview = (article: NewsAdminListItem): void => {
    setReviewingArticle(article);
    setReviewOpen(true);
  };

  // 处理发布/下架
  const handlePublish = (article: NewsAdminListItem): void => {
    const action = article.isPublished ? '下架' : '发布';
    if (window.confirm(`确定要${action}文章"${article.title}"吗？`)) {
      updateMutation.mutate({
        id: article.id,
        request: {
          isPublished: !article.isPublished,
        },
      });
    }
  };

  // 处理置顶/取消置顶
  const handleTop = (article: NewsAdminListItem): void => {
    const action = article.isTop ? '取消置顶' : '置顶';
    if (window.confirm(`确定要${action}文章"${article.title}"吗？`)) {
      updateMutation.mutate({
        id: article.id,
        request: {
          isTop: !article.isTop,
        },
      });
    }
  };

  // 处理保存文章
  const handleSaveArticle = (data: CreateNewsRequest | UpdateNewsRequest): void => {
    if (editingArticle) {
      // 更新
      updateMutation.mutate(
        { id: editingArticle.id, request: data as UpdateNewsRequest },
        {
          onSuccess: () => {
            setEditorOpen(false);
            setEditingArticle(null);
          },
        }
      );
    } else {
      // 创建
      createMutation.mutate(data as CreateNewsRequest, {
        onSuccess: () => {
          setEditorOpen(false);
        },
      });
    }
  };

  // 处理审核提交
  const handleReviewSubmit = (request: ReviewNewsRequest): void => {
    if (!reviewingArticle) return;

    reviewMutation.mutate(
      { id: reviewingArticle.id, request },
      {
        onSuccess: () => {
          setReviewOpen(false);
          setReviewingArticle(null);
        },
      }
    );
  };

  // 刷新分类数据
  const handleRefreshCategories = (): void => {
    void refetchCategories();
    void refetchStats();
  };

  // 获取待审核数量
  const pendingCount = newsStats?.pendingReview ?? 0;

  return (
    <div className="min-h-screen bg-gray-100">
      {/* 页面头部 */}
      <div className="bg-white shadow">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">新闻管理</h1>
              <p className="mt-1 text-sm text-gray-500">管理新闻文章、分类和审核</p>
            </div>
            <button
              onClick={handleCreate}
              className="inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
            >
              <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
              </svg>
              新建文章
            </button>
          </div>
        </div>
      </div>

      {/* 标签页 */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 mt-6">
        <div className="border-b border-gray-200">
          <nav className="-mb-px flex space-x-8">
            <button
              onClick={() => setActiveTab('articles')}
              className={`whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'articles'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              文章列表
              {pendingCount > 0 && (
                <span className="ml-2 px-2 py-0.5 text-xs bg-red-100 text-red-600 rounded-full">
                  {pendingCount}
                </span>
              )}
            </button>
            <button
              onClick={() => setActiveTab('categories')}
              className={`whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'categories'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              分类管理
            </button>
          </nav>
        </div>
      </div>

      {/* 内容区域 */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        {activeTab === 'articles' && (
          <Suspense fallback={<NewsAdminSectionSkeleton rows={4} />}>
            <LazyNewsArticlesPanel
              items={newsData?.items || []}
              total={newsData?.total || 0}
              page={page}
              pageSize={pageSize}
              category={category}
              keyword={keyword}
              reviewStatus={reviewStatus}
              isLoading={isLoadingNews}
              onPageChange={setPage}
              onKeywordChange={setKeyword}
              onCategoryChange={setCategory}
              onReviewStatusChange={setReviewStatus}
              onResetFilters={() => {
                setPage(1);
                setKeyword('');
                setCategory(undefined);
                setReviewStatus(undefined);
              }}
              onEdit={handleEdit}
              onDelete={handleDelete}
              onReview={handleReview}
              onPublish={handlePublish}
              onTop={handleTop}
            />
          </Suspense>
        )}

        {activeTab === 'categories' && (
          <Suspense fallback={<NewsAdminSectionSkeleton rows={3} />}>
            <LazyCategoryManager
              categories={categories}
              stats={newsStats || null}
              isLoading={isLoadingCategories || isLoadingStats}
              onRefresh={handleRefreshCategories}
            />
          </Suspense>
        )}
      </div>

      {/* 编辑器弹窗 */}
      {editorOpen && (
        <Suspense fallback={null}>
          <LazyArticleEditor
            article={editingArticle as NewsArticle | null}
            isOpen={editorOpen}
            isLoading={createMutation.isPending || updateMutation.isPending}
            onClose={() => {
              setEditorOpen(false);
              setEditingArticle(null);
            }}
            onSave={handleSaveArticle}
          />
        </Suspense>
      )}

      {/* 审核弹窗 */}
      {reviewingArticle && (
        <Suspense fallback={null}>
          <LazyArticleReview
            article={reviewingArticle}
            isOpen={reviewOpen}
            isLoading={reviewMutation.isPending}
            onClose={() => {
              setReviewOpen(false);
              setReviewingArticle(null);
            }}
            onConfirm={handleReviewSubmit}
          />
        </Suspense>
      )}
    </div>
  );
}