/**
 * 反馈表单组件
 */

import React, { useState, useCallback } from 'react';

import type { FeedbackType, CreateFeedbackDTO } from '../types';

import { FeedbackTypeSelector } from './FeedbackTypeSelector';

/**
 * FeedbackFormProps 接口
 */
export interface FeedbackFormProps {
  /** 提交回调 */
  onSubmit: (data: CreateFeedbackDTO) => void;
  /** 提交中状态 */
  isSubmitting?: boolean;
  /** 自定义类名 */
  className?: string;
  /** 取消回调 */
  onCancel?: () => void;
}

/**
 * 反馈表单组件
 */
export function FeedbackForm({
  onSubmit,
  isSubmitting = false,
  className = '',
  onCancel,
}: FeedbackFormProps): React.ReactElement {
  const [type, setType] = useState<FeedbackType>('suggestion');
  const [subject, setSubject] = useState('');
  const [content, setContent] = useState('');
  const [contact, setContact] = useState('');
  const [errors, setErrors] = useState<Record<string, string>>({});

  /**
   * 验证表单
   */
  const validate = useCallback((): boolean => {
    const newErrors: Record<string, string> = {};

    if (!subject.trim()) {
      newErrors.subject = '请输入反馈标题';
    } else if (subject.trim().length < 5) {
      newErrors.subject = '标题至少需要5个字符';
    } else if (subject.trim().length > 200) {
      newErrors.subject = '标题不能超过200个字符';
    }

    if (!content.trim()) {
      newErrors.content = '请输入反馈内容';
    } else if (content.trim().length < 10) {
      newErrors.content = '内容至少需要10个字符';
    } else if (content.trim().length > 2000) {
      newErrors.content = '内容不能超过2000个字符';
    }

    // 联系方式可选，但如果填写需要验证格式
    if (contact.trim()) {
      // 简单验证手机号或邮箱
      const phoneRegex = /^1[3-9]\d{9}$/;
      const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
      if (!phoneRegex.test(contact) && !emailRegex.test(contact)) {
        newErrors.contact = '请输入有效的手机号或邮箱';
      }
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  }, [subject, content, contact]);

  /**
   * 处理表单提交
   */
  const handleSubmit = useCallback(
    (e: React.FormEvent) => {
      e.preventDefault();

      if (!validate()) {
        return;
      }

      onSubmit({
        type,
        subject: subject.trim(),
        content: content.trim(),
        contact: contact.trim() || undefined,
      });
    },
    [validate, onSubmit, type, subject, content, contact]
  );

  return (
    <form onSubmit={handleSubmit} className={`space-y-6 ${className}`}>
      {/* 反馈类型选择 */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          反馈类型 <span className="text-red-500">*</span>
        </label>
        <FeedbackTypeSelector value={type} onChange={setType} disabled={isSubmitting} />
      </div>

      {/* 反馈标题 */}
      <div>
        <label htmlFor="subject" className="block text-sm font-medium text-gray-700 mb-2">
          反馈标题 <span className="text-red-500">*</span>
        </label>
        <input
          type="text"
          id="subject"
          value={subject}
          onChange={(e) => setSubject(e.target.value)}
          disabled={isSubmitting}
          placeholder="请简要描述您的问题或建议"
          className={`
            w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent
            ${errors.subject ? 'border-red-500' : 'border-gray-300'}
          `}
        />
        {errors.subject && <p className="mt-1 text-sm text-red-500">{errors.subject}</p>}
        <p className="mt-1 text-xs text-gray-500">{subject.length}/200</p>
      </div>

      {/* 反馈内容 */}
      <div>
        <label htmlFor="content" className="block text-sm font-medium text-gray-700 mb-2">
          反馈内容 <span className="text-red-500">*</span>
        </label>
        <textarea
          id="content"
          rows={6}
          value={content}
          onChange={(e) => setContent(e.target.value)}
          disabled={isSubmitting}
          placeholder="请详细描述您遇到的问题或建议，帮助我们更好地改进产品..."
          className={`
            w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none
            ${errors.content ? 'border-red-500' : 'border-gray-300'}
          `}
        />
        {errors.content && <p className="mt-1 text-sm text-red-500">{errors.content}</p>}
        <p className="mt-1 text-xs text-gray-500">{content.length}/2000</p>
      </div>

      {/* 联系方式 */}
      <div>
        <label htmlFor="contact" className="block text-sm font-medium text-gray-700 mb-2">
          联系方式 <span className="text-gray-400">(选填)</span>
        </label>
        <input
          type="text"
          id="contact"
          value={contact}
          onChange={(e) => setContact(e.target.value)}
          disabled={isSubmitting}
          placeholder="手机号或邮箱，方便我们与您联系"
          className={`
            w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent
            ${errors.contact ? 'border-red-500' : 'border-gray-300'}
          `}
        />
        {errors.contact && <p className="mt-1 text-sm text-red-500">{errors.contact}</p>}
      </div>

      {/* 操作按钮 */}
      <div className="flex items-center justify-end space-x-4 pt-4 border-t">
        {onCancel && (
          <button
            type="button"
            onClick={onCancel}
            disabled={isSubmitting}
            className="px-6 py-2 text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200 transition-colors disabled:opacity-50"
          >
            取消
          </button>
        )}
        <button
          type="submit"
          disabled={isSubmitting}
          className="px-6 py-2 text-white bg-blue-600 rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50 flex items-center"
        >
          {isSubmitting ? (
            <>
              <svg
                className="animate-spin -ml-1 mr-2 h-4 w-4 text-white"
                fill="none"
                viewBox="0 0 24 24"
              >
                <circle
                  className="opacity-25"
                  cx="12"
                  cy="12"
                  r="10"
                  stroke="currentColor"
                  strokeWidth="4"
                />
                <path
                  className="opacity-75"
                  fill="currentColor"
                  d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                />
              </svg>
              提交中...
            </>
          ) : (
            '提交反馈'
          )}
        </button>
      </div>
    </form>
  );
}