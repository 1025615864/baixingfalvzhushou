/**
 * PromotionForm - 推广链接创建/编辑表单组件
 * 
 * 用于创建或编辑推广链接
 */

import { useState } from 'react';

interface PromotionFormData {
  customCode?: string;
  expiresInDays?: number;
  description?: string;
}

interface PromotionFormProps {
  /** 初始数据（编辑模式） */
  initialData?: PromotionFormData;
  /** 提交回调 */
  onSubmit: (data: PromotionFormData) => Promise<void>;
  /** 取消回调 */
  onCancel?: () => void;
  /** 自定义类名 */
  className?: string;
  /** 是否编辑模式 */
  isEdit?: boolean;
}

/**
 * 过期时间选项
 */
const expireOptions = [
  { value: 7, label: '7天' },
  { value: 30, label: '30天' },
  { value: 90, label: '90天' },
  { value: 180, label: '半年' },
  { value: 365, label: '一年' },
  { value: 0, label: '永不过期' },
];

/**
 * 推广链接创建/编辑表单组件
 * 
 * @example
 * ```tsx
 * // 创建模式
 * <PromotionForm
 *   onSubmit={async (data) => {
 *     await createPromotionLink(data);
 *   }}
 * />
 * 
 * // 编辑模式
 * <PromotionForm
 *   isEdit
 *   initialData={{ customCode: 'mycode', expiresInDays: 30 }}
 *   onSubmit={async (data) => {
 *     await updatePromotionLink(data);
 *   }}
 *   onCancel={() => setShowForm(false)}
 * />
 * ```
 */
export function PromotionForm({
  initialData,
  onSubmit,
  onCancel,
  className = '',
  isEdit = false,
}: PromotionFormProps): JSX.Element {
  const [formData, setFormData] = useState<PromotionFormData>({
    customCode: initialData?.customCode || '',
    expiresInDays: initialData?.expiresInDays || 30,
    description: initialData?.description || '',
  });

  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errors, setErrors] = useState<Partial<Record<keyof PromotionFormData, string>>>({});

  /**
   * 验证表单
   */
  const validate = (): boolean => {
    const newErrors: Partial<Record<keyof PromotionFormData, string>> = {};

    if (formData.customCode) {
      // 验证自定义码格式：字母、数字、下划线、横线，3-20位
      const codeRegex = /^[a-zA-Z0-9_-]{3,20}$/;
      if (!codeRegex.test(formData.customCode)) {
        newErrors.customCode = '推广码只能包含字母、数字、下划线和横线，长度3-20位';
      }
    }

    if (formData.description && formData.description.length > 100) {
      newErrors.description = '描述不能超过100个字符';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  /**
   * 处理提交
   */
  const handleSubmit = (e: React.FormEvent): void => {
    e.preventDefault();

    if (!validate()) return;

    setIsSubmitting(true);
    onSubmit(formData)
      .then(() => {
        // 提交成功
      })
      .catch(() => {
        // 提交失败，错误由调用方处理
      })
      .finally(() => {
        setIsSubmitting(false);
      });
  };

  /**
   * 处理输入变化
   */
  const handleChange = (field: keyof PromotionFormData, value: string | number): void => {
    setFormData((prev) => ({ ...prev, [field]: value }));
    // 清除对应字段的错误
    if (errors[field]) {
      setErrors((prev) => ({ ...prev, [field]: undefined }));
    }
  };

  return (
    <form onSubmit={handleSubmit} className={`space-y-4 ${className}`}>
      {/* 自定义推广码 */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          自定义推广码
          <span className="text-gray-400 font-normal ml-1">（可选）</span>
        </label>
        <div className="relative">
          <input
            type="text"
            value={formData.customCode}
            onChange={(e) => handleChange('customCode', e.target.value)}
            placeholder="如: my-promo-code"
            className={`
              w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition-all
              ${errors.customCode ? 'border-red-300 focus:ring-red-200' : 'border-gray-300'}
            `}
            maxLength={20}
          />
          {formData.customCode && (
            <button
              type="button"
              onClick={() => handleChange('customCode', '')}
              className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          )}
        </div>
        {errors.customCode ? (
          <p className="mt-1 text-sm text-red-500">{errors.customCode}</p>
        ) : (
          <p className="mt-1 text-xs text-gray-500">
            不填写则系统自动生成，支持字母、数字、下划线和横线
          </p>
        )}
      </div>

      {/* 过期时间 */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          链接有效期
        </label>
        <div className="flex flex-wrap gap-2">
          {expireOptions.map((option) => (
            <button
              key={option.value}
              type="button"
              onClick={() => handleChange('expiresInDays', option.value)}
              className={`
                px-4 py-2 rounded-lg text-sm font-medium transition-colors
                ${formData.expiresInDays === option.value
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }
              `}
            >
              {option.label}
            </button>
          ))}
        </div>
      </div>

      {/* 描述 */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          备注描述
          <span className="text-gray-400 font-normal ml-1">（可选）</span>
        </label>
        <textarea
          value={formData.description}
          onChange={(e) => handleChange('description', e.target.value)}
          placeholder="添加备注信息，方便管理..."
          rows={3}
          maxLength={100}
          className={`
            w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition-all resize-none
            ${errors.description ? 'border-red-300 focus:ring-red-200' : 'border-gray-300'}
          `}
        />
        <div className="flex justify-between mt-1">
          {errors.description ? (
            <p className="text-sm text-red-500">{errors.description}</p>
          ) : (
            <span />
          )}
          <span className="text-xs text-gray-400">
            {(formData.description || '').length}/100
          </span>
        </div>
      </div>

      {/* 预览 */}
      {formData.customCode && (
        <div className="p-4 bg-blue-50 rounded-lg">
          <div className="text-sm text-gray-600 mb-1">链接预览：</div>
          <div className="text-sm font-medium text-blue-700 break-all">
            {window.location.origin}/promo/{formData.customCode}
          </div>
        </div>
      )}

      {/* 按钮组 */}
      <div className="flex gap-3 pt-4">
        {onCancel && (
          <button
            type="button"
            onClick={onCancel}
            disabled={isSubmitting}
            className="flex-1 px-4 py-2.5 border border-gray-300 text-gray-700 rounded-lg font-medium hover:bg-gray-50 disabled:opacity-50 transition-colors"
          >
            取消
          </button>
        )}
        <button
          type="submit"
          disabled={isSubmitting}
          className={`
            flex-1 px-4 py-2.5 rounded-lg font-medium transition-colors
            ${isSubmitting
              ? 'bg-gray-400 text-white cursor-not-allowed'
              : 'bg-blue-600 text-white hover:bg-blue-700'
            }
          `}
        >
          {isSubmitting ? (
            <span className="flex items-center justify-center gap-2">
              <svg className="animate-spin w-4 h-4" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
              </svg>
              {isEdit ? '保存中...' : '创建中...'}
            </span>
          ) : (
            isEdit ? '保存修改' : '创建链接'
          )}
        </button>
      </div>
    </form>
  );
}

export default PromotionForm;