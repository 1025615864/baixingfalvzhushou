/**
 * PointsBalance - 积分余额显示组件
 *
 * 支持多种展示变体：default、inline、compact、detailed
 */

import { useEffect, useState, useMemo } from 'react';

import { Skeleton } from '../../../components/ui/Skeleton';

/**
 * 积分余额组件变体类型
 */
type PointsBalanceVariant = 'default' | 'inline' | 'compact' | 'detailed';

/**
 * 积分余额组件属性接口
 */
export interface PointsBalanceProps {
  /** 当前积分余额 */
  balance?: number;
  /** 变体类型 */
  variant?: PointsBalanceVariant;
  /** 今日获得积分（detailed变体使用） */
  todayEarned?: number;
  /** 连续签到天数（detailed变体使用） */
  continuousDays?: number;
  /** 加载状态 */
  isLoading?: boolean;
  /** 自定义样式类 */
  className?: string;
  /** 点击回调 */
  onClick?: () => void;
  /** 测试ID */
  'data-testid'?: string;
}

/**
 * 格式化数字，添加千分位分隔符
 */
function formatNumber(num: number | undefined | null): string {
  if (num === undefined || num === null) {
    return '0';
  }
  return num.toLocaleString('zh-CN');
}

/**
 * 积分图标组件
 */
function PointsIcon({ className = '' }: { className?: string }): JSX.Element {
  return (
    <svg
      className={className}
      fill="currentColor"
      viewBox="0 0 20 20"
      xmlns="http://www.w3.org/2000/svg"
    >
      <path d="M10 2a6 6 0 00-6 6v3.586l-.707.707A1 1 0 004 14h12a1 1 0 00.707-1.707L16 11.586V8a6 6 0 00-6-6zM10 18a3 3 0 01-3-3h6a3 3 0 01-3 3z" />
    </svg>
  );
}

/**
 * 火焰图标组件（用于连续签到）
 */
function FireIcon({ className = '' }: { className?: string }): JSX.Element {
  return (
    <svg
      className={className}
      fill="currentColor"
      viewBox="0 0 20 20"
      xmlns="http://www.w3.org/2000/svg"
    >
      <path
        fillRule="evenodd"
        d="M12.395 2.553a1 1 0 00-1.45-.385c-.345.23-.614.558-.822.88-.214.33-.403.713-.57 1.116-.334.804-.614 1.768-.84 2.734a31.365 31.365 0 00-.613 3.58 2.64 2.64 0 01-.945-1.067c-.328-.68-.398-1.534-.398-2.654A1 1 0 005.05 6.05 6.981 6.981 0 003 11a7 7 0 1011.95-4.95c-.592-.591-.98-.985-1.348-1.467-.363-.476-.724-1.063-1.207-2.03zM12.12 15.12A3 3 0 017 13s.879.5 2.5.5c0-1 .5-4 1.25-4.5.5 1 .786 1.293 1.371 1.879A2.99 2.99 0 0113 13a2.99 2.99 0 01-.879 2.121z"
        clipRule="evenodd"
      />
    </svg>
  );
}

/**
 * 向上箭头图标组件
 */
function TrendUpIcon({ className = '' }: { className?: string }): JSX.Element {
  return (
    <svg
      className={className}
      fill="none"
      stroke="currentColor"
      viewBox="0 0 24 24"
      xmlns="http://www.w3.org/2000/svg"
    >
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth={2}
        d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6"
      />
    </svg>
  );
}

/**
 * 带动画的数字组件
 */
function AnimatedNumber({ value, className = '' }: { value: number; className?: string }): JSX.Element {
  const [displayValue, setDisplayValue] = useState(value);

  useEffect(() => {
    const startValue = displayValue;
    const endValue = value;
    const duration = 500; // 动画持续时间（毫秒）
    const startTime = performance.now();

    const animate = (currentTime: number) => {
      const elapsed = currentTime - startTime;
      const progress = Math.min(elapsed / duration, 1);
      
      // 使用 easeOutQuart 缓动函数
      const easeProgress = 1 - Math.pow(1 - progress, 4);
      
      const currentValue = Math.round(startValue + (endValue - startValue) * easeProgress);
      setDisplayValue(currentValue);

      if (progress < 1) {
        requestAnimationFrame(animate);
      }
    };

    requestAnimationFrame(animate);
    // displayValue is intentionally excluded - animation uses internal state
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [value]);

  return <span className={className}>{formatNumber(displayValue)}</span>;
}

/**
 * 默认变体 - 卡片样式（较大展示）
 */
function DefaultVariant({
  balance,
  isLoading,
  className = '',
  onClick,
  'data-testid': dataTestId,
}: {
  balance: number;
  isLoading: boolean;
  className?: string;
  onClick?: () => void;
  'data-testid'?: string;
}): JSX.Element {
  if (isLoading) {
    return (
      <div className={`flex items-center gap-3 ${className}`} data-testid={dataTestId}>
        <Skeleton width={48} height={48} rounded="full" />
        <div className="flex flex-col gap-2">
          <Skeleton width={120} height={32} rounded="md" />
        </div>
      </div>
    );
  }

  return (
    <div
      className={`
        flex items-center gap-3 p-4
        bg-gradient-to-br from-yellow-50 to-amber-50
        dark:from-yellow-900/20 dark:to-amber-900/20
        rounded-xl border border-yellow-200 dark:border-yellow-800
        transition-all duration-200 hover:shadow-md
        ${onClick ? 'cursor-pointer' : ''}
        ${className}
      `}
      onClick={onClick}
      role={onClick ? 'button' : undefined}
      tabIndex={onClick ? 0 : undefined}
      data-testid={dataTestId}
    >
      {/* 积分图标 */}
      <div className="flex items-center justify-center w-12 h-12 bg-yellow-500 rounded-full shadow-lg shadow-yellow-500/30">
        <PointsIcon className="w-6 h-6 text-white" />
      </div>
      
      {/* 积分显示 */}
      <div className="flex flex-col">
        <span className="text-sm text-gray-500 dark:text-gray-400">我的积分</span>
        <div className="flex items-baseline gap-1">
          <AnimatedNumber
            value={balance}
            className="text-3xl font-bold text-yellow-600 dark:text-yellow-400"
          />
          <span className="text-sm text-gray-500 dark:text-gray-400">积分</span>
        </div>
      </div>
    </div>
  );
}

/**
 * 行内变体 - 用于导航栏
 */
function InlineVariant({
  balance,
  isLoading,
  className = '',
  onClick,
  'data-testid': dataTestId,
}: {
  balance: number;
  isLoading: boolean;
  className?: string;
  onClick?: () => void;
  'data-testid'?: string;
}): JSX.Element {
  if (isLoading) {
    return (
      <div className={`flex items-center gap-1.5 ${className}`} data-testid={dataTestId}>
        <Skeleton width={16} height={16} rounded="full" />
        <Skeleton width={60} height={16} rounded="sm" />
      </div>
    );
  }

  return (
    <div
      className={`
        inline-flex items-center gap-1.5 px-2 py-1
        bg-yellow-100/50 dark:bg-yellow-900/30
        rounded-full text-sm
        transition-colors duration-200
        ${onClick ? 'cursor-pointer hover:bg-yellow-100 dark:hover:bg-yellow-900/50' : ''}
        ${className}
      `}
      onClick={onClick}
      role={onClick ? 'button' : undefined}
      data-testid={dataTestId}
    >
      <span role="img" aria-label="积分">💰</span>
      <span className="font-medium text-yellow-700 dark:text-yellow-300 tabular-nums">
        {formatNumber(balance)}
      </span>
      <span className="text-yellow-600 dark:text-yellow-400">积分</span>
    </div>
  );
}

/**
 * 紧凑变体 - 用于小卡片
 */
function CompactVariant({
  balance,
  isLoading,
  className = '',
  onClick,
  'data-testid': dataTestId,
}: {
  balance: number;
  isLoading: boolean;
  className?: string;
  onClick?: () => void;
  'data-testid'?: string;
}): JSX.Element {
  if (isLoading) {
    return (
      <div className={`flex items-center gap-2 ${className}`} data-testid={dataTestId}>
        <Skeleton width={24} height={24} rounded="full" />
        <Skeleton width={80} height={24} rounded="md" />
      </div>
    );
  }

  return (
    <div
      className={`
        flex items-center gap-2
        transition-transform duration-200
        ${onClick ? 'cursor-pointer hover:scale-105' : ''}
        ${className}
      `}
      onClick={onClick}
      role={onClick ? 'button' : undefined}
      data-testid={dataTestId}
    >
      <div className="flex items-center justify-center w-8 h-8 bg-yellow-500 rounded-full">
        <PointsIcon className="w-4 h-4 text-white" />
      </div>
      <span className="text-xl font-bold text-gray-800 dark:text-gray-200 tabular-nums">
        {formatNumber(balance)}
      </span>
    </div>
  );
}

/**
 * 详细变体 - 用于个人中心
 */
function DetailedVariant({
  balance,
  todayEarned,
  continuousDays,
  isLoading,
  className = '',
  onClick,
  'data-testid': dataTestId,
}: {
  balance: number;
  todayEarned?: number;
  continuousDays?: number;
  isLoading: boolean;
  className?: string;
  onClick?: () => void;
  'data-testid'?: string;
}): JSX.Element {
  if (isLoading) {
    return (
      <div className={`space-y-4 ${className}`} data-testid={dataTestId}>
        <div className="flex items-center gap-3">
          <Skeleton width={56} height={56} rounded="full" />
          <div className="flex flex-col gap-2">
            <Skeleton width={150} height={36} rounded="md" />
            <Skeleton width={100} height={16} rounded="sm" />
          </div>
        </div>
        <div className="grid grid-cols-2 gap-3">
          <Skeleton width="100%" height={60} rounded="lg" />
          <Skeleton width="100%" height={60} rounded="lg" />
        </div>
      </div>
    );
  }

  return (
    <div
      className={`
        p-6 bg-gradient-to-br from-yellow-50 via-amber-50 to-orange-50
        dark:from-yellow-900/30 dark:via-amber-900/20 dark:to-orange-900/30
        rounded-2xl border border-yellow-200 dark:border-yellow-800/50
        shadow-lg shadow-yellow-500/10
        transition-all duration-300 hover:shadow-xl hover:shadow-yellow-500/20
        ${onClick ? 'cursor-pointer' : ''}
        ${className}
      `}
      onClick={onClick}
      role={onClick ? 'button' : undefined}
      data-testid={dataTestId}
    >
      {/* 主积分显示 */}
      <div className="flex items-center gap-4 mb-6">
        <div className="flex items-center justify-center w-14 h-14 bg-gradient-to-br from-yellow-400 to-amber-500 rounded-full shadow-lg shadow-yellow-500/30">
          <PointsIcon className="w-7 h-7 text-white" />
        </div>
        <div>
          <div className="flex items-baseline gap-2">
            <AnimatedNumber
              value={balance}
              className="text-4xl font-bold text-gray-800 dark:text-gray-100"
            />
            <span className="text-base text-gray-500 dark:text-gray-400">积分</span>
          </div>
          <span className="text-sm text-gray-400 dark:text-gray-500">当前可用余额</span>
        </div>
      </div>

      {/* 统计信息 */}
      <div className="grid grid-cols-2 gap-3">
        {/* 今日获得 */}
        <div className="flex items-center gap-3 p-3 bg-white/60 dark:bg-gray-800/60 rounded-xl">
          <div className="flex items-center justify-center w-10 h-10 bg-green-100 dark:bg-green-900/30 rounded-lg">
            <TrendUpIcon className="w-5 h-5 text-green-600 dark:text-green-400" />
          </div>
          <div>
            <div className="text-lg font-semibold text-gray-800 dark:text-gray-200">
              +{todayEarned !== undefined ? formatNumber(todayEarned) : '--'}
            </div>
            <div className="text-xs text-gray-500 dark:text-gray-400">今日获得</div>
          </div>
        </div>

        {/* 连续签到 */}
        <div className="flex items-center gap-3 p-3 bg-white/60 dark:bg-gray-800/60 rounded-xl">
          <div className="flex items-center justify-center w-10 h-10 bg-orange-100 dark:bg-orange-900/30 rounded-lg">
            <FireIcon className="w-5 h-5 text-orange-600 dark:text-orange-400" />
          </div>
          <div>
            <div className="text-lg font-semibold text-gray-800 dark:text-gray-200">
              {continuousDays !== undefined ? `${continuousDays}天` : '--'}
            </div>
            <div className="text-xs text-gray-500 dark:text-gray-400">连续签到</div>
          </div>
        </div>
      </div>
    </div>
  );
}

/**
 * 积分余额显示组件
 * 
 * 支持多种变体展示方式：
 * - default: 默认卡片样式（较大展示）
 * - inline: 行内展示（用于导航栏）
 * - compact: 紧凑版（用于小卡片）
 * - detailed: 详细版（用于个人中心）
 * 
 * @example
 * ```tsx
 * // 默认变体
 * <PointsBalance balance={1234} />
 * 
 * // 行内变体（导航栏）
 * <PointsBalance balance={1234} variant="inline" />
 * 
 * // 紧凑变体（小卡片）
 * <PointsBalance balance={1234} variant="compact" />
 * 
 * // 详细变体（个人中心）
 * <PointsBalance 
 *   balance={1234} 
 *   variant="detailed"
 *   todayEarned={50}
 *   continuousDays={7}
 * />
 * ```
 */
export function PointsBalance({
  balance = 0,
  variant = 'default',
  todayEarned,
  continuousDays,
  isLoading = false,
  className = '',
  onClick,
  'data-testid': dataTestId,
}: PointsBalanceProps): JSX.Element {
  // 使用 useMemo 缓存变体组件的 props
  const componentProps = useMemo(() => ({
    balance,
    isLoading,
    className,
    onClick,
    'data-testid': dataTestId,
  }), [balance, isLoading, className, onClick, dataTestId]);

  // 根据变体类型渲染对应组件
  switch (variant) {
    case 'inline':
      return <InlineVariant {...componentProps} />;

    case 'compact':
      return <CompactVariant {...componentProps} />;

    case 'detailed':
      return (
        <DetailedVariant
          {...componentProps}
          todayEarned={todayEarned}
          continuousDays={continuousDays}
        />
      );

    case 'default':
    default:
      return <DefaultVariant {...componentProps} />;
  }
}

// 导出变体类型和属性接口
export type { PointsBalanceVariant };
export default PointsBalance;
