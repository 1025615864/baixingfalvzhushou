import { useConsultationDetail } from '../../hooks/useConsultationDetail';

interface ConsultationDetailProps {
  id: string;
  onBack?: () => void;
}

export function ConsultationDetail({ id, onBack }: ConsultationDetailProps): JSX.Element {
  const { data: consultation, isLoading, isError } = useConsultationDetail(id);

  if (isLoading) {
    return (
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 animate-pulse">
        <div className="h-8 bg-gray-200 rounded w-3/4 mb-4" />
        <div className="h-4 bg-gray-200 rounded w-full mb-2" />
        <div className="h-4 bg-gray-200 rounded w-2/3" />
      </div>
    );
  }

  if (isError || !consultation) {
    return (
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 text-center">
        <p className="text-red-600 mb-4">加载咨询详情失败</p>
        <button
          onClick={onBack}
          className="text-primary-600 hover:text-primary-700 font-medium"
          type="button"
        >
          返回列表
        </button>
      </div>
    );
  }

  const getStatusColor = (status: string): string => {
    const colors: Record<string, string> = {
      pending: 'bg-yellow-100 text-yellow-800',
      assigned: 'bg-blue-100 text-blue-800',
      in_progress: 'bg-green-100 text-green-800',
      completed: 'bg-gray-100 text-gray-800',
      cancelled: 'bg-red-100 text-red-800',
    };
    return colors[status] || 'bg-gray-100 text-gray-800';
  };

  const getStatusLabel = (status: string): string => {
    const labels: Record<string, string> = {
      pending: '待处理',
      assigned: '已分配',
      in_progress: '进行中',
      completed: '已完成',
      cancelled: '已取消',
    };
    return labels[status] || status;
  };

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200">
      {/* Header */}
      <div className="px-6 py-4 border-b border-gray-200">
        <div className="flex items-center justify-between mb-2">
          <button
            onClick={onBack}
            className="text-sm text-gray-500 hover:text-gray-700 flex items-center gap-1"
            type="button"
          >
            ← 返回
          </button>
          <span className={`px-3 py-1 text-sm font-medium rounded-full ${getStatusColor(consultation.status)}`}>
            {getStatusLabel(consultation.status)}
          </span>
        </div>
        <h2 className="text-xl font-bold text-gray-900">{consultation.subject}</h2>
        <p className="text-gray-600 mt-1">{consultation.description}</p>
        {consultation.lawyerName && (
          <p className="text-sm text-primary-600 mt-2">
            负责律师：{consultation.lawyerName}
          </p>
        )}
      </div>

      {/* Messages */}
      <div className="px-6 py-4 space-y-4 max-h-96 overflow-y-auto">
        <p className="text-gray-500 text-center">暂无消息</p>
      </div>

      {/* Reply Input */}
      {consultation.status !== 'completed' && consultation.status !== 'cancelled' && (
        <div className="px-6 py-4 border-t border-gray-200">
          <div className="flex gap-2">
            <input
              type="text"
              placeholder="输入回复..."
              className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
              disabled={consultation.status === 'pending'}
            />
            <button
              type="button"
              className="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:bg-gray-300"
              disabled={consultation.status === 'pending'}
            >
              发送
            </button>
          </div>
          {consultation.status === 'pending' && (
            <p className="text-sm text-yellow-600 mt-2">
              正在为您分配律师，请稍候...
            </p>
          )}
        </div>
      )}
    </div>
  );
}