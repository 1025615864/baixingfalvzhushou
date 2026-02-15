/**
 * Card 组件
 * 美化后的卡片容器组件，支持多种变体和交互效果
 */

import React from 'react';

export interface CardProps {
  children: React.ReactNode;
  className?: string;
  variant?: 'default' | 'hover' | 'interactive' | 'flat' | 'outline';
  padding?: 'none' | 'sm' | 'md' | 'lg' | 'xl';
  shadow?: 'none' | 'sm' | 'md' | 'lg';
  onClick?: () => void;
}

export function Card({
  children,
  className = '',
  variant = 'default',
  padding = 'md',
  shadow = 'md',
  onClick,
}: CardProps): JSX.Element {
  const baseStyles = 'bg-white rounded-2xl overflow-hidden transition-all duration-300';

  const variantStyles = {
    default: 'border border-slate-100 shadow-soft',
    hover: 'border border-slate-100 shadow-soft hover:shadow-soft-lg hover:-translate-y-1 hover:border-primary-200 cursor-pointer',
    interactive: 'border border-slate-100 shadow-soft hover:shadow-soft-lg hover:-translate-y-1 hover:border-primary-200 cursor-pointer active:scale-[0.98]',
    flat: 'border border-slate-200',
    outline: 'border-2 border-slate-200 hover:border-primary-300',
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
    <div
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
    >
      {children}
    </div>
  );
}

// 卡片头部
export interface CardHeaderProps {
  children: React.ReactNode;
  className?: string;
}

export function CardHeader({ children, className = '' }: CardHeaderProps): JSX.Element {
  return (
    <div className={`mb-4 ${className}`}>
      {children}
    </div>
  );
}

// 卡片标题
export interface CardTitleProps {
  children: React.ReactNode;
  className?: string;
  as?: 'h1' | 'h2' | 'h3' | 'h4' | 'h5' | 'h6';
}

export function CardTitle({
  children,
  className = '',
  as: Component = 'h3',
}: CardTitleProps): JSX.Element {
  return (
    <Component className={`text-lg font-semibold text-slate-900 ${className}`}>
      {children}
    </Component>
  );
}

// 卡片描述
export interface CardDescriptionProps {
  children: React.ReactNode;
  className?: string;
}

export function CardDescription({ children, className = '' }: CardDescriptionProps): JSX.Element {
  return (
    <p className={`text-sm text-slate-500 mt-1 ${className}`}>
      {children}
    </p>
  );
}

// 卡片内容
export interface CardContentProps {
  children: React.ReactNode;
  className?: string;
}

export function CardContent({ children, className = '' }: CardContentProps): JSX.Element {
  return (
    <div className={className}>
      {children}
    </div>
  );
}

// 卡片底部
export interface CardFooterProps {
  children: React.ReactNode;
  className?: string;
}

export function CardFooter({ children, className = '' }: CardFooterProps): JSX.Element {
  return (
    <div className={`mt-4 pt-4 border-t border-slate-100 flex items-center gap-3 ${className}`}>
      {children}
    </div>
  );
}

// 特色卡片（带图标）
export interface FeatureCardProps {
  icon: React.ReactNode;
  title: string;
  description: string;
  className?: string;
  iconBgColor?: string;
  iconColor?: string;
  onClick?: () => void;
}

export function FeatureCard({
  icon,
  title,
  description,
  className = '',
  iconBgColor = 'bg-primary-100',
  iconColor = 'text-primary-600',
  onClick,
}: FeatureCardProps): JSX.Element {
  return (
    <Card
      variant={onClick ? 'interactive' : 'hover'}
      className={className}
      onClick={onClick}
    >
      <div className="flex items-start gap-4">
        <div className={`flex-shrink-0 w-12 h-12 ${iconBgColor} ${iconColor} rounded-xl flex items-center justify-center`}>
          {icon}
        </div>
        <div className="flex-1 min-w-0">
          <CardTitle className="text-base">{title}</CardTitle>
          <CardDescription className="mt-1">{description}</CardDescription>
        </div>
      </div>
    </Card>
  );
}

// 统计卡片
export interface StatCardProps {
  value: string | number;
  label: string;
  icon?: React.ReactNode;
  trend?: {
    value: number;
    isPositive: boolean;
  };
  className?: string;
}

export function StatCard({
  value,
  label,
  icon,
  trend,
  className = '',
}: StatCardProps): JSX.Element {
  return (
    <Card variant="default" className={className}>
      <div className="flex items-start justify-between">
        <div>
          <p className="text-2xl font-bold text-slate-900">{value}</p>
          <p className="text-sm text-slate-500 mt-1">{label}</p>
          {trend && (
            <div className={`flex items-center gap-1 mt-2 text-sm font-medium ${
              trend.isPositive ? 'text-green-600' : 'text-red-600'
            }`}>
              <span>{trend.isPositive ? '↑' : '↓'}</span>
              <span>{Math.abs(trend.value)}%</span>
            </div>
          )}
        </div>
        {icon && (
          <div className="flex-shrink-0 w-10 h-10 bg-primary-50 text-primary-600 rounded-lg flex items-center justify-center">
            {icon}
          </div>
        )}
      </div>
    </Card>
  );
}
