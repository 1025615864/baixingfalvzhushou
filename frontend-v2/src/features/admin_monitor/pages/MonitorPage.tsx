/**
 * MonitorPage - 系统监控页面
 * 管理员系统监控仪表盘
 */

import { useState, useMemo } from 'react';

import { MetricCard, StatusCard, ResourceCard } from '../components/MetricCard';
import { AlertList, AlertSummary } from '../components/AlertList';
import { LogViewer } from '../components/LogViewer';
import {
  ResourceUsageChart,
  RequestTrendChart,
  ApiEndpointChart,
  StatusDistributionChart,
} from '../components/Charts';
import {
  useDashboard,
  useHealthCheck,
  useSystemInfo,
  useAlerts,
  useResourceUsageData,
  useRequestTrendData,
  useApiMetrics,
  useDatabaseStatus,
  useCacheStatus,
  useWebSocketStatus,
  useLogs,
} from '../hooks/useMonitor';

// ==================== 图标组件 ====================

const Icons = {
  LayoutDashboard: ({ className }: { className?: string }) => (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <rect x="3" y="3" width="7" height="7" />
      <rect x="14" y="3" width="7" height="7" />
      <rect x="14" y="14" width="7" height="7" />
      <rect x="3" y="14" width="7" height="7" />
    </svg>
  ),
  Activity: ({ className }: { className?: string }) => (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M22 12h-4l-3 9L9 3l-3 9H2" />
    </svg>
  ),
  AlertCircle: ({ className }: { className?: string }) => (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="12" cy="12" r="10" />
      <line x1="12" y1="8" x2="12" y2="12" />
      <line x1="12" y1="16" x2="12.01" y2="16" />
    </svg>
  ),
  FileText: ({ className }: { className?: string }) => (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M14.5 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7.5L14.5 2z" />
      <polyline points="14 2 14 8 20 8" />
    </svg>
  ),
  Server: ({ className }: { className?: string }) => (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <rect x="2" y="2" width="20" height="8" rx="2" ry="2" />
      <rect x="2" y="14" width="20" height="8" rx="2" ry="2" />
      <line x1="6" y1="6" x2="6.01" y2="6" />
      <line x1="6" y1="18" x2="6.01" y2="18" />
    </svg>
  ),
  RefreshCw: ({ className }: { className?: string }) => (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M21 12a9 9 0 0 0-9-9 9.75 9.75 0 0 0-6.74 2.74L3 8" />
      <path d="M3 3v5h5" />
      <path d="M3 12a9 9 0 0 0 9 9 9.75 9.75 0 0 0 6.74-2.74L21 16" />
      <path d="M16 16h5v5" />
    </svg>
  ),
  Cpu: ({ className }: { className?: string }) => (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <rect x="4" y="4" width="16" height="16" rx="2" />
      <rect x="9" y="9" width="6" height="6" />
      <path d="M9 1v3M15 1v3M9 20v3M15 20v3M20 9h3M20 14h3M1 9h3M1 14h3" />
    </svg>
  ),
  Database: ({ className }: { className?: string }) => (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <ellipse cx="12" cy="5" rx="9" ry="3" />
      <path d="M3 5V19A9 3 0 0 0 21 19V5" />
      <path d="M3 12A9 3 0 0 0 21 12" />
    </svg>
  ),
  Wifi: ({ className }: { className?: string }) => (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M5 12.55a11 11 0 0 1 14.08 0" />
      <path d="M1.42 9a16 16 0 0 1 21.16 0" />
      <path d="M8.53 16.11a6 6 0 0 1 6.95 0" />
      <line x1="12" y1="20" x2="12.01" y2="20" />
    </svg>
  ),
  Users: ({ className }: { className?: string }) => (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2" />
      <circle cx="9" cy="7" r="4" />
      <path d="M23 21v-2a4 4 0 0 0-3-3.87" />
      <path d="M16 3.13a4 4 0 0 1 0 7.75" />
    </svg>
  ),
  TrendingUp: ({ className }: { className?: string }) => (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <polyline points="23 6 13.5 15.5 8.5 10.5 1 18" />
      <polyline points="17 6 23 6 23 12" />
    </svg>
  ),
};

// ==================== Tab组件 ====================

type TabType = 'overview' | 'metrics' | 'alerts' | 'logs';

interface TabButtonProps {
  active: boolean;
  onClick: () => void;
  icon: React.ReactNode;
  label: string;
  badge?: number;
}

function TabButton({ active, onClick, icon, label, badge }: TabButtonProps): JSX.Element {
  return (
    <button
      onClick={onClick}
      className={`flex items-center gap-2 rounded-lg px-4 py-2 text-sm font-medium transition-colors ${
        active
          ? 'bg-blue-500 text-white'
          : 'text-gray-600 hover:bg-gray-100'
      }`}
    >
      {icon}
      {label}
      {badge !== undefined && badge > 0 && (
        <span className="ml-1 rounded-full bg-red-500 px-2 py-0.5 text-xs text-white">
          {badge}
        </span>
      )}
    </button>
  );
}

// ==================== 主组件 ====================

/**
 * 系统监控页面组件
 */
export function MonitorPage(): JSX.Element {
  const [activeTab, setActiveTab] = useState<TabType>('overview');

  // 数据获取
  const { data: dashboard, isLoading: dashboardLoading, refetch: refetchDashboard } = useDashboard();
  const { data: health, isLoading: healthLoading } = useHealthCheck();
  const { data: systemInfo, isLoading: systemInfoLoading } = useSystemInfo();
  const { data: alerts, isLoading: alertsLoading } = useAlerts(24);
  const resourceData = useResourceUsageData();
  const requestData = useRequestTrendData();
  const { data: apiMetrics, isLoading: apiMetricsLoading } = useApiMetrics();
  const { data: databaseStatus, isLoading: dbStatusLoading } = useDatabaseStatus();
  const { data: cacheStatus, isLoading: cacheStatusLoading } = useCacheStatus();
  const { data: websocketStatus, isLoading: wsStatusLoading } = useWebSocketStatus();
  const { data: logsData, isLoading: logsLoading } = useLogs();

  // 计算未解决的严重告警数
  const criticalAlertCount = useMemo(() => {
    return alerts?.alerts.filter((a) => !a.resolved && (a.level === 'critical' || a.level === 'error')).length ?? 0;
  }, [alerts]);

  // 刷新所有数据
  const handleRefresh = () => {
    void refetchDashboard();
  };

  // 渲染概览Tab
  const renderOverview = () => (
    <div className="space-y-6">
      {/* 关键指标卡片 */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <MetricCard
          title="系统状态"
          value={health?.status === 'healthy' ? '正常' : '异常'}
          icon="Server"
          color={health?.status === 'healthy' ? 'green' : 'red'}
          loading={healthLoading}
        />
        <MetricCard
          title="在线用户"
          value={dashboard?.websocketStatus.onlineUsers ?? 0}
          unit="人"
          icon="Users"
          color="blue"
          loading={dashboardLoading}
        />
        <MetricCard
          title="CPU使用率"
          value={systemInfo?.cpu.percent ?? 0}
          unit="%"
          icon="Cpu"
          color={systemInfo && systemInfo.cpu.percent > 80 ? 'red' : 'green'}
          loading={systemInfoLoading}
        />
        <MetricCard
          title="API请求/分"
          value={dashboard?.apiMetrics.endpoints ? Object.values(dashboard.apiMetrics.endpoints).reduce((sum, ep) => sum + ep.count, 0) : 0}
          icon="Activity"
          color="purple"
          loading={dashboardLoading}
        />
      </div>

      {/* 资源使用 */}
      <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">
        <ResourceCard
          title="内存使用"
          used={systemInfo ? systemInfo.memory.totalGb - systemInfo.memory.availableGb : 0}
          total={systemInfo?.memory.totalGb ?? 0}
          unit="GB"
          percentage={systemInfo?.memory.percent ?? 0}
          color={systemInfo && systemInfo.memory.percent > 80 ? 'red' : 'green'}
        />
        <ResourceCard
          title="磁盘使用"
          used={systemInfo ? systemInfo.disk.totalGb - systemInfo.disk.freeGb : 0}
          total={systemInfo?.disk.totalGb ?? 0}
          unit="GB"
          percentage={systemInfo?.disk.percent ?? 0}
          color={systemInfo && systemInfo.disk.percent > 80 ? 'red' : 'green'}
        />
        <ResourceCard
          title="WebSocket连接"
          used={websocketStatus?.totalConnections ?? 0}
          total={1000}
          unit="连接"
          percentage={((websocketStatus?.totalConnections ?? 0) / 1000) * 100}
          color="blue"
        />
      </div>

      {/* 告警摘要和系统状态 */}
      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <AlertSummary
          alerts={alerts?.alerts ?? []}
          onViewAll={() => setActiveTab('alerts')}
        />
        <div className="rounded-lg border bg-white p-4 shadow-sm">
          <h3 className="mb-4 font-semibold text-gray-900">服务状态</h3>
          <div className="space-y-2">
            <StatusCard
              title="数据库"
              status={databaseStatus?.status ?? 'unhealthy'}
              message={databaseStatus?.version ? `版本: ${databaseStatus.version}` : undefined}
              loading={dbStatusLoading}
            />
            <StatusCard
              title="缓存服务"
              status={cacheStatus?.status === 'healthy' ? 'healthy' : cacheStatus?.status === 'not_configured' ? 'degraded' : 'unhealthy'}
              message={cacheStatus?.message}
              loading={cacheStatusLoading}
            />
            <StatusCard
              title="WebSocket"
              status={websocketStatus && websocketStatus.totalConnections > 0 ? 'healthy' : 'degraded'}
              message={`${websocketStatus?.onlineUsers ?? 0} 在线用户`}
              loading={wsStatusLoading}
            />
          </div>
        </div>
      </div>

      {/* 图表 */}
      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <ResourceUsageChart data={resourceData} loading={systemInfoLoading} />
        <RequestTrendChart data={requestData} loading={dashboardLoading} />
      </div>
    </div>
  );

  // 渲染指标Tab
  const renderMetrics = () => (
    <div className="space-y-6">
      {/* API端点性能 */}
      <div className="rounded-lg border bg-white p-4 shadow-sm">
        <h3 className="mb-4 font-semibold text-gray-900">API性能指标</h3>
        <ApiEndpointChart
          endpoints={apiMetrics?.endpoints ?? {}}
          loading={apiMetricsLoading}
        />
      </div>

      {/* 系统状态分布 */}
      <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">
        <StatusDistributionChart
          healthy={health?.components.filter((c) => c.status === 'healthy').length ?? 0}
          unhealthy={health?.components.filter((c) => c.status === 'unhealthy').length ?? 0}
          degraded={health?.components.filter((c) => c.status === 'degraded').length ?? 0}
          loading={healthLoading}
        />
        <div className="lg:col-span-2 rounded-lg border bg-white p-4 shadow-sm">
          <h3 className="mb-4 font-semibold text-gray-900">组件详情</h3>
          <div className="space-y-2">
            {health?.components.map((component, index) => (
              <StatusCard
                key={index}
                title={component.name}
                status={component.status}
                message={component.message}
                responseTime={component.responseTime}
              />
            ))}
          </div>
        </div>
      </div>
    </div>
  );

  // 渲染告警Tab
  const renderAlerts = () => (
    <div className="space-y-6">
      <AlertList
        alerts={alerts?.alerts ?? []}
        loading={alertsLoading}
        showFilters={true}
        maxHeight="600px"
      />
    </div>
  );

  // 渲染日志Tab
  const renderLogs = () => (
    <div className="space-y-6">
      <LogViewer
        logs={logsData?.logs ?? []}
        total={logsData?.total ?? 0}
        loading={logsLoading}
      />
    </div>
  );

  return (
    <div className="min-h-screen bg-gray-50 p-4 sm:p-6 lg:p-8">
      {/* 页面头部 */}
      <div className="mb-6 flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">系统监控</h1>
          <p className="mt-1 text-sm text-gray-500">
            实时监控系统运行状态和性能指标
          </p>
        </div>
        <button
          onClick={handleRefresh}
          className="flex items-center gap-2 rounded-lg border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50"
        >
          <Icons.RefreshCw className="h-4 w-4" />
          刷新数据
        </button>
      </div>

      {/* Tab导航 */}
      <div className="mb-6 flex flex-wrap gap-2">
        <TabButton
          active={activeTab === 'overview'}
          onClick={() => setActiveTab('overview')}
          icon={<Icons.LayoutDashboard className="h-4 w-4" />}
          label="概览"
        />
        <TabButton
          active={activeTab === 'metrics'}
          onClick={() => setActiveTab('metrics')}
          icon={<Icons.Activity className="h-4 w-4" />}
          label="指标"
        />
        <TabButton
          active={activeTab === 'alerts'}
          onClick={() => setActiveTab('alerts')}
          icon={<Icons.AlertCircle className="h-4 w-4" />}
          label="告警"
          badge={criticalAlertCount}
        />
        <TabButton
          active={activeTab === 'logs'}
          onClick={() => setActiveTab('logs')}
          icon={<Icons.FileText className="h-4 w-4" />}
          label="日志"
        />
      </div>

      {/* Tab内容 */}
      <div className="animate-in fade-in duration-200">
        {activeTab === 'overview' && renderOverview()}
        {activeTab === 'metrics' && renderMetrics()}
        {activeTab === 'alerts' && renderAlerts()}
        {activeTab === 'logs' && renderLogs()}
      </div>
    </div>
  );
}

export default MonitorPage;