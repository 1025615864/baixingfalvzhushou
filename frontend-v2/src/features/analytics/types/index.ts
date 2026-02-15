/**
 * Analytics（数据分析统计）类型定义
 */

// ==================== 行为日志相关类型 ====================

/** 行为类型 */
export type BehaviorAction =
  | 'page_view'    // 页面浏览
  | 'click'        // 点击
  | 'submit'       // 提交
  | 'search'       // 搜索
  | 'download'     // 下载
  | 'share'        // 分享
  | 'favorite'     // 收藏
  | 'comment'      // 评论
  | 'like'         // 点赞
  | 'purchase'     // 购买
  | 'register'     // 注册
  | 'login'        // 登录
  | 'logout';      // 登出

/** 资源类型 */
export type ResourceType =
  | 'post'
  | 'consultation'
  | 'lawyer'
  | 'news'
  | 'knowledge'
  | 'contract'
  | 'document'
  | 'payment'
  | 'order';

/** 行为日志项 */
export interface BehaviorLogItem {
  id: number;
  action: string;
  resourceType: string | null;
  resourceId: number | null;
  metadata: string | null;
  createdAt: string;
}

/** 行为日志请求 */
export interface LogBehaviorRequest {
  action: string;
  resourceType?: string;
  resourceId?: number;
  metadata?: Record<string, unknown>;
  sessionId?: string;
}

/** 行为日志响应 */
export interface LogBehaviorResponse {
  id: number;
  userId: number | null;
  action: string;
  resourceType: string | null;
  resourceId: number | null;
  metadata: string | null;
  createdAt: string;
}

/** 行为历史响应 */
export interface BehaviorHistoryResponse {
  userId: number;
  total: number;
  items: BehaviorLogItem[];
}

/** 资源浏览次数响应 */
export interface ResourceViewCountResponse {
  resourceType: string;
  resourceId: number;
  viewCount: number;
}

// ==================== 行为统计相关类型 ====================

/** 行为统计项 */
export interface ActionStatisticsItem {
  action: string;
  count: number;
}

/** 行为统计响应 */
export interface ActionStatisticsResponse {
  startDate: string;
  endDate: string;
  items: ActionStatisticsItem[];
}

// ==================== 漏斗分析相关类型 ====================

/** 漏斗步骤请求 */
export interface FunnelStepRequest {
  name: string;
  action: string;
  resourceType?: string;
  condition?: Record<string, unknown>;
}

/** 转化漏斗分析请求 */
export interface ConversionFunnelRequest {
  startDate: string;
  endDate: string;
  funnelSteps: FunnelStepRequest[];
}

/** 漏斗步骤结果 */
export interface FunnelStepResult {
  name: string;
  count: number;
  conversionRate: number;
  dropRate: number;
}

/** 转化漏斗分析响应 */
export interface ConversionFunnelResponse {
  startDate: string;
  endDate: string;
  steps: FunnelStepResult[];
}

/** 漏斗图表数据项 */
export interface FunnelChartDataItem {
  name: string;
  value: number;
  conversionRate: number;
  dropRate: number;
  color?: string;
}

// ==================== 用户留存相关类型 ====================

/** 留存分析请求 */
export interface RetentionRequest {
  cohortDate: string;
  retentionDays?: number[];
}

/** 留存项 */
export interface RetentionItem {
  day: number;
  count: number;
  rate: number;
}

/** 留存分析响应 */
export interface RetentionResponse {
  cohortDate: string;
  cohortCount: number;
  retention: RetentionItem[];
}

// ==================== Dashboard 相关类型 ====================

/** 关键指标响应 */
export interface MetricsResponse {
  dau: number;
  mau: number;
  totalRevenue: number;
  payingUsers: number;
  timestamp: string;
}

/** 统计数据卡片 */
export interface StatCardData {
  title: string;
  value: number;
  change?: number;
  changeType?: 'increase' | 'decrease';
  unit?: string;
  icon?: string;
}

/** 收入数据点 */
export interface RevenueDataPoint {
  date: string;
  revenue: number;
  membership?: number;
  consultation?: number;
  other?: number;
}

/** 收入来源 */
export interface RevenueSource {
  name: string;
  value: number;
  percentage: number;
  color: string;
}

/** 收入统计响应 */
export interface RevenueResponse {
  trend: RevenueDataPoint[];
  sources: RevenueSource[];
  total: number;
}

/** 转化漏斗步骤 */
export interface ConversionFunnelStep {
  name: string;
  count: number;
  conversionRate: number;
  dropRate: number;
  color?: string;
}

/** 转化漏斗数据 */
export interface ConversionFunnelData {
  steps: ConversionFunnelStep[];
  totalUsers: number;
  overallConversion: number;
  startDate: string;
  endDate: string;
}

/** 用户活跃度数据点 */
export interface UserActivityPoint {
  date: string;
  activeUsers: number;
  newUsers: number;
  returningUsers: number;
}

/** 功能使用情况 */
export interface FeatureUsage {
  feature: string;
  usageCount: number;
  percentage: number;
  color?: string;
}

/** 用户行为数据 */
export interface UserBehaviorData {
  activityTrend: UserActivityPoint[];
  featureUsage: FeatureUsage[];
  totalSessions: number;
  averageSessionDuration: number;
}

// ==================== 趋势数据相关类型 ====================

/** 趋势数据点 */
export interface TrendDataPoint {
  date: string;
  value: number;
  label?: string;
}

/** 趋势数据 */
export interface TrendData {
  metricName: string;
  data: TrendDataPoint[];
  period: string;
}

/** 对比趋势数据 */
export interface ComparisonTrendData {
  currentPeriod: TrendData;
  previousPeriod: TrendData;
  growthRate: number;
}

// ==================== 数据表格相关类型 ====================

/** 表格列定义 */
export interface DataTableColumn<T = Record<string, unknown>> {
  key: string;
  title: string;
  dataIndex?: string;
  width?: number;
  align?: 'left' | 'center' | 'right';
  render?: (record: T, index: number) => JSX.Element | string | number;
  sorter?: (a: T, b: T) => number;
}

/** 表格分页配置 */
export interface DataTablePagination {
  current: number;
  pageSize: number;
  total: number;
  onChange?: (page: number, pageSize: number) => void;
}

/** API 通用分页请求 */
export interface PaginationRequest {
  limit?: number;
  offset?: number;
}

/** API 通用分页响应 */
export interface PaginationResponse<T> {
  items: T[];
  total: number;
  limit: number;
  offset: number;
}

// ==================== 用户统计相关类型 ====================

/** 用户统计概览 */
export interface UserStatisticsOverview {
  totalUsers: number;
  newUsersToday: number;
  newUsersThisWeek: number;
  newUsersThisMonth: number;
  activeUsersToday: number;
  activeUsersYesterday: number;
  activeUsersThisWeek: number;
  activeUsersThisMonth: number;
}

/** 用户分布数据 */
export interface UserDistribution {
  type: string;
  count: number;
  percentage: number;
}

/** 用户增长数据点 */
export interface UserGrowthPoint {
  date: string;
  totalUsers: number;
  newUsers: number;
}

// ==================== 概览数据类型 ====================

/** 数据概览响应 */
export interface OverviewData {
  users: UserStatisticsOverview & {
    activeUsersYesterday: number;
  };
  revenue: {
    today: number;
    yesterday: number;
    thisWeek: number;
    thisMonth: number;
    total: number;
  };
  content: {
    totalPosts: number;
    totalConsultations: number;
    totalDocuments: number;
    totalContracts: number;
  };
  engagement: {
    avgSessionDuration: number;
    totalSessions: number;
    bounceRate: number;
  };
}