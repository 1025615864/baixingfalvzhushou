/**
 * Button 组件
 * 美化后的按钮组件，支持多种变体、尺寸和状态
 */

import React from 'react';
import { Loader2 } from 'lucide-react';

export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'accent' | 'outline' | 'ghost' | 'white' | 'danger';
  size?: 'sm' | 'md' | 'lg' | 'xl';
  isLoading?: boolean;
  leftIcon?: React.ReactNode;
  rightIcon?: React.ReactNode;
  fullWidth?: boolean;
  children: React.ReactNode;
}

export function Button({
  children,
  variant = 'primary',
  size = 'md',
  isLoading = false,
  leftIcon,
  rightIcon,
  fullWidth = false,
  className = '',
  disabled,
  ...props
}: ButtonProps): JSX.Element {
  const baseStyles = 'inline-flex items-center justify-center font-semibold rounded-xl transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed active:scale-[0.98]';

  const variantStyles = {
    primary: 'bg-primary-600 text-white hover:bg-primary-700 hover:shadow-lg hover:shadow-primary-500/30 focus:ring-primary-500',
    secondary: 'bg-secondary-500 text-white hover:bg-secondary-600 hover:shadow-lg hover:shadow-secondary-500/30 focus:ring-secondary-500',
    accent: 'bg-accent-500 text-white hover:bg-accent-600 hover:shadow-lg hover:shadow-accent-500/30 focus:ring-accent-500',
    outline: 'border-2 border-primary-600 text-primary-600 hover:bg-primary-50 hover:border-primary-700 hover:text-primary-700 focus:ring-primary-500 bg-transparent',
    ghost: 'text-slate-600 hover:bg-slate-100 hover:text-slate-900 focus:ring-slate-500 bg-transparent',
    white: 'bg-white text-primary-600 hover:bg-primary-50 focus:ring-white shadow-lg shadow-black/10',
    danger: 'bg-red-600 text-white hover:bg-red-700 hover:shadow-lg hover:shadow-red-500/30 focus:ring-red-500',
  };

  const sizeStyles = {
    sm: 'px-3 py-1.5 text-sm gap-1.5',
    md: 'px-4 py-2.5 text-sm gap-2',
    lg: 'px-6 py-3 text-base gap-2',
    xl: 'px-8 py-4 text-lg gap-3',
  };

  const iconSizes = {
    sm: 'w-4 h-4',
    md: 'w-4 h-4',
    lg: 'w-5 h-5',
    xl: 'w-6 h-6',
  };

  return (
    <button
      className={`
        ${baseStyles}
        ${variantStyles[variant]}
        ${sizeStyles[size]}
        ${fullWidth ? 'w-full' : ''}
        ${className}
      `}
      disabled={disabled || isLoading}
      {...props}
    >
      {isLoading && (
        <Loader2 className={`${iconSizes[size]} animate-spin`} />
      )}
      {!isLoading && leftIcon && (
        <span className="flex-shrink-0">{leftIcon}</span>
      )}
      <span>{children}</span>
      {!isLoading && rightIcon && (
        <span className="flex-shrink-0">{rightIcon}</span>
      )}
    </button>
  );
}

// 图标按钮
export interface IconButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'accent' | 'ghost' | 'white';
  size?: 'sm' | 'md' | 'lg';
  isLoading?: boolean;
  children: React.ReactNode;
}

export function IconButton({
  children,
  variant = 'ghost',
  size = 'md',
  isLoading = false,
  className = '',
  disabled,
  ...props
}: IconButtonProps): JSX.Element {
  const baseStyles = 'inline-flex items-center justify-center rounded-xl transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed active:scale-[0.98]';

  const variantStyles = {
    primary: 'bg-primary-600 text-white hover:bg-primary-700 hover:shadow-lg hover:shadow-primary-500/30 focus:ring-primary-500',
    secondary: 'bg-secondary-500 text-white hover:bg-secondary-600 hover:shadow-lg hover:shadow-secondary-500/30 focus:ring-secondary-500',
    accent: 'bg-accent-500 text-white hover:bg-accent-600 hover:shadow-lg hover:shadow-accent-500/30 focus:ring-accent-500',
    ghost: 'text-slate-600 hover:bg-slate-100 hover:text-slate-900 focus:ring-slate-500',
    white: 'bg-white text-slate-700 hover:bg-slate-50 focus:ring-slate-500 shadow-sm',
  };

  const sizeStyles = {
    sm: 'w-8 h-8',
    md: 'w-10 h-10',
    lg: 'w-12 h-12',
  };

  const iconSizes = {
    sm: 'w-4 h-4',
    md: 'w-5 h-5',
    lg: 'w-6 h-6',
  };

  return (
    <button
      className={`
        ${baseStyles}
        ${variantStyles[variant]}
        ${sizeStyles[size]}
        ${className}
      `}
      disabled={disabled || isLoading}
      {...props}
    >
      {isLoading ? (
        <Loader2 className={`${iconSizes[size]} animate-spin`} />
      ) : (
        <span className={iconSizes[size]}>{children}</span>
      )}
    </button>
  );
}
