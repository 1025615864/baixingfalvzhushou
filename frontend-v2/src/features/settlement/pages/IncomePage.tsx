/**
 * IncomePage - 收入记录页面
 *
 * 功能：收入记录列表、筛选、导出
 */

import { logger } from '@/shared/lib/logger';
import { useState } from 'react';

import { useIncomeRecords, useWalletBalance } from '../hooks/useSettlements';
import { formatCurrency, formatDate } from '../utils/format';
import type { IncomeStatus } from '../types';

type StatusFilter = 'all' | IncomeStatus;

/**
 * 状态标签配置
 */
const statusConfig: Record<IncomeStatus, { label: string; color: string }> = {
  pending: { label: '待结算', color: 'text-yellow-600 bg-yellow-50' },
  settled: { label: '已结算', color: 'text-green-600 bg-green-50' },
  cancelled: { label: '已取消', color: 'text-red-600 bg-red-50' },
};

/**
 * 收入统计卡片
 */
function IncomeStatsCard(): JSX.Element {
  const { data: wallet } = useWalletBalance();

  return (
    <div className="bg-gradient-to-r from-green-600 to-emerald-600 rounded-xl shadow-lg p-6 text-white">
      <p className="text-white/70 text-sm mb-2">累计收入</p>
      <p className="text-4xl font-bold mb-4">
        {formatCurrency(wallet?.totalIncome || 0)}
      </p>
      <div className="grid grid-cols-3 gap-4 pt-4 border-t border-white/20">
        <div>
          <p className="text-white/60 text-xs">已结算</p>
          <p className="text-lg font-semibold">
            {formatCurrency((wallet?.totalIncome || 0) - (wallet?.pendingAmount || 0))}
          </p>
        </div>
        <div>
          <p className="text-white/60 text-xs">待结算</p>
          <p className="text-lg font-semibold">
            {formatCurrency(wallet?.pendingAmount || 0)}
          </p>
        </div>
        <div>
          <p className="text-white/60 text-xs">可提现</p>
          <p className="text-lg font-semibold">
            {formatCurrency(wallet?.availableAmount || 0)}
          </p>
        </div>
      </div>
    </div>
  );
}

/**
 * 筛选工具栏
 */
function FilterToolbar({
  statusFilter,
  onStatusFilterChange,
  onExport,
  total,
}: {
  statusFilter: StatusFilter;
  onStatusFilterChange: (status: StatusFilter) => void;
  onExport: () => void;
  total: number;
}): JSX.Element {
  const statusOptions: Array<{ value: StatusFilter; label: string }> = [
    { value: 'all', label: '全部状态' },
    { value: 'pending', label: '待结算' },
    { value: 'settled', label: '已结算' },
    { value: 'cancelled', label: '已取消' },
  ];

  return (
    <div className="bg-white rounded-xl shadow-sm p-4 mb-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        {/* 状态筛选 */}
        <div className="flex items-center gap-2">
          <span className="text-sm text-gray-600">状态：</span>
          <div className="flex gap-2">
            {statusOptions.map((option) => (
              <button
                key={option.value}
                onClick={() => onStatusFilterChange(option.value)}
                className={`px-3 py-1.5 text-sm rounded-lg transition-colors ${
                  statusFilter === option.value
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }`}
              >
                {option.label}
              </button>
            ))}
          </div>
        </div>

        {/* 操作按钮 */}
        <div className="flex items-center gap-3">
          <span className="text-sm text-gray-500">
            共 {total} 条记录
          </span>
          <button
            onClick={onExport}
            className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors text-sm font-medium"
          >
            📥 导出 CSV
          </button>
        </div>
      </div>
    </div>
  );
}

/**
 * 收入记录表格
 */
function IncomeTable({
  statusFilter,
}: {
  statusFilter: StatusFilter;
}): JSX.Element {
  const [page, setPage] = useState(1);
  const pageSize = 20;

  const { data, isLoading, error } = useIncomeRecords({
    page,
    pageSize,
    ...(statusFilter !== 'all' && { status: statusFilter }),
  });

  const records = data?.items || [];
  const meta = data?.meta;

  // 处理导出
  const handleExport = async (): Promise<void> => {
    try {
      const params: string[] = ['page=1', 'page_size=1000'];
      if (statusFilter !== 'all') {
        params.push(`status=${statusFilter}`);
      }
      const queryString = params.join('&');

      const response = await fetch(`/api/settlement/lawyer/income-records/export?${queryString}`, {
        method: 'GET',
        headers: {
          Authorization: `Bearer ${localStorage.getItem('token')}`,
        },
      });

      if (!response.ok) {
        throw new Error('导出失败');
      }

      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `income_records_${new Date().toISOString().split('T')[0]}.csv`;
      link.click();
      window.URL.revokeObjectURL(url);
    } catch (err) {
      logger.error('导出失败:', err);
      alert('导出失败，请稍后重试');
    }
  };

  // 分页处理
  const totalPages = meta?.totalPages || 1;

  return (
    <div className="space-y-4">
      <FilterToolbar
        statusFilter={statusFilter}
        onStatusFilterChange={() => {
          setPage(1);
        }}
        onExport={() => {
          void handleExport();
        }}
        total={meta?.total || 0}
      />

      {isLoading ? (
        <div className="bg-white rounded-xl shadow-sm p-6 animate-pulse">
          <div className="space-y-3">
            {[1, 2, 3, 4, 5].map((i) => (
              <div key={i} className="h-16 bg-gray-100 rounded"></div>
            ))}
          </div>
        </div>
      ) : error ? (
        <div className="bg-red-50 border border-red-200 rounded-xl p-6">
          <p className="text-red-600">加载收入记录失败</p>
        </div>
      ) : records.length === 0 ? (
        <div className="bg-white rounded-xl shadow-sm p-12 text-center">
          <div className="w-16 h-16 mx-auto mb-4 bg-gray-100 rounded-full flex items-center justify-center">
            <svg
              className="w-8 h-8 text-gray-400"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
              />
            </svg>
          </div>
          <h3 className="text-lg font-medium text-gray-900 mb-2">暂无收入记录</h3>
          <p className="text-gray-500">当您有咨询收入时，这里会显示详细的收入记录</p>
        </div>
      ) : (
        <>
          {/* 记录列表 */}
          <div className="bg-white rounded-xl shadow-sm overflow-hidden">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    收入来源
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    描述
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    金额
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    状态
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    结算时间
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    创建时间
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {records.map((record) => {
                  const statusInfo = statusConfig[record.status];
                  return (
                    <tr key={record.id} className="hover:bg-gray-50">
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm font-medium text-gray-900">
                          {record.sourceType === 'consultation' ? '咨询收入' : record.sourceType}
                        </div>
                        {record.orderNo && (
                          <div className="text-xs text-gray-500">
                            订单号：{record.orderNo}
                          </div>
                        )}
                      </td>
                      <td className="px-6 py-4">
                        <div className="text-sm text-gray-900">{record.description}</div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm font-semibold text-green-600">
                          +{formatCurrency(record.lawyerIncome || record.amount)}
                        </div>
                        {record.platformFee && (
                          <div className="text-xs text-gray-500">
                            平台费：{formatCurrency(record.platformFee)}
                          </div>
                        )}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span
                          className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${statusInfo.color}`}
                        >
                          {statusInfo.label}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {record.settleTime ? formatDate(record.settleTime) : '-'}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {formatDate(record.createdAt)}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>

          {/* 分页 */}
          {totalPages > 1 && (
            <div className="bg-white rounded-xl shadow-sm p-4 flex items-center justify-between">
              <div className="text-sm text-gray-500">
                第 {meta?.page || 1} 页，共 {meta?.totalPages || 1} 页，总计{' '}
                {meta?.total || 0} 条记录
              </div>
              <div className="flex gap-2">
                <button
                  onClick={() => setPage((p) => Math.max(1, p - 1))}
                  disabled={page === 1}
                  className="px-4 py-2 border rounded-lg text-sm font-medium disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50"
                >
                  上一页
                </button>
                <button
                  onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                  disabled={page === totalPages}
                  className="px-4 py-2 border rounded-lg text-sm font-medium disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50"
                >
                  下一页
                </button>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}

/**
 * 收入记录页面
 */
export function IncomePage(): JSX.Element {
  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 py-8">
        {/* 页面标题 */}
        <div className="mb-6">
          <h1 className="text-2xl font-bold text-gray-900">收入记录</h1>
          <p className="text-gray-500 mt-1">查看和管理您的所有收入</p>
        </div>

        {/* 统计卡片 */}
        <div className="mb-6">
          <IncomeStatsCard />
        </div>

        {/* 收入表格 */}
        <IncomeTable statusFilter="all" />
      </div>
    </div>
  );
}