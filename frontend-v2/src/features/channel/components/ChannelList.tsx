/**
 * ChannelList 组件 - 渠道列表
 */

import { useState } from 'react';

import type { Channel, ChannelStatus } from '../types';

interface ChannelListProps {
  channels: Channel[];
  selectedChannelId?: string;
  onSelectChannel: (channel: Channel) => void;
  onEditChannel: (channel: Channel) => void;
  onDeleteChannel: (channelId: string) => void;
  onCreateChannel: () => void;
  isLoading?: boolean;
}

interface ChannelTypeBadgeProps {
  type: Channel['type'];
}

function ChannelTypeBadge({ type }: ChannelTypeBadgeProps): JSX.Element {
  const typeMap: Record<Channel['type'], { label: string; color: string }> = {
    weixin: { label: '微信', color: 'bg-green-100 text-green-800' },
    douyin: { label: '抖音', color: 'bg-pink-100 text-pink-800' },
    xiaohongshu: { label: '小红书', color: 'bg-red-100 text-red-800' },
    zhihu: { label: '知乎', color: 'bg-blue-100 text-blue-800' },
    bilibili: { label: 'B站', color: 'bg-cyan-100 text-cyan-800' },
    website: { label: '官网', color: 'bg-purple-100 text-purple-800' },
    other: { label: '其他', color: 'bg-gray-100 text-gray-800' },
  };

  const { label, color } = typeMap[type] || typeMap.other;

  return (
    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${color}`}>
      {label}
    </span>
  );
}

interface StatusBadgeProps {
  status: ChannelStatus;
}

function StatusBadge({ status }: StatusBadgeProps): JSX.Element {
  const statusMap: Record<ChannelStatus, { label: string; color: string }> = {
    active: { label: '启用', color: 'bg-green-100 text-green-800' },
    inactive: { label: '停用', color: 'bg-gray-100 text-gray-800' },
  };

  const { label, color } = statusMap[status];

  return (
    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${color}`}>
      {label}
    </span>
  );
}

export function ChannelList({
  channels,
  selectedChannelId,
  onSelectChannel,
  onEditChannel,
  onDeleteChannel,
  onCreateChannel,
  isLoading = false,
}: ChannelListProps): JSX.Element {
  const [filterStatus, setFilterStatus] = useState<ChannelStatus | 'all'>('all');

  const filteredChannels = filterStatus === 'all'
    ? channels
    : channels.filter(c => c.status === filterStatus);

  if (isLoading) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <div className="animate-pulse space-y-4">
          <div className="h-8 bg-gray-200 rounded w-1/4"></div>
          <div className="space-y-3">
            {[1, 2, 3].map((i) => (
              <div key={i} className="h-16 bg-gray-200 rounded"></div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow">
      {/* 头部 */}
      <div className="px-6 py-4 border-b border-gray-200 flex items-center justify-between">
        <h2 className="text-lg font-medium text-gray-900">渠道列表</h2>
        <button
          onClick={onCreateChannel}
          className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
        >
          + 新增渠道
        </button>
      </div>

      {/* 筛选器 */}
      <div className="px-6 py-3 border-b border-gray-200 bg-gray-50">
        <div className="flex items-center space-x-4">
          <span className="text-sm text-gray-500">筛选：</span>
          <select
            value={filterStatus}
            onChange={(e) => setFilterStatus(e.target.value as ChannelStatus | 'all')}
            className="text-sm border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500"
          >
            <option value="all">全部状态</option>
            <option value="active">已启用</option>
            <option value="inactive">已停用</option>
          </select>
        </div>
      </div>

      {/* 渠道列表 */}
      <div className="divide-y divide-gray-200">
        {filteredChannels.length === 0 ? (
          <div className="px-6 py-12 text-center">
            <p className="text-gray-500">暂无渠道数据</p>
            <button
              onClick={onCreateChannel}
              className="mt-4 text-blue-600 hover:text-blue-800 text-sm font-medium"
            >
              创建第一个渠道
            </button>
          </div>
        ) : (
          filteredChannels.map((channel) => (
            <div
              key={channel.id}
              className={`px-6 py-4 hover:bg-gray-50 cursor-pointer transition-colors ${
                selectedChannelId === channel.id ? 'bg-blue-50 border-l-4 border-blue-500' : ''
              }`}
              onClick={() => onSelectChannel(channel)}
            >
              <div className="flex items-center justify-between">
                <div className="flex-1">
                  <div className="flex items-center space-x-3">
                    <h3 className="text-sm font-medium text-gray-900">{channel.name}</h3>
                    <ChannelTypeBadge type={channel.type} />
                    <StatusBadge status={channel.status} />
                  </div>
                  <p className="mt-1 text-sm text-gray-500">
                    {channel.description || '暂无描述'}
                  </p>
                  <div className="mt-2 flex items-center space-x-4 text-xs text-gray-400">
                    <span>Slug: {channel.slug}</span>
                    <span>ID: {channel.id}</span>
                  </div>
                </div>
                <div className="flex items-center space-x-2">
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      onEditChannel(channel);
                    }}
                    className="p-2 text-gray-400 hover:text-blue-600 transition-colors"
                    title="编辑"
                  >
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                    </svg>
                  </button>
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      if (window.confirm(`确定要删除渠道 "${channel.name}" 吗？`)) {
                        onDeleteChannel(channel.id);
                      }
                    }}
                    className="p-2 text-gray-400 hover:text-red-600 transition-colors"
                    title="删除"
                  >
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                    </svg>
                  </button>
                </div>
              </div>
            </div>
          ))
        )}
      </div>

      {/* 统计信息 */}
      <div className="px-6 py-3 border-t border-gray-200 bg-gray-50 text-sm text-gray-500">
        共 {filteredChannels.length} 个渠道
        {filterStatus !== 'all' && ` (${filterStatus === 'active' ? '已启用' : '已停用'})`}
      </div>
    </div>
  );
}