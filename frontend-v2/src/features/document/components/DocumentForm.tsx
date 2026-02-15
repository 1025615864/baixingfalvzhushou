/**
 * 文档表单组件
 * 用于创建和编辑文档
 */

import React, { useState, useEffect } from 'react';

import type { DocumentType, CreateDocumentDTO, UpdateDocumentDTO, DocumentDetail } from '../types';
import { DOCUMENT_TYPE_LABELS } from '../types';

export interface DocumentFormProps {
  /** 初始数据（编辑模式） */
  initialData?: DocumentDetail;
  /** 提交回调 */
  onSubmit: (data: CreateDocumentDTO | UpdateDocumentDTO) => void;
  /** 取消回调 */
  onCancel?: () => void;
  /** 是否提交中 */
  isSubmitting?: boolean;
  /** 表单模式 */
  mode?: 'create' | 'edit';
  /** 额外样式类 */
  className?: string;
}

/**
 * 文档表单组件
 */
export function DocumentForm({
  initialData,
  onSubmit,
  onCancel,
  isSubmitting = false,
  mode = 'create',
  className = '',
}: DocumentFormProps): React.ReactElement {
  const [formData, setFormData] = useState<{
    documentType: DocumentType;
    title: string;
    content: string;
  }>({
    documentType: 'other',
    title: '',
    content: '',
  });

  const [errors, setErrors] = useState<Partial<Record<keyof typeof formData, string>>>({});

  // 初始化表单数据（编辑模式）
  useEffect(() => {
    if (initialData && mode === 'edit') {
      setFormData({
        documentType: initialData.documentType,
        title: initialData.title,
        content: initialData.content,
      });
    }
  }, [initialData, mode]);

  // 验证表单
  const validateForm = (): boolean => {
    const newErrors: Partial<Record<keyof typeof formData, string>> = {};

    if (!formData.title.trim()) {
      newErrors.title = '请输入文档标题';
    } else if (formData.title.length > 200) {
      newErrors.title = '标题不能超过200个字符';
    }

    if (!formData.content.trim()) {
      newErrors.content = '请输入文档内容';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  // 处理字段变化
  const handleChange = (
    field: keyof typeof formData,
    value: string
  ) => {
    setFormData(prev => ({ ...prev, [field]: value }));
    // 清除对应字段的错误
    if (errors[field]) {
      setErrors(prev => ({ ...prev, [field]: undefined }));
    }
  };

  // 处理表单提交
  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!validateForm()) {
      return;
    }

    if (mode === 'create') {
      const submitData: CreateDocumentDTO = {
        documentType: formData.documentType,
        title: formData.title.trim(),
        content: formData.content.trim(),
      };
      onSubmit(submitData);
    } else {
      const submitData: UpdateDocumentDTO = {
        title: formData.title.trim(),
        content: formData.content.trim(),
      };
      onSubmit(submitData);
    }
  };

  // 文档类型选项
  const documentTypeOptions = Object.entries(DOCUMENT_TYPE_LABELS).map(([key, config]) => ({
    value: key as DocumentType,
    label: config.label,
  }));

  return (
    <form onSubmit={handleSubmit} className={`space-y-6 ${className}`}>
      {/* 文档类型选择（仅创建模式显示） */}
      {mode === 'create' && (
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            文档类型 <span className="text-red-500">*</span>
          </label>
          <select
            value={formData.documentType}
            onChange={(e) => handleChange('documentType', e.target.value as DocumentType)}
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none bg-white"
          >
            {documentTypeOptions.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        </div>
      )}

      {/* 文档标题 */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          文档标题 <span className="text-red-500">*</span>
        </label>
        <input
          type="text"
          value={formData.title}
          onChange={(e) => handleChange('title', e.target.value)}
          placeholder="请输入文档标题"
          maxLength={200}
          className={`
            w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none
            ${errors.title ? 'border-red-500' : 'border-gray-300'}
          `}
        />
        {errors.title && (
          <p className="mt-1 text-sm text-red-500">{errors.title}</p>
        )}
        <p className="mt-1 text-xs text-gray-500 text-right">
          {formData.title.length}/200
        </p>
      </div>

      {/* 文档内容 */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          文档内容 <span className="text-red-500">*</span>
        </label>
        <textarea
          value={formData.content}
          onChange={(e) => handleChange('content', e.target.value)}
          placeholder="请输入文档内容"
          rows={12}
          className={`
            w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none resize-y
            ${errors.content ? 'border-red-500' : 'border-gray-300'}
          `}
        />
        {errors.content && (
          <p className="mt-1 text-sm text-red-500">{errors.content}</p>
        )}
        <p className="mt-1 text-xs text-gray-500 text-right">
          {formData.content.length} 字符
        </p>
      </div>

      {/* 操作按钮 */}
      <div className="flex items-center justify-end gap-3 pt-4 border-t border-gray-200">
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
          className="px-6 py-2 text-white bg-blue-600 rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50 flex items-center gap-2"
        >
          {isSubmitting && (
            <svg className="animate-spin h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
          )}
          {mode === 'create' ? '创建文档' : '保存修改'}
        </button>
      </div>
    </form>
  );
}