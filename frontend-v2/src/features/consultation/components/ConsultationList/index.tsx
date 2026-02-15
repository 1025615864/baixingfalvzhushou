import { useConsultations } from '../../hooks/useConsultations';
import { ConsultationCard } from '../ConsultationCard';
import type { Consultation } from '../../types';

const SKELETON_COUNT = 3;

interface ConsultationListProps {
  onSelect?: (id: string) => void;
}

export function ConsultationList({ onSelect }: ConsultationListProps): JSX.Element {
  const { data: consultations, isLoading, isError } = useConsultations();

  if (isLoading) {
    return (
      <div className="space-y-4">
        {Array.from({ length: SKELETON_COUNT }, (_, index) => (
          <div key={index} className="bg-white rounded-lg shadow-sm border border-gray-200 p-4 animate-pulse">
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
        <p className="text-red-600">加载咨询列表失败，请稍后重试</p>
      </div>
    );
  }

  const items = consultations?.items ?? [];

  if (!items.length) {
    return (
      <div className="text-center py-8 bg-white rounded-lg border border-gray-200">
        <p className="text-gray-500 mb-4">暂无咨询记录</p>
        <p className="text-sm text-gray-400">
          点击&ldquo;发起咨询&rdquo;开始您的第一个法律咨询
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {items.map((consultation: Consultation) => (
        <ConsultationCard
          key={consultation.id}
          consultation={consultation}
          onClick={onSelect}
        />
      ))}
    </div>
  );
}