/**
 * Recommendation（推荐系统）Query Keys
 * 用于 React Query 的缓存管理
 */

/**
 * 推荐系统模块的基础 query key
 */
export const recommendationKeys = {
  all: ['recommendation'] as const,

  /** 个性化推荐 */
  personalized: () => [...recommendationKeys.all, 'personalized'] as const,
  personalizedRecommendations: (lawyerLimit?: number, postLimit?: number, newsLimit?: number) =>
    [...recommendationKeys.personalized(), { lawyerLimit, postLimit, newsLimit }] as const,

  /** 增强推荐 */
  enhanced: () => [...recommendationKeys.all, 'enhanced'] as const,
  enhancedRecommendations: (recommendationType?: string, limit?: number) =>
    [...recommendationKeys.enhanced(), { recommendationType, limit }] as const,

  /** 增强首页 */
  enhancedHome: (lawyerLimit?: number, postLimit?: number, newsLimit?: number, knowledgeLimit?: number) =>
    [...recommendationKeys.all, 'enhanced-home', { lawyerLimit, postLimit, newsLimit, knowledgeLimit }] as const,

  /** 推荐权重 */
  weights: () => [...recommendationKeys.all, 'weights'] as const,

  /** 引导问卷 */
  survey: () => [...recommendationKeys.all, 'survey'] as const,

  /** 是否需要引导 */
  shouldOnboarding: () => [...recommendationKeys.all, 'should-onboarding'] as const,

  /** 律师推荐 */
  lawyers: () => [...recommendationKeys.all, 'lawyers'] as const,
  lawyerRecommendations: (limit?: number) =>
    [...recommendationKeys.lawyers(), { limit }] as const,
  lawyerByConsultation: (limit?: number) =>
    [...recommendationKeys.all, 'lawyers-by-consultation', { limit }] as const,
  lawyerByLocation: (city?: string, limit?: number) =>
    [...recommendationKeys.all, 'lawyers-by-location', { city, limit }] as const,

  /** 帖子推荐 */
  posts: () => [...recommendationKeys.all, 'posts'] as const,
  postRecommendations: (limit?: number) =>
    [...recommendationKeys.posts(), { limit }] as const,

  /** 新闻推荐 */
  news: () => [...recommendationKeys.all, 'news'] as const,
  newsRecommendations: (limit?: number) =>
    [...recommendationKeys.news(), { limit }] as const,

  /** 知识推荐 */
  knowledge: () => [...recommendationKeys.all, 'knowledge'] as const,
  knowledgeByInterests: (limit?: number) =>
    [...recommendationKeys.all, 'knowledge-by-interests', { limit }] as const,

  /** 首页推荐 */
  home: () => [...recommendationKeys.all, 'home'] as const,
  homeRecommendations: (limit?: number) =>
    [...recommendationKeys.all, 'home-recommendations', { limit }] as const,
} as const;

export default recommendationKeys;