import type { Consultation } from '../../types';

interface ConsultationCardProps {
  consultation: Consultation;
  onClick?: (id: string) => void;
}

export function ConsultationCard({ consultation, onClick }: ConsultationCardProps): JSX.Element {
  const statusConfig: Record<Consultation['status'], { label: string; color: string }> = {
    pending: { label: '待处理', color: 'bg-yellow-100 text-yellow-800' },
    assigned: { label: '已分配', color: 'bg-blue-100 text-blue-800' },
    in_progress: { label: '进行中', color: 'bg-green-100 text-green-800' },
    completed: { label: '已完成', color: 'bg-gray-100 text-gray-800' },
    cancelled: { label: '已取消', color: 'bg-red-100 text-red-800' },
  };

  const typeConfig: Record<string, string> = {
    legal: '法律咨询',
    contract: '合同审查',
    dispute: '纠纷调解',
  };

  const status = statusConfig[consultation.status];
  const typeLabel = typeConfig[consultation.category ?? ''] || '其他';

  const handleClick = (): void => {
    onClick?.(consultation.id);
  };

  return (
    <div
      className="bg-white rounded-lg shadow-sm border border-gray-200 p-4 cursor-pointer hover:shadow-md transition-shadow"
      onClick={handleClick}
      role="button"
      tabIndex={0}
      onKeyDown={(e): void => {
        if (e.key === 'Enter' || e.key === ' ') {
          handleClick();
        }
      }}
    >
      <div className="flex items-start justify-between mb-2">
        <h3 className="text-lg font-semibold text-gray-900 line-clamp-1">{consultation.subject}</h3>
        <span className={`px-2 py-1 text-xs font-medium rounded-full ${status.color}`}>
          {status.label}
        </span>
      </div>
      
      <p className="text-sm text-gray-600 line-clamp-2 mb-3">{consultation.description}</p>
      
      <div className="flex items-center justify-between text-sm text-gray-500">
        <div className="flex items-center gap-2">
          <span className="bg-gray-100 px-2 py-0.5 rounded text-xs">{typeLabel}</span>
          {consultation.lawyerName && (
            <span className="text-primary-600">{consultation.lawyerName}</span>
          )}
        </div>
        <time dateTime={consultation.createdAt}>
          {new Date(consultation.createdAt).toLocaleDateString('zh-CN')}
        </time>
      </div>
    </div>
  );
}