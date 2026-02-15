import { useLawyers } from '../../hooks/useLawyers';
import { LawyerCard } from '../LawyerCard';
import type { Lawyer } from '../../types';

interface LawyerListProps {
  onSelect?: (id: string) => void;
  onConsult?: (id: string) => void;
}

export function LawyerList({ onSelect, onConsult }: LawyerListProps): JSX.Element {
  const { data: lawyers, isLoading, isError } = useLawyers();

  if (isLoading) {
    return (
      <div className="space-y-4">
        {Array.from({ length: 3 }, (_, index) => (
          <div
            key={index}
            className="bg-white rounded-lg shadow-sm border border-gray-200 p-5 animate-pulse"
          >
            <div className="flex items-start gap-4">
              <div className="w-16 h-16 rounded-full bg-gray-200 flex-shrink-0" />
              <div className="flex-1 space-y-2">
                <div className="h-5 bg-gray-200 rounded w-1/4" />
                <div className="h-4 bg-gray-200 rounded w-1/3" />
                <div className="h-4 bg-gray-200 rounded w-full" />
                <div className="h-4 bg-gray-200 rounded w-2/3" />
              </div>
            </div>
          </div>
        ))}
      </div>
    );
  }

  if (isError) {
    return (
      <div className="text-center py-8">
        <p className="text-red-600">加载律师列表失败，请稍后重试</p>
      </div>
    );
  }

  const items = lawyers?.lawyers ?? [];

  if (!items.length) {
    return (
      <div className="text-center py-8 bg-white rounded-lg border border-gray-200">
        <p className="text-gray-500">暂无符合条件的律师</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {items.map((lawyer: Lawyer) => (
        <LawyerCard
          key={lawyer.id}
          lawyer={lawyer}
          onClick={onSelect}
          onConsult={onConsult}
        />
      ))}
    </div>
  );
}