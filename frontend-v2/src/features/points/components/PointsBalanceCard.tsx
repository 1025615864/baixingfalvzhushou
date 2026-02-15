/**
 * PointsBalanceCard - 卡片式积分余额展示组件
 *
 * 带有背景装饰的积分余额卡片，适用于积分中心首页
 */

import { usePointsBalance } from '../hooks/usePoints';
import { Skeleton } from '../../../components/ui/Skeleton';
import { EmptyState } from '../../../components/ui/EmptyState';

interface PointsBalanceCardProps {
  /** 点击签到回调 */
  onCheckIn?: () => void;
  /** 点击兑换回调 */
  onExchange?: () => void;
  /** 自定义类名 */
  className?: string;
  /** 是否显示操作按钮 */
  showActions?: boolean;
}

/**
 * 卡片式积分余额展示组件
 * 
 * @example
 * ```tsx
 * // 基本使用
 * <PointsBalanceCard />
 * 
 * // 带操作按钮
 * <PointsBalanceCard 
 *   showActions 
 *   onCheckIn={() => handleCheckIn()}
 *   onExchange={() => navigate('/points/mall')}
 * />
 * ```
 */
export function PointsBalanceCard({
  onCheckIn,
  onExchange,
  className = '',
  showActions = true,
}: PointsBalanceCardProps): JSX.Element {
  const { data: balance, isLoading, error, refetch } = usePointsBalance();

  if (isLoading) {
    return (
      <div className={`relative overflow-hidden bg-gradient-to-br from-yellow-400 via-yellow-500 to-orange-500 rounded-2xl p-6 ${className}`}>
        <div className="relative z-10">
          <Skeleton width={80} height={16} className="bg-white/30 mb-4" />
          <Skeleton width={120} height={48} className="bg-white/30 mb-2" />
          <Skeleton width={100} height={14} className="bg-white/30" />
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className={`bg-gray-50 rounded-2xl p-6 ${className}`}>
        <EmptyState
          icon="error"
          title="加载失败"
          description="无法获取积分信息"
          action={
            <button
              onClick={() => void refetch()}
              className="px-4 py-2 text-sm font-medium text-blue-600 bg-blue-50 rounded-lg hover:bg-blue-100"
            >
              重新加载
            </button>
          }
          compact
        />
      </div>
    );
  }

  const currentBalance = balance?.balance ?? 0;
  const continuousDays = balance?.continuousDays ?? 0;

  return (
    <div className={`relative overflow-hidden bg-gradient-to-br from-yellow-400 via-yellow-500 to-orange-500 rounded-2xl p-6 text-white ${className}`}>
      {/* 装饰背景 */}
      <div className="absolute top-0 right-0 -mt-4 -mr-4 w-32 h-32 bg-white/10 rounded-full blur-2xl" />
      <div className="absolute bottom-0 left-0 -mb-4 -ml-4 w-24 h-24 bg-white/10 rounded-full blur-xl" />
      
      {/* 积分图标装饰 */}
      <div className="absolute top-4 right-4 opacity-20">
        <svg className="w-24 h-24" fill="currentColor" viewBox="0 0 20 20">
          <path d="M10 2a6 6 0 00-6 6v3.586l-.707.707A1 1 0 004 14h12a1 1 0 00.707-1.707L16 11.586V8a6 6 0 00-6-6zM10 18a3 3 0 01-3-3h6a3 3 0 01-3 3z" />
        </svg>
      </div>

      <div className="relative z-10">
        {/* 标签 */}
        <div className="flex items-center gap-2 mb-2">
          <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
            <path d="M10 2a6 6 0 00-6 6v3.586l-.707.707A1 1 0 004 14h12a1 1 0 00.707-1.707L16 11.586V8a6 6 0 00-6-6zM10 18a3 3 0 01-3-3h6a3 3 0 01-3 3z" />
          </svg>
          <span className="text-yellow-100 font-medium">我的积分</span>
        </div>

        {/* 积分余额 */}
        <div className="mb-4">
          <div className="text-4xl font-bold mb-1">
            {currentBalance.toLocaleString()}
          </div>
          <div className="text-yellow-100 text-sm">
            可用积分
          </div>
        </div>

        {/* 连续签到 */}
        {continuousDays > 0 && (
          <div className="flex items-center gap-1 text-sm text-yellow-100 mb-4">
            <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
            </svg>
            <span>连续签到 {continuousDays} 天</span>
          </div>
        )}

        {/* 操作按钮 */}
        {showActions && (
          <div className="flex gap-3">
            {onCheckIn && (
              <button
                onClick={onCheckIn}
                className="flex-1 px-4 py-2 bg-white text-yellow-600 rounded-lg font-medium hover:bg-yellow-50 transition-colors shadow-sm"
              >
                每日签到
              </button>
            )}
            {onExchange && (
              <button
                onClick={onExchange}
                className="flex-1 px-4 py-2 bg-yellow-600/50 text-white border border-yellow-400 rounded-lg font-medium hover:bg-yellow-600/70 transition-colors"
              >
                积分兑换
              </button>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

export default PointsBalanceCard;