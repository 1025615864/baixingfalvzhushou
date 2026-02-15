/**
 * VerticalChannel（垂直频道）Hooks
 * 使用 React Query 管理垂直频道状态
 */

import { useQuery } from '@tanstack/react-query';

import {
  apiGetVerticalChannels,
  apiGetChannelNews,
  apiGetChannelConsultationTypes,
  apiGetChannelDocumentTypes,
  apiGetChannelStats,
} from '../api';
import type { VerticalChannelKey } from '../types';

// Query Keys
const VERTICAL_CHANNEL_KEYS = {
  channels: ['vertical-channels'],
  channelNews: (channelKey: VerticalChannelKey, page: number, pageSize: number) =>
    ['vertical-channel', channelKey, 'news', page, pageSize],
  channelConsultationTypes: (channelKey: VerticalChannelKey) =>
    ['vertical-channel', channelKey, 'consultation-types'],
  channelDocumentTypes: (channelKey: VerticalChannelKey) =>
    ['vertical-channel', channelKey, 'document-types'],
  channelStats: (channelKey: VerticalChannelKey) =>
    ['vertical-channel', channelKey, 'stats'],
};

/**
 * 获取垂直频道列表
 */
export function useVerticalChannels() {
  return useQuery({
    queryKey: VERTICAL_CHANNEL_KEYS.channels,
    queryFn: () => apiGetVerticalChannels(),
  });
}

/**
 * 获取频道新闻列表
 */
export function useChannelNews(
  channelKey: VerticalChannelKey,
  page = 1,
  pageSize = 20
) {
  return useQuery({
    queryKey: VERTICAL_CHANNEL_KEYS.channelNews(channelKey, page, pageSize),
    queryFn: () => apiGetChannelNews(channelKey, page, pageSize),
    enabled: Boolean(channelKey),
  });
}

/**
 * 获取频道咨询类型
 */
export function useChannelConsultationTypes(channelKey: VerticalChannelKey) {
  return useQuery({
    queryKey: VERTICAL_CHANNEL_KEYS.channelConsultationTypes(channelKey),
    queryFn: () => apiGetChannelConsultationTypes(channelKey),
    enabled: Boolean(channelKey),
  });
}

/**
 * 获取频道文书类型
 */
export function useChannelDocumentTypes(channelKey: VerticalChannelKey) {
  return useQuery({
    queryKey: VERTICAL_CHANNEL_KEYS.channelDocumentTypes(channelKey),
    queryFn: () => apiGetChannelDocumentTypes(channelKey),
    enabled: Boolean(channelKey),
  });
}

/**
 * 获取频道统计数据
 */
export function useChannelStats(channelKey: VerticalChannelKey) {
  return useQuery({
    queryKey: VERTICAL_CHANNEL_KEYS.channelStats(channelKey),
    queryFn: () => apiGetChannelStats(channelKey),
    enabled: Boolean(channelKey),
  });
}