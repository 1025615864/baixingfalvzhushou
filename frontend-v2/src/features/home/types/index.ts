/**
 * Home（首页）类型定义
 */

// ==================== 核心类型 ====================

/** 首页横幅类型 */
export interface HomeBanner {
  id: string;
  title: string;
  subtitle?: string;
  description?: string;
  imageUrl: string;
  buttonText?: string;
  buttonLink?: string;
  isActive: boolean;
  order: number;
}

/** 快捷入口类型 */
export interface QuickAction {
  id: string;
  title: string;
  description?: string;
  icon: string;
  link: string;
  badge?: string;
  isNew?: boolean;
  order: number;
  color?: string;
}

/** 推荐内容类型 */
export interface Recommendation {
  id: string;
  type: 'lawyer' | 'article' | 'consultation' | 'knowledge';
  title: string;
  description?: string;
  imageUrl?: string;
  link: string;
  tags?: string[];
  rating?: number;
  viewCount?: number;
  authorName?: string;
  authorAvatar?: string;
  createdAt?: string;
  relevanceScore?: number;
}

/** 功能卡片类型 */
export interface FeatureCard {
  id: string;
  title: string;
  description: string;
  icon: string;
  link: string;
  color: 'blue' | 'green' | 'purple' | 'orange' | 'red' | 'teal';
  stats?: {
    label: string;
    value: string;
  };
}

/** 统计数据类型 */
export interface HomeStats {
  totalConsultations: number;
  totalLawyers: number;
  totalUsers: number;
  totalArticles: number;
  solvedCases: number;
  satisfactionRate: number;
}

/** 首页数据聚合 */
export interface HomeData {
  banners: HomeBanner[];
  quickActions: QuickAction[];
  recommendations: Recommendation[];
  featureCards: FeatureCard[];
  stats: HomeStats;
  lastUpdated: string;
}

// ==================== API 请求/响应类型 ====================

/** 获取首页数据请求 */
export interface GetHomeDataRequest {
  includeStats?: boolean;
  recommendationLimit?: number;
}

/** 获取首页数据响应 */
export interface GetHomeDataResponse {
  data: HomeData;
}

/** 获取推荐内容请求 */
export interface GetRecommendationsRequest {
  type?: 'lawyer' | 'article' | 'consultation' | 'knowledge' | 'all';
  limit?: number;
  offset?: number;
}

/** 获取推荐内容响应 */
export interface GetRecommendationsResponse {
  recommendations: Recommendation[];
  total: number;
}

/** 获取快捷入口响应 */
export interface GetQuickActionsResponse {
  actions: QuickAction[];
}

/** 获取统计数据响应 */
export interface GetHomeStatsResponse {
  stats: HomeStats;
}

/** 追踪点击请求 */
export interface TrackClickRequest {
  itemId: string;
  itemType: string;
  source: string;
}

/** 追踪点击响应 */
export interface TrackClickResponse {
  success: boolean;
}

/** 更新用户兴趣请求 */
export interface UpdateInterestsRequest {
  interests: string[];
}

/** 更新用户兴趣响应 */
export interface UpdateInterestsResponse {
  success: boolean;
  interests: string[];
}