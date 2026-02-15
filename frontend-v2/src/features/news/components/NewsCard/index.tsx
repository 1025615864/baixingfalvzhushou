import { categoryNames } from '../../hooks/useNews';
import type { News } from '../../types';

interface NewsCardProps {
  news: News;
  onClick?: (id: string) => void;
}

export function NewsCard({ news, onClick }: NewsCardProps): JSX.Element {
  const handleClick = (): void => {
    onClick?.(news.id);
  };

  return (
    <article
      className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden cursor-pointer hover:shadow-md transition-shadow"
      onClick={handleClick}
      role="button"
      tabIndex={0}
      onKeyDown={(e): void => {
        if (e.key === 'Enter' || e.key === ' ') {
          handleClick();
        }
      }}
    >
      {/* Cover Image */}
      {news.coverImage ? (
        <div className="h-40 bg-gray-200">
          <img
            src={news.coverImage}
            alt={news.title}
            className="w-full h-full object-cover"
          />
        </div>
      ) : (
        <div className="h-40 bg-gradient-to-br from-primary-100 to-primary-50 flex items-center justify-center">
          <span className="text-4xl">📰</span>
        </div>
      )}

      {/* Content */}
      <div className="p-4">
        <div className="flex items-center gap-2 mb-2">
          <span className="px-2 py-0.5 bg-primary-50 text-primary-700 text-xs font-medium rounded">
            {categoryNames[news.category] || news.category}
          </span>
          {news.isFeatured && (
            <span className="px-2 py-0.5 bg-yellow-50 text-yellow-700 text-xs font-medium rounded">
              精选
            </span>
          )}
        </div>

        <h3 className="font-semibold text-gray-900 line-clamp-2 mb-2 hover:text-primary-600">
          {news.title}
        </h3>

        <p className="text-sm text-gray-600 line-clamp-2 mb-3">
          {news.summary}
        </p>

        <div className="flex items-center justify-between text-xs text-gray-400">
          <div className="flex items-center gap-3">
            <span>{news.author}</span>
            <time dateTime={news.publishedAt}>
              {new Date(news.publishedAt).toLocaleDateString('zh-CN')}
            </time>
          </div>
          <div className="flex items-center gap-3">
            <span>👁 {news.viewCount.toLocaleString()}</span>
            <span>👍 {news.likeCount}</span>
          </div>
        </div>
      </div>
    </article>
  );
}