/**
 * Channel（渠道管理）类型定义
 */

// ==================== 核心类型 ====================

/** 渠道类型 */
export type ChannelType = 'weixin' | 'douyin' | 'xiaohongshu' | 'zhihu' | 'bilibili' | 'website' | 'other';

/** 渠道状态 */
export type ChannelStatus = 'active' | 'inactive';

/** 渠道配置 */
export interface Channel {
  id: string;
  name: string;
  slug: string;
  description?: string;
  type: ChannelType;
  status: ChannelStatus;
  landingConfig?: LandingConfig;
  offerConfig?: OfferConfig;
  trackingConfig?: TrackingConfig;
  createdAt?: string;
  updatedAt?: string;
}

/** 落地页配置 */
export interface LandingConfig {
  title: string;
  subtitle: string;
  heroBackgroundColor: string;
  welcomeMessage: string;
  ctaText: string;
  features: LandingFeature[];
  guidanceSteps: GuidanceStep[];
}

/** 落地页特性 */
export interface LandingFeature {
  id: string;
  title: string;
  description: string;
}

/** 引导步骤 */
export interface GuidanceStep {
  id: string;
  step: number;
  title: string;
  description: string;
  actionType: string;
}

/** 优惠配置 */
export interface OfferConfig {
  id: string;
  title: string;
  description: string;
  discountAmount: number;
  discountType: 'fixed' | 'percentage';
  promoCode: string;
  bannerStyle: string;
}

/** 追踪配置 */
export interface TrackingConfig {
  attributionWindow: number;
  enableTracking: boolean;
}

/** 转化漏斗 */
export interface ConversionFunnel {
  visits: number;
  visitsPercentage: number;
  registers: number;
  registersPercentage: number;
  activations: number;
  activationsPercentage: number;
  payments: number;
  paymentsPercentage: number;
}

/** 渠道指标 */
export interface ChannelMetrics {
  visitCount: number;
  registerCount: number;
  activationCount: number;
  paymentCount: number;
  totalRevenue: number;
  avgOrderValue: number;
  conversionRate: number;
  activationRate: number;
  paymentRate: number;
}

/** 渠道分析数据 */
export interface ChannelAnalytics {
  channelId: string;
  channelName: string;
  funnel: ConversionFunnel;
  metrics: ChannelMetrics;
}

/** 渠道对比数据 */
export interface ChannelComparison {
  channelId: string;
  channelName: string;
  metrics: {
    visits: number;
    registers: number;
    payments: number;
    revenue: number;
  };
}

// ==================== API 请求/响应类型 ====================

/** 获取渠道列表请求 */
export interface GetChannelListRequest {
  status?: ChannelStatus;
}

/** 获取渠道列表响应 */
export interface GetChannelListResponse {
  channels: Channel[];
}

/** 获取单个渠道请求 */
export interface GetChannelRequest {
  channelId: string;
}

/** 获取单个渠道响应 */
export interface GetChannelResponse {
  channel: Channel;
}

/** 通过 slug 获取渠道请求 */
export interface GetChannelBySlugRequest {
  slug: string;
}

/** 创建渠道请求 */
export interface CreateChannelRequest {
  name: string;
  slug: string;
  description?: string;
  type: ChannelType;
  status?: ChannelStatus;
  landingConfig?: LandingConfig;
  offerConfig?: OfferConfig;
  trackingConfig?: TrackingConfig;
}

/** 创建渠道响应 */
export interface CreateChannelResponse {
  channelId: string;
  channel: Channel;
}

/** 更新渠道请求 */
export interface UpdateChannelRequest {
  channelId: string;
  name?: string;
  slug?: string;
  description?: string;
  type?: ChannelType;
  status?: ChannelStatus;
  landingConfig?: LandingConfig;
  offerConfig?: OfferConfig;
  trackingConfig?: TrackingConfig;
}

/** 更新渠道响应 */
export interface UpdateChannelResponse {
  success: boolean;
  channel: Channel;
}

/** 删除渠道请求 */
export interface DeleteChannelRequest {
  channelId: string;
}

/** 删除渠道响应 */
export interface DeleteChannelResponse {
  success: boolean;
}

/** 获取渠道分析请求 */
export interface GetChannelAnalyticsRequest {
  channelIds?: string[];
  startDate?: string;
  endDate?: string;
}

/** 获取渠道分析响应 */
export interface GetChannelAnalyticsResponse {
  analytics: ChannelAnalytics[];
}

/** 获取单个渠道分析请求 */
export interface GetSingleChannelAnalyticsRequest {
  channelId: string;
  startDate?: string;
  endDate?: string;
}

/** 获取单个渠道分析响应 */
export interface GetSingleChannelAnalyticsResponse {
  analytics: ChannelAnalytics;
}

/** 对比渠道请求 */
export interface CompareChannelsRequest {
  channelIds: string[];
  startDate?: string;
  endDate?: string;
}

/** 对比渠道响应 */
export interface CompareChannelsResponse {
  comparison: ChannelComparison[];
}

/** 埋点事件 */
export interface TrackEvent {
  eventType: 'visit' | 'register' | 'activation' | 'payment';
  userId?: string;
  sessionId?: string;
  channelParams: ChannelParams;
  metadata?: Record<string, unknown>;
  timestamp?: string;
}

/** 渠道参数 */
export interface ChannelParams {
  source?: string;
  medium?: string;
  campaign?: string;
  content?: string;
  term?: string;
  channelId?: string;
}

/** 上报埋点请求 */
export interface TrackEventsRequest {
  events: TrackEvent[];
}

/** 上报埋点响应 */
export interface TrackEventsResponse {
  success: boolean;
  count: number;
}

/** 渠道统计汇总 */
export interface ChannelStatsSummary {
  totalChannels: number;
  activeChannels: number;
  totalVisits: number;
  totalRegisters: number;
  totalPayments: number;
  totalRevenue: number;
  avgConversionRate: number;
}