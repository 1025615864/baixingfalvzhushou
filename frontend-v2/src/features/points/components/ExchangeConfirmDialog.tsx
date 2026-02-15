/**
 * ExchangeConfirmDialog - 兑换确认弹窗组件
 *
 * 积分兑换前的确认对话框
 */

import { useState } from 'react';

import type { PointsProduct } from '../types';

interface ExchangeConfirmDialogProps {
  /** 是否显示 */
  isOpen: boolean;
  /** 商品信息 */
  product: PointsProduct | null;
  /** 当前积分余额 */
  currentBalance: number;
  /** 确认回调 */
  onConfirm: () => Promise<void>;
  /** 取消回调 */
  onCancel: () => void;
  /** 自定义类名 */
  className?: string;
}

/**
 * 兑换确认弹窗组件
 * 
 * @example
 * ```tsx
 * const [showDialog, setShowDialog] = useState(false);
 * const [selectedProduct, setSelectedProduct] = useState<PointsProduct | null>(null);
 * 
 * <ExchangeConfirmDialog
 *   isOpen={showDialog}
 *   product={selectedProduct}
 *   currentBalance={balance}
 *   onConfirm={async () => {
 *     await exchangeProduct(selectedProduct.id);
 *     setShowDialog(false);
 *   }}
 *   onCancel={() => setShowDialog(false)}
 * />
 * ```
 */
export function ExchangeConfirmDialog({
  isOpen,
  product,
  currentBalance,
  onConfirm,
  onCancel,
  className = '',
}: ExchangeConfirmDialogProps): JSX.Element | null {
  const [isSubmitting, setIsSubmitting] = useState(false);

  if (!isOpen || !product) return null;

  const isInsufficient = currentBalance < product.pointsRequired;
  const isOutOfStock = product.stock === 0;

  const handleConfirm = async (): Promise<void> => {
    if (isInsufficient || isOutOfStock || isSubmitting) return;

    setIsSubmitting(true);
    try {
      await onConfirm();
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      {/* 遮罩层 */}
      <div
        className="absolute inset-0 bg-black/50 backdrop-blur-sm"
        onClick={!isSubmitting ? onCancel : undefined}
      />

      {/* 弹窗内容 */}
      <div
        className={`
          relative w-full max-w-md bg-white dark:bg-gray-800 rounded-2xl shadow-2xl
          transform transition-all duration-300 scale-100
          ${className}
        `}
      >
        {/* 头部 */}
        <div className="flex items-center justify-between p-6 border-b border-gray-100 dark:border-gray-700">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
            确认兑换
          </h3>
          {!isSubmitting && (
            <button
              onClick={onCancel}
              className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 transition-colors"
              aria-label="关闭"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          )}
        </div>

        {/* 商品信息 */}
        <div className="p-6">
          <div className="flex gap-4 mb-6">
            {/* 商品图片 */}
            <div className="w-20 h-20 bg-gray-100 dark:bg-gray-700 rounded-lg overflow-hidden flex-shrink-0">
              {product.imageUrl ? (
                <img
                  src={product.imageUrl}
                  alt={product.name}
                  className="w-full h-full object-cover"
                />
              ) : (
                <div className="w-full h-full flex items-center justify-center text-gray-400">
                  <svg className="w-8 h-8" fill="currentColor" viewBox="0 0 20 20">
                    <path d="M10 2a6 6 0 00-6 6v3.586l-.707.707A1 1 0 004 14h12a1 1 0 00.707-1.707L16 11.586V8a6 6 0 00-6-6zM10 18a3 3 0 01-3-3h6a3 3 0 01-3 3z" />
                  </svg>
                </div>
              )}
            </div>

            {/* 商品详情 */}
            <div className="flex-1">
              <h4 className="font-medium text-gray-900 dark:text-gray-100 mb-1">
                {product.name}
              </h4>
              <p className="text-sm text-gray-500 dark:text-gray-400 line-clamp-2">
                {product.description}
              </p>
              <div className="mt-2 flex items-center gap-2">
                <span className="text-yellow-600 font-bold">
                  {product.pointsRequired.toLocaleString()} 积分
                </span>
                {product.stock >= 0 && product.stock < 10 && (
                  <span className="text-xs px-2 py-0.5 bg-red-100 text-red-600 rounded-full">
                    仅剩 {product.stock} 件
                  </span>
                )}
              </div>
            </div>
          </div>

          {/* 兑换信息 */}
          <div className="space-y-3 p-4 bg-gray-50 dark:bg-gray-700/50 rounded-lg">
            <div className="flex justify-between text-sm">
              <span className="text-gray-500 dark:text-gray-400">当前积分</span>
              <span className="font-medium text-gray-900 dark:text-gray-100">
                {currentBalance.toLocaleString()}
              </span>
            </div>
            <div className="flex justify-between text-sm">
              <span className="text-gray-500 dark:text-gray-400">兑换所需</span>
              <span className="font-medium text-yellow-600">
                -{product.pointsRequired.toLocaleString()}
              </span>
            </div>
            <div className="border-t border-gray-200 dark:border-gray-600 pt-3 flex justify-between">
              <span className="text-gray-700 dark:text-gray-300 font-medium">兑换后剩余</span>
              <span className={`font-bold ${currentBalance - product.pointsRequired >= 0 ? 'text-gray-900 dark:text-gray-100' : 'text-red-500'}`}>
                {(currentBalance - product.pointsRequired).toLocaleString()}
              </span>
            </div>
          </div>

          {/* 警告信息 */}
          {isInsufficient && (
            <div className="mt-4 p-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg flex items-center gap-2 text-sm text-red-600 dark:text-red-400">
              <svg className="w-5 h-5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              积分不足，无法兑换此商品
            </div>
          )}

          {isOutOfStock && (
            <div className="mt-4 p-3 bg-orange-50 dark:bg-orange-900/20 border border-orange-200 dark:border-orange-800 rounded-lg flex items-center gap-2 text-sm text-orange-600 dark:text-orange-400">
              <svg className="w-5 h-5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              该商品已售罄
            </div>
          )}
        </div>

        {/* 底部按钮 */}
        <div className="flex gap-3 p-6 pt-0">
          <button
            onClick={onCancel}
            disabled={isSubmitting}
            className="flex-1 px-4 py-2.5 border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 rounded-lg font-medium hover:bg-gray-50 dark:hover:bg-gray-700 disabled:opacity-50 transition-colors"
          >
            取消
          </button>
          <button
            onClick={() => void handleConfirm()}
            disabled={isInsufficient || isOutOfStock || isSubmitting}
            className={`
              flex-1 px-4 py-2.5 rounded-lg font-medium transition-all
              ${isInsufficient || isOutOfStock
                ? 'bg-gray-100 text-gray-400 cursor-not-allowed'
                : 'bg-yellow-500 text-white hover:bg-yellow-600 shadow-sm hover:shadow'
              }
            `}
          >
            {isSubmitting ? (
              <span className="flex items-center justify-center gap-2">
                <svg className="animate-spin w-4 h-4" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                </svg>
                兑换中...
              </span>
            ) : isInsufficient ? (
              '积分不足'
            ) : isOutOfStock ? (
              '已售罄'
            ) : (
              '确认兑换'
            )}
          </button>
        </div>
      </div>
    </div>
  );
}

export default ExchangeConfirmDialog;