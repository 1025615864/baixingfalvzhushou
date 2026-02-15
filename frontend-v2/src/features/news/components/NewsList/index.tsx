import { useNews } from '../../hooks/useNews';
import { NewsCard } from '../NewsCard';
import type { News } from '../../types';

interface NewsListProps {
  featuredOnly?: boolean;
  onSelect?: (id: string) => void;
}

export function NewsList({ featuredOnly, onSelect }: NewsListProps): JSX.Element {
  const { data: news, isLoading, isError } = useNews({
    featured: featuredOnly,
  });

  if (isLoading) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {Array.from({ length: 3 }, (_, index) => (
          <div
            key={index}
            className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden animate-pulse"
          >
            <div className="h-40 bg-gray-200" />
            <div className="p-4 space-y-2">
              <div className="h-4 bg-gray-200 rounded w-1/4" />
              <div className="h-5 bg-gray-200 rounded w-3/4" />
              <div className="h-4 bg-gray-200 rounded w-full" />
              <div className="h-4 bg-gray-200 rounded w-2/3" />
            </div>
          </div>
        ))}
      </div>
    );
  }

  if (isError) {
    return (
      <div className="text-center py-8">
        <p className="text-red-600">加载资讯失败，请稍后重试</p>
      </div>
    );
  }

  if (!news?.length) {
    return (
      <div className="text-center py-8 bg-white rounded-lg border border-gray-200">
        <p className="text-gray-500">暂无资讯</p>
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      {news.map((item: News) => (
        <NewsCard key={item.id} news={item} onClick={onSelect} />
      ))}
    </div>
  );
}