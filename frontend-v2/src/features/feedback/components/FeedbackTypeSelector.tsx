/**
 * 反馈类型选择器组件
 */

import React from 'react';

import type { FeedbackType } from '../types';
import { getFeedbackTypeClass, getFeedbackTypeLabel } from '../types';

/**
 * FeedbackTypeSelectorProps 接口
 */
export interface FeedbackTypeSelectorProps {
  /** 当前选中的类型 */
  value: FeedbackType;
  /** 选择变化回调 */
  onChange: (type: FeedbackType) => void;
  /** 是否禁用 */
  disabled?: boolean;
  /** 自定义类名 */
  className?: string;
}

/**
 * 反馈类型选项配置
 */
const FEEDBACK_TYPE_OPTIONS: { type: FeedbackType; icon: React.ReactNode }[] = [
  {
    type: 'suggestion',
    icon: (
      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth={2}
          d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z"
        />
      </svg>
    ),
  },
  {
    type: 'bug',
    icon: (
      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth={2}
          d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
        />
      </svg>
    ),
  },
  {
    type: 'complaint',
    icon: (
      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth={2}
          d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
        />
      </svg>
    ),
  },
  {
    type: 'other',
    icon: (
      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth={2}
          d="M8 12h.01M12 12h.01M16 12h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
        />
      </svg>
    ),
  },
];

/**
 * 反馈类型选择器组件
 */
export function FeedbackTypeSelector({
  value,
  onChange,
  disabled = false,
  className = '',
}: FeedbackTypeSelectorProps): React.ReactElement {
  return (
    <div className={`grid grid-cols-2 gap-3 ${className}`}>
      {FEEDBACK_TYPE_OPTIONS.map((option) => {
        const isSelected = value === option.type;
        const typeClass = getFeedbackTypeClass(option.type);

        return (
          <button
            key={option.type}
            type="button"
            disabled={disabled}
            onClick={() => onChange(option.type)}
            className={`
              relative flex items-center p-3 rounded-lg border-2 transition-all duration-200
              ${isSelected ? `border-blue-500 bg-blue-50` : 'border-gray-200 hover:border-gray-300 bg-white'}
              ${disabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}
            `}
          >
            <span className={`${typeClass} p-2 rounded-md mr-3`}>{option.icon}</span>
            <span className="font-medium text-gray-700">{getFeedbackTypeLabel(option.type)}</span>

            {isSelected && (
              <span className="absolute top-2 right-2 text-blue-500">
                <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                  <path
                    fillRule="evenodd"
                    d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
                    clipRule="evenodd"
                  />
                </svg>
              </span>
            )}
          </button>
        );
      })}
    </div>
  );
}