/**
 * LawyerRecommendation 组件 - 律师推荐卡片
 */

import type { LawyerMatchResult } from '../types';

interface LawyerRecommendationProps {
  recommendation: LawyerMatchResult;
  onSelect: (lawyerId: string) => void;
  onBook: (lawyerId: string) => void;
  rank?: number;
}

export function LawyerRecommendation({
  recommendation,
  onSelect,
  onBook,
  rank,
}: LawyerRecommendationProps): JSX.Element {
  const {
    lawyerId,
    lawyerName,
    specialties,
    rating,
    completedCount,
    overallScore,
    matchReasons,
  } = recommendation;

  return (
    <div
      className="rounded-lg border border-gray-200 bg-white p-4 shadow-sm transition-shadow hover:shadow-md"
      role="button"
      tabIndex={0}
      onClick={() => onSelect(lawyerId)}
      onKeyDown={(e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          onSelect(lawyerId);
        }
      }}
    >
      {/* 排名标签 */}
      {rank !== undefined && rank <= 3 && (
        <div className="absolute -left-2 -top-2 flex h-6 w-6 items-center justify-center rounded-full bg-yellow-400 text-xs font-bold text-white shadow-sm">
          {rank}
        </div>
      )}

      {/* 头部信息 */}
      <div className="mb-3 flex items-start justify-between">
        <div className="flex items-center gap-3">
          <div className="flex h-12 w-12 items-center justify-center rounded-full bg-blue-100 text-lg font-bold text-blue-600">
            {lawyerName.charAt(0)}
          </div>
          <div>
            <h3 className="font-semibold text-gray-900">{lawyerName}</h3>
            <p className="text-sm text-gray-500 line-clamp-1">{specialties}</p>
          </div>
        </div>
        <div className="text-right">
          <div className="text-lg font-bold text-blue-600">{overallScore.toFixed(0)}%</div>
          <div className="text-xs text-gray-400">匹配度</div>
        </div>
      </div>

      {/* 匹配原因 */}
      {matchReasons.length > 0 && (
        <div className="mb-3 flex flex-wrap gap-1">
          {matchReasons.map((reason, index) => (
            <span
              key={index}
              className="inline-flex items-center rounded-full bg-green-50 px-2 py-0.5 text-xs text-green-700"
            >
              {reason}
            </span>
          ))}
        </div>
      )}

      {/* 统计数据 */}
      <div className="mb-4 grid grid-cols-2 gap-2 text-sm">
        <div className="flex items-center gap-1">
          <span className="text-gray-400">评分:</span>
          <span className="font-medium text-yellow-500">★ {rating.toFixed(1)}</span>
        </div>
        <div className="flex items-center gap-1">
          <span className="text-gray-400">咨询:</span>
          <span className="font-medium text-gray-700">{completedCount} 单</span>
        </div>
      </div>

      {/* 操作按钮 */}
      <div className="flex gap-2">
        <button
          type="button"
          onClick={(e) => {
            e.stopPropagation();
            onSelect(lawyerId);
          }}
          className="flex-1 rounded-md border border-gray-300 bg-white px-3 py-1.5 text-sm font-medium text-gray-700 transition-colors hover:bg-gray-50"
        >
          查看详情
        </button>
        <button
          type="button"
          onClick={(e) => {
            e.stopPropagation();
            onBook(lawyerId);
          }}
          className="flex-1 rounded-md bg-blue-600 px-3 py-1.5 text-sm font-medium text-white transition-colors hover:bg-blue-700"
        >
          立即预约
        </button>
      </div>
    </div>
  );
}