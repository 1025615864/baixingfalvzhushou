import { Suspense, lazy } from 'react';
import { BarChartOutlined, CheckCircleOutlined, ExportOutlined, RobotOutlined, TeamOutlined } from '@ant-design/icons';
import { Button, Card, Col, Row, Space, Statistic } from 'antd';

import { useAdminStats } from '../hooks/useAdmin';
import { useAIConfigStatsSummary } from '../hooks/useAIConfig';

const LazyStatsCards = lazy(() => import('./StatsCards').then((module) => ({ default: module.StatsCards })));

function AdminOverviewSkeleton({ rows = 2 }: { rows?: number }): JSX.Element {
  return (
    <div className="space-y-4">
      {Array.from({ length: rows }).map((_, index) => (
        <div key={index} className="h-24 animate-pulse rounded-lg bg-slate-100" />
      ))}
    </div>
  );
}

interface AdminOverviewPanelProps {
  onNavigate: (tab: string) => void;
}

export function AdminOverviewPanel({ onNavigate }: AdminOverviewPanelProps): JSX.Element {
  const { data: statsData, isLoading: statsLoading } = useAdminStats();
  const { data: aiConfigStats } = useAIConfigStatsSummary();

  return (
    <div className="space-y-6">
      <Suspense fallback={<AdminOverviewSkeleton rows={2} />}>
        <LazyStatsCards stats={statsData || null} loading={statsLoading} />
      </Suspense>

      <Card title="快速入口" className="mt-6">
        <Space size="large">
          <Button type="primary" icon={<TeamOutlined />} onClick={() => onNavigate('users')}>
            用户管理
          </Button>
          <Button icon={<RobotOutlined />} onClick={() => onNavigate('ai-config')}>
            AI配置
          </Button>
          <Button icon={<BarChartOutlined />} onClick={() => onNavigate('analytics')}>
            查看统计
          </Button>
          <Button icon={<ExportOutlined />} onClick={() => onNavigate('export')}>
            数据导出
          </Button>
        </Space>
      </Card>

      <Card title="系统状态" className="mt-6">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="p-4 bg-green-50 rounded-lg">
            <div className="text-green-600 font-medium">系统运行正常</div>
            <div className="text-green-400 text-sm">所有服务正常</div>
          </div>
          <div className="p-4 bg-blue-50 rounded-lg">
            <div className="text-blue-600 font-medium">API 响应正常</div>
            <div className="text-blue-400 text-sm">平均响应时间: 45ms</div>
          </div>
          <div className="p-4 bg-purple-50 rounded-lg">
            <div className="text-purple-600 font-medium">数据库连接正常</div>
            <div className="text-purple-400 text-sm">连接池: 8/20</div>
          </div>
        </div>
      </Card>

      <Card title="AI服务状态" className="mt-6">
        <Row gutter={16}>
          <Col span={6}>
            <Statistic title="总配置数" value={aiConfigStats?.total || 0} prefix={<RobotOutlined />} />
          </Col>
          <Col span={6}>
            <Statistic
              title="已启用"
              value={aiConfigStats?.enabled || 0}
              valueStyle={{ color: '#3f8600' }}
              prefix={<CheckCircleOutlined />}
            />
          </Col>
          <Col span={6}>
            <Statistic title="健康" value={aiConfigStats?.healthy || 0} valueStyle={{ color: '#52c41a' }} />
          </Col>
          <Col span={6}>
            <Statistic title="总调用次数" value={aiConfigStats?.total_calls || 0} />
          </Col>
        </Row>
      </Card>
    </div>
  );
}
