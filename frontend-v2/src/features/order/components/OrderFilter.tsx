/**
 * OrderFilter - 订单筛选组件
 */

import type { OrderStatus, OrderType, OrderFilterParams } from '../types';

interface OrderFilterProps {
  value: OrderFilterParams;
  onChange: (value: OrderFilterParams) => void;
}

/**
 * 订单状态选项
 */
const statusOptions: Array<{ value: OrderStatus | ''; label: string }> = [
  { value: '', label: '全部状态' },
  { value: 'pending', label: '待支付' },
  { value: 'paid', label: '已支付' },
  { value: 'processing', label: '处理中' },
  { value: 'completed', label: '已完成' },
  { value: 'cancelled', label: '已取消' },
  { value: 'refunded', label: '已退款' },
];

/**
 * 订单类型选项
 */
const typeOptions: Array<{ value: OrderType | ''; label: string }> = [
  { value: '', label: '全部类型' },
  { value: 'consultation', label: '咨询订单' },
  { value: 'document', label: '文档订单' },
  { value: 'membership', label: '会员订单' },
  { value: 'service', label: '服务订单' },
  { value: 'other', label: '其他订单' },
];

/**
 * 订单筛选组件
 */
export function OrderFilter({ value, onChange }: OrderFilterProps): JSX.Element {
  const handleStatusChange = (status: string): void => {
    onChange({
      ...value,
      status: status as OrderStatus | undefined,
    });
  };

  const handleTypeChange = (orderType: string): void => {
    onChange({
      ...value,
      orderType: orderType as OrderType | undefined,
    });
  };

  const handleKeywordChange = (keyword: string): void => {
    onChange({
      ...value,
      keyword: keyword || undefined,
    });
  };

  const handleDateChange = (field: 'startDate' | 'endDate', date: string): void => {
    onChange({
      ...value,
      [field]: date || undefined,
    });
  };

  const handleReset = (): void => {
    onChange({});
  };

  const hasActiveFilters = value.status || value.orderType || value.startDate || value.endDate || value.keyword;

  return (
    <div className="bg-white rounded-lg border p-4 space-y-4">
      {/* 筛选行 */}
      <div className="flex flex-col sm:flex-row gap-4 flex-wrap">
        {/* 状态筛选 */}
        <div className="flex items-center gap-2">
          <label htmlFor="order-status" className="text-sm font-medium text-gray-700 whitespace-nowrap">
            订单状态：
          </label>
          <select
            id="order-status"
            value={value.status || ''}
            onChange={(e) => handleStatusChange(e.target.value)}
            className="px-3 py-1.5 text-sm border rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            {statusOptions.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        </div>

        {/* 类型筛选 */}
        <div className="flex items-center gap-2">
          <label htmlFor="order-type" className="text-sm font-medium text-gray-700 whitespace-nowrap">
            订单类型：
          </label>
          <select
            id="order-type"
            value={value.orderType || ''}
            onChange={(e) => handleTypeChange(e.target.value)}
            className="px-3 py-1.5 text-sm border rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            {typeOptions.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        </div>

        {/* 关键词搜索 */}
        <div className="flex items-center gap-2 flex-1 min-w-[200px]">
          <input
            type="text"
            placeholder="搜索订单号或标题"
            value={value.keyword || ''}
            onChange={(e) => handleKeywordChange(e.target.value)}
            className="flex-1 px-3 py-1.5 text-sm border rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>

        {/* 重置按钮 */}
        {hasActiveFilters && (
          <button
            type="button"
            onClick={handleReset}
            className="px-3 py-1.5 text-sm text-gray-600 hover:text-gray-900 border rounded hover:bg-gray-50 transition-colors"
          >
            重置筛选
          </button>
        )}
      </div>

      {/* 日期范围筛选 */}
      <div className="flex flex-col sm:flex-row gap-4 items-center">
        <span className="text-sm font-medium text-gray-700">创建时间：</span>
        <div className="flex items-center gap-2 flex-1">
          <input
            type="date"
            value={value.startDate || ''}
            onChange={(e) => handleDateChange('startDate', e.target.value)}
            className="px-3 py-1.5 text-sm border rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
          <span className="text-gray-500">至</span>
          <input
            type="date"
            value={value.endDate || ''}
            onChange={(e) => handleDateChange('endDate', e.target.value)}
            className="px-3 py-1.5 text-sm border rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>
      </div>
    </div>
  );
}