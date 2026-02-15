/**
 * Channel（渠道管理）API 层
 * 基于统一的 apiClient，对接后端 /api/v1/channel-tracking 端点
 */

import { apiClient } from "@/shared/lib/api/client";

import type {
  Channel,
  ChannelAnalytics,
  ChannelComparison,
  ChannelStatus,
  ChannelType,
  ChannelStatsSummary,
  LandingConfig,
  OfferConfig,
  TrackingConfig,
  TrackEvent,
  CreateChannelRequest,
  UpdateChannelRequest,
} from '../types';


// API 基础路径
const API_BASE = '/channel-tracking';

// ==================== 后端响应类型定义 ====================

/** 后端落地页特性 */
interface BackendLandingFeature {
  id: string;
  title: string;
  description: string;
}

/** 后端引导步骤 */
interface BackendGuidanceStep {
  id: string;
  step: number;
  title: string;
  description: string;
  action_type: string;
}

/** 后端落地页配置 */
interface BackendLandingConfig {
  title: string;
  subtitle: string;
  hero_background_color: string;
  welcome_message: string;
  cta_text: string;
  features: BackendLandingFeature[];
  guidance_steps: BackendGuidanceStep[];
}

/** 后端优惠配置 */
interface BackendOfferConfig {
  id: string;
  title: string;
  description: string;
  discount_amount: number;
  discount_type: 'fixed' | 'percentage';
  promo_code: string;
  banner_style: string;
}

/** 后端追踪配置 */
interface BackendTrackingConfig {
  attribution_window: number;
  enable_tracking: boolean;
}

/** 后端渠道响应 */
interface BackendChannelResponse {
  id: number;
  name: string;
  code: string;
  description?: string;
  url?: string;
  type: ChannelType;
  status: ChannelStatus;
  visit_count: number;
  register_count: number;
  activation_count: number;
  payment_count: number;
  total_revenue: number;
  conversion_rate: number;
  activation_rate: number;
  payment_rate: number;
  avg_order_value: number;
  landing_config?: BackendLandingConfig;
  offer_config?: BackendOfferConfig;
  tracking_config?: BackendTrackingConfig;
  created_at: string;
  updated_at: string;
}

/** 后端渠道列表响应 */
interface BackendChannelListResponse {
  channels: BackendChannelResponse[];
  total: number;
  page: number;
  page_size: number;
}

/** 后端转化漏斗 */
interface BackendConversionFunnel {
  visits: number;
  visits_percentage: number;
  registers: number;
  registers_percentage: number;
  activations: number;
  activations_percentage: number;
  payments: number;
  payments_percentage: number;
}

/** 后端渠道指标 */
interface BackendChannelMetrics {
  visit_count: number;
  register_count: number;
  activation_count: number;
  payment_count: number;
  total_revenue: number;
  avg_order_value: number;
  conversion_rate: number;
  activation_rate: number;
  payment_rate: number;
}

/** 后端渠道分析数据 */
interface BackendChannelAnalytics {
  channel_id: number;
  channel_name: string;
  funnel: BackendConversionFunnel;
  metrics: BackendChannelMetrics;
}

/** 后端渠道对比数据 */
interface BackendChannelComparisonMetrics {
  visits: number;
  registers: number;
  activations: number;
  payments: number;
  revenue: number;
  conversion_rate: number;
}

interface BackendChannelComparison {
  channel_id: number;
  channel_code: string;
  channel_name: string;
  metrics: BackendChannelComparisonMetrics;
}

/** 后端渠道统计 */
interface BackendChannelStats {
  total_channels: number;
  active_channels: number;
  total_visits: number;
  total_registers: number;
  total_activations: number;
  total_payments: number;
  total_revenue: number;
  avg_conversion_rate: number;
}

/** 后端埋点响应 */
interface BackendTrackResponse {
  success: boolean;
  count: number;
}

// ==================== 转换函数 ====================

/**
 * 转换后端落地页配置到前端格式
 */
function mapBackendToLandingConfig(config?: BackendLandingConfig): LandingConfig | undefined {
  if (!config) return undefined;
  
  return {
    title: config.title,
    subtitle: config.subtitle,
    heroBackgroundColor: config.hero_background_color,
    welcomeMessage: config.welcome_message,
    ctaText: config.cta_text,
    features: config.features.map(f => ({
      id: f.id,
      title: f.title,
      description: f.description,
    })),
    guidanceSteps: config.guidance_steps.map(s => ({
      id: s.id,
      step: s.step,
      title: s.title,
      description: s.description,
      actionType: s.action_type,
    })),
  };
}

/**
 * 转换前端落地页配置到后端格式
 */
function mapLandingConfigToBackend(config?: LandingConfig): BackendLandingConfig | undefined {
  if (!config) return undefined;
  
  return {
    title: config.title,
    subtitle: config.subtitle,
    hero_background_color: config.heroBackgroundColor,
    welcome_message: config.welcomeMessage,
    cta_text: config.ctaText,
    features: config.features.map(f => ({
      id: f.id,
      title: f.title,
      description: f.description,
    })),
    guidance_steps: config.guidanceSteps.map(s => ({
      id: s.id,
      step: s.step,
      title: s.title,
      description: s.description,
      action_type: s.actionType,
    })),
  };
}

/**
 * 转换后端优惠配置到前端格式
 */
function mapBackendToOfferConfig(config?: BackendOfferConfig): OfferConfig | undefined {
  if (!config) return undefined;
  
  return {
    id: config.id,
    title: config.title,
    description: config.description,
    discountAmount: config.discount_amount,
    discountType: config.discount_type,
    promoCode: config.promo_code,
    bannerStyle: config.banner_style,
  };
}

/**
 * 转换前端优惠配置到后端格式
 */
function mapOfferConfigToBackend(config?: OfferConfig): BackendOfferConfig | undefined {
  if (!config) return undefined;
  
  return {
    id: config.id,
    title: config.title,
    description: config.description,
    discount_amount: config.discountAmount,
    discount_type: config.discountType,
    promo_code: config.promoCode,
    banner_style: config.bannerStyle,
  };
}

/**
 * 转换后端追踪配置到前端格式
 */
function mapBackendToTrackingConfig(config?: BackendTrackingConfig): TrackingConfig | undefined {
  if (!config) return undefined;
  
  return {
    attributionWindow: config.attribution_window,
    enableTracking: config.enable_tracking,
  };
}

/**
 * 转换前端追踪配置到后端格式
 */
function mapTrackingConfigToBackend(config?: TrackingConfig): BackendTrackingConfig | undefined {
  if (!config) return undefined;
  
  return {
    attribution_window: config.attributionWindow,
    enable_tracking: config.enableTracking,
  };
}

/**
 * 转换后端渠道到前端格式
 */
function mapBackendToChannel(data: BackendChannelResponse): Channel {
  return {
    id: String(data.id),
    name: data.name,
    slug: data.code,
    description: data.description,
    type: data.type,
    status: data.status,
    landingConfig: mapBackendToLandingConfig(data.landing_config),
    offerConfig: mapBackendToOfferConfig(data.offer_config),
    trackingConfig: mapBackendToTrackingConfig(data.tracking_config),
    createdAt: data.created_at,
    updatedAt: data.updated_at,
  };
}

/**
 * 转换后端分析数据到前端格式
 */
function mapBackendToChannelAnalytics(data: BackendChannelAnalytics): ChannelAnalytics {
  return {
    channelId: String(data.channel_id),
    channelName: data.channel_name,
    funnel: {
      visits: data.funnel.visits,
      visitsPercentage: data.funnel.visits_percentage,
      registers: data.funnel.registers,
      registersPercentage: data.funnel.registers_percentage,
      activations: data.funnel.activations,
      activationsPercentage: data.funnel.activations_percentage,
      payments: data.funnel.payments,
      paymentsPercentage: data.funnel.payments_percentage,
    },
    metrics: {
      visitCount: data.metrics.visit_count,
      registerCount: data.metrics.register_count,
      activationCount: data.metrics.activation_count,
      paymentCount: data.metrics.payment_count,
      totalRevenue: data.metrics.total_revenue,
      avgOrderValue: data.metrics.avg_order_value,
      conversionRate: data.metrics.conversion_rate,
      activationRate: data.metrics.activation_rate,
      paymentRate: data.metrics.payment_rate,
    },
  };
}

// ==================== 渠道列表 API ====================

/**
 * 获取渠道列表
 */
export async function apiGetChannelList(
  status?: ChannelStatus,
  page: number = 1,
  pageSize: number = 10,
  name?: string,
  type?: ChannelType
): Promise<{ channels: Channel[]; total: number; page: number; pageSize: number }> {
  const response = await apiClient.get<BackendChannelListResponse>(`${API_BASE}/list`, {
    params: {
      status,
      page,
      page_size: pageSize,
      name,
      type,
    },
  });

  return {
    channels: response.data.channels.map(mapBackendToChannel),
    total: response.data.total,
    page: response.data.page,
    pageSize: response.data.page_size,
  };
}

// ==================== 渠道详情 API ====================

/**
 * 获取单个渠道
 */
export async function apiGetChannel(channelId: string): Promise<Channel> {
  const response = await apiClient.get<BackendChannelResponse>(`${API_BASE}/detail/${channelId}`);
  return mapBackendToChannel(response.data);
}

/**
 * 通过 code 获取渠道
 */
export async function apiGetChannelByCode(code: string): Promise<Channel> {
  const response = await apiClient.get<BackendChannelResponse>(`${API_BASE}/detail/by-code/${code}`);
  return mapBackendToChannel(response.data);
}

// ==================== 渠道管理 API ====================

/**
 * 创建渠道
 */
export async function apiCreateChannel(request: CreateChannelRequest): Promise<Channel> {
  const response = await apiClient.post<BackendChannelResponse>(API_BASE, {
    name: request.name,
    code: request.slug,
    description: request.description,
    type: request.type,
    status: request.status ?? 'active',
    landing_config: mapLandingConfigToBackend(request.landingConfig),
    offer_config: mapOfferConfigToBackend(request.offerConfig),
    tracking_config: mapTrackingConfigToBackend(request.trackingConfig),
  });

  return mapBackendToChannel(response.data);
}

/**
 * 更新渠道
 */
export async function apiUpdateChannel(
  channelId: string,
  request: Omit<UpdateChannelRequest, 'channelId'>
): Promise<Channel> {
  const response = await apiClient.put<BackendChannelResponse>(`${API_BASE}/${channelId}`, {
    name: request.name,
    code: request.slug,
    description: request.description,
    type: request.type,
    status: request.status,
    landing_config: mapLandingConfigToBackend(request.landingConfig),
    offer_config: mapOfferConfigToBackend(request.offerConfig),
    tracking_config: mapTrackingConfigToBackend(request.trackingConfig),
  });

  return mapBackendToChannel(response.data);
}

/**
 * 删除渠道
 */
export async function apiDeleteChannel(channelId: string): Promise<void> {
  await apiClient.delete(`${API_BASE}/${channelId}`);
}

// ==================== 渠道分析 API ====================

/**
 * 获取渠道分析数据
 */
export async function apiGetChannelAnalytics(
  channelIds?: string[],
  startDate?: string,
  endDate?: string
): Promise<ChannelAnalytics[]> {
  const response = await apiClient.get<BackendChannelAnalytics[]>(`${API_BASE}/analytics`, {
    params: {
      channel_ids: channelIds?.join(','),
      start_date: startDate,
      end_date: endDate,
    },
  });

  return response.data.map(mapBackendToChannelAnalytics);
}

/**
 * 获取单个渠道分析数据
 */
export async function apiGetSingleChannelAnalytics(
  channelId: string,
  startDate?: string,
  endDate?: string
): Promise<ChannelAnalytics> {
  const response = await apiClient.get<BackendChannelAnalytics>(`${API_BASE}/analytics/${channelId}`, {
    params: {
      start_date: startDate,
      end_date: endDate,
    },
  });

  return mapBackendToChannelAnalytics(response.data);
}

/**
 * 对比渠道数据
 */
export async function apiCompareChannels(
  channelIds: string[],
  startDate?: string,
  endDate?: string
): Promise<ChannelComparison[]> {
  const response = await apiClient.get<BackendChannelComparison[]>(`${API_BASE}/analytics/compare`, {
    params: {
      channel_ids: channelIds.join(','),
      start_date: startDate,
      end_date: endDate,
    },
  });

  return response.data.map(item => ({
    channelId: String(item.channel_id),
    channelName: item.channel_name,
    metrics: {
      visits: item.metrics.visits,
      registers: item.metrics.registers,
      payments: item.metrics.payments,
      revenue: item.metrics.revenue,
    },
  }));
}

// ==================== 追踪事件 API ====================

/**
 * 上报埋点事件
 */
export async function apiTrackEvents(events: TrackEvent[]): Promise<{ success: boolean; count: number }> {
  const response = await apiClient.post<BackendTrackResponse>(`${API_BASE}/track`, 
    events.map(event => ({
      event_type: event.eventType,
      user_id: event.userId,
      session_id: event.sessionId,
      channel_params: {
        source: event.channelParams.source,
        medium: event.channelParams.medium,
        campaign: event.channelParams.campaign,
        content: event.channelParams.content,
        term: event.channelParams.term,
        channel_id: event.channelParams.channelId,
      },
      metadata: event.metadata,
      timestamp: event.timestamp ?? new Date().toISOString(),
    }))
  );

  return {
    success: response.data.success,
    count: response.data.count,
  };
}

// ==================== 渠道统计 API ====================

/**
 * 获取渠道统计汇总
 */
export async function apiGetChannelStatsSummary(): Promise<ChannelStatsSummary> {
  const response = await apiClient.get<BackendChannelStats>(`${API_BASE}/stats`);

  return {
    totalChannels: response.data.total_channels,
    activeChannels: response.data.active_channels,
    totalVisits: response.data.total_visits,
    totalRegisters: response.data.total_registers,
    totalPayments: response.data.total_payments,
    totalRevenue: response.data.total_revenue,
    avgConversionRate: response.data.avg_conversion_rate,
  };
}

// ==================== 统一导出 ====================

/**
 * Channel API 统一导出对象
 */
export const channelApi = {
  // 渠道列表
  getChannelList: apiGetChannelList,
  
  // 渠道详情
  getChannel: apiGetChannel,
  getChannelByCode: apiGetChannelByCode,
  
  // 渠道管理
  createChannel: apiCreateChannel,
  updateChannel: apiUpdateChannel,
  deleteChannel: apiDeleteChannel,
  
  // 渠道分析
  getChannelAnalytics: apiGetChannelAnalytics,
  getSingleChannelAnalytics: apiGetSingleChannelAnalytics,
  compareChannels: apiCompareChannels,
  
  // 追踪事件
  trackEvents: apiTrackEvents,
  
  // 统计汇总
  getChannelStatsSummary: apiGetChannelStatsSummary,
} as const;

export default channelApi;