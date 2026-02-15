/**
 * ChannelList（频道列表组件）
 * 展示垂直频道列表（婚姻、劳动等）
 */

import { Link } from 'react-router-dom';

import type { VerticalChannel } from '../types';

interface ChannelListProps {
  channels: VerticalChannel[];
  isLoading: boolean;
}

/**
 * 获取频道图标组件
 */
function getChannelIcon(iconName: string): JSX.Element {
  const iconClassName = "w-12 h-12 mb-4";

  switch (iconName) {
    case 'marriage':
      // 心形图标 - 婚姻
      return (
        <svg className={iconClassName} fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z" />
        </svg>
      );
    case 'labor':
      // 公文包图标 - 劳动
      return (
        <svg className={iconClassName} fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M21 13.255A23.931 23.931 0 0112 15c-3.183 0-6.22-.62-9-1.745M16 6V4a2 2 0 00-2-2h-4a2 2 0 00-2 2v2m4 6h.01M5 20h14a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
        </svg>
      );
    default:
      return (
        <svg className={iconClassName} fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
        </svg>
      );
  }
}

/**
 * 频道列表组件
 */
export function ChannelList({ channels, isLoading }: ChannelListProps): JSX.Element {
  if (isLoading) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {[1, 2, 3].map((i) => (
          <div
            key={i}
            className="bg-white rounded-xl shadow-sm p-6 animate-pulse"
          >
            <div className="w-12 h-12 bg-gray-200 rounded-lg mb-4" />
            <div className="h-6 bg-gray-200 rounded mb-2" />
            <div className="h-4 bg-gray-200 rounded" />
          </div>
        ))}
      </div>
    );
  }

  if (channels.length === 0) {
    return (
      <div className="text-center py-12 bg-gray-50 rounded-xl">
        <p className="text-gray-500">暂无频道数据</p>
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
      {channels.map((channel) => (
        <Link
          key={channel.key}
          to={`/vertical-channel/${channel.key}`}
          className="group bg-white rounded-xl shadow-sm hover:shadow-md transition-shadow p-6 border border-gray-100"
        >
          <div className="text-indigo-600 group-hover:text-indigo-700 transition-colors">
            {getChannelIcon(channel.icon)}
          </div>
          <h3 className="text-xl font-semibold text-gray-900 mb-2">
            {channel.name}
          </h3>
          <p className="text-gray-600 text-sm leading-relaxed">
            {channel.description}
          </p>
          <div className="mt-4 flex items-center text-indigo-600 text-sm font-medium">
            <span>进入频道</span>
            <svg
              className="w-4 h-4 ml-1 group-hover:translate-x-1 transition-transform"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M9 5l7 7-7 7"
              />
            </svg>
          </div>
        </Link>
      ))}
    </div>
  );
}