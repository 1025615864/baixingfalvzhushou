// News Feature Module
export { NewsCard } from './components/NewsCard';
export { NewsList } from './components/NewsList';

export { useNews, useNewsDetail, useLikeNews, categoryNames } from './hooks/useNews';

export type {
  News,
  NewsListItem,
  NewsArticle,
  NewsCategory,
  NewsCategoryType,
  NewsFilters,
  NewsLikeDTO,
  NewsComment,
  GetNewsListResponse,
  GetNewsDetailResponse,
  GetHotNewsResponse,
  GetRecommendedNewsResponse,
} from './types';