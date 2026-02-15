/**
 * ReminderModal 组件
 * 提醒表单弹窗
 */

import type { ReminderModalProps } from '../types';

import { ReminderForm } from './ReminderForm';

export const ReminderModal: React.FC<ReminderModalProps> = ({
  isOpen,
  onClose,
  reminder,
  mode,
  onSubmit,
  isLoading,
}) => {
  if (!isOpen) return null;

  const title = mode === 'create' ? '新建提醒' : '编辑提醒';

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      {/* 遮罩层 */}
      <div
        className="fixed inset-0 bg-black bg-opacity-50 transition-opacity"
        onClick={onClose}
      />

      {/* 弹窗内容 */}
      <div className="flex min-h-full items-center justify-center p-4">
        <div className="relative w-full max-w-lg transform overflow-hidden rounded-lg bg-white text-left shadow-xl transition-all">
          {/* 头部 */}
          <div className="flex items-center justify-between border-b border-gray-200 px-6 py-4">
            <h3 className="text-lg font-semibold text-gray-900">{title}</h3>
            <button
              type="button"
              onClick={onClose}
              className="rounded-full p-1 text-gray-400 hover:bg-gray-100 hover:text-gray-500"
            >
              <svg
                className="h-5 w-5"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M6 18L18 6M6 6l12 12"
                />
              </svg>
            </button>
          </div>

          {/* 表单 */}
          <div className="px-6 py-4">
            <ReminderForm
              initialData={reminder}
              onSubmit={onSubmit}
              onCancel={onClose}
              isLoading={isLoading}
            />
          </div>
        </div>
      </div>
    </div>
  );
};