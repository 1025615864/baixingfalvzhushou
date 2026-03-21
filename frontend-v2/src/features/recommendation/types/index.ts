/**
 * Recommendation（推荐系统）类型定义
 */

/** 律师推荐项 */
export interface LawyerRecommendation {
  lawyerId: number;
  lawyerName: string;
  avatar?: string;
  specialties?: string;
  rating: number;
  reviewCount: number;
  consultationCount: number;
  isVerified: boolean;
  matchScore: number;
}

/** 帖子推荐项 */
export interface PostRecommendation {
  postId: number;
  title: string;
  content?: string;
  authorId: number;
  authorName: string;
  viewCount: number;
  likeCount: number;
  commentCount: number;
  createdAt: string;
  matchScore: number;
}

/** 新闻推荐项 */
export interface NewsRecommendation {
  newsId: number;
  title: string;
  summary?: string;
  category?: string;
  viewCount: number;
  createdAt: string;
  matchScore: number;
}

/** 个性化推荐结果 */
export interface PersonalizedRecommendations {
  userId: number;
  lawyers: LawyerRecommendation[];
  posts: PostRecommendation[];
  news: NewsRecommendation[];
  similarUsersContent: Array<Record<string, unknown>>;
}

/** 增强推荐项 */
export interface EnhancedRecommendationItem {
  id: string;
  type: string;
  title: string;
  score: number;
  reason: string;
  metadata: Record<string, unknown>;
}

/** 增强推荐结果 */
export interface EnhancedRecommendations {
  items: EnhancedRecommendationItem[];
  total: number;
  source: string;
}

/** 用户画像 */
export interface UserProfile {
  interestTags: string[];
  interestWeights: Record<string, number>;
  preferredContentTypes: string[];
  usageFrequency: string;
  onboardingCompleted: boolean;
}

/** 引导问卷问题选项 */
export interface SurveyQuestionOption {
  value: string;
  label: string;
}

/** 引导问卷问题 */
export interface SurveyQuestion {
  id: string;
  type: 'single' | 'multiple' | 'text' | 'slider';
  question: string;
  options?: SurveyQuestionOption[];
  required?: boolean;
}

/** 引导问卷答案 */
export interface OnboardingAnswers {
  [questionId: string]: string | string[] | number;
}

/** 交互记录请求 */
export interface InteractionRequest {
  contentId: string;
  contentType: string;
  tags?: string[];
  interactionType?: string;
  weight?: number;
}