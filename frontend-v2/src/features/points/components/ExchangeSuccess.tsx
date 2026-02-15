/**
 * ExchangeSuccess - 兑换成功提示组件
 * 
 * 积分兑换成功后的展示组件
 */

import { useEffect, useState } from 'react';

import type { ExchangeOrder } from '../types';

interface ExchangeSuccessProps {
  /** 是否显示 */
  isOpen: boolean;
  /** 订单信息 */
  order: ExchangeOrder | null;
  /** 关闭回调 */
  onClose: () => void;
  /** 查看订单回调 */
  onViewOrder?: () => void;
  /** 继续兑换回调 */
  onContinue?: () => void;
  /** 自定义类名 */
  className?: string;
}

/**
 * 兑换成功提示组件
 * 
 * @example
 * ```tsx
 * const [showSuccess, setShowSuccess] = useState(false);
 * const [order, setOrder] = useState<ExchangeOrder | null>(null);
 * 
 * <ExchangeSuccess
 *   isOpen={showSuccess}
 *   order={order}
 *   onClose={() => setShowSuccess(false)}
 *   onViewOrder={() => navigate('/points/orders')}
 *   onContinue={() => setShowSuccess(false)}
 * />
 * ```
 */
export function ExchangeSuccess({
  isOpen,
  order,
  onClose,
  onViewOrder,
  onContinue,
  className = '',
}: ExchangeSuccessProps): JSX.Element | null {
  const [showConfetti, setShowConfetti] = useState(false);

  useEffect(() => {
    if (isOpen) {
      setShowConfetti(true);
      const timer = setTimeout(() => setShowConfetti(false), 3000);
      return () => clearTimeout(timer);
    }
  }, [isOpen]);

  if (!isOpen || !order) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      {/* 遮罩层 */}
      <div
        className="absolute inset-0 bg-black/50 backdrop-blur-sm"
        onClick={onClose}
      />

      {/* 弹窗内容 */}
      <div
        className={`
          relative w-full max-w-md bg-white dark:bg-gray-800 rounded-2xl shadow-2xl
          transform transition-all duration-500 scale-100
          overflow-hidden
          ${className}
        `}
      >
        {/* 顶部装饰 */}
        <div className="relative h-32 bg-gradient-to-br from-yellow-400 via-yellow-500 to-orange-500 overflow-hidden">
          {/* 彩纸效果 */}
          {showConfetti && (
            <div className="absolute inset-0 pointer-events-none">
              {Array.from({ length: 20 }).map((_, i) => (
                <div
                  key={i}
                  className="absolute w-2 h-2 bg-white/80 rounded-full animate-ping"
                  style={{
                    left: `${Math.random() * 100}%`,
                    top: `${Math.random() * 100}%`,
                    animationDelay: `${Math.random() * 0.5}s`,
                    animationDuration: `${1 + Math.random()}s`,
                  }}
                />
              ))}
            </div>
          )}

          {/* 成功图标 */}
          <div className="absolute -bottom-8 left-1/2 transform -translate-x-1/2">
            <div className="w-16 h-16 bg-white dark:bg-gray-800 rounded-full flex items-center justify-center shadow-lg">
              <div className="w-12 h-12 bg-green-500 rounded-full flex items-center justify-center">
                <svg
                  className="w-7 h-7 text-white"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={3}
                    d="M5 13l4 4L19 7"
                  />
                </svg>
              </div>
            </div>
          </div>
        </div>

        {/* 内容区域 */}
        <div className="pt-12 pb-6 px-6 text-center">
          <h3 className="text-xl font-bold text-gray-900 dark:text-gray-100 mb-2">
            兑换成功！
          </h3>
          <p className="text-gray-500 dark:text-gray-400 mb-6">
            恭喜您成功兑换商品
          </p>

          {/* 订单信息 */}
          <div className="bg-gray-50 dark:bg-gray-700/50 rounded-xl p-4 mb-6">
            <div className="flex items-center gap-3 mb-4">
              <div className="w-12 h-12 bg-yellow-100 dark:bg-yellow-900/30 rounded-lg flex items-center justify-center">
                <svg
                  className="w-6 h-6 text-yellow-600"
                  fill="currentColor"
                  viewBox="0 0 20 20"
                >
                  <path d="M10 2a6 6 0 00-6 6v3.586l-.707.707A1 1 0 004 14h12a1 1 0 00.707-1.707L16 11.586V8a6 6 0 00-6-6zM10 18a3 3 0 01-3-3h6a3 3 0 01-3 3z" />
                </svg>
              </div>
              <div className="text-left">
                <div className="font-medium text-gray-900 dark:text-gray-100">
                  {order.productName}
                </div>
                <div className="text-sm text-gray-500 dark:text-gray-400">
                  订单号：{order.id.slice(-8)}
                </div>
              </div>
            </div>

            <div className="space-y-2 text-sm">
              <div className="flex justify-between">
                <span className="text-gray-500 dark:text-gray-400">消耗积分</span>
                <span className="font-medium text-yellow-600">
                  -{order.pointsSpent.toLocaleString()}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-500 dark:text-gray-400">订单状态</span>
                <span className="font-medium text-green-600">兑换成功</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-500 dark:text-gray-400">兑换时间</span>
                <span className="text-gray-700 dark:text-gray-300">
                  {new Date(order.createdAt).toLocaleString('zh-CN')}
                </span>
              </div>
            </div>
          </div>

          {/* 按钮组 */}
          <div className="flex gap-3">
            {onContinue && (
              <button
                onClick={onContinue}
                className="flex-1 px-4 py-2.5 border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 rounded-lg font-medium hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
              >
                继续兑换
              </button>
            )}
            {onViewOrder ? (
              <button
                onClick={onViewOrder}
                className="flex-1 px-4 py-2.5 bg-yellow-500 text-white rounded-lg font-medium hover:bg-yellow-600 transition-colors shadow-sm"
              >
                查看订单
              </button>
            ) : (
              <button
                onClick={onClose}
                className="flex-1 px-4 py-2.5 bg-yellow-500 text-white rounded-lg font-medium hover:bg-yellow-600 transition-colors shadow-sm"
              >
                我知道了
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

/**
 * 简单的兑换成功提示（非弹窗）
 */
export function ExchangeSuccessInline({
  order,
  className = '',
}: {
  order: ExchangeOrder;
  className?: string;
}): JSX.Element {
  return (
    <div
      className={`
        flex items-center gap-3 p-4 bg-green-50 dark:bg-green-900/20 
        border border-green-200 dark:border-green-800 rounded-lg
        ${className}
      `}
    >
      <div className="w-10 h-10 bg-green-500 rounded-full flex items-center justify-center flex-shrink-0">
        <svg
          className="w-5 h-5 text-white"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M5 13l4 4L19 7"
          />
        </svg>
      </div>
      <div>
        <div className="font-medium text-green-800 dark:text-green-200">
          兑换成功！
        </div>
        <div className="text-sm text-green-600 dark:text-green-300">
          {order.productName} · 消耗 {order.pointsSpent} 积分
        </div>
      </div>
    </div>
  );
}

export default ExchangeSuccess;