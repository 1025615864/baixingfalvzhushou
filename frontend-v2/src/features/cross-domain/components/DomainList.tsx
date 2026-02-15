/**
 * DomainList - 域名列表组件
 */

import type { DomainConfig, DomainStatus } from '../types';

interface DomainListProps {
  domains: DomainConfig[];
  isLoading: boolean;
  error: Error | null;
  onEdit: (domain: DomainConfig) => void;
  onDelete: (domainId: number) => void;
  onVerify: (domain: DomainConfig) => void;
}

const statusLabels: Record<DomainStatus, string> = {
  active: '正常',
  pending: '待验证',
  disabled: '已禁用',
  expired: '已过期',
};

const statusColors: Record<DomainStatus, string> = {
  active: 'bg-green-100 text-green-800',
  pending: 'bg-yellow-100 text-yellow-800',
  disabled: 'bg-red-100 text-red-800',
  expired: 'bg-gray-100 text-gray-800',
};

/**
 * 域名列表组件
 */
export function DomainList({
  domains,
  isLoading,
  error,
  onEdit,
  onDelete,
  onVerify,
}: DomainListProps): JSX.Element {
  if (isLoading) {
    return (
      <div className="p-6 bg-white rounded-lg shadow-sm">
        <div className="animate-pulse space-y-4">
          <div className="h-4 bg-gray-200 rounded w-1/4" />
          <div className="space-y-2">
            <div className="h-12 bg-gray-200 rounded" />
            <div className="h-12 bg-gray-200 rounded" />
            <div className="h-12 bg-gray-200 rounded" />
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-6 bg-white rounded-lg shadow-sm">
        <div className="text-red-500">加载域名列表失败</div>
      </div>
    );
  }

  if (!domains || domains.length === 0) {
    return (
      <div className="p-6 bg-white rounded-lg shadow-sm">
        <div className="text-center text-gray-500 py-8">
          <svg
            className="w-12 h-12 mx-auto mb-4 text-gray-300"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={1.5}
              d="M21 12a9 9 0 01-9 9m9-9a9 9 0 00-9-9m9 9H3m9 9a9 9 0 01-9-9m9 9c1.657 0 3-4.03 3-9s-1.343-9-3-9m0 18c-1.657 0-3-4.03-3-9s1.343-9 3-9m-9 9a9 9 0 019-9"
            />
          </svg>
          <p>暂无域名配置</p>
          <p className="text-sm text-gray-400 mt-1">点击上方按钮添加域名</p>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow-sm overflow-hidden">
      <div className="overflow-x-auto">
        <table className="w-full text-left">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-xs font-medium text-gray-500 uppercase tracking-wider">
                域名
              </th>
              <th className="px-6 py-3 text-xs font-medium text-gray-500 uppercase tracking-wider">
                状态
              </th>
              <th className="px-6 py-3 text-xs font-medium text-gray-500 uppercase tracking-wider">
                验证状态
              </th>
              <th className="px-6 py-3 text-xs font-medium text-gray-500 uppercase tracking-wider">
                创建时间
              </th>
              <th className="px-6 py-3 text-xs font-medium text-gray-500 uppercase tracking-wider text-right">
                操作
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-200">
            {domains.map((domain) => (
              <tr key={domain.id} className="hover:bg-gray-50">
                <td className="px-6 py-4">
                  <div>
                    <p className="text-sm font-medium text-gray-900">{domain.domain}</p>
                    {domain.description && (
                      <p className="text-sm text-gray-500 mt-0.5">{domain.description}</p>
                    )}
                  </div>
                </td>
                <td className="px-6 py-4">
                  <span
                    className={`inline-flex px-2.5 py-0.5 text-xs font-medium rounded-full ${statusColors[domain.status]}`}
                  >
                    {statusLabels[domain.status]}
                  </span>
                </td>
                <td className="px-6 py-4">
                  {domain.isVerified ? (
                    <span className="inline-flex items-center px-2.5 py-0.5 text-xs font-medium rounded-full bg-green-100 text-green-800">
                      <svg className="w-3 h-3 mr-1" fill="currentColor" viewBox="0 0 20 20">
                        <path
                          fillRule="evenodd"
                          d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
                          clipRule="evenodd"
                        />
                      </svg>
                      已验证
                    </span>
                  ) : (
                    <span className="inline-flex items-center px-2.5 py-0.5 text-xs font-medium rounded-full bg-orange-100 text-orange-800">
                      <svg className="w-3 h-3 mr-1" fill="currentColor" viewBox="0 0 20 20">
                        <path
                          fillRule="evenodd"
                          d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z"
                          clipRule="evenodd"
                        />
                      </svg>
                      未验证
                    </span>
                  )}
                </td>
                <td className="px-6 py-4 text-sm text-gray-500">
                  {new Date(domain.createdAt).toLocaleDateString('zh-CN')}
                </td>
                <td className="px-6 py-4 text-right">
                  <div className="flex items-center justify-end gap-2">
                    {!domain.isVerified && (
                      <button
                        onClick={() => onVerify(domain)}
                        className="px-3 py-1.5 text-sm text-orange-600 hover:bg-orange-50 rounded-md transition-colors"
                      >
                        验证
                      </button>
                    )}
                    <button
                      onClick={() => onEdit(domain)}
                      className="px-3 py-1.5 text-sm text-blue-600 hover:bg-blue-50 rounded-md transition-colors"
                    >
                      编辑
                    </button>
                    <button
                      onClick={() => onDelete(domain.id)}
                      className="px-3 py-1.5 text-sm text-red-600 hover:bg-red-50 rounded-md transition-colors"
                    >
                      删除
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}