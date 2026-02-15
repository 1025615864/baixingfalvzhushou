import { KnowledgeCard } from '../KnowledgeCard';
import type { KnowledgeArticle } from '../../types';

interface KnowledgeListProps {
  items: KnowledgeArticle[];
  isLoading?: boolean;
  isError?: boolean;
  onSelect?: (id: string) => void;
}

export function KnowledgeList({
  items,
  isLoading = false,
  isError = false,
  onSelect,
}: KnowledgeListProps): JSX.Element {

  if (isLoading) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {Array.from({ length: 4 }, (_, index) => (
          <div
            key={index}
            className="bg-white rounded-lg shadow-sm border border-gray-200 p-5 animate-pulse"
          >
            <div className="h-4 bg-gray-200 rounded w-20 mb-3" />
            <div className="h-6 bg-gray-200 rounded w-3/4 mb-2" />
            <div className="h-4 bg-gray-200 rounded w-full mb-2" />
            <div className="h-4 bg-gray-200 rounded w-2/3" />
          </div>
        ))}
      </div>
    );
  }

  if (isError) {
    return (
      <div className="text-center py-8">
        <p className="text-red-600">加载知识库失败，请稍后重试</p>
      </div>
    );
  }

  if (!items?.length) {
    return (
      <div className="text-center py-8 bg-white rounded-lg border border-gray-200">
        <p className="text-gray-500">暂无相关内容</p>
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
      {items.map((item) => (
        <KnowledgeCard key={item.id} item={item} onClick={onSelect} />
      ))}
    </div>
  );
}