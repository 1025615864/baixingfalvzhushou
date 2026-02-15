/**
 * LoginAuditTable - 登录审计表格组件
 */

import { useState } from 'react';
import {
  CalendarOutlined,
  EnvironmentOutlined,
  DesktopOutlined,
  ExclamationCircleOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined,
  ClockCircleOutlined,
} from '@ant-design/icons';

import type { LoginStatus } from '../types';
import { useLoginAudit, formatLoginStatus, formatRelativeTime } from '../hooks/useSecurity';

interface LoginAuditTableProps {
  pageSize?: number;
}

const statusIcons: Record<LoginStatus, React.ReactNode> = {
  success: <CheckCircleOutlined className="text-green-500" />,
  failed: <CloseCircleOutlined className="text-red-500" />,
  blocked: <ExclamationCircleOutlined className="text-orange-500" />,
  expired: <ClockCircleOutlined className="text-gray-500" />,
};

/**
 * 登录审计表格组件
 */
export function LoginAuditTable({ pageSize = 10 }: LoginAuditTableProps): JSX.Element {
  const [page, setPage] = useState<number>(1);
  const [filterStatus, setFilterStatus] = useState<LoginStatus | ''>('');
  
  const { data, isLoading, error } = useLoginAudit({
    page,
    pageSize,
    status: filterStatus || undefined,
  });

  const handlePageChange = (newPage: number): void => {
    if (newPage > 0 && (!data || newPage <= Math.ceil(data.total / pageSize))) {
      setPage(newPage);
    }
  };

  if (isLoading) {
    return (
      <div className="bg-white rounded-lg shadow-sm p-6">
        <div className="animate-pulse space-y-4">
          <div className="h-8 bg-gray-200 rounded w-1/4" />
          <div className="space-y-3">
            {Array.from({ length: 5 }).map((_, i) => (
              <div key={i} className="h-12 bg-gray-200 rounded" />
            ))}
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-white rounded-lg shadow-sm p-6">
        <div className="flex items-center text-red-600">
          <ExclamationCircleOutlined className="mr-2" />
          <span>加载登录记录失败</span>
        </div>
      </div>
    );
  }

  const records = data?.records || [];
  const total = data?.total || 0;
  const totalPages = Math.ceil(total / pageSize);

  return (
    <div className="bg-white rounded-lg shadow-sm">
      {/* 标题和筛选 */}
      <div className="p-4 border-b border-gray-200 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <h3 className="text-lg font-semibold text-gray-900">登录审计日志</h3>
        <div className="flex items-center gap-2">
          <select
            value={filterStatus}
            onChange={(e) => {
              setFilterStatus(e.target.value as LoginStatus | '');
              setPage(1);
            }}
            className="px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="">所有状态</option>
            <option value="success">成功</option>
            <option value="failed">失败</option>
            <option value="blocked">被阻止</option>
            <option value="expired">已过期</option>
          </select>
        </div>
      </div>

      {/* 表格 */}
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                状态
              </th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                设备/浏览器
              </th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                IP地址/位置
              </th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                时间
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-200">
            {records.length === 0 ? (
              <tr>
                <td colSpan={4} className="px-4 py-8 text-center text-gray-500">
                  暂无登录记录
                </td>
              </tr>
            ) : (
              records.map((record) => (
                <tr key={record.id} className="hover:bg-gray-50">
                  <td className="px-4 py-4 whitespace-nowrap">
                    <div className="flex items-center">
                      {statusIcons[record.status]}
                      <span className={`ml-2 text-sm ${formatLoginStatus(record.status).color}`}>
                        {formatLoginStatus(record.status).text}
                      </span>
                    </div>
                    {record.failureReason && (
                      <div className="text-xs text-gray-500 mt-1">
                        原因: {record.failureReason}
                      </div>
                    )}
                  </td>
                  <td className="px-4 py-4">
                    <div className="flex items-start">
                      <DesktopOutlined className="text-gray-400 mr-2 mt-0.5" />
                      <div>
                        <div className="text-sm text-gray-900">{record.browser}</div>
                        <div className="text-xs text-gray-500">{record.os} • {record.deviceType}</div>
                      </div>
                    </div>
                  </td>
                  <td className="px-4 py-4">
                    <div className="flex items-start">
                      <EnvironmentOutlined className="text-gray-400 mr-2 mt-0.5" />
                      <div>
                        <div className="text-sm text-gray-900">{record.ipAddress}</div>
                        {record.location && (
                          <div className="text-xs text-gray-500">{record.location}</div>
                        )}
                      </div>
                    </div>
                  </td>
                  <td className="px-4 py-4 whitespace-nowrap">
                    <div className="flex items-center text-sm text-gray-900">
                      <CalendarOutlined className="text-gray-400 mr-2" />
                      {formatRelativeTime(record.createdAt)}
                    </div>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* 分页 */}
      {totalPages > 1 && (
        <div className="p-4 border-t border-gray-200 flex items-center justify-between">
          <div className="text-sm text-gray-500">
            共 {total} 条记录，第 {page} / {totalPages} 页
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={() => handlePageChange(page - 1)}
              disabled={page <= 1}
              className="px-3 py-1 text-sm border border-gray-300 rounded hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              上一页
            </button>
            <button
              onClick={() => handlePageChange(page + 1)}
              disabled={page >= totalPages}
              className="px-3 py-1 text-sm border border-gray-300 rounded hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              下一页
            </button>
          </div>
        </div>
      )}
    </div>
  );
}