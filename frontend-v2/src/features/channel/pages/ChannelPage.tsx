/**
 * ChannelPage 页面 - 渠道管理页面
 */

import { useState } from 'react';

import type { Channel, CreateChannelRequest } from '../types';
import { useChannelManager, useDeleteChannel, useCreateChannel, useUpdateChannel } from '../hooks/useChannel';
import { ChannelList } from '../components/ChannelList';
import { ChannelStats } from '../components/ChannelStats';
import { ChannelForm } from '../components/ChannelForm';

type ViewMode = 'list' | 'create' | 'edit';

export function ChannelPage(): JSX.Element {
  const [viewMode, setViewMode] = useState<ViewMode>('list');
  const [selectedChannel, setSelectedChannel] = useState<Channel | undefined>(undefined);

  const {
    channels,
    statsSummary,
    analytics,
    isLoading,
    error,
  } = useChannelManager();

  const deleteChannel = useDeleteChannel();
  const createChannel = useCreateChannel();
  const updateChannel = useUpdateChannel();

  const handleSelectChannel = (channel: Channel): void => {
    setSelectedChannel(channel);
  };

  const handleCreateChannel = (): void => {
    setSelectedChannel(undefined);
    setViewMode('create');
  };

  const handleEditChannel = (channel: Channel): void => {
    setSelectedChannel(channel);
    setViewMode('edit');
  };

  const handleDeleteChannel = (channelId: string): void => {
    void (async (): Promise<void> => {
      try {
        await deleteChannel.mutateAsync(channelId);
        alert('渠道删除成功');
        if (selectedChannel?.id === channelId) {
          setSelectedChannel(undefined);
        }
      } catch (err) {
        const errorMessage = err instanceof Error ? err.message : '删除失败';
        alert(errorMessage);
      }
    })();
  };

  const handleSubmitChannel = (data: CreateChannelRequest): void => {
    void (async (): Promise<void> => {
      try {
        if (viewMode === 'create') {
          await createChannel.mutateAsync(data);
          alert('渠道创建成功');
        } else if (viewMode === 'edit' && selectedChannel) {
          await updateChannel.mutateAsync({
            channelId: selectedChannel.id,
            data: {
              name: data.name,
              slug: data.slug,
              description: data.description,
              type: data.type,
              status: data.status,
              landingConfig: data.landingConfig,
              offerConfig: data.offerConfig,
              trackingConfig: data.trackingConfig,
            },
          });
          alert('渠道更新成功');
        }
        setViewMode('list');
        setSelectedChannel(undefined);
      } catch (err) {
        const errorMessage = err instanceof Error ? err.message : '操作失败';
        alert(errorMessage);
      }
    })();
  };

  const handleCancel = (): void => {
    setViewMode('list');
    setSelectedChannel(undefined);
  };

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 p-6">
        <div className="max-w-7xl mx-auto">
          <div className="bg-red-50 border border-red-200 rounded-lg p-6 text-center">
            <h3 className="text-lg font-medium text-red-800 mb-2">加载失败</h3>
            <p className="text-red-600">{error.message}</p>
            <button
              onClick={() => window.location.reload()}
              className="mt-4 px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700"
            >
              重新加载
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* 页面头部 */}
      <div className="bg-white shadow">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <h1 className="text-xl font-semibold text-gray-900">渠道管理</h1>
            {viewMode === 'list' && (
              <button
                onClick={handleCreateChannel}
                className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
              >
                + 新增渠道
              </button>
            )}
          </div>
        </div>
      </div>

      {/* 页面内容 */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {viewMode === 'list' ? (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
            {/* 左侧：渠道列表 */}
            <div className="lg:col-span-1">
              <ChannelList
                channels={channels}
                selectedChannelId={selectedChannel?.id}
                onSelectChannel={handleSelectChannel}
                onEditChannel={handleEditChannel}
                onDeleteChannel={handleDeleteChannel}
                onCreateChannel={handleCreateChannel}
                isLoading={isLoading}
              />
            </div>

            {/* 右侧：渠道统计 */}
            <div className="lg:col-span-2">
              <ChannelStats
                summary={statsSummary}
                analytics={analytics}
                selectedChannelId={selectedChannel?.id}
                isLoading={isLoading}
              />
            </div>
          </div>
        ) : (
          /* 创建/编辑表单 */
          <div className="max-w-4xl mx-auto">
            <div className="mb-6 flex items-center space-x-2 text-sm text-gray-500">
              <button
                onClick={handleCancel}
                className="hover:text-blue-600 transition-colors"
              >
                ← 返回列表
              </button>
              <span>/</span>
              <span>{viewMode === 'create' ? '新增渠道' : '编辑渠道'}</span>
            </div>
            <ChannelForm
              channel={selectedChannel}
              onSubmit={handleSubmitChannel}
              onCancel={handleCancel}
              isLoading={createChannel.isPending || updateChannel.isPending}
            />
          </div>
        )}
      </div>
    </div>
  );
}