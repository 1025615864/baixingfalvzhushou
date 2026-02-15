/**
 * CheckInSuccessAnimation - 签到成功动画组件
 * 功能：签到成功时的彩纸动画效果 + 浮动数字动画
 */
/* eslint-disable react-refresh/only-export-components */

import { useEffect, useState, useCallback } from 'react';

interface CheckInSuccessAnimationProps {
  /** 触发动画的积分值 */
  points: number;
  /** 动画触发状态 */
  isAnimating: boolean;
  /** 动画位置 */
  position?: { x: number; y: number };
  /** 动画完成回调 */
  onComplete?: () => void;
  className?: string;
}

/**
 * 彩纸粒子
 */
interface ConfettiParticle {
  id: number;
  x: number;
  y: number;
  rotation: number;
  color: string;
  size: number;
  velocityX: number;
  velocityY: number;
  opacity: number;
}

/**
 * 签到成功动画组件
 */
export function CheckInSuccessAnimation({
  points,
  isAnimating,
  position,
  onComplete,
  className = '',
}: CheckInSuccessAnimationProps): JSX.Element {
  const [particles, setParticles] = useState<ConfettiParticle[]>([]);
  const [showFloatingText, setShowFloatingText] = useState(false);
  const [floatingPosition, setFloatingPosition] = useState({ x: 0, y: 0 });

  /**
   * 生成随机颜色
   */
  const getRandomColor = useCallback((): string => {
    const colors = [
      '#FFD700', // 金色
      '#FF6B6B', // 红色
      '#4ECDC4', // 青色
      '#45B7D1', // 蓝色
      '#96CEB4', // 绿色
      '#FFEAA7', // 黄色
      '#DDA0DD', // 紫色
      '#FF8C94', // 粉色
    ];
    return colors[Math.floor(Math.random() * colors.length)];
  }, []);

  /**
   * 初始化彩纸粒子
   */
  const initParticles = useCallback((centerX: number, centerY: number): ConfettiParticle[] => {
    const particleCount = 30;
    return Array.from({ length: particleCount }, (_, i) => ({
      id: i,
      x: centerX,
      y: centerY,
      rotation: Math.random() * 360,
      color: getRandomColor(),
      size: Math.random() * 8 + 4,
      velocityX: (Math.random() - 0.5) * 400,
      velocityY: (Math.random() - 1) * 600 - 100,
      opacity: 1,
    }));
  }, [getRandomColor]);

  /**
   * 动画帧更新
   */
  useEffect(() => {
    if (!isAnimating) return;

    const centerX = position?.x ?? window.innerWidth / 2;
    const centerY = position?.y ?? window.innerHeight / 2;

    // 初始化粒子
    setParticles(initParticles(centerX, centerY));
    setFloatingPosition({ x: centerX, y: centerY - 50 });
    setShowFloatingText(true);

    let animationId: number;
    const startTime = Date.now();

    const animate = () => {
      const elapsed = Date.now() - startTime;

      setParticles((prev) =>
        prev.map((particle) => {
          const t = elapsed / 1000; // 转换为秒
          const gravity = 500;
          const friction = 0.99;

          return {
            ...particle,
            x: particle.x + particle.velocityX * 0.016,
            y: particle.y + particle.velocityY * 0.016 + gravity * t * t * 0.5,
            rotation: particle.rotation + particle.velocityX * 0.1,
            velocityX: particle.velocityX * friction,
            velocityY: particle.velocityY + gravity * 0.016,
            opacity: Math.max(0, 1 - elapsed / 2000),
          };
        })
      );

      if (elapsed < 2000) {
        animationId = requestAnimationFrame(animate);
      } else {
        setParticles([]);
        setShowFloatingText(false);
        onComplete?.();
      }
    };

    animationId = requestAnimationFrame(animate);

    // 隐藏浮动文字
    const textTimer = setTimeout(() => {
      setShowFloatingText(false);
    }, 1500);

    return () => {
      cancelAnimationFrame(animationId);
      clearTimeout(textTimer);
    };
  }, [isAnimating, position, initParticles, onComplete]);

  if (!isAnimating && particles.length === 0 && !showFloatingText) {
    return <></>;
  }

  return (
    <div className={`fixed inset-0 pointer-events-none z-50 ${className}`}>
      {/* 彩纸粒子 */}
      {particles.map((particle) => (
        <div
          key={particle.id}
          className="absolute rounded-sm"
          style={{
            left: `${particle.x}px`,
            top: `${particle.y}px`,
            width: `${particle.size}px`,
            height: `${particle.size * 0.6}px`,
            backgroundColor: particle.color,
            transform: `rotate(${particle.rotation}deg)`,
            opacity: particle.opacity,
            transition: 'none',
          }}
        />
      ))}

      {/* 浮动积分文字 */}
      {showFloatingText && (
        <div
          className="absolute transform -translate-x-1/2 -translate-y-1/2 animate-float-up"
          style={{
            left: `${floatingPosition.x}px`,
            top: `${floatingPosition.y}px`,
          }}
        >
          <div className="flex items-center gap-1 text-3xl font-bold text-yellow-500 drop-shadow-lg">
            <span>+</span>
            <span>{points}</span>
            <span className="text-lg">积分</span>
          </div>
        </div>
      )}

      <style>{`
        @keyframes float-up {
          0% {
            opacity: 1;
            transform: translate(-50%, -50%) translateY(0) scale(1);
          }
          100% {
            opacity: 0;
            transform: translate(-50%, -50%) translateY(-100px) scale(1.2);
          }
        }
        .animate-float-up {
          animation: float-up 1.5s ease-out forwards;
        }
      `}</style>
    </div>
  );
}

/**
 * 签到成功动画触发器 Hook
 */
export function useCheckInSuccessAnimation() {
  const [animationState, setAnimationState] = useState<{
    isAnimating: boolean;
    points: number;
    position?: { x: number; y: number };
  }>({
    isAnimating: false,
    points: 0,
  });

  const triggerAnimation = useCallback(
    (points: number, position?: { x: number; y: number }) => {
      setAnimationState({
        isAnimating: true,
        points,
        position,
      });
    },
    []
  );

  const handleComplete = useCallback(() => {
    setAnimationState((prev) => ({ ...prev, isAnimating: false }));
  }, []);

  return {
    animationState,
    triggerAnimation,
    handleComplete,
  };
}