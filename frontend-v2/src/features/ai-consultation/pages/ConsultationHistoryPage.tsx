/**
 * ConsultationHistoryPage - 咨询历史页面
 * 
 * 显示用户的法律咨询历史记录
 */

import { useState } from 'react';
import { useNavigate } from 'react-router-dom';

import { useSessions } from '../hooks/useAIConsultation';
import type { AISession } from '../types';

/**
 * 咨询历史页面
 */
export function ConsultationHistoryPage(): JSX.Element {
  const navigate = useNavigate();
  const { data: sessions, isLoading } = useSessions({ pageSize: 20 });
  const [filter, setFilter] = useState<'all' | 'active' | 'completed'>('all');

  const filteredSessions = sessions?.filter((session) => {
    if (filter === 'all') return true;
    if (filter === 'active') return session.status === 'active';
    if (filter === 'completed') return session.status === 'archived';
    return true;
  });

  const getStatusLabel = (status: string): string => {
    const labels: Record<string, string> = {
      active: '进行中',
      archived: '已完成',
      deleted: '已删除',
    };
    return labels[status] || status;
  };

  return (
    <div className="container mx-auto px-4 py-6 max-w-4xl">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900" data-testid="page-title">咨询历史</h1>
          <p className="text-gray-600 mt-1">查看您的法律咨询记录</p>
        </div>
        <button
          onClick={() => navigate('/consultation/new')}
          className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors flex items-center gap-2"
          type="button"
        >
          <span>+</span>
          发起咨询
        </button>
      </div>

      {/* 筛选器 */}
      <div className="flex gap-2 mb-4">
        <button
          onClick={() => setFilter('all')}
          className={`px-3 py-1.5 rounded-lg text-sm transition-colors ${
            filter === 'all'
              ? 'bg-blue-100 text-blue-700'
              : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
          }`}
        >
          全部
        </button>
        <button
          onClick={() => setFilter('active')}
          className={`px-3 py-1.5 rounded-lg text-sm transition-colors ${
            filter === 'active'
              ? 'bg-blue-100 text-blue-700'
              : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
          }`}
        >
          进行中
        </button>
        <button
          onClick={() => setFilter('completed')}
          className={`px-3 py-1.5 rounded-lg text-sm transition-colors ${
            filter === 'completed'
              ? 'bg-blue-100 text-blue-700'
              : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
          }`}
        >
          已完成
        </button>
      </div>

      {/* 咨询列表 */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden" data-testid="consultation-list">
        {isLoading ? (
          <div className="p-4 space-y-3">
            {[1, 2, 3].map((i) => (
              <div key={i} className="h-16 bg-gray-100 rounded-lg animate-pulse" />
            ))}
          </div>
        ) : filteredSessions && filteredSessions.length > 0 ? (
          <table className="w-full">
            <thead className="bg-gray-50 border-b border-gray-200">
              <tr>
                <th className="px-4 py-3 text-left text-sm font-medium text-gray-500">标题</th>
                <th className="px-4 py-3 text-left text-sm font-medium text-gray-500">状态</th>
                <th className="px-4 py-3 text-left text-sm font-medium text-gray-500">最后活动</th>
                <th className="px-4 py-3 text-left text-sm font-medium text-gray-500">操作</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {filteredSessions.map((session: AISession) => (
                <tr key={session.id} className="hover:bg-gray-50 transition-colors">
                  <td className="px-4 py-3">
                    <div className="font-medium text-gray-900">{session.title}</div>
                  </td>
                  <td className="px-4 py-3">
                    <span className={`px-2 py-1 text-xs font-medium rounded-full ${getStatusLabel(session.status) === '进行中' ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'}`}>
                      {getStatusLabel(session.status)}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-sm text-gray-500">
                    {new Date(session.lastActivityAt).toLocaleDateString('zh-CN')}
                  </td>
                  <td className="px-4 py-3">
                    <button
                      onClick={() => navigate(`/ai-consultation/${session.id}`)}
                      className="text-blue-600 hover:text-blue-800 text-sm font-medium"
                      type="button"
                    >
                      查看
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : (
          <div className="p-8 text-center">
            <p className="text-gray-500 mb-4">暂无咨询记录</p>
            <button
              onClick={() => navigate('/consultation/new')}
              className="text-blue-600 hover:text-blue-800 font-medium"
              type="button"
            >
              发起第一个咨询
            </button>
          </div>
        )}
      </div>
    </div>
  );
}