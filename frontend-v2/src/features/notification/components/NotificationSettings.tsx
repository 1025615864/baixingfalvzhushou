/**
 * 通知设置组件
 */

import React, { useState } from 'react';

import { NotificationSettings as NotificationSettingsType } from '../types';

export interface NotificationSettingsProps {
  /** 当前设置 */
  settings?: NotificationSettingsType;
  /** 保存回调 */
  onSave?: (settings: NotificationSettingsType) => void;
  /** 是否加载中 */
  isLoading?: boolean;
}

/**
 * 默认设置
 */
const defaultSettings: NotificationSettingsType = {
  system_enabled: true,
  consultation_enabled: true,
  comment_reply_enabled: true,
  like_enabled: true,
  order_enabled: true,
  news_enabled: false,
};

/**
 * 通知设置组件
 */
export function NotificationSettings({
  settings = defaultSettings,
  onSave,
  isLoading = false,
}: NotificationSettingsProps): React.ReactElement {
  const [localSettings, setLocalSettings] = useState<NotificationSettingsType>(settings);

  const handleToggle = (key: keyof NotificationSettingsType): void => {
    setLocalSettings((prev) => ({
      ...prev,
      [key]: !prev[key],
    }));
  };

  const handleSave = (): void => {
    onSave?.(localSettings);
  };

  const settingItems: Array<{
    key: keyof NotificationSettingsType;
    title: string;
    description: string;
  }> = [
    {
      key: 'system_enabled',
      title: '系统通知',
      description: '接收系统维护、更新等重要通知',
    },
    {
      key: 'consultation_enabled',
      title: '咨询通知',
      description: '接收咨询回复、预约提醒等通知',
    },
    {
      key: 'comment_reply_enabled',
      title: '评论回复',
      description: '当有人回复您的评论时接收通知',
    },
    {
      key: 'like_enabled',
      title: '点赞通知',
      description: '当有人点赞您的内容时接收通知',
    },
    {
      key: 'order_enabled',
      title: '订单通知',
      description: '接收订单状态变更、支付提醒等通知',
    },
    {
      key: 'news_enabled',
      title: '新闻订阅',
      description: '接收订阅的新闻更新通知',
    },
  ];

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200">
      <div className="px-6 py-4 border-b border-gray-100">
        <h2 className="text-lg font-medium text-gray-900">通知设置</h2>
        <p className="mt-1 text-sm text-gray-500">
          管理您接收通知的方式和内容
        </p>
      </div>

      <div className="divide-y divide-gray-100">
        {settingItems.map((item) => (
          <div
            key={item.key}
            className="flex items-center justify-between px-6 py-4 hover:bg-gray-50 transition-colors"
          >
            <div className="flex-1">
              <h3 className="text-sm font-medium text-gray-900">
                {item.title}
              </h3>
              <p className="mt-0.5 text-xs text-gray-500">
                {item.description}
              </p>
            </div>
            <button
              type="button"
              role="switch"
              aria-checked={localSettings[item.key]}
              onClick={() => handleToggle(item.key)}
              className={`
                relative inline-flex h-6 w-11 flex-shrink-0 cursor-pointer rounded-full
                border-2 border-transparent transition-colors duration-200 ease-in-out
                focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2
                ${localSettings[item.key] ? 'bg-primary-600' : 'bg-gray-200'}
              `}
            >
              <span
                className={`
                  pointer-events-none inline-block h-5 w-5 transform rounded-full
                  bg-white shadow ring-0 transition duration-200 ease-in-out
                  ${localSettings[item.key] ? 'translate-x-5' : 'translate-x-0'}
                `}
              />
            </button>
          </div>
        ))}
      </div>

      <div className="px-6 py-4 bg-gray-50 rounded-b-lg">
        <button
          type="button"
          onClick={handleSave}
          disabled={isLoading}
          className={`
            inline-flex justify-center rounded-md px-4 py-2 text-sm font-medium
            text-white shadow-sm focus:outline-none focus:ring-2 focus:ring-offset-2
            ${isLoading
              ? 'bg-gray-400 cursor-not-allowed'
              : 'bg-primary-600 hover:bg-primary-700 focus:ring-primary-500'
            }
          `}
        >
          {isLoading ? '保存中...' : '保存设置'}
        </button>
      </div>
    </div>
  );
}