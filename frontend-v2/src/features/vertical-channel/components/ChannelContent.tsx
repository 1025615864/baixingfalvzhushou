/**
 * ChannelContent（频道内容组件）
 * 展示频道新闻内容列表
 */

import type { NewsItem } from '../types';

interface ChannelContentProps {
  news: NewsItem[];
  isLoading: boolean;
  onNewsClick?: (newsId: number) => void;
}

/**
 * 获取风险等级样式
 */
function getRiskLevelStyles(riskLevel: string | null): { bg: string; text: string; label: string } {
  switch (riskLevel) {
    case 'high':
      return { bg: 'bg-red-100', text: 'text-red-700', label: '高风险' };
    case 'medium':
      return { bg: 'bg-yellow-100', text: 'text-yellow-700', label: '中风险' };
    case 'low':
      return { bg: 'bg-green-100', text: 'text-green-700', label: '低风险' };
    default:
      return { bg: 'bg-gray-100', text: 'text-gray-700', label: '未评估' };
  }
}

/**
 * 格式化日期
 */
function formatDate(dateString: string): string {
  const date = new Date(dateString);
  const now = new Date();
  const diffTime = now.getTime() - date.getTime();
  const diffDays = Math.floor(diffTime / (1000 * 60 * 60 * 24));

  if (diffDays === 0) {
    const diffHours = Math.floor(diffTime / (1000 * 60 * 60));
    if (diffHours === 0) {
      const diffMinutes = Math.floor(diffTime / (1000 * 60));
      return diffMinutes <= 0 ? '刚刚' : `${diffMinutes}分钟前`;
    }
    return `${diffHours}小时前`;
  } else if (diffDays === 1) {
    return '昨天';
  } else if (diffDays < 7) {
    return `${diffDays}天前`;
  } else {
    return date.toLocaleDateString('zh-CN', { month: 'short', day: 'numeric' });
  }
}

/**
 * 频道内容组件
 */
export function ChannelContent({ news, isLoading, onNewsClick }: ChannelContentProps): JSX.Element {
  if (isLoading) {
    return (
      <div className="space-y-4">
        {[1, 2, 3, 4, 5].map((i) => (
          <div
            key={i}
            className="bg-white rounded-xl p-6 animate-pulse border border-gray-100"
          >
            <div className="h-6 bg-gray-200 rounded w-3/4 mb-3" />
            <div className="h-4 bg-gray-200 rounded w-full mb-2" />
            <div className="h-4 bg-gray-200 rounded w-2/3" />
          </div>
        ))}
      </div>
    );
  }

  if (news.length === 0) {
    return (
      <div className="text-center py-12 bg-gray-50 rounded-xl">
        <div className="text-4xl mb-4">📰</div>
        <h3 className="text-lg font-medium text-gray-900 mb-2">暂无新闻内容</h3>
        <p className="text-gray-500">该频道暂时没有相关新闻</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {news.map((item) => {
        const riskStyles = getRiskLevelStyles(item.riskLevel);

        return (
          <article
            key={item.id}
            onClick={() => onNewsClick?.(item.id)}
            className="bg-white rounded-xl p-6 border border-gray-100 hover:shadow-md transition-shadow cursor-pointer group"
          >
            {/* 标题 */}
            <h3 className="text-lg font-semibold text-gray-900 mb-2 group-hover:text-indigo-600 transition-colors line-clamp-2">
              {item.title}
            </h3>

            {/* 内容摘要 */}
            <p className="text-gray-600 text-sm leading-relaxed mb-3 line-clamp-2">
              {item.content}
            </p>

            {/* 底部信息 */}
            <div className="flex flex-wrap items-center gap-4 text-xs text-gray-500">
              {/* 来源 */}
              <span className="flex items-center gap-1">
                <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 20H5a2 2 0 01-2-2V6a2 2 0 012-2h10a2 2 0 012 2v1m2 13a2 2 0 01-2-2V7m2 13a2 2 0 002-2V9a2 2 0 00-2-2h-2m-4-3H9M7 16h6M7 8h6v4H7V8z" />
                </svg>
                {item.source}
              </span>

              {/* 发布时间 */}
              <span className="flex items-center gap-1">
                <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                {formatDate(item.publishTime)}
              </span>

              {/* 阅读量 */}
              <span className="flex items-center gap-1">
                <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                </svg>
                {item.viewCount.toLocaleString()}
              </span>

              {/* 收藏数 */}
              <span className={`flex items-center gap-1 ${item.isFavorite ? 'text-amber-500' : ''}`}>
                <svg className={`w-3 h-3 ${item.isFavorite ? 'fill-current' : ''}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 5a2 2 0 012-2h10a2 2 0 012 2v16l-7-3.5L5 21V5z" />
                </svg>
                {item.favoriteCount.toLocaleString()}
              </span>

              {/* 风险等级 */}
              {item.riskLevel && (
                <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${riskStyles.bg} ${riskStyles.text}`}>
                  {riskStyles.label}
                </span>
              )}
            </div>

            {/* 关键词标签 */}
            {item.keywords.length > 0 && (
              <div className="flex flex-wrap gap-2 mt-3">
                {item.keywords.slice(0, 5).map((keyword) => (
                  <span
                    key={keyword}
                    className="px-2 py-0.5 bg-gray-100 text-gray-600 rounded text-xs"
                  >
                    #{keyword}
                  </span>
                ))}
              </div>
            )}
          </article>
        );
      })}
    </div>
  );
}