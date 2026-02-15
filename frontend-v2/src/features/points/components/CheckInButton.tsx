/**
 * CheckInButton - 独立签到按钮组件
 * 功能：可嵌入其他页面的签到按钮
 * 显示连续签到天数和动画效果
 */

import { useState, useEffect, useCallback } from 'react';

import { useCheckIn } from '../hooks/usePoints';

import { CheckInSuccessAnimation } from './CheckInSuccessAnimation';

interface CheckInButtonProps {
  /** 连续签到天数 */
  continuousDays?: number;
  /** 今日是否已签到 */
  hasCheckedIn?: boolean;
  /** 签到成功回调 */
  onCheckInSuccess?: (points: number, days: number) => void;
  /** 按钮尺寸 */
  size?: 'sm' | 'md' | 'lg';
  /** 是否显示动画 */
  showAnimation?: boolean;
  className?: string;
  /** 测试ID */
  'data-testid'?: string;
}

/**
 * 独立签到按钮组件
 */
export function CheckInButton({
  continuousDays = 0,
  hasCheckedIn: initialHasCheckedIn = false,
  onCheckInSuccess,
  size = 'md',
  showAnimation = true,
  className = '',
  'data-testid': dataTestId,
}: CheckInButtonProps): JSX.Element {
  const [hasCheckedIn, setHasCheckedIn] = useState(initialHasCheckedIn);
  const [days, setDays] = useState(continuousDays);
  const [isAnimating, setIsAnimating] = useState(false);
  const [earnedPoints, setEarnedPoints] = useState(0);
  const [buttonPosition, setButtonPosition] = useState<{ x: number; y: number }>();
  
  const buttonRef = useCallback((node: HTMLButtonElement | null) => {
    if (node) {
      const rect = node.getBoundingClientRect();
      setButtonPosition({
        x: rect.left + rect.width / 2,
        y: rect.top + rect.height / 2,
      });
    }
  }, []);

  const checkInMutation = useCheckIn();

  // 同步外部状态
  useEffect(() => {
    setHasCheckedIn(initialHasCheckedIn);
  }, [initialHasCheckedIn]);

  useEffect(() => {
    setDays(continuousDays);
  }, [continuousDays]);

  /**
   * 处理签到
   */
  const handleCheckIn = async () => {
    if (hasCheckedIn || checkInMutation.isPending) return;

    try {
      const result = await checkInMutation.mutateAsync();
      
      // 更新状态
      setHasCheckedIn(true);
      setDays(result.continuousDays);
      setEarnedPoints(result.pointsEarned);
      
      // 触发动画
      if (showAnimation) {
        setIsAnimating(true);
      }
      
      // 回调
      onCheckInSuccess?.(result.pointsEarned, result.continuousDays);
    } catch (err) {
      // 错误处理
      console.error('签到失败:', err);
    }
  };

  /**
   * 动画完成回调
   */
  const handleAnimationComplete = useCallback(() => {
    setIsAnimating(false);
  }, []);

  // 尺寸样式
  const sizeStyles = {
    sm: 'px-3 py-1.5 text-sm',
    md: 'px-4 py-2 text-base',
    lg: 'px-6 py-3 text-lg',
  };

  // 图标尺寸
  const iconSizes = {
    sm: 'w-4 h-4',
    md: 'w-5 h-5',
    lg: 'w-6 h-6',
  };

  if (hasCheckedIn) {
    return (
      <>
        <div
          className={`inline-flex items-center gap-2 bg-green-100 text-green-700 rounded-full ${sizeStyles[size]} ${className}`}
        >
          <svg className={`${iconSizes[size]} text-green-500`} fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
          </svg>
          <span className="font-medium">已签到</span>
          <span className="text-green-600/70">·</span>
          <span>{days} 天</span>
        </div>
        
        {showAnimation && (
          <CheckInSuccessAnimation
            points={earnedPoints}
            isAnimating={isAnimating}
            position={buttonPosition}
            onComplete={handleAnimationComplete}
          />
        )}
      </>
    );
  }

  return (
    <>
      <button
        ref={buttonRef}
        onClick={() => void handleCheckIn()}
        disabled={checkInMutation.isPending}
        className={`
          inline-flex items-center gap-2 font-medium rounded-full
          bg-gradient-to-r from-amber-500 to-orange-500 text-white
          hover:from-amber-600 hover:to-orange-600
          active:scale-95 transition-all duration-200
          disabled:opacity-50 disabled:cursor-not-allowed
          shadow-lg hover:shadow-xl
          ${sizeStyles[size]}
          ${className}
        `}
        data-testid={dataTestId}
      >
        {checkInMutation.isPending ? (
          <>
            <svg className={`${iconSizes[size]} animate-spin`} fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
            </svg>
            <span>签到中...</span>
          </>
        ) : (
          <>
            <svg className={iconSizes[size]} fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v13m0-13V6a2 2 0 112 2h-2zm0 0V5.5A2.5 2.5 0 109.5 8H12zm-7 4h14M5 12a2 2 0 110-4h14a2 2 0 110 4M5 12v7a2 2 0 002 2h10a2 2 0 002-2v-7" />
            </svg>
            <span>签到</span>
            {days > 0 && (
              <span className="ml-1 px-1.5 py-0.5 bg-white/20 rounded text-xs">
                {days}天
              </span>
            )}
          </>
        )}
      </button>
      
      {showAnimation && (
        <CheckInSuccessAnimation
          points={earnedPoints}
          isAnimating={isAnimating}
          position={buttonPosition}
          onComplete={handleAnimationComplete}
        />
      )}
    </>
  );
}

/**
 * 紧凑版签到按钮（仅图标）
 */
export function CheckInButtonCompact({
  hasCheckedIn: initialHasCheckedIn = false,
  onCheckInSuccess,
  className = '',
  'data-testid': dataTestId,
}: Omit<CheckInButtonProps, 'size' | 'continuousDays' | 'showAnimation'> & { 'data-testid'?: string }): JSX.Element {
  const [hasCheckedIn, setHasCheckedIn] = useState(initialHasCheckedIn);
  const [isAnimating, setIsAnimating] = useState(false);
  const [earnedPoints, setEarnedPoints] = useState(0);
  const [buttonPosition, setButtonPosition] = useState<{ x: number; y: number }>();
  
  const buttonRef = useCallback((node: HTMLButtonElement | null) => {
    if (node) {
      const rect = node.getBoundingClientRect();
      setButtonPosition({
        x: rect.left + rect.width / 2,
        y: rect.top + rect.height / 2,
      });
    }
  }, []);

  const checkInMutation = useCheckIn();

  useEffect(() => {
    setHasCheckedIn(initialHasCheckedIn);
  }, [initialHasCheckedIn]);

  const handleCheckIn = async () => {
    if (hasCheckedIn || checkInMutation.isPending) return;

    try {
      const result = await checkInMutation.mutateAsync();
      setHasCheckedIn(true);
      setEarnedPoints(result.pointsEarned);
      setIsAnimating(true);
      onCheckInSuccess?.(result.pointsEarned, result.continuousDays);
    } catch (err) {
      console.error('签到失败:', err);
    }
  };

  const handleAnimationComplete = useCallback(() => {
    setIsAnimating(false);
  }, []);

  return (
    <>
      <button
        ref={buttonRef}
        onClick={() => void handleCheckIn()}
        disabled={hasCheckedIn || checkInMutation.isPending}
        className={`
          p-2 rounded-full transition-all duration-200
          ${hasCheckedIn
            ? 'bg-green-100 text-green-600'
            : 'bg-amber-100 text-amber-600 hover:bg-amber-200'
          }
          disabled:opacity-50 disabled:cursor-not-allowed
          ${className}
        `}
        title={hasCheckedIn ? '已签到' : '点击签到'}
        data-testid={dataTestId}
      >
        {checkInMutation.isPending ? (
          <svg className="w-5 h-5 animate-spin" fill="none" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
          </svg>
        ) : hasCheckedIn ? (
          <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
          </svg>
        ) : (
          <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v13m0-13V6a2 2 0 112 2h-2zm0 0V5.5A2.5 2.5 0 109.5 8H12zm-7 4h14M5 12a2 2 0 110-4h14a2 2 0 110 4M5 12v7a2 2 0 002 2h10a2 2 0 002-2v-7" />
          </svg>
        )}
      </button>
      
      <CheckInSuccessAnimation
        points={earnedPoints}
        isAnimating={isAnimating}
        position={buttonPosition}
        onComplete={handleAnimationComplete}
      />
    </>
  );
}