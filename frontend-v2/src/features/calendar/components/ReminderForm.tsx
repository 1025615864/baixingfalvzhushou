/**
 * ReminderForm 组件
 * 创建/编辑提醒表单
 */

import { useState, useEffect } from 'react';

import type { ReminderFormProps, RepeatType } from '../types';

const REPEAT_OPTIONS: { value: RepeatType; label: string }[] = [
  { value: 'none', label: '不重复' },
  { value: 'daily', label: '每天' },
  { value: 'weekly', label: '每周' },
  { value: 'monthly', label: '每月' },
  { value: 'yearly', label: '每年' },
];

export const ReminderForm: React.FC<ReminderFormProps> = ({
  initialData,
  onSubmit,
  onCancel,
  isLoading,
}) => {
  const [title, setTitle] = useState('');
  const [note, setNote] = useState('');
  const [dueAt, setDueAt] = useState('');
  const [remindAt, setRemindAt] = useState('');
  const [repeatType, setRepeatType] = useState<RepeatType>('none');
  const [errors, setErrors] = useState<Record<string, string>>({});

  // 初始化表单数据
  useEffect(() => {
    if (initialData) {
      setTitle(initialData.title || '');
      setNote(initialData.note || '');
      if (initialData.dueAt) {
        const date = new Date(initialData.dueAt);
        setDueAt(date.toISOString().slice(0, 16)); // YYYY-MM-DDTHH:mm
      }
      if (initialData.remindAt) {
        const date = new Date(initialData.remindAt);
        setRemindAt(date.toISOString().slice(0, 16));
      }
      setRepeatType(initialData.repeatType || 'none');
    }
  }, [initialData]);

  const validate = (): boolean => {
    const newErrors: Record<string, string> = {};

    if (!title.trim()) {
      newErrors.title = '请输入提醒标题';
    } else if (title.length > 200) {
      newErrors.title = '标题不能超过200个字符';
    }

    if (!dueAt) {
      newErrors.dueAt = '请选择到期时间';
    }

    if (note && note.length > 8000) {
      newErrors.note = '备注不能超过8000个字符';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = (e: React.FormEvent): void => {
    e.preventDefault();

    if (!validate()) return;

    const data = {
      title: title.trim(),
      note: note.trim() || undefined,
      dueAt: new Date(dueAt).toISOString(),
      remindAt: remindAt ? new Date(remindAt).toISOString() : undefined,
      repeatType,
    };

    onSubmit(data);
  };

  // 设置默认时间为当前时间加1小时
  const setDefaultTime = (): void => {
    const now = new Date();
    now.setHours(now.getHours() + 1);
    now.setMinutes(0);
    setDueAt(now.toISOString().slice(0, 16));
  };

  // 如果到期时间为空，设置默认值（仅在挂载时执行一次）
  useEffect(() => {
    if (!dueAt && !initialData?.dueAt) {
      setDefaultTime();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      {/* 标题输入 */}
      <div>
        <label
          htmlFor="title"
          className="block text-sm font-medium text-gray-700 mb-1"
        >
          提醒标题 <span className="text-red-500">*</span>
        </label>
        <input
          type="text"
          id="title"
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          placeholder="输入提醒标题"
          className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 ${
            errors.title ? 'border-red-500' : 'border-gray-300'
          }`}
          maxLength={200}
        />
        {errors.title && (
          <p className="mt-1 text-sm text-red-500">{errors.title}</p>
        )}
        <p className="mt-1 text-xs text-gray-400 text-right">
          {title.length}/200
        </p>
      </div>

      {/* 到期时间 */}
      <div>
        <label
          htmlFor="dueAt"
          className="block text-sm font-medium text-gray-700 mb-1"
        >
          到期时间 <span className="text-red-500">*</span>
        </label>
        <input
          type="datetime-local"
          id="dueAt"
          value={dueAt}
          onChange={(e) => setDueAt(e.target.value)}
          className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 ${
            errors.dueAt ? 'border-red-500' : 'border-gray-300'
          }`}
        />
        {errors.dueAt && (
          <p className="mt-1 text-sm text-red-500">{errors.dueAt}</p>
        )}
      </div>

      {/* 提醒时间 */}
      <div>
        <label
          htmlFor="remindAt"
          className="block text-sm font-medium text-gray-700 mb-1"
        >
          提醒时间 <span className="text-gray-400">(可选)</span>
        </label>
        <input
          type="datetime-local"
          id="remindAt"
          value={remindAt}
          onChange={(e) => setRemindAt(e.target.value)}
          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
        <p className="mt-1 text-xs text-gray-400">
          设置提前提醒时间，如果不设置则不会提前通知
        </p>
      </div>

      {/* 重复规则 */}
      <div>
        <label
          htmlFor="repeatType"
          className="block text-sm font-medium text-gray-700 mb-1"
        >
          重复规则
        </label>
        <select
          id="repeatType"
          value={repeatType}
          onChange={(e) => setRepeatType(e.target.value as RepeatType)}
          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          {REPEAT_OPTIONS.map((option) => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </select>
      </div>

      {/* 备注 */}
      <div>
        <label
          htmlFor="note"
          className="block text-sm font-medium text-gray-700 mb-1"
        >
          备注 <span className="text-gray-400">(可选)</span>
        </label>
        <textarea
          id="note"
          value={note}
          onChange={(e) => setNote(e.target.value)}
          placeholder="输入备注信息"
          rows={3}
          className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 ${
            errors.note ? 'border-red-500' : 'border-gray-300'
          }`}
          maxLength={8000}
        />
        {errors.note && (
          <p className="mt-1 text-sm text-red-500">{errors.note}</p>
        )}
        <p className="mt-1 text-xs text-gray-400 text-right">
          {note.length}/8000
        </p>
      </div>

      {/* 按钮组 */}
      <div className="flex justify-end gap-3 pt-4 border-t border-gray-200">
        <button
          type="button"
          onClick={onCancel}
          className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          取消
        </button>
        <button
          type="submit"
          disabled={isLoading}
          className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {isLoading ? '保存中...' : '保存'}
        </button>
      </div>
    </form>
  );
};