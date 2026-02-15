/**
 * PointsBalanceInline - 行内积分余额展示组件
 * 
 * 紧凑的积分余额展示，适用于导航栏、头部等空间有限的场景
 */

import { usePointsBalance } from '../hooks/usePoints';
import { Skeleton } from '../../../components/ui/Skeleton';

interface PointsBalanceInlineProps {
  /** 是否显示图标 */
  showIcon?: boolean;
  /** 点击回调 */
  onClick?: () => void;
  /** 自定义类名 */
  className?: string;
  /** 尺寸：sm | md | lg */
  size?: 'sm' | 'md' | 'lg';
}

/**
 * 尺寸样式映射
 */
const sizeMap = {
  sm: {
    icon: 'w-4 h-4',
    text: 'text-sm',
    container: 'gap-1',
  },
  md: {
    icon: 'w-5 h-5',
    text: 'text-base',
    container: 'gap-1.5',
  },
  lg: {
    icon: 'w-6 h-6',
    text: 'text-lg',
    container: 'gap-2',
  },
};

/**
 * 行内积分余额展示组件
 * 
 * @example
 * ```tsx
 * // 导航栏中使用
 * <PointsBalanceInline size="sm" onClick={() => navigate('/points')} />
 * 
 * // 带点击效果
 * <PointsBalanceInline 
 *   size="md" 
 *   className="cursor-pointer hover:bg-gray-100 rounded-full px-3 py-1"
 *   onClick={() => setShowDetail(true)}
 * />
 * ```
 */
export function PointsBalanceInline({
  showIcon = true,
  onClick,
  className = '',
  size = 'md',
}: PointsBalanceInlineProps): JSX.Element {
  const { data: balance, isLoading } = usePointsBalance();
  const styles = sizeMap[size];

  if (isLoading) {
    return (
      <div className={`flex items-center ${styles.container} ${className}`}>
        {showIcon && (
          <Skeleton width={size === 'sm' ? 16 : size === 'md' ? 20 : 24} height={size === 'sm' ? 16 : size === 'md' ? 20 : 24} rounded="full" />
        )}
        <Skeleton width={50} height={size === 'sm' ? 14 : size === 'md' ? 16 : 18} rounded="sm" />
      </div>
    );
  }

  const displayBalance = balance?.balance ?? 0;

  return (
    <div
      className={`
        inline-flex items-center ${styles.container}
        text-yellow-600 font-medium
        ${onClick ? 'cursor-pointer' : ''}
        ${className}
      `}
      onClick={onClick}
      role={onClick ? 'button' : undefined}
      tabIndex={onClick ? 0 : undefined}
      onKeyDown={
        onClick
          ? (e) => {
              if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                onClick();
              }
            }
          : undefined
      }
    >
      {showIcon && (
        <svg
          className={styles.icon}
          fill="currentColor"
          viewBox="0 0 20 20"
          aria-hidden="true"
        >
          <path d="M10 2a6 6 0 00-6 6v3.586l-.707.707A1 1 0 004 14h12a1 1 0 00.707-1.707L16 11.586V8a6 6 0 00-6-6zM10 18a3 3 0 01-3-3h6a3 3 0 01-3 3z" />
        </svg>
      )}
      <span className={styles.text}>
        {displayBalance.toLocaleString()}
      </span>
    </div>
  );
}

export default PointsBalanceInline;