/**
 * FormField - 统一表单字段组件
 * 
 * 提供一致的表单字段布局、标签、验证提示和帮助文本
 */

import React, { forwardRef, useId } from 'react';

/**
 * 基础表单字段属性
 */
export interface FormFieldBaseProps {
  /** 字段标签 */
  label: string;
  /** 帮助文本 */
  helperText?: string;
  /** 错误信息 */
  error?: string;
  /** 是否必填 */
  required?: boolean;
  /** 是否禁用 */
  disabled?: boolean;
  /** 自定义类名 */
  className?: string;
  /** 标签位置 */
  labelPosition?: 'top' | 'left';
  /** 标签宽度（仅 labelPosition='left' 时有效） */
  labelWidth?: string;
}

/**
 * FormField 包装器属性
 */
export interface FormFieldWrapperProps extends FormFieldBaseProps {
  /** 子元素 */
  children: React.ReactNode;
  /** 字段 ID（自动生成如果未提供） */
  id?: string;
  /** 隐藏标签（用于无障碍但视觉隐藏） */
  hideLabel?: boolean;
  /** 额外的提示信息 */
  hint?: React.ReactNode;
}

/**
 * FormField 包装器组件
 * 
 * @example
 * ```tsx
 * <FormField
 *   label="用户名"
 *   required
 *   error={errors.username}
 *   helperText="请输入4-20个字符"
 * >
 *   <Input {...register('username')} />
 * </FormField>
 * ```
 */
export function FormField({
  label,
  helperText,
  error,
  required = false,
  disabled = false,
  className = '',
  labelPosition = 'top',
  labelWidth = '120px',
  id: propId,
  hideLabel = false,
  hint,
  children,
}: FormFieldWrapperProps): JSX.Element {
  const autoId = useId();
  const id = propId || autoId;
  const errorId = `${id}-error`;
  const helperId = `${id}-helper`;

  const labelClasses = `
    block text-sm font-medium text-slate-700
    ${hideLabel ? 'sr-only' : ''}
    ${labelPosition === 'left' ? 'flex-shrink-0' : 'mb-1.5'}
  `;

  const LabelContent = (
    <label htmlFor={id} className={labelClasses} style={labelPosition === 'left' ? { width: labelWidth } : undefined}>
      {label}
      {required && <span className="text-red-500 ml-1" aria-hidden="true">*</span>}
    </label>
  );

  return (
    <div
      className={`
        ${labelPosition === 'left' ? 'flex items-start gap-4' : ''}
        ${disabled ? 'opacity-50' : ''}
        ${className}
      `}
    >
      {LabelContent}
      <div className={labelPosition === 'left' ? 'flex-1' : ''}>
        {/* 输入控件 */}
        <div className="relative">
          {React.cloneElement(children as React.ReactElement, {
            id,
            disabled,
            'aria-invalid': !!error,
            'aria-describedby': error ? errorId : helperText ? helperId : undefined,
            'aria-required': required,
          })}
        </div>

        {/* 提示信息 */}
        {hint && !error && (
          <div className="mt-1.5 text-sm text-slate-500">{hint}</div>
        )}

        {/* 错误信息 */}
        {error && (
          <p
            id={errorId}
            className="mt-1.5 text-sm text-red-500 flex items-center gap-1"
            role="alert"
          >
            <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
              <path
                fillRule="evenodd"
                d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z"
                clipRule="evenodd"
              />
            </svg>
            {error}
          </p>
        )}

        {/* 帮助文本 */}
        {helperText && !error && (
          <p id={helperId} className="mt-1.5 text-sm text-slate-500">
            {helperText}
          </p>
        )}
      </div>
    </div>
  );
}

/**
 * FormFieldInput - 带输入框的表单字段
 */
export interface FormFieldInputProps extends FormFieldBaseProps {
  /** 输入框类型 */
  type?: 'text' | 'password' | 'email' | 'number' | 'tel' | 'url' | 'search';
  /** 输入框占位符 */
  placeholder?: string;
  /** 输入值 */
  value?: string | number;
  /** 默认值 */
  defaultValue?: string | number;
  /** 值变化回调 */
  onChange?: (e: React.ChangeEvent<HTMLInputElement>) => void;
  /** 获得焦点回调 */
  onFocus?: (e: React.FocusEvent<HTMLInputElement>) => void;
  /** 失去焦点回调 */
  onBlur?: (e: React.FocusEvent<HTMLInputElement>) => void;
  /** 最大长度 */
  maxLength?: number;
  /** 最小长度 */
  minLength?: number;
  /** 自动完成 */
  autoComplete?: string;
  /** 自动聚焦 */
  autoFocus?: boolean;
  /** 只读 */
  readOnly?: boolean;
  /** 字段 ID */
  id?: string;
  /** 左侧图标 */
  leftIcon?: React.ReactNode;
  /** 右侧图标 */
  rightIcon?: React.ReactNode;
  /** 全宽 */
  fullWidth?: boolean;
}

export const FormFieldInput = forwardRef<HTMLInputElement, FormFieldInputProps>(
  (
    {
      label,
      helperText,
      error,
      required,
      disabled,
      className,
      labelPosition,
      type = 'text',
      placeholder,
      value,
      defaultValue,
      onChange,
      onFocus,
      onBlur,
      maxLength,
      minLength,
      autoComplete,
      autoFocus,
      readOnly,
      id,
      leftIcon,
      rightIcon,
      fullWidth = true,
    },
    ref
  ) => {
    return (
      <FormField
        label={label}
        helperText={helperText}
        error={error}
        required={required}
        disabled={disabled}
        className={className}
        labelPosition={labelPosition}
        id={id}
      >
        <div className={`relative ${fullWidth ? 'w-full' : ''}`}>
          {leftIcon && (
            <div className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400">
              {leftIcon}
            </div>
          )}
          <input
            ref={ref}
            type={type}
            value={value}
            defaultValue={defaultValue}
            onChange={onChange}
            onFocus={onFocus}
            onBlur={onBlur}
            placeholder={placeholder}
            disabled={disabled}
            maxLength={maxLength}
            minLength={minLength}
            autoComplete={autoComplete}
            autoFocus={autoFocus}
            readOnly={readOnly}
            className={`
              w-full px-4 py-2.5
              ${leftIcon ? 'pl-10' : ''}
              ${rightIcon ? 'pr-10' : ''}
              bg-white border rounded-lg
              text-slate-900 placeholder-slate-400
              transition-all duration-200
              focus:outline-none focus:ring-2
              ${error
                ? 'border-red-300 focus:ring-red-500/20 focus:border-red-500'
                : 'border-slate-200 focus:ring-primary-500/20 focus:border-primary-500 hover:border-slate-300'
              }
              ${disabled ? 'bg-slate-50 text-slate-400 cursor-not-allowed' : ''}
            `}
          />
          {rightIcon && (
            <div className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400">
              {rightIcon}
            </div>
          )}
        </div>
      </FormField>
    );
  }
);

FormFieldInput.displayName = 'FormFieldInput';

/**
 * FormFieldTextarea - 带文本域的表单字段
 */
export interface FormFieldTextareaProps extends FormFieldBaseProps {
  /** 占位符 */
  placeholder?: string;
  /** 值 */
  value?: string;
  /** 默认值 */
  defaultValue?: string;
  /** 值变化回调 */
  onChange?: (e: React.ChangeEvent<HTMLTextAreaElement>) => void;
  /** 获得焦点回调 */
  onFocus?: (e: React.FocusEvent<HTMLTextAreaElement>) => void;
  /** 失去焦点回调 */
  onBlur?: (e: React.FocusEvent<HTMLTextAreaElement>) => void;
  /** 行数 */
  rows?: number;
  /** 最大长度 */
  maxLength?: number;
  /** 字段 ID */
  id?: string;
  /** 自动调整高度 */
  autoResize?: boolean;
  /** 最小行数 */
  minRows?: number;
  /** 最大行数 */
  maxRows?: number;
}

export const FormFieldTextarea = forwardRef<HTMLTextAreaElement, FormFieldTextareaProps>(
  (
    {
      label,
      helperText,
      error,
      required,
      disabled,
      className,
      labelPosition,
      placeholder,
      value,
      defaultValue,
      onChange,
      onFocus,
      onBlur,
      rows = 4,
      maxLength,
      id,
      autoResize = false,
      minRows = 2,
      maxRows = 10,
    },
    ref
  ) => {
    return (
      <FormField
        label={label}
        helperText={helperText}
        error={error}
        required={required}
        disabled={disabled}
        className={className}
        labelPosition={labelPosition}
        id={id}
      >
        <textarea
          ref={ref}
          value={value}
          defaultValue={defaultValue}
          onChange={onChange}
          onFocus={onFocus}
          onBlur={onBlur}
          placeholder={placeholder}
          disabled={disabled}
          rows={autoResize ? minRows : rows}
          maxLength={maxLength}
          className={`
            w-full px-4 py-3
            bg-white border rounded-lg
            text-slate-900 placeholder-slate-400
            transition-all duration-200
            focus:outline-none focus:ring-2
            ${error
              ? 'border-red-300 focus:ring-red-500/20 focus:border-red-500'
              : 'border-slate-200 focus:ring-primary-500/20 focus:border-primary-500 hover:border-slate-300'
            }
            ${disabled ? 'bg-slate-50 text-slate-400 cursor-not-allowed' : ''}
            ${autoResize ? 'resize-none overflow-y-auto' : 'resize-y'}
          `}
          style={autoResize ? { minHeight: `${minRows * 24 + 24}px`, maxHeight: `${maxRows * 24 + 24}px` } : undefined}
        />
      </FormField>
    );
  }
);

FormFieldTextarea.displayName = 'FormFieldTextarea';

/**
 * FormFieldSelect - 带选择框的表单字段
 */
export interface SelectOption {
  value: string;
  label: string;
  disabled?: boolean;
}

export interface FormFieldSelectProps extends FormFieldBaseProps {
  /** 选项列表 */
  options: SelectOption[];
  /** 占位符 */
  placeholder?: string;
  /** 值 */
  value?: string;
  /** 默认值 */
  defaultValue?: string;
  /** 值变化回调 */
  onChange?: (e: React.ChangeEvent<HTMLSelectElement>) => void;
  /** 获得焦点回调 */
  onFocus?: (e: React.FocusEvent<HTMLSelectElement>) => void;
  /** 失去焦点回调 */
  onBlur?: (e: React.FocusEvent<HTMLSelectElement>) => void;
  /** 字段 ID */
  id?: string;
}

export const FormFieldSelect = forwardRef<HTMLSelectElement, FormFieldSelectProps>(
  (
    {
      label,
      helperText,
      error,
      required,
      disabled,
      className,
      labelPosition,
      options,
      placeholder,
      value,
      defaultValue,
      onChange,
      onFocus,
      onBlur,
      id,
    },
    ref
  ) => {
    return (
      <FormField
        label={label}
        helperText={helperText}
        error={error}
        required={required}
        disabled={disabled}
        className={className}
        labelPosition={labelPosition}
        id={id}
      >
        <div className="relative">
          <select
            ref={ref}
            value={value}
            defaultValue={defaultValue}
            onChange={onChange}
            onFocus={onFocus}
            onBlur={onBlur}
            disabled={disabled}
            className={`
              w-full px-4 py-2.5 pr-10
              bg-white border rounded-lg
              text-slate-900
              transition-all duration-200
              focus:outline-none focus:ring-2
              appearance-none cursor-pointer
              ${error
                ? 'border-red-300 focus:ring-red-500/20 focus:border-red-500'
                : 'border-slate-200 focus:ring-primary-500/20 focus:border-primary-500 hover:border-slate-300'
              }
              ${disabled ? 'bg-slate-50 text-slate-400 cursor-not-allowed' : ''}
            `}
          >
            {placeholder && (
              <option value="" disabled>
                {placeholder}
              </option>
            )}
            {options.map((option) => (
              <option key={option.value} value={option.value} disabled={option.disabled}>
                {option.label}
              </option>
            ))}
          </select>
          <div className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 pointer-events-none">
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
            </svg>
          </div>
        </div>
      </FormField>
    );
  }
);

FormFieldSelect.displayName = 'FormFieldSelect';

/**
 * FormFieldCheckbox - 带复选框的表单字段
 */
export interface FormFieldCheckboxProps extends Omit<FormFieldBaseProps, 'labelPosition'> {
  /** 选中状态 */
  checked?: boolean;
  /** 默认选中 */
  defaultChecked?: boolean;
  /** 值变化回调 */
  onChange?: (e: React.ChangeEvent<HTMLInputElement>) => void;
  /** 字段 ID */
  id?: string;
  /** 复选框描述 */
  description?: string;
}

export const FormFieldCheckbox = forwardRef<HTMLInputElement, FormFieldCheckboxProps>(
  (
    {
      label,
      helperText,
      error,
      required,
      disabled,
      className,
      checked,
      defaultChecked,
      onChange,
      id,
      description,
    },
    ref
  ) => {
    return (
      <div className={`${disabled ? 'opacity-50' : ''} ${className}`}>
        <label className="flex items-start gap-3 cursor-pointer">
          <input
            ref={ref}
            type="checkbox"
            id={id}
            checked={checked}
            defaultChecked={defaultChecked}
            onChange={onChange}
            disabled={disabled}
            className="
              mt-0.5 h-4 w-4
              text-primary-600 border-slate-300 rounded
              focus:ring-primary-500 focus:ring-2 focus:ring-offset-0
              cursor-pointer
            "
            aria-invalid={!!error}
            aria-required={required}
          />
          <div className="flex-1">
            <span className="text-sm font-medium text-slate-700">
              {label}
              {required && <span className="text-red-500 ml-1">*</span>}
            </span>
            {description && (
              <p className="text-sm text-slate-500 mt-0.5">{description}</p>
            )}
            {error && (
              <p className="mt-1 text-sm text-red-500" role="alert">
                {error}
              </p>
            )}
            {helperText && !error && (
              <p className="mt-1 text-sm text-slate-500">{helperText}</p>
            )}
          </div>
        </label>
      </div>
    );
  }
);

FormFieldCheckbox.displayName = 'FormFieldCheckbox';

export default FormField;