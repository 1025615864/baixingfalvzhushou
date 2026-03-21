import React from 'react';
import { motion } from 'framer-motion';

export interface MotionCardProps {
  children: React.ReactNode;
  className?: string;
  variant?: 'default' | 'hover' | 'interactive';
  padding?: 'none' | 'sm' | 'md' | 'lg' | 'xl';
  shadow?: 'none' | 'sm' | 'md' | 'lg';
  onClick?: () => void;
  /**
   * 初始动画状态
   * @default false
   */
  initial?: boolean;
  /**
   * 动画延迟 (秒)
   * @default 0
   */
  delay?: number;
}

/**
 * MotionCard 动画卡片组件
 * 提供流畅的入场动画和交互效果
 */
export function MotionCard({
  children,
  className = '',
  variant = 'default',
  padding = 'md',
  shadow = 'md',
  onClick,
  initial = false,
  delay = 0,
}: MotionCardProps): JSX.Element {
  const baseStyles = 'bg-white rounded-2xl overflow-hidden';

  const variantStyles = {
    default: 'border border-slate-100 shadow-soft',
    hover: 'border border-slate-100 shadow-soft cursor-pointer',
    interactive: 'border border-slate-100 shadow-soft cursor-pointer',
    flat: 'border border-slate-200',
    outline: 'border-2 border-slate-200',
  };

  const paddingStyles = {
    none: '',
    sm: 'p-4',
    md: 'p-6',
    lg: 'p-8',
    xl: 'p-10',
  };

  const shadowStyles = {
    none: '',
    sm: 'shadow-sm',
    md: 'shadow-soft',
    lg: 'shadow-soft-lg',
  };

  return (
    <motion.div
      className={`
        ${baseStyles}
        ${variantStyles[variant]}
        ${paddingStyles[padding]}
        ${shadowStyles[shadow]}
        ${className}
      `}
      onClick={onClick}
      role={onClick ? 'button' : undefined}
      tabIndex={onClick ? 0 : undefined}
      initial={initial ? { opacity: 0, y: 20 } : false}
      animate={{ opacity: 1, y: 0 }}
      whileHover={variant !== 'default' ? {
        y: -4,
        boxShadow: '0 20px 40px -12px rgba(0, 0, 0, 0.15)',
        borderColor: 'rgba(51, 102, 255, 0.3)',
      } : undefined}
      whileTap={onClick ? { scale: 0.98 } : undefined}
      transition={{
        duration: 0.3,
        delay,
        ease: 'easeOut',
      }}
    >
      {children}
    </motion.div>
  );
}

export interface FeatureCardProps {
  icon: React.ReactNode;
  title: string;
  description: string;
  onClick?: () => void;
  className?: string;
  delay?: number;
}

/**
 * FeatureCard 功能卡片组件
 * 带图标的功能介绍卡片，带入场动画
 */
export function FeatureCard({
  icon,
  title,
  description,
  onClick,
  className = '',
  delay = 0,
}: FeatureCardProps): JSX.Element {
  return (
    <MotionCard
      variant="interactive"
      padding="lg"
      className={className}
      onClick={onClick}
      delay={delay}
    >
      <div className="flex flex-col items-center text-center">
        <div className="w-14 h-14 rounded-2xl bg-primary-50 text-primary-600 flex items-center justify-center mb-4">
          {icon}
        </div>
        <h3 className="text-lg font-semibold text-slate-900 mb-2">
          {title}
        </h3>
        <p className="text-slate-500 text-sm leading-relaxed">
          {description}
        </p>
      </div>
    </MotionCard>
  );
}

export interface StatCardProps {
  icon: React.ReactNode;
  value: string | number;
  label: string;
  trend?: {
    value: number;
    isPositive: boolean;
  };
  className?: string;
  delay?: number;
}

/**
 * StatCard 统计卡片组件
 * 用于展示关键数据指标
 */
export function StatCard({
  icon,
  value,
  label,
  trend,
  className = '',
  delay = 0,
}: StatCardProps): JSX.Element {
  return (
    <MotionCard padding="lg" className={className} delay={delay}>
      <div className="flex items-start justify-between">
        <div className="w-12 h-12 rounded-xl bg-primary-50 text-primary-600 flex items-center justify-center">
          {icon}
        </div>
        {trend && (
          <div className={`flex items-center gap-1 text-sm font-medium ${
            trend.isPositive ? 'text-green-600' : 'text-red-600'
          }`}>
            <span>{trend.isPositive ? '↑' : '↓'}</span>
            <span>{Math.abs(trend.value)}%</span>
          </div>
        )}
      </div>
      <div className="mt-4">
        <div className="text-3xl font-bold text-slate-900">
          {value}
        </div>
        <div className="text-sm text-slate-500 mt-1">
          {label}
        </div>
      </div>
    </MotionCard>
  );
}
