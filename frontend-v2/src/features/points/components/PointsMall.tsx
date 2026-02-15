/**
 * PointsMall - 积分商城组件
 *
 * 支持分类筛选、分页和兑换功能
 */

import { useState } from 'react';

import { usePointsProducts, useExchangeProduct, usePointsBalance } from '../hooks/usePoints';
import { usePagination } from '../../../components/ui/usePagination';
import { Pagination } from '../../../components/ui/Pagination';
import { FilterDropdown } from '../../../components/ui/FilterDropdown';
import { CardSkeleton } from '../../../components/ui/Skeleton';
import { EmptyState, EmptyError } from '../../../components/ui/EmptyState';
import type { PointsProduct, ExchangeOrder } from '../types';

import { ExchangeConfirmDialog } from './ExchangeConfirmDialog';
import { ExchangeSuccess } from './ExchangeSuccess';


interface PointsMallProps {
  className?: string;
  /** 兑换成功回调 */
  onExchangeSuccess?: (order: ExchangeOrder) => void;
}

/**
 * 商品类型筛选选项
 */
const productTypeOptions = [
  { value: 'virtual', label: '虚拟商品' },
  { value: 'physical', label: '实物商品' },
  { value: 'service', label: '服务' },
  { value: 'coupon', label: '优惠券' },
];

/**
 * 排序选项
 */
const sortOptions = [
  { value: 'points_asc', label: '积分从低到高' },
  { value: 'points_desc', label: '积分从高到低' },
  { value: 'newest', label: '最新上架' },
  { value: 'popular', label: '最受欢迎' },
];

/**
 * 获取类型标签
 */
function getTypeLabel(type: string): string {
  const labelMap: Record<string, string> = {
    virtual: '虚拟',
    physical: '实物',
    service: '服务',
    coupon: '优惠券',
  };
  return labelMap[type] || type;
}

/**
 * 积分商城组件
 */
export function PointsMall({ className = '', onExchangeSuccess }: PointsMallProps): JSX.Element {
  // 分类筛选
  const [selectedTypes, setSelectedTypes] = useState<string[]>([]);
  const [selectedSort, setSelectedSort] = useState<string>('');

  // 兑换状态
  const [confirmProduct, setConfirmProduct] = useState<PointsProduct | null>(null);
  const [exchangeOrder, setExchangeOrder] = useState<ExchangeOrder | null>(null);
  const [showSuccess, setShowSuccess] = useState(false);

  // 使用分页 hook
  const pagination = usePagination({
    initialPage: 1,
    initialPageSize: 12,
    pageSizeOptions: [12, 24, 48],
  });

  // 获取数据
  const { data: balance, isLoading: isBalanceLoading } = usePointsBalance();
  const {
    data: products,
    isLoading: isProductsLoading,
    error,
    refetch,
  } = usePointsProducts(selectedTypes.length === 1 ? selectedTypes[0] : undefined);

  const exchangeMutation = useExchangeProduct();

  const isLoading = isBalanceLoading || isProductsLoading;

  // 过滤和排序商品
  const filteredProducts = (products ?? []).filter((product) => {
    // 多选类型筛选
    if (selectedTypes.length > 0) {
      return selectedTypes.includes(product.productType);
    }
    return true;
  }).sort((a, b) => {
    // 排序
    switch (selectedSort) {
      case 'points_asc':
        return a.pointsRequired - b.pointsRequired;
      case 'points_desc':
        return b.pointsRequired - a.pointsRequired;
      case 'newest':
        return b.id.localeCompare(a.id);
      default:
        return 0;
    }
  });

  // 客户端分页
  const totalProducts = filteredProducts.length;
  const startIndex = (pagination.page - 1) * pagination.pageSize;
  const endIndex = startIndex + pagination.pageSize;
  const paginatedProducts = filteredProducts.slice(startIndex, endIndex);

  // 更新分页总数据数
  if (totalProducts !== pagination.total) {
    pagination.setTotal(totalProducts);
  }

  // 处理兑换
  const handleExchange = (product: PointsProduct): void => {
    if (!balance || balance.balance < product.pointsRequired) {
      return;
    }

    if (product.stock === 0) {
      return;
    }

    setConfirmProduct(product);
  };

  const handleConfirmExchange = async (): Promise<void> => {
    if (!confirmProduct) return;

    try {
      const result = await exchangeMutation.mutateAsync({ productId: confirmProduct.id });
      setConfirmProduct(null);
      setExchangeOrder(result.order);
      setShowSuccess(true);
      onExchangeSuccess?.(result.order);
    } catch {
      // 错误处理由 hook 统一管理
    }
  };

  const handleCloseSuccess = (): void => {
    setShowSuccess(false);
    setExchangeOrder(null);
  };

  // 清除筛选
  const handleClearFilters = (): void => {
    setSelectedTypes([]);
    setSelectedSort('');
    pagination.goToFirstPage();
  };

  // 是否有筛选条件
  const hasFilters = selectedTypes.length > 0 || selectedSort !== '';

  if (isLoading) {
    return (
      <div className={`space-y-4 ${className}`}>
        {/* 筛选骨架 */}
        <div className="flex flex-wrap gap-3 mb-6">
          <div className="w-32 h-10 bg-gray-200 rounded-lg animate-pulse" />
          <div className="w-40 h-10 bg-gray-200 rounded-lg animate-pulse" />
        </div>
        {/* 商品列表骨架 */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {Array.from({ length: 6 }).map((_, index) => (
            <CardSkeleton key={index} hasImage lines={2} />
          ))}
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className={`${className}`}>
        <EmptyError
          title="加载失败"
          description="无法获取商品列表"
          onRetry={() => { void refetch(); }}
        />
      </div>
    );
  }

  return (
    <div className={className}>
      {/* 筛选栏 */}
      <div className="flex flex-wrap items-center justify-between gap-3 mb-6">
        <div className="flex flex-wrap items-center gap-3">
          {/* 类型筛选 */}
          <FilterDropdown
            label="分类"
            placeholder="全部分类"
            multiple
            options={productTypeOptions}
            value={selectedTypes}
            onChange={(value) => {
              setSelectedTypes(value);
              pagination.goToFirstPage();
            }}
          />

          {/* 排序 */}
          <FilterDropdown
            label="排序"
            placeholder="默认排序"
            options={sortOptions}
            value={selectedSort ? [selectedSort] : []}
            onChange={(value) => {
              setSelectedSort(value[0] || '');
              pagination.goToFirstPage();
            }}
          />

          {/* 清除筛选 */}
          {hasFilters && (
            <button
              onClick={handleClearFilters}
              className="px-3 py-2 text-sm font-medium text-gray-600 hover:text-gray-800 hover:bg-gray-100 rounded-lg transition-colors dark:text-gray-400 dark:hover:text-gray-200 dark:hover:bg-gray-700"
            >
              清除筛选
            </button>
          )}
        </div>

        {/* 商品数量 */}
        <div className="text-sm text-gray-500 dark:text-gray-400">
          共 <span className="font-medium text-gray-900 dark:text-gray-100">{totalProducts}</span> 件商品
        </div>
      </div>

      {/* 商品列表 */}
      {filteredProducts.length === 0 ? (
        <EmptyState
          icon="box"
          title="暂无商品"
          description={hasFilters ? '没有找到符合条件的商品，尝试调整筛选条件' : '积分商城正在筹备中，敬请期待'}
          size="md"
          action={
            hasFilters && (
              <button
                onClick={handleClearFilters}
                className="px-4 py-2 text-sm font-medium text-blue-600 hover:text-blue-700"
              >
                清除筛选
              </button>
            )
          }
        />
      ) : (
        <>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 mb-6">
            {paginatedProducts.map((product) => (
              <div
                key={product.id}
                className="flex flex-col bg-white rounded-lg border overflow-hidden hover:shadow-md transition-shadow dark:bg-gray-800 dark:border-gray-700"
              >
                {/* 商品图片 */}
                <div className="relative aspect-video bg-gray-100 dark:bg-gray-700">
                  {product.imageUrl ? (
                    <img
                      src={product.imageUrl}
                      alt={product.name}
                      className="w-full h-full object-cover"
                    />
                  ) : (
                    <div className="flex items-center justify-center w-full h-full text-gray-400">
                      <svg className="w-12 h-12" fill="currentColor" viewBox="0 0 20 20">
                        <path d="M10 2a6 6 0 00-6 6v3.586l-.707.707A1 1 0 004 14h12a1 1 0 00.707-1.707L16 11.586V8a6 6 0 00-6-6zM10 18a3 3 0 01-3-3h6a3 3 0 01-3 3z" />
                      </svg>
                    </div>
                  )}
                  <span className="absolute top-2 left-2 px-2 py-1 text-xs font-medium bg-white/90 dark:bg-gray-800/90 rounded">
                    {getTypeLabel(product.productType)}
                  </span>
                  {product.stock >= 0 && product.stock < 10 && product.stock > 0 && (
                    <span className="absolute top-2 right-2 px-2 py-1 text-xs font-medium bg-red-500 text-white rounded">
                      仅剩 {product.stock} 件
                    </span>
                  )}
                </div>

                {/* 商品信息 */}
                <div className="flex-1 p-4">
                  <h3 className="font-medium text-gray-900 dark:text-gray-100 mb-1">{product.name}</h3>
                  <p className="text-sm text-gray-500 dark:text-gray-400 line-clamp-2 mb-3">
                    {product.description}
                  </p>

                  <div className="flex items-center justify-between">
                    <div className="flex items-baseline gap-1">
                      <span className="text-xl font-bold text-yellow-600">
                        {product.pointsRequired.toLocaleString()}
                      </span>
                      <span className="text-sm text-gray-500">积分</span>
                    </div>

                    <button
                      onClick={() => handleExchange(product)}
                      disabled={
                        exchangeMutation.isPending ||
                        product.stock === 0 ||
                        (balance !== undefined && balance.balance < product.pointsRequired)
                      }
                      className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                        product.stock === 0
                          ? 'bg-gray-100 text-gray-400 cursor-not-allowed'
                          : balance !== undefined && balance.balance < product.pointsRequired
                            ? 'bg-gray-100 text-gray-400 cursor-not-allowed'
                            : 'bg-blue-600 text-white hover:bg-blue-700'
                      }`}
                    >
                      {exchangeMutation.isPending && confirmProduct?.id === product.id
                        ? '兑换中...'
                        : product.stock === 0
                          ? '已售罄'
                          : balance !== undefined && balance.balance < product.pointsRequired
                            ? '积分不足'
                            : '立即兑换'
                      }
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>

          {/* 分页 */}
          {totalProducts > pagination.pageSize && (
            <Pagination
              currentPage={pagination.page}
              totalPages={Math.ceil(totalProducts / pagination.pageSize)}
              total={totalProducts}
              onChange={(newPage: number) => {
                pagination.goToPage(newPage);
              }}
              showTotal
            />
          )}
        </>
      )}

      {/* 兑换确认弹窗 */}
      <ExchangeConfirmDialog
        isOpen={!!confirmProduct}
        product={confirmProduct}
        currentBalance={balance?.balance ?? 0}
        onConfirm={handleConfirmExchange}
        onCancel={() => setConfirmProduct(null)}
      />

      {/* 兑换成功弹窗 */}
      <ExchangeSuccess
        isOpen={showSuccess}
        order={exchangeOrder}
        onClose={handleCloseSuccess}
        onContinue={handleCloseSuccess}
      />
    </div>
  );
}

export default PointsMall;