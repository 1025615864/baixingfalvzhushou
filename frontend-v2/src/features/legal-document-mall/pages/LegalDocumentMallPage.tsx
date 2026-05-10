/**
 * 法律文书商城页面
 * 整合所有组件，实现完整的商城功能
 */

import { logger } from '@/shared/lib/logger';
import { useState, useCallback, useMemo } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import {
  Search,
  FileText,
  Star,
  Crown,
  Gift,
  ChevronRight,
  Filter,
  LayoutGrid,
  X,
  TrendingUp,
  Clock,
} from 'lucide-react';

import { Badge } from '@/components/ui/Badge';
import { Button } from '@/components/ui/Button';
import { Card } from '@/components/ui/Card';
import { Input } from '@/components/ui/Input';
import { Skeleton } from '@/components/ui/Skeleton';
import { useAuthStore } from '@/features/auth/store/authStore';

import DocumentCategoryList from '../components/DocumentCategoryList';
import DocumentCard from '../components/DocumentCard';
import DocumentGrid, { type SortOption } from '../components/DocumentGrid';
import DocumentPurchaseFlow from '../components/DocumentPurchaseFlow';
import {
  useCategories,
  useDocuments,
  useFeaturedDocuments,
  useFreeDocuments,
  useToggleFavorite,
} from '../hooks/useLegalDocuments';
import type { LegalDocument } from '../types';

/**
 * 搜索栏组件
 */
function SearchBar({
  keyword,
  onSearch,
  onClear,
}: {
  keyword: string;
  onSearch: (keyword: string) => void;
  onClear: () => void;
}) {
  const [localKeyword, setLocalKeyword] = useState(keyword);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSearch(localKeyword);
  };

  const handleClear = () => {
    setLocalKeyword('');
    onClear();
  };

  return (
    <form onSubmit={handleSubmit} className="relative">
      <Search className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400 w-5 h-5" />
      <Input
        type="text"
        placeholder="搜索法律文书名称、描述、标签..."
        value={localKeyword}
        onChange={(e) => setLocalKeyword(e.target.value)}
        className="pl-12 pr-24 h-12 text-base bg-white border-gray-200 focus:border-blue-500 focus:ring-blue-500"
      />
      <div className="absolute right-2 top-1/2 -translate-y-1/2 flex items-center gap-2">
        {localKeyword && (
          <button
            type="button"
            onClick={handleClear}
            className="p-1 hover:bg-gray-100 rounded"
          >
            <X className="w-4 h-4 text-gray-400" />
          </button>
        )}
        <Button type="submit" size="sm" className="h-8">
          搜索
        </Button>
      </div>
    </form>
  );
}

/**
 * 快捷筛选标签
 */
function QuickFilters({
  activeFilter,
  onFilterChange,
}: {
  activeFilter: string;
  onFilterChange: (filter: string) => void;
}) {
  const filters = [
    { key: 'all', label: '全部', icon: LayoutGrid },
    { key: 'free', label: '免费', icon: Gift },
    { key: 'featured', label: '精选', icon: Star },
    { key: 'new', label: '最新', icon: Clock },
    { key: 'popular', label: '热门', icon: TrendingUp },
  ];

  return (
    <div className="flex items-center gap-2 flex-wrap">
      {filters.map((filter) => {
        const Icon = filter.icon;
        const isActive = activeFilter === filter.key;
        return (
          <button
            key={filter.key}
            onClick={() => onFilterChange(filter.key)}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-full text-sm font-medium transition-colors ${
              isActive
                ? 'bg-blue-600 text-white'
                : 'bg-white text-gray-600 hover:bg-gray-100 border border-gray-200'
            }`}
          >
            <Icon className="w-3.5 h-3.5" />
            {filter.label}
          </button>
        );
      })}
    </div>
  );
}

/**
 * 推荐文书轮播区域
 */
function FeaturedSection({
  documents,
  onPurchase,
  onToggleFavorite,
  onViewDetail,
  isLoading,
}: {
  documents?: LegalDocument[];
  onPurchase: (doc: LegalDocument) => void;
  onToggleFavorite: (doc: LegalDocument) => void;
  onViewDetail: (doc: LegalDocument) => void;
  isLoading?: boolean;
}) {
  if (isLoading) {
    return (
      <div className="mb-8">
        <div className="flex items-center gap-2 mb-4">
          <Crown className="w-5 h-5 text-yellow-500" />
          <h2 className="text-xl font-bold text-gray-900">精选推荐</h2>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {[1, 2, 3].map((i) => (
            <Card key={i} className="p-4">
              <Skeleton className="h-4 w-3/4 mb-2" />
              <Skeleton className="h-3 w-full mb-1" />
              <Skeleton className="h-3 w-2/3 mb-3" />
              <Skeleton className="h-8 w-full" />
            </Card>
          ))}
        </div>
      </div>
    );
  }

  if (!documents || documents.length === 0) return null;

  return (
    <div className="mb-8">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <Crown className="w-5 h-5 text-yellow-500" />
          <h2 className="text-xl font-bold text-gray-900">精选推荐</h2>
          <Badge variant="default" className="text-xs">
            编辑推荐
          </Badge>
        </div>
        <Button variant="ghost" size="sm" className="text-gray-600">
          查看更多
          <ChevronRight className="w-4 h-4 ml-1" />
        </Button>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {documents.slice(0, 6).map((doc) => (
          <DocumentCard
            key={doc.id}
            document={doc}
            onPurchase={onPurchase}
            onToggleFavorite={onToggleFavorite}
            onClick={onViewDetail}
            showMemberPrice
          />
        ))}
      </div>
    </div>
  );
}

/**
 * 免费文书区域
 */
function FreeSection({
  documents,
  onPurchase,
  onToggleFavorite,
  onViewDetail,
  isLoading,
}: {
  documents?: LegalDocument[];
  onPurchase: (doc: LegalDocument) => void;
  onToggleFavorite: (doc: LegalDocument) => void;
  onViewDetail: (doc: LegalDocument) => void;
  isLoading?: boolean;
}) {
  if (isLoading) {
    return (
      <div className="mb-8">
        <div className="flex items-center gap-2 mb-4">
          <Gift className="w-5 h-5 text-green-500" />
          <h2 className="text-xl font-bold text-gray-900">免费文书</h2>
        </div>
        <div className="flex gap-4 overflow-hidden">
          {[1, 2, 3, 4].map((i) => (
            <Card key={i} className="p-4 min-w-[280px] flex-shrink-0">
              <Skeleton className="h-4 w-3/4 mb-2" />
              <Skeleton className="h-3 w-full mb-1" />
              <Skeleton className="h-3 w-2/3 mb-3" />
              <Skeleton className="h-8 w-full" />
            </Card>
          ))}
        </div>
      </div>
    );
  }

  if (!documents || documents.length === 0) return null;

  return (
    <div className="mb-8">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <Gift className="w-5 h-5 text-green-500" />
          <h2 className="text-xl font-bold text-gray-900">免费文书</h2>
          <Badge variant="success" className="text-xs text-green-600 border-green-200">
            限时免费
          </Badge>
        </div>
        <Button variant="ghost" size="sm" className="text-gray-600">
          查看更多
          <ChevronRight className="w-4 h-4 ml-1" />
        </Button>
      </div>
      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-4">
        {documents.slice(0, 10).map((doc) => (
          <DocumentCard
            key={doc.id}
            document={doc}
            onPurchase={onPurchase}
            onToggleFavorite={onToggleFavorite}
            onClick={onViewDetail}
            showMemberPrice={false}
            compact
          />
        ))}
      </div>
    </div>
  );
}

/**
 * 主页面组件
 */
export default function LegalDocumentMallPage() {
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();
  const { isAuthenticated } = useAuthStore();

  // 状态管理
  const [selectedCategory, setSelectedCategory] = useState<string | null>(
    searchParams.get('category')
  );
  const [keyword, setKeyword] = useState<string>(searchParams.get('keyword') || '');
  const [activeFilter, setActiveFilter] = useState<string>('all');
  const [page, setPage] = useState<number>(1);
  const [sort, setSort] = useState<SortOption>({
    key: 'created_at',
    label: '最新发布',
    direction: 'desc',
  });
  const [showMobileFilter, setShowMobileFilter] = useState(false);

  // 购买流程状态
  const [purchaseDocument, setPurchaseDocument] = useState<LegalDocument | null>(null);
  const [showPurchaseFlow, setShowPurchaseFlow] = useState(false);

  // 数据查询
  const categoriesQuery = useCategories();
  const documentsQuery = useDocuments({
    category: selectedCategory || undefined,
    keyword: keyword || undefined,
    page,
    page_size: 20,
    is_featured: activeFilter === 'featured' ? true : undefined,
    is_free: activeFilter === 'free' ? true : undefined,
  });
  const featuredQuery = useFeaturedDocuments(6);
  const freeQuery = useFreeDocuments(10);

  // 突变操作
  const favoriteMutation = useToggleFavorite();

  // 计算分类统计
  const categoryCounts = useMemo(() => {
    // 这里可以从服务端获取实际统计数据，暂时返回空对象
    return {};
  }, []);

  // 处理搜索
  const handleSearch = useCallback(
    (kw: string) => {
      setKeyword(kw);
      setPage(1);
      if (kw) {
        searchParams.set('keyword', kw);
      } else {
        searchParams.delete('keyword');
      }
      setSearchParams(searchParams);
    },
    [searchParams, setSearchParams]
  );

  // 处理分类选择
  const handleCategorySelect = useCallback(
    (category: string | null) => {
      setSelectedCategory(category);
      setPage(1);
      if (category) {
        searchParams.set('category', category);
      } else {
        searchParams.delete('category');
      }
      setSearchParams(searchParams);
    },
    [searchParams, setSearchParams]
  );

  // 处理筛选变化
  const handleFilterChange = useCallback((filter: string) => {
    setActiveFilter(filter);
    setPage(1);
  }, []);

  // 处理排序变化
  const handleSortChange = useCallback((newSort: SortOption) => {
    setSort(newSort);
    setPage(1);
  }, []);

  // 处理购买
  const handlePurchase = useCallback((doc: LegalDocument) => {
    if (!isAuthenticated) {
      navigate('/login');
      return;
    }
    setPurchaseDocument(doc);
    setShowPurchaseFlow(true);
  }, [isAuthenticated, navigate]);

  // 处理购买成功
  const handlePurchaseSuccess = useCallback(() => {
    // 刷新列表
    void documentsQuery.refetch();
    // 关闭购买弹窗
    setShowPurchaseFlow(false);
    setPurchaseDocument(null);
  }, [documentsQuery]);

  // 处理收藏 - 改为同步函数，用于 onClick
  const handleToggleFavorite = useCallback(
    (doc: LegalDocument) => {
      if (!isAuthenticated) {
        navigate('/login');
        return;
      }
      // 执行收藏操作，不等待结果
      void favoriteMutation.mutateAsync({
        documentId: doc.id,
        isFavorited: doc.is_favorited || false,
      }).catch(() => {
        logger.error('收藏操作失败');
      });
    },
    [isAuthenticated, favoriteMutation, navigate]
  );

  // 查看详情
  const handleViewDetail = useCallback(
    (doc: LegalDocument) => {
      navigate(`/legal-documents/${doc.id}`);
    },
    [navigate]
  );

  return (
    <div className="min-h-screen bg-gray-50">
      {/* 顶部Banner */}
      <div className="bg-gradient-to-r from-blue-600 via-blue-700 to-indigo-700 text-white">
        <div className="container mx-auto px-4 py-10">
          <div className="max-w-3xl mx-auto text-center">
            <div className="flex items-center justify-center gap-2 mb-4">
              <FileText className="w-8 h-8" />
              <h1 className="text-3xl md:text-4xl font-bold">法律文书商城</h1>
            </div>
            <p className="text-blue-100 text-lg mb-6">
              专业法律文书模板，覆盖民事、商事、劳动等多个领域，一键下载使用
            </p>

            {/* 搜索框 */}
            <SearchBar keyword={keyword} onSearch={handleSearch} onClear={() => handleSearch('')} />
          </div>

          {/* 快捷筛选 */}
          <div className="max-w-3xl mx-auto mt-6">
            <QuickFilters activeFilter={activeFilter} onFilterChange={handleFilterChange} />
          </div>
        </div>
      </div>

      <div className="container mx-auto px-4 py-8">
        <div className="flex gap-8">
          {/* 侧边栏 - 桌面端 */}
          <div className="hidden lg:block w-72 flex-shrink-0">
            <DocumentCategoryList
              categories={categoriesQuery.data || []}
              selectedCategory={selectedCategory}
              onSelectCategory={handleCategorySelect}
              categoryCounts={categoryCounts}
              isLoading={categoriesQuery.isLoading}
              collapsible
              defaultExpanded
              showSearch
              showCounts
              className="sticky top-4"
            />
          </div>

          {/* 主内容区 */}
          <div className="flex-1 min-w-0">
            {/* 移动端筛选按钮 */}
            <div className="lg:hidden mb-4">
              <Button
                variant="outline"
                onClick={() => setShowMobileFilter(true)}
                className="w-full"
              >
                <Filter className="w-4 h-4 mr-2" />
                筛选分类
              </Button>
            </div>

            {/* 推荐文书（首页时显示） */}
            {activeFilter === 'all' && !keyword && !selectedCategory && (
              <FeaturedSection
                documents={featuredQuery.data?.items}
                onPurchase={handlePurchase}
                onToggleFavorite={handleToggleFavorite}
                onViewDetail={handleViewDetail}
                isLoading={featuredQuery.isLoading}
              />
            )}

            {/* 免费文书（首页时显示） */}
            {activeFilter === 'all' && !keyword && !selectedCategory && (
              <FreeSection
                documents={freeQuery.data?.items}
                onPurchase={handlePurchase}
                onToggleFavorite={handleToggleFavorite}
                onViewDetail={handleViewDetail}
                isLoading={freeQuery.isLoading}
              />
            )}

            {/* 全部文书列表 */}
            <section>
              <DocumentGrid
                documents={documentsQuery.data?.items || []}
                total={documentsQuery.data?.total || 0}
                page={page}
                pageSize={documentsQuery.data?.page_size || 20}
                isLoading={documentsQuery.isLoading}
                onPageChange={setPage}
                onSortChange={handleSortChange}
                onPurchase={handlePurchase}
                onToggleFavorite={handleToggleFavorite}
                onDocumentClick={handleViewDetail}
                showMemberPrice
                showViewToggle
                showSort
                showPagination
                defaultSort={sort}
              />
            </section>
          </div>
        </div>
      </div>

      {/* 移动端筛选弹窗 */}
      {showMobileFilter && (
        <div className="fixed inset-0 z-50 lg:hidden">
          <div className="absolute inset-0 bg-black/50" onClick={() => setShowMobileFilter(false)} />
          <div className="absolute right-0 top-0 bottom-0 w-80 bg-white shadow-xl overflow-y-auto">
            <div className="p-4 border-b border-gray-100 flex items-center justify-between">
              <h3 className="font-medium">筛选分类</h3>
              <button onClick={() => setShowMobileFilter(false)} className="p-1 hover:bg-gray-100 rounded">
                <X className="w-5 h-5" />
              </button>
            </div>
            <div className="p-4">
              <DocumentCategoryList
                categories={categoriesQuery.data || []}
                selectedCategory={selectedCategory}
                onSelectCategory={(cat) => {
                  handleCategorySelect(cat);
                  setShowMobileFilter(false);
                }}
                categoryCounts={categoryCounts}
                isLoading={categoriesQuery.isLoading}
                collapsible={false}
                showSearch={false}
                showCounts
              />
            </div>
          </div>
        </div>
      )}

      {/* 购买流程弹窗 */}
      {purchaseDocument && (
        <DocumentPurchaseFlow
          document={purchaseDocument}
          isOpen={showPurchaseFlow}
          onClose={() => {
            setShowPurchaseFlow(false);
            setPurchaseDocument(null);
          }}
          onSuccess={handlePurchaseSuccess}
          onError={(error) => {
            logger.error('购买失败', error);
          }}
          userPoints={1000} // TODO: 从用户状态获取
          userMemberTier={null} // TODO: 从用户状态获取
        />
      )}
    </div>
  );
}