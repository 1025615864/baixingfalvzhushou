// ============================================
// 服务发现模块
// 支持开发环境和生产环境切换
// ============================================

export interface ServiceConfig {
  host: string;
  port: number;
  basePath: string;
}

export interface ServiceEndpoints {
  [service: string]: string;
}

// 服务配置
const SERVICE_CONFIGS: Record<string, ServiceConfig> = {
  auth: { host: 'localhost', port: 8000, basePath: '/api/v1/auth' },
  user: { host: 'localhost', port: 8000, basePath: '/api/v1/users' },
  payment: { host: 'localhost', port: 8000, basePath: '/api/v1/payment' },
  accounting: { host: 'localhost', port: 8000, basePath: '/api/v1' },
  legal: { host: 'localhost', port: 8000, basePath: '/api/v1/legal' },
  ai: { host: 'localhost', port: 8000, basePath: '/api/v1/ai' },
  news: { host: 'localhost', port: 8000, basePath: '/api/v1/news' },
  community: { host: 'localhost', port: 8000, basePath: '/api/v1/community' },
  points: { host: 'localhost', port: 8000, basePath: '/api/v1/points' },
  notification: { host: 'localhost', port: 8000, basePath: '/api/v1/notifications' },
  recommendation: { host: 'localhost', port: 8000, basePath: '/api/v1/recommendations' },
  search: { host: 'localhost', port: 8000, basePath: '/api/v1/search' },
};

// 生产环境服务URL（通过API Gateway）
const PROD_SERVICE_URLS: Record<string, string> = {
  auth: '/api/v1/auth',
  user: '/api/v1/users',
  payment: '/api/v1/payment',
  accounting: '/api/v1',
  legal: '/api/v1/legal',
  ai: '/api/v1/ai',
  news: '/api/v1/news',
  community: '/api/v1/community',
  points: '/api/v1/points',
  notification: '/api/v1/notifications',
  recommendation: '/api/v1/recommendations',
  search: '/api/v1/search',
};

export class ServiceDiscovery {
  private endpoints: ServiceEndpoints;
  private isProduction: boolean;

  constructor(customEndpoints?: ServiceEndpoints) {
    this.isProduction = import.meta.env.PROD;
    this.endpoints = this.resolveEndpoints(customEndpoints);
  }

  private resolveEndpoints(customEndpoints?: ServiceEndpoints): ServiceEndpoints {
    if (this.isProduction) {
      return PROD_SERVICE_URLS;
    }

    if (customEndpoints) {
      return Object.entries(customEndpoints).reduce((acc, [key, url]) => {
        acc[key] = url;
        return acc;
      }, {} as ServiceEndpoints);
    }

    // 开发环境默认配置
    return Object.entries(SERVICE_CONFIGS).reduce((acc, [key, config]) => {
      acc[key] = `http://${config.host}:${config.port}${config.basePath}`;
      return acc;
    }, {} as ServiceEndpoints);
  }

  getEndpoint(service: string): string {
    return this.endpoints[service] || this.endpoints['auth'];
  }

  getUrl(service: string, path: string): string {
    const base = this.getEndpoint(service);
    return `${base}${path}`;
  }

  isDev(): boolean {
    return !this.isProduction;
  }

  isProd(): boolean {
    return this.isProduction;
  }
}

// 导出单例
export const serviceDiscovery = new ServiceDiscovery();

// 服务端点快速访问
export const getAuthEndpoint = () => serviceDiscovery.getEndpoint('auth');
export const getUserEndpoint = () => serviceDiscovery.getEndpoint('user');
export const getPaymentEndpoint = () => serviceDiscovery.getEndpoint('payment');
export const getLegalEndpoint = () => serviceDiscovery.getEndpoint('legal');
export const getAIEndpoint = () => serviceDiscovery.getEndpoint('ai');
export const getNewsEndpoint = () => serviceDiscovery.getEndpoint('news');
export const getCommunityEndpoint = () => serviceDiscovery.getEndpoint('community');
export const getPointsEndpoint = () => serviceDiscovery.getEndpoint('points');
export const getNotificationEndpoint = () => serviceDiscovery.getEndpoint('notification');
export const getRecommendationEndpoint = () => serviceDiscovery.getEndpoint('recommendation');
export const getSearchEndpoint = () => serviceDiscovery.getEndpoint('search');
