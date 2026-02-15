/**
 * VerticalChannel（垂直频道）类型定义
 * 婚姻/劳动法律服务专属入口
 */

// ==================== 核心类型 ====================

/** 垂直频道键 */
export type VerticalChannelKey = 'marriage' | 'labor';

/** 垂直频道 */
export interface VerticalChannel {
  key: VerticalChannelKey;
  name: string;
  description: string;
  icon: string;
}

/** 垂直频道列表响应 */
export interface VerticalChannelsResponse {
  channels: VerticalChannel[];
}

/** 咨询类型 */
export interface ConsultationType {
  key: string;
  name: string;
  description: string;
}

/** 垂直频道咨询类型响应 */
export interface ChannelConsultationTypesResponse {
  channelKey: string;
  channelName: string;
  types: ConsultationType[];
}

/** 文书类型 */
export interface DocumentType {
  key: string;
  name: string;
  description: string;
}

/** 垂直频道文书类型响应 */
export interface ChannelDocumentTypesResponse {
  channelKey: string;
  channelName: string;
  types: DocumentType[];
}

/** 新闻项 */
export interface NewsItem {
  id: number;
  title: string;
  content: string;
  source: string;
  publishTime: string;
  viewCount: number;
  isFavorite: boolean;
  favoriteCount: number;
  riskLevel: 'low' | 'medium' | 'high' | null;
  keywords: string[];
}

/** 新闻列表响应 */
export interface NewsListResponse {
  items: NewsItem[];
  total: number;
  page: number;
  pageSize: number;
}

/** 垂直频道统计数据 */
export interface ChannelStats {
  channelKey: string;
  channelName: string;
  newsCount: number;
  keywords: string[];
}

/** 频道内容项 */
export interface ChannelContent {
  id: string;
  title: string;
  description: string;
  type: 'news' | 'consultation' | 'document';
  coverUrl?: string;
  createdAt: string;
  metadata?: Record<string, string>;
}

/** 专题 */
export interface Topic {
  id: string;
  name: string;
  description: string;
  channelKey: VerticalChannelKey;
  icon?: string;
  contentCount: number;
  createdAt: string;
}

// ==================== API 请求/响应类型 ====================

/** 获取垂直频道列表请求 */
export interface GetVerticalChannelListRequest {
  // 无需参数
}

/** 获取频道内容请求 */
export interface GetChannelContentsRequest {
  channelKey: VerticalChannelKey;
  page?: number;
  pageSize?: number;
}

/** 获取专题列表请求 */
export interface GetTopicListRequest {
  channelKey?: VerticalChannelKey;
}

/** 获取频道统计请求 */
export interface GetChannelStatsRequest {
  channelKey: VerticalChannelKey;
}

/** 获取咨询类型请求 */
export interface GetConsultationTypesRequest {
  channelKey: VerticalChannelKey;
}

/** 获取文书类型请求 */
export interface GetDocumentTypesRequest {
  channelKey: VerticalChannelKey;
}

/** 获取频道新闻请求 */
export interface GetChannelNewsRequest {
  channelKey: VerticalChannelKey;
  page?: number;
  pageSize?: number;
}

/** 获取频道内容响应 */
export interface GetChannelContentsResponse {
  contents: ChannelContent[];
  total: number;
  page: number;
  pageSize: number;
}

/** 获取专题列表响应 */
export interface GetTopicListResponse {
  topics: Topic[];
}

/** 频道导航项 */
export interface ChannelNavItem {
  key: string;
  label: string;
  icon: string;
  path: string;
}

/** 频道配置 */
export interface ChannelConfig {
  key: VerticalChannelKey;
  heroTitle: string;
  heroSubtitle: string;
  heroDescription: string;
  features: ChannelFeature[];
  quickActions: QuickAction[];
}

/** 频道特性 */
export interface ChannelFeature {
  icon: string;
  title: string;
  description: string;
}

/** 快速操作 */
export interface QuickAction {
  key: string;
  title: string;
  description: string;
  path: string;
  icon: string;
}