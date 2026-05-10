import { settlementStatusConfig } from '../../hooks/useSettlements';
import type { SettlementRecord, SettlementStatus } from '../../types';

interface SettlementCardProps {
  settlement: SettlementRecord;
}

export function SettlementCard({ settlement }: SettlementCardProps): JSX.Element {
  const settlementStatus: SettlementStatus = settlement.status;
  const status = settlementStatusConfig[settlementStatus];

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
      <div className="flex items-start justify-between mb-3">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="text-lg font-bold text-gray-900">
              {settlement.period} 结算
            </span>
            <span className={`px-2 py-0.5 text-xs font-medium rounded ${status.color}`}>
              {status.label}
            </span>
          </div>
          <p className="text-sm text-gray-500">
            {new Date(settlement.startDate).toLocaleDateString('zh-CN')} - {new Date(settlement.endDate).toLocaleDateString('zh-CN')}
          </p>
        </div>
        <div className="text-right">
          <p className="text-xl font-bold text-green-600">
            +¥{settlement.netAmount.toFixed(2)}
          </p>
          <p className="text-xs text-gray-400">净收入</p>
        </div>
      </div>

      <div className="grid grid-cols-3 gap-4 py-3 border-t border-b border-gray-100">
        <div className="text-center">
          <p className="text-sm font-medium text-gray-900">¥{settlement.totalIncome.toFixed(2)}</p>
          <p className="text-xs text-gray-400">总收入</p>
        </div>
        <div className="text-center border-x border-gray-100">
          <p className="text-sm font-medium text-red-600">-¥{settlement.platformFee.toFixed(2)}</p>
          <p className="text-xs text-gray-400">平台费 (10%)</p>
        </div>
        <div className="text-center">
          <p className="text-sm font-medium text-orange-600">-¥{settlement.taxAmount.toFixed(2)}</p>
          <p className="text-xs text-gray-400">税费 (9%)</p>
        </div>
      </div>

      <div className="flex items-center justify-between pt-3 text-xs text-gray-400">
        <time dateTime={settlement.createdAt}>
          结算时间: {new Date(settlement.createdAt).toLocaleString('zh-CN')}
        </time>
        {settlement.completedAt && (
          <span className="text-green-600">✓ 已到账</span>
        )}
      </div>
    </div>
  );
}