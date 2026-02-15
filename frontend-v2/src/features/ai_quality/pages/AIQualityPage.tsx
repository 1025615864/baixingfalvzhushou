/**
 * AIQualityPage - AI质量监控中心页面
 */

import { useState } from 'react';

import {
  useAIMetrics,
  useDashboardData,
  useQualityTrend,
  useSessionQuality,
  useSessionDetail,
  useReviewSession,
  useQualityAlerts,
  useAcknowledgeAlert,
  useResolveAlert,
  useAILogs,
} from '../hooks/useAIQuality';
import { QualityDashboard } from '../components/QualityDashboard';
import { SessionReview } from '../components/SessionReview';
import { AlertList } from '../components/AlertList';
import { MetricsChart } from '../components/MetricsChart';
import type { AlertLevel, AlertStatus, AlertType, ReviewResult, QualityLevel } from '../types';

/**
 * AI质量监控中心页面
 */
export function AIQualityPage(): JSX.Element {
  const [activeTab, setActiveTab] = useState('dashboard');
  const [selectedSessionId, setSelectedSessionId] = useState<string | null>(null);

  // 告警筛选和分页状态
  const [alertFilters, setAlertFilters] = useState<{
    level?: AlertLevel;
    status?: AlertStatus;
    type?: AlertType;
  }>({});
  const [alertPage, setAlertPage] = useState(1);
  const [alertPageSize] = useState(20);

  // 会话筛选和分页状态
  const [sessionFilters, setSessionFilters] = useState<{
    quality_level?: QualityLevel;
    start_date?: string;
    end_date?: string;
    search?: string;
  }>({});
  const [sessionPage, setSessionPage] = useState(1);
  const [sessionPageSize] = useState(20);

  // 质量指标数据
  const { data: metrics, isLoading: metricsLoading } = useAIMetrics();
  const { data: dashboardData, isLoading: dashboardLoading } = useDashboardData();
  const { data: trendData, isLoading: trendLoading } = useQualityTrend(7);

  // 会话列表 - 使用筛选和分页状态
  const { data: sessionList, isLoading: sessionListLoading } = useSessionQuality({
    page: sessionPage,
    page_size: sessionPageSize,
    ...sessionFilters,
  });

  // 会话详情
  const { data: sessionDetail, isLoading: sessionDetailLoading } = useSessionDetail({
    session_id: selectedSessionId || '',
  });

  // 告警列表
  const { data: alertsData, isLoading: alertsLoading } = useQualityAlerts({
    page: alertPage,
    page_size: alertPageSize,
    ...alertFilters,
  });

  // 日志列表
  const { data: logsData, isLoading: logsLoading } = useAILogs({
    limit: 100,
  });

  // Mutations
  const reviewMutation = useReviewSession();
  const acknowledgeMutation = useAcknowledgeAlert();
  const resolveMutation = useResolveAlert();

  // 处理会话选择
  const handleSessionSelect = (sessionId: string): void => {
    setSelectedSessionId(sessionId);
  };

  // 处理审核提交
  const handleReview = (
    result: ReviewResult,
    score: number,
    comment: string,
    issues: string[],
    suggestions: string[]
  ): void => {
    if (selectedSessionId) {
      reviewMutation.mutate({
        session_id: selectedSessionId,
        result,
        quality_score: score,
        comment,
        issues,
        suggestions,
      });
    }
  };

  // 处理确认告警
  const handleAcknowledgeAlert = (alertId: string): void => {
    acknowledgeMutation.mutate({ alert_id: alertId });
  };

  // 处理解决告警
  const handleResolveAlert = (alertId: string): void => {
    resolveMutation.mutate({ alert_id: alertId, resolution: '已处理' });
  };

  // 处理告警筛选
  const handleAlertFilterChange = (filters: {
    level?: AlertLevel;
    status?: AlertStatus;
    type?: AlertType;
  }): void => {
    setAlertFilters(filters);
    setAlertPage(1); // 重置分页
  };

  // 处理告警分页
  const handleAlertPageChange = (page: number): void => {
    setAlertPage(page);
  };

  // 处理会话筛选
  const handleSessionFilterChange = (filters: {
    quality_level?: QualityLevel;
    start_date?: string;
    end_date?: string;
    search?: string;
  }): void => {
    setSessionFilters(filters);
    setSessionPage(1); // 重置分页
  };

  // 处理会话分页
  const handleSessionPageChange = (page: number): void => {
    setSessionPage(page);
  };

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="mx-auto max-w-7xl">
        {/* 页面头部 */}
        <div className="mb-6">
          <h1 className="text-2xl font-bold text-gray-900">AI质量监控中心</h1>
          <p className="mt-1 text-sm text-gray-500">
            监控AI咨询质量指标、会话审核、告警管理和数据分析
          </p>
        </div>

        {/* 标签页导航 */}
        <div className="mb-6 border-b border-gray-200">
          <nav className="-mb-px flex space-x-8">
            {[
              { id: 'dashboard', label: '质量仪表盘' },
              { id: 'sessions', label: '会话审核' },
              { id: 'alerts', label: '告警管理' },
              { id: 'metrics', label: '指标分析' },
            ].map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`whitespace-nowrap border-b-2 py-4 px-1 text-sm font-medium transition-colors ${
                  activeTab === tab.id
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:border-gray-300 hover:text-gray-700'
                }`}
              >
                {tab.label}
              </button>
            ))}
          </nav>
        </div>
  
        {/* 标签页内容 */}
        <div className="space-y-6">
          {activeTab === 'dashboard' && (
            <QualityDashboard
              data={dashboardData}
              trendData={trendData}
              loading={dashboardLoading || trendLoading}
            />
          )}
  
          {activeTab === 'sessions' && (
            <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
              {/* 会话列表 */}
              <div className="lg:col-span-1">
                <div className="rounded-lg bg-white p-4 shadow-sm">
                  <div className="mb-4 flex items-center justify-between">
                    <h3 className="text-lg font-medium text-gray-900">会话列表</h3>
                    {/* 会话筛选占位 - 后续可添加筛选UI */}
                    <button
                      onClick={() => handleSessionFilterChange({})}
                      className="text-xs text-gray-400 hover:text-gray-600"
                    >
                      重置筛选
                    </button>
                  </div>
                  <div className="max-h-[800px] space-y-2 overflow-y-auto">
                    {sessionListLoading ? (
                      <div className="space-y-2">
                        {[1, 2, 3, 4, 5].map((i) => (
                          <div key={i} className="h-16 animate-pulse rounded bg-gray-200"></div>
                        ))}
                      </div>
                    ) : sessionList?.sessions.length === 0 ? (
                      <div className="py-8 text-center text-gray-500">暂无会话数据</div>
                    ) : (
                      sessionList?.sessions.map((session) => (
                        <button
                          key={session.id}
                          onClick={() => handleSessionSelect(session.session_id)}
                          className={`w-full rounded-lg border p-3 text-left transition-colors ${
                            selectedSessionId === session.session_id
                              ? 'border-blue-500 bg-blue-50'
                              : 'border-gray-200 hover:bg-gray-50'
                          }`}
                        >
                          <div className="flex items-center justify-between">
                            <span className="text-sm font-medium text-gray-900">
                              {session.user_name || `用户${session.user_id}`}
                            </span>
                            <span
                              className={`rounded px-2 py-0.5 text-xs ${
                                session.quality_score && session.quality_score >= 70
                                  ? 'bg-green-100 text-green-700'
                                  : session.quality_score && session.quality_score >= 50
                                  ? 'bg-yellow-100 text-yellow-700'
                                  : 'bg-red-100 text-red-700'
                              }`}
                            >
                              {session.quality_score?.toFixed(0) || 'N/A'}
                            </span>
                          </div>
                          <div className="mt-1 flex items-center justify-between text-xs text-gray-500">
                            <span>{session.message_count} 条消息</span>
                            <span>{new Date(session.created_at).toLocaleDateString()}</span>
                          </div>
                          {session.topics.length > 0 && (
                            <div className="mt-1 flex flex-wrap gap-1">
                              {session.topics.slice(0, 3).map((topic) => (
                                <span
                                  key={topic}
                                  className="rounded bg-gray-100 px-1.5 py-0.5 text-xs text-gray-600"
                                >
                                  {topic}
                                </span>
                              ))}
                            </div>
                          )}
                        </button>
                      ))
                    )}
                  </div>
                  {/* 分页控制 */}
                  {sessionList && sessionList.total > sessionPageSize && (
                    <div className="mt-4 flex items-center justify-center gap-2 border-t pt-4">
                      <button
                        onClick={() => handleSessionPageChange(sessionPage - 1)}
                        disabled={sessionPage <= 1}
                        className="rounded px-3 py-1 text-sm text-gray-600 hover:bg-gray-100 disabled:opacity-50"
                      >
                        上一页
                      </button>
                      <span className="text-sm text-gray-500">
                        第 {sessionPage} 页
                      </span>
                      <button
                        onClick={() => handleSessionPageChange(sessionPage + 1)}
                        disabled={sessionPage * sessionPageSize >= (sessionList?.total || 0)}
                        className="rounded px-3 py-1 text-sm text-gray-600 hover:bg-gray-100 disabled:opacity-50"
                      >
                        下一页
                      </button>
                    </div>
                  )}
                </div>
              </div>
  
              {/* 会话详情和审核 */}
              <div className="lg:col-span-2">
                {selectedSessionId ? (
                  <SessionReview
                    session={sessionDetail}
                    loading={sessionDetailLoading}
                    onReview={handleReview}
                  />
                ) : (
                  <div className="flex h-full min-h-[400px] items-center justify-center rounded-lg bg-white p-12 shadow-sm">
                    <div className="text-center">
                      <svg
                        className="mx-auto h-12 w-12 text-gray-400"
                        fill="none"
                        viewBox="0 0 24 24"
                        stroke="currentColor"
                      >
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          strokeWidth={2}
                          d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"
                        />
                      </svg>
                      <p className="mt-4 text-gray-500">请从左侧选择一个会话进行审核</p>
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}
  
          {activeTab === 'alerts' && alertsData && (
            <AlertList
              alerts={alertsData.alerts}
              total={alertsData.total}
              page={alertsData.page}
              pageSize={alertsData.page_size}
              summary={alertsData.summary}
              loading={alertsLoading}
              onPageChange={handleAlertPageChange}
              onAcknowledge={handleAcknowledgeAlert}
              onResolve={handleResolveAlert}
              onFilterChange={handleAlertFilterChange}
            />
          )}
  
          {activeTab === 'metrics' && (
            <MetricsChart
              metrics={metrics}
              trendData={trendData}
              loading={metricsLoading || trendLoading}
            />
          )}
        </div>

        {/* 日志预览 */}
        <div className="mt-8">
          <h3 className="mb-4 text-lg font-medium text-gray-900">最近日志</h3>
          <div className="rounded-lg bg-white p-4 shadow-sm">
            <div className="max-h-64 overflow-y-auto">
              {logsLoading ? (
                <div className="space-y-2">
                  {[1, 2, 3, 4, 5].map((i) => (
                    <div key={i} className="h-8 animate-pulse rounded bg-gray-200"></div>
                  ))}
                </div>
              ) : logsData?.logs.length === 0 ? (
                <div className="py-8 text-center text-gray-500">暂无日志数据</div>
              ) : (
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-4 py-2 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                        时间
                      </th>
                      <th className="px-4 py-2 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                        级别
                      </th>
                      <th className="px-4 py-2 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                        会话
                      </th>
                      <th className="px-4 py-2 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                        响应时间
                      </th>
                      <th className="px-4 py-2 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                        质量分
                      </th>
                      <th className="px-4 py-2 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                        话题
                      </th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-200">
                    {logsData?.logs.slice(0, 10).map((log) => (
                      <tr key={log.request_id} className="hover:bg-gray-50">
                        <td className="whitespace-nowrap px-4 py-2 text-sm text-gray-500">
                          {new Date(log.timestamp).toLocaleString()}
                        </td>
                        <td className="whitespace-nowrap px-4 py-2">
                          <span
                            className={`inline-flex rounded px-2 py-0.5 text-xs font-medium ${
                              log.level === 'error'
                                ? 'bg-red-100 text-red-700'
                                : log.level === 'warning'
                                ? 'bg-yellow-100 text-yellow-700'
                                : 'bg-blue-100 text-blue-700'
                            }`}
                          >
                            {log.level === 'error' ? '错误' : log.level === 'warning' ? '警告' : '信息'}
                          </span>
                        </td>
                        <td className="whitespace-nowrap px-4 py-2 text-sm text-gray-900">
                          {log.session_id ? log.session_id.slice(0, 8) : '-'}
                        </td>
                        <td className="whitespace-nowrap px-4 py-2 text-sm text-gray-900">
                          {log.response_time_ms}ms
                        </td>
                        <td className="whitespace-nowrap px-4 py-2 text-sm text-gray-900">
                          {log.quality_score || '-'}
                        </td>
                        <td className="px-4 py-2 text-sm text-gray-500">
                          {log.topics.slice(0, 2).join(', ') || '-'}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}