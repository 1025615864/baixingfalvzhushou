/**
 * VerticalChannel（垂直频道）API 层
 */

import type {
  VerticalChannel,
  VerticalChannelKey,
  VerticalChannelsResponse,
  ChannelConsultationTypesResponse,
  ChannelDocumentTypesResponse,
  NewsListResponse,
  ChannelStats,
} from '../types';

// API 基础路径
const API_BASE = '/vertical';

/** API 错误响应 */
interface ApiErrorResponse {
  detail?: string;
}

/**
 * 安全获取 JSON 响应
 */
async function safeJson<T>(response: Response): Promise<T> {
  const data = await response.json() as T;
  return data;
}

/**
 * 获取 API 错误信息
 */
function getErrorMessage(error: unknown, defaultMsg: string): string {
  if (typeof error === 'object' && error !== null && 'detail' in error) {
    return (error as ApiErrorResponse).detail || defaultMsg;
  }
  return defaultMsg;
}

/**
 * 获取垂直频道列表
 */
export async function apiGetVerticalChannels(): Promise<VerticalChannel[]> {
  const response = await fetch(`${API_BASE}/channels`, {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json',
    },
    credentials: 'include',
  });

  if (!response.ok) {
    const error = await safeJson<ApiErrorResponse>(response).catch(() => ({ detail: '获取频道列表失败' }));
    throw new Error(getErrorMessage(error, '获取频道列表失败'));
  }

  const data = await safeJson<VerticalChannelsResponse>(response);
  return data.channels;
}

/**
 * 获取频道新闻列表
 */
export async function apiGetChannelNews(
  channelKey: VerticalChannelKey,
  page = 1,
  pageSize = 20
): Promise<NewsListResponse> {
  const searchParams = new URLSearchParams();
  searchParams.set('page', page.toString());
  searchParams.set('page_size', pageSize.toString());

  const response = await fetch(`${API_BASE}/channels/${channelKey}/news?${searchParams.toString()}`, {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json',
    },
    credentials: 'include',
  });

  if (!response.ok) {
    const error = await safeJson<ApiErrorResponse>(response).catch(() => ({ detail: '获取频道新闻失败' }));
    throw new Error(getErrorMessage(error, '获取频道新闻失败'));
  }

  return await safeJson<NewsListResponse>(response);
}

/**
 * 获取频道咨询类型
 */
export async function apiGetChannelConsultationTypes(channelKey: VerticalChannelKey): Promise<ChannelConsultationTypesResponse> {
  const response = await fetch(`${API_BASE}/channels/${channelKey}/consultation/types`, {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json',
    },
    credentials: 'include',
  });

  if (!response.ok) {
    const error = await safeJson<ApiErrorResponse>(response).catch(() => ({ detail: '获取咨询类型失败' }));
    throw new Error(getErrorMessage(error, '获取咨询类型失败'));
  }

  return await safeJson<ChannelConsultationTypesResponse>(response);
}

/**
 * 获取频道文书类型
 */
export async function apiGetChannelDocumentTypes(channelKey: VerticalChannelKey): Promise<ChannelDocumentTypesResponse> {
  const response = await fetch(`${API_BASE}/channels/${channelKey}/document/types`, {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json',
    },
    credentials: 'include',
  });

  if (!response.ok) {
    const error = await safeJson<ApiErrorResponse>(response).catch(() => ({ detail: '获取文书类型失败' }));
    throw new Error(getErrorMessage(error, '获取文书类型失败'));
  }

  return await safeJson<ChannelDocumentTypesResponse>(response);
}

/**
 * 获取频道统计数据
 */
export async function apiGetChannelStats(channelKey: VerticalChannelKey): Promise<ChannelStats> {
  const response = await fetch(`${API_BASE}/channels/${channelKey}/stats`, {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json',
    },
    credentials: 'include',
  });

  if (!response.ok) {
    const error = await safeJson<ApiErrorResponse>(response).catch(() => ({ detail: '获取频道统计失败' }));
    throw new Error(getErrorMessage(error, '获取频道统计失败'));
  }

  return await safeJson<ChannelStats>(response);
}