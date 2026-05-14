import { useQuery } from '@tanstack/react-query';
import {
  Activity, Server, Database, Wifi, AlertTriangle,
  CheckCircle, XCircle, RefreshCw, Clock, Monitor
} from 'lucide-react';
import { Button, Card, Typography } from 'antd';
import { apiClient } from '@/shared/lib/api/client';

const { Title, Text } = Typography;

interface HealthStatus {
  status: string;
  components: Record<string, string>;
}

interface MetricsSummary {
  api_requests: number;
  api_errors: number;
  ai_responses: number;
  websocket_connections: number;
  online_users: number;
}

interface AlertItem {
  rule_name: string;
  level: string;
  message: string;
  timestamp: string;
  resolved: boolean;
}

interface SystemInfo {
  platform: string;
  python_version: string;
  memory: { total_gb: number; available_gb: number; percent: number };
  disk: { total_gb: number; free_gb: number; percent: number };
  cpu: { percent: number; count: number };
}

interface DbStatus {
  status: string;
  connection: string;
  version?: string;
}

async function fetchHealth(): Promise<HealthStatus> {
  const { data } = await apiClient.get<HealthStatus>('/admin/monitor/health');
  return (data as unknown as { data: HealthStatus }).data ?? data;
}

async function fetchMetrics(): Promise<MetricsSummary> {
  const { data } = await apiClient.get<MetricsSummary>('/admin/monitor/metrics');
  return (data as unknown as { data: MetricsSummary }).data ?? data;
}

async function fetchAlerts(): Promise<{ alerts: AlertItem[]; total: number }> {
  const { data } = await apiClient.get<{ alerts: AlertItem[]; total: number }>('/admin/monitor/alerts', { params: { hours: 24 } });
  return (data as unknown as { data: { alerts: AlertItem[]; total: number } }).data ?? data;
}

async function fetchSystemInfo(): Promise<SystemInfo> {
  const { data } = await apiClient.get<SystemInfo>('/admin/monitor/system-info');
  return (data as unknown as { data: SystemInfo }).data ?? data;
}

async function fetchDbStatus(): Promise<DbStatus> {
  const { data } = await apiClient.get<DbStatus>('/admin/monitor/database-status');
  return (data as unknown as { data: DbStatus }).data ?? data;
}

function StatCard({
  icon: Icon,
  label,
  value,
  color,
}: {
  icon: React.ComponentType<{ className?: string }>;
  label: string;
  value: string | number;
  color: string;
}) {
  return (
    <Card className="h-full">
      <div className="flex items-center gap-3">
        <div className={`p-2.5 rounded-lg ${color.replace('text-', 'bg-').replace('600', '50')}`}>
          <Icon className={`w-5 h-5 ${color}`} />
        </div>
        <div>
          <Text className="text-gray-500 text-xs">{label}</Text>
          <div className="text-xl font-bold text-gray-900">{value}</div>
        </div>
      </div>
    </Card>
  );
}

export function SystemMonitorPanel(): JSX.Element {
  const { data: health, isLoading: healthLoading, refetch: refetchHealth } = useQuery({
    queryKey: ['admin', 'monitor', 'health'],
    queryFn: fetchHealth,
    refetchInterval: 30_000,
  });

  const { data: metrics, isLoading: metricsLoading } = useQuery({
    queryKey: ['admin', 'monitor', 'metrics'],
    queryFn: fetchMetrics,
    refetchInterval: 30_000,
  });

  const { data: alerts } = useQuery({
    queryKey: ['admin', 'monitor', 'alerts'],
    queryFn: fetchAlerts,
    refetchInterval: 30_000,
  });

  const { data: sysInfo } = useQuery({
    queryKey: ['admin', 'monitor', 'system'],
    queryFn: fetchSystemInfo,
    refetchInterval: 60_000,
  });

  const { data: dbStatus } = useQuery({
    queryKey: ['admin', 'monitor', 'db'],
    queryFn: fetchDbStatus,
    refetchInterval: 30_000,
  });

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <Title level={4} className="!mb-0">系统监控</Title>
        <Button
          icon={<RefreshCw className="w-4 h-4" />}
          onClick={() => { void refetchHealth(); }}
          size="small"
        >
          刷新
        </Button>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <StatCard
          icon={health?.status === 'healthy' ? CheckCircle : XCircle}
          label="系统状态"
          value={health?.status === 'healthy' ? '正常' : '异常'}
          color={health?.status === 'healthy' ? 'text-green-600' : 'text-red-600'}
        />
        <StatCard icon={Activity} label="API 请求" value={metrics?.api_requests ?? '--'} color="text-blue-600" />
        <StatCard icon={Wifi} label="在线用户" value={metrics?.online_users ?? '--'} color="text-purple-600" />
        <StatCard icon={Server} label="WS 连接" value={metrics?.websocket_connections ?? '--'} color="text-cyan-600" />
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <Card title={<span className="flex items-center gap-2"><Monitor className="w-4 h-4" />系统资源</span>}>
          {sysInfo ? (
            <div className="space-y-3">
              {sysInfo.memory && (
                <div>
                  <div className="flex justify-between text-sm mb-1">
                    <Text className="text-gray-500">内存</Text>
                    <Text>{sysInfo.memory.percent}%</Text>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div
                      className={`h-2 rounded-full ${sysInfo.memory.percent > 80 ? 'bg-red-500' : 'bg-green-500'}`}
                      style={{ width: `${sysInfo.memory.percent}%` }}
                    />
                  </div>
                  <Text className="text-xs text-gray-400">{sysInfo.memory.available_gb}GB / {sysInfo.memory.total_gb}GB</Text>
                </div>
              )}
              {sysInfo.cpu && (
                <div>
                  <div className="flex justify-between text-sm mb-1">
                    <Text className="text-gray-500">CPU ({sysInfo.cpu.count}核)</Text>
                    <Text>{sysInfo.cpu.percent}%</Text>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div
                      className={`h-2 rounded-full ${sysInfo.cpu.percent > 80 ? 'bg-red-500' : 'bg-blue-500'}`}
                      style={{ width: `${Math.min(sysInfo.cpu.percent, 100)}%` }}
                    />
                  </div>
                </div>
              )}
              {sysInfo.disk && (
                <div>
                  <div className="flex justify-between text-sm mb-1">
                    <Text className="text-gray-500">磁盘</Text>
                    <Text>{sysInfo.disk.percent}%</Text>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div
                      className={`h-2 rounded-full ${sysInfo.disk.percent > 80 ? 'bg-red-500' : 'bg-yellow-500'}`}
                      style={{ width: `${sysInfo.disk.percent}%` }}
                    />
                  </div>
                  <Text className="text-xs text-gray-400">{sysInfo.disk.free_gb}GB / {sysInfo.disk.total_gb}GB</Text>
                </div>
              )}
              <Text className="text-xs text-gray-400">
                {sysInfo.platform} · Python {sysInfo.python_version}
              </Text>
            </div>
          ) : (
            <div className="animate-pulse space-y-3">{[1, 2, 3].map(i => <div key={i} className="h-6 bg-gray-100 rounded" />)}</div>
          )}
        </Card>

        <Card title={<span className="flex items-center gap-2"><Database className="w-4 h-4" />数据库 & 告警</span>}>
          <div className="space-y-3">
            {dbStatus ? (
              <div className={`flex items-center gap-2 p-2 rounded ${dbStatus.status === 'healthy' ? 'bg-green-50' : 'bg-red-50'}`}>
                {dbStatus.status === 'healthy' ? <CheckCircle className="w-4 h-4 text-green-600" /> : <XCircle className="w-4 h-4 text-red-600" />}
                <Text className={dbStatus.status === 'healthy' ? 'text-green-700' : 'text-red-700'}>
                  {dbStatus.connection} · {dbStatus.version ?? 'unknown'}
                </Text>
              </div>
            ) : (
              <div className="animate-pulse h-8 bg-gray-100 rounded" />
            )}

            <Text className="text-sm font-medium text-gray-700 flex items-center gap-2">
              <AlertTriangle className="w-4 h-4" /> 最近告警
            </Text>
            {alerts?.alerts && alerts.alerts.length > 0 ? (
              <div className="space-y-2 max-h-48 overflow-y-auto">
                {alerts.alerts.slice(0, 8).map((a, i) => (
                  <div key={i} className={`p-2 rounded text-sm flex items-start gap-2 ${
                    a.level === 'critical' ? 'bg-red-50' :
                    a.level === 'warning' ? 'bg-yellow-50' : 'bg-blue-50'
                  }`}>
                    <span className={`w-2 h-2 rounded-full mt-1.5 flex-shrink-0 ${
                      a.level === 'critical' ? 'bg-red-500' :
                      a.level === 'warning' ? 'bg-yellow-500' : 'bg-blue-500'
                    }`} />
                    <div className="flex-1 min-w-0">
                      <Text className="text-xs text-gray-700 block truncate">{a.message}</Text>
                      <Text className="text-xs text-gray-400 flex items-center gap-1">
                        <Clock className="w-3 h-3" />
                        {new Date(a.timestamp).toLocaleString('zh-CN')}
                      </Text>
                    </div>
                    {a.resolved && <CheckCircle className="w-4 h-4 text-green-500 flex-shrink-0" />}
                  </div>
                ))}
              </div>
            ) : (
              <Text className="text-xs text-gray-400">暂无告警</Text>
            )}
          </div>
        </Card>
      </div>
    </div>
  );
}