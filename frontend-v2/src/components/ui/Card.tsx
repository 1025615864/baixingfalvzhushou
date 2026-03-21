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
  onMouseEnter?: () => void;
  onMouseLeave?: () => void;
}

export function Card({
  children,
  className = '',
  variant = 'default',
  padding = 'md',
  shadow = 'md',
  onClick,
  onMouseEnter,
  onMouseLeave,
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
      onMouseEnter={onMouseEnter}
      onMouseLeave={onMouseLeave}
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
}

export function CardTitle({ children, className = '' }: CardTitleProps): JSX.Element {
  return (
    <h3 className={`text-lg font-semibold text-slate-900 ${className}`}>
      {children}
    </h3>
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
    <div className={`mt-4 pt-4 border-t border-slate-100 ${className}`}>
      {children}
    </div>
  );
}

