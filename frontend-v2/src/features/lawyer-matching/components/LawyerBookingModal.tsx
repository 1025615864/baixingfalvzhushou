/**
 * LawyerBookingModal 组件 - 律师预约弹窗
 */

import { useState, useCallback } from 'react';

import { useCreateBooking } from '../hooks/useLawyerMatching';
import type { ConsultationType } from '../types';

interface LawyerBookingModalProps {
  lawyerId: string;
  lawyerName: string;
  isOpen: boolean;
  onClose: () => void;
  onSuccess: () => void;
}

const CONSULTATION_TYPES: { value: ConsultationType; label: string; description: string }[] = [
  {
    value: 'phone',
    label: '电话咨询',
    description: '通过语音电话进行法律咨询',
  },
  {
    value: 'video',
    label: '视频咨询',
    description: '通过视频通话进行面对面咨询',
  },
  {
    value: 'in_person',
    label: '线下咨询',
    description: '预约线下会面咨询',
  },
  {
    value: 'online',
    label: '在线咨询',
    description: '通过即时消息进行咨询',
  },
];

const DURATION_OPTIONS = [
  { value: 30, label: '30 分钟' },
  { value: 60, label: '1 小时' },
  { value: 90, label: '1.5 小时' },
  { value: 120, label: '2 小时' },
];

export function LawyerBookingModal({
  lawyerId,
  lawyerName,
  isOpen,
  onClose,
  onSuccess,
}: LawyerBookingModalProps): JSX.Element | null {
  const [consultationType, setConsultationType] = useState<ConsultationType>('phone');
  const [scheduledDate, setScheduledDate] = useState<string>('');
  const [scheduledTime, setScheduledTime] = useState<string>('');
  const [duration, setDuration] = useState<number>(60);
  const [topic, setTopic] = useState<string>('');
  const [description, setDescription] = useState<string>('');
  const [errors, setErrors] = useState<Record<string, string>>({});

  const createBooking = useCreateBooking();

  const validateForm = useCallback((): boolean => {
    const newErrors: Record<string, string> = {};

    if (!scheduledDate) {
      newErrors.date = '请选择预约日期';
    } else {
      const selectedDate = new Date(scheduledDate);
      const today = new Date();
      today.setHours(0, 0, 0, 0);
      if (selectedDate < today) {
        newErrors.date = '预约日期不能早于今天';
      }
    }

    if (!scheduledTime) {
      newErrors.time = '请选择预约时间';
    }

    if (!topic.trim()) {
      newErrors.topic = '请输入咨询主题';
    } else if (topic.length > 100) {
      newErrors.topic = '咨询主题不能超过100字';
    }

    if (description.length > 500) {
      newErrors.description = '问题描述不能超过500字';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  }, [scheduledDate, scheduledTime, topic, description]);

  const handleSubmit = useCallback(
    (e: React.FormEvent) => {
      e.preventDefault();

      if (!validateForm()) {
        return;
      }

      const scheduledDateTime = `${scheduledDate}T${scheduledTime}:00`;

      createBooking.mutate(
        {
          lawyerId,
          consultationType,
          scheduledTime: scheduledDateTime,
          duration,
          topic: topic.trim(),
          description: description.trim() || undefined,
        },
        {
          onSuccess: () => {
            onSuccess();
            onClose();
          },
        }
      );
    },
    [
      validateForm,
      lawyerId,
      consultationType,
      scheduledDate,
      scheduledTime,
      duration,
      topic,
      description,
      createBooking,
      onSuccess,
      onClose,
    ]
  );

  const handleClose = useCallback(() => {
    if (!createBooking.isPending) {
      onClose();
    }
  }, [createBooking.isPending, onClose]);

  if (!isOpen) {
    return null;
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
      <div className="w-full max-w-lg max-h-[90vh] overflow-y-auto rounded-xl bg-white shadow-xl">
        {/* 头部 */}
        <div className="sticky top-0 flex items-center justify-between border-b border-gray-100 bg-white px-6 py-4">
          <h2 className="text-lg font-semibold text-gray-900">
            预约咨询 - {lawyerName}
          </h2>
          <button
            type="button"
            onClick={handleClose}
            disabled={createBooking.isPending}
            className="rounded-full p-1 text-gray-400 hover:bg-gray-100 hover:text-gray-600"
          >
            <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* 表单内容 */}
        <form onSubmit={handleSubmit} className="p-6 space-y-6">
          {/* 咨询方式 */}
          <div>
            <label className="mb-2 block text-sm font-medium text-gray-700">
              咨询方式 <span className="text-red-500">*</span>
            </label>
            <div className="grid grid-cols-2 gap-3">
              {CONSULTATION_TYPES.map((type) => (
                <button
                  key={type.value}
                  type="button"
                  onClick={() => setConsultationType(type.value)}
                  className={`flex flex-col items-start rounded-lg border p-3 text-left transition-colors ${
                    consultationType === type.value
                      ? 'border-blue-500 bg-blue-50 text-blue-700'
                      : 'border-gray-200 bg-white text-gray-700 hover:border-gray-300'
                  }`}
                >
                  <span className="font-medium">{type.label}</span>
                  <span className="mt-1 text-xs opacity-75">{type.description}</span>
                </button>
              ))}
            </div>
          </div>

          {/* 预约时间 */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label htmlFor="booking-date" className="mb-1 block text-sm font-medium text-gray-700">
                预约日期 <span className="text-red-500">*</span>
              </label>
              <input
                id="booking-date"
                type="date"
                value={scheduledDate}
                onChange={(e) => setScheduledDate(e.target.value)}
                min={new Date().toISOString().split('T')[0]}
                className={`w-full rounded-lg border px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                  errors.date ? 'border-red-300' : 'border-gray-300'
                }`}
              />
              {errors.date && <p className="mt-1 text-xs text-red-500">{errors.date}</p>}
            </div>
            <div>
              <label htmlFor="booking-time" className="mb-1 block text-sm font-medium text-gray-700">
                预约时间 <span className="text-red-500">*</span>
              </label>
              <input
                id="booking-time"
                type="time"
                value={scheduledTime}
                onChange={(e) => setScheduledTime(e.target.value)}
                className={`w-full rounded-lg border px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                  errors.time ? 'border-red-300' : 'border-gray-300'
                }`}
              />
              {errors.time && <p className="mt-1 text-xs text-red-500">{errors.time}</p>}
            </div>
          </div>

          {/* 咨询时长 */}
          <div>
            <label className="mb-2 block text-sm font-medium text-gray-700">
              咨询时长
            </label>
            <div className="flex flex-wrap gap-2">
              {DURATION_OPTIONS.map((option) => (
                <button
                  key={option.value}
                  type="button"
                  onClick={() => setDuration(option.value)}
                  className={`rounded-lg border px-4 py-2 text-sm font-medium transition-colors ${
                    duration === option.value
                      ? 'border-blue-500 bg-blue-500 text-white'
                      : 'border-gray-300 bg-white text-gray-700 hover:bg-gray-50'
                  }`}
                >
                  {option.label}
                </button>
              ))}
            </div>
          </div>

          {/* 咨询主题 */}
          <div>
            <label htmlFor="booking-topic" className="mb-1 block text-sm font-medium text-gray-700">
              咨询主题 <span className="text-red-500">*</span>
            </label>
            <input
              id="booking-topic"
              type="text"
              value={topic}
              onChange={(e) => setTopic(e.target.value)}
              placeholder="请简要描述咨询主题，如：劳动合同纠纷"
              maxLength={100}
              className={`w-full rounded-lg border px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                errors.topic ? 'border-red-300' : 'border-gray-300'
              }`}
            />
            {errors.topic ? (
              <p className="mt-1 text-xs text-red-500">{errors.topic}</p>
            ) : (
              <p className="mt-1 text-right text-xs text-gray-400">{topic.length}/100</p>
            )}
          </div>

          {/* 问题描述 */}
          <div>
            <label htmlFor="booking-description" className="mb-1 block text-sm font-medium text-gray-700">
              问题描述
            </label>
            <textarea
              id="booking-description"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="请详细描述您的问题，便于律师提前准备..."
              rows={4}
              maxLength={500}
              className={`w-full resize-none rounded-lg border px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                errors.description ? 'border-red-300' : 'border-gray-300'
              }`}
            />
            {errors.description ? (
              <p className="mt-1 text-xs text-red-500">{errors.description}</p>
            ) : (
              <p className="mt-1 text-right text-xs text-gray-400">{description.length}/500</p>
            )}
          </div>

          {/* 错误提示 */}
          {createBooking.error && (
            <div className="rounded-lg bg-red-50 p-3 text-sm text-red-600">
              {createBooking.error.message}
            </div>
          )}

          {/* 底部按钮 */}
          <div className="flex gap-3 pt-2">
            <button
              type="button"
              onClick={handleClose}
              disabled={createBooking.isPending}
              className="flex-1 rounded-lg border border-gray-300 bg-white px-4 py-2.5 text-sm font-medium text-gray-700 transition-colors hover:bg-gray-50 disabled:opacity-50"
            >
              取消
            </button>
            <button
              type="submit"
              disabled={createBooking.isPending}
              className="flex-1 rounded-lg bg-blue-600 px-4 py-2.5 text-sm font-medium text-white transition-colors hover:bg-blue-700 disabled:opacity-50"
            >
              {createBooking.isPending ? '提交中...' : '确认预约'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}