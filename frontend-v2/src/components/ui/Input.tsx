/**
 * Input 组件
 * 美化后的输入框组件，支持多种状态和变体
 */

import React, { forwardRef } from 'react';
import { Eye, EyeOff, AlertCircle, CheckCircle } from 'lucide-react';

export interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  helperText?: string;
  error?: string;
  success?: boolean;
  leftIcon?: React.ReactNode;
  rightIcon?: React.ReactNode;
  fullWidth?: boolean;
}

export const Input = forwardRef<HTMLInputElement, InputProps>(
  ({ 
    label, 
    helperText, 
    error, 
    success,
    leftIcon, 
    rightIcon, 
    fullWidth = false,
    className = '',
    disabled,
    type = 'text',
    ...props 
  }, ref) => {
    const [showPassword, setShowPassword] = React.useState(false);
    const isPassword = type === 'password';
    const inputType = isPassword ? (showPassword ? 'text' : 'password') : type;

    const baseStyles = 'w-full px-4 py-3 bg-white border rounded-xl text-slate-900 placeholder-slate-400 transition-all duration-200 focus:outline-none focus:ring-2';
    
    const stateStyles = error
      ? 'border-red-300 focus:ring-red-500/20 focus:border-red-500'
      : success
      ? 'border-green-300 focus:ring-green-500/20 focus:border-green-500'
      : 'border-slate-200 focus:ring-primary-500/20 focus:border-primary-500 hover:border-slate-300';

    const disabledStyles = disabled ? 'bg-slate-50 text-slate-400 cursor-not-allowed' : '';

    return (
      <div className={`${fullWidth ? 'w-full' : ''}`}>
        {label && (
          <label className="block text-sm font-medium text-slate-700 mb-1.5">
            {label}
          </label>
        )}
        <div className="relative">
          {leftIcon && (
            <div className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-400">
              {leftIcon}
            </div>
          )}
          <input
            ref={ref}
            type={inputType}
            disabled={disabled}
            className={`
              ${baseStyles}
              ${stateStyles}
              ${disabledStyles}
              ${leftIcon ? 'pl-11' : ''}
              ${(rightIcon || isPassword) ? 'pr-11' : ''}
              ${className}
            `}
            {...props}
          />
          {isPassword && (
            <button
              type="button"
              onClick={() => setShowPassword(!showPassword)}
              className="absolute right-4 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600 transition-colors"
            >
              {showPassword ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
            </button>
          )}
          {!isPassword && rightIcon && (
            <div className="absolute right-4 top-1/2 -translate-y-1/2 text-slate-400">
              {rightIcon}
            </div>
          )}
          {error && (
            <div className="absolute right-4 top-1/2 -translate-y-1/2 text-red-500">
              <AlertCircle className="w-5 h-5" />
            </div>
          )}
          {success && !error && (
            <div className="absolute right-4 top-1/2 -translate-y-1/2 text-green-500">
              <CheckCircle className="w-5 h-5" />
            </div>
          )}
        </div>
        {(helperText || error) && (
          <p className={`mt-1.5 text-sm ${error ? 'text-red-500' : 'text-slate-500'}`}>
            {error || helperText}
          </p>
        )}
      </div>
    );
  }
);

Input.displayName = 'Input';

// Textarea 组件
export interface TextareaProps extends React.TextareaHTMLAttributes<HTMLTextAreaElement> {
  label?: string;
  helperText?: string;
  error?: string;
  fullWidth?: boolean;
  rows?: number;
}

export const Textarea = forwardRef<HTMLTextAreaElement, TextareaProps>(
  ({ 
    label, 
    helperText, 
    error, 
    fullWidth = false,
    rows = 4,
    className = '',
    disabled,
    ...props 
  }, ref) => {
    const baseStyles = 'w-full px-4 py-3 bg-white border rounded-xl text-slate-900 placeholder-slate-400 transition-all duration-200 focus:outline-none focus:ring-2 resize-none';
    
    const stateStyles = error
      ? 'border-red-300 focus:ring-red-500/20 focus:border-red-500'
      : 'border-slate-200 focus:ring-primary-500/20 focus:border-primary-500 hover:border-slate-300';

    const disabledStyles = disabled ? 'bg-slate-50 text-slate-400 cursor-not-allowed' : '';

    return (
      <div className={`${fullWidth ? 'w-full' : ''}`}>
        {label && (
          <label className="block text-sm font-medium text-slate-700 mb-1.5">
            {label}
          </label>
        )}
        <textarea
          ref={ref}
          rows={rows}
          disabled={disabled}
          className={`
            ${baseStyles}
            ${stateStyles}
            ${disabledStyles}
            ${className}
          `}
          {...props}
        />
        {(helperText || error) && (
          <p className={`mt-1.5 text-sm ${error ? 'text-red-500' : 'text-slate-500'}`}>
            {error || helperText}
          </p>
        )}
      </div>
    );
  }
);

Textarea.displayName = 'Textarea';

// Select 组件
export interface SelectOption {
  value: string;
  label: string;
}

export interface SelectProps extends React.SelectHTMLAttributes<HTMLSelectElement> {
  label?: string;
  helperText?: string;
  error?: string;
  options: SelectOption[];
  fullWidth?: boolean;
}

export const Select = forwardRef<HTMLSelectElement, SelectProps>(
  ({ 
    label, 
    helperText, 
    error, 
    options,
    fullWidth = false,
    className = '',
    disabled,
    ...props 
  }, ref) => {
    const baseStyles = 'w-full px-4 py-3 bg-white border rounded-xl text-slate-900 transition-all duration-200 focus:outline-none focus:ring-2 appearance-none cursor-pointer';
    
    const stateStyles = error
      ? 'border-red-300 focus:ring-red-500/20 focus:border-red-500'
      : 'border-slate-200 focus:ring-primary-500/20 focus:border-primary-500 hover:border-slate-300';

    const disabledStyles = disabled ? 'bg-slate-50 text-slate-400 cursor-not-allowed' : '';

    return (
      <div className={`${fullWidth ? 'w-full' : ''}`}>
        {label && (
          <label className="block text-sm font-medium text-slate-700 mb-1.5">
            {label}
          </label>
        )}
        <div className="relative">
          <select
            ref={ref}
            disabled={disabled}
            className={`
              ${baseStyles}
              ${stateStyles}
              ${disabledStyles}
              pr-10
              ${className}
            `}
            {...props}
          >
            {options.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
          <div className="absolute right-4 top-1/2 -translate-y-1/2 text-slate-400 pointer-events-none">
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
            </svg>
          </div>
        </div>
        {(helperText || error) && (
          <p className={`mt-1.5 text-sm ${error ? 'text-red-500' : 'text-slate-500'}`}>
            {error || helperText}
          </p>
        )}
      </div>
    );
  }
);

Select.displayName = 'Select';

// Search Input 组件
export interface SearchInputProps extends Omit<InputProps, 'leftIcon'> {
  onSearch?: (value: string) => void;
  loading?: boolean;
}

export const SearchInput = forwardRef<HTMLInputElement, SearchInputProps>(
  ({ onSearch, loading, ...props }, ref) => {
    const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
      if (e.key === 'Enter' && onSearch) {
        onSearch((e.target as HTMLInputElement).value);
      }
    };

    return (
      <Input
        ref={ref}
        leftIcon={
          loading ? (
            <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
            </svg>
          ) : (
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
          )
        }
        onKeyDown={handleKeyDown}
        {...props}
      />
    );
  }
);

SearchInput.displayName = 'SearchInput';
