import React from 'react';
import { DashboardOutlined, DownloadOutlined, FileTextOutlined, TeamOutlined } from '@ant-design/icons';
import { Button, Card, Space, Typography } from 'antd';

import { useExportLawfirms, useExportNews, useExportPosts, useExportUsers } from '../hooks/useAdmin';

const { Title } = Typography;

const ExportCard: React.FC<{
  title: string;
  description: string;
  icon: React.ReactNode;
  onExport: () => void;
  loading: boolean;
}> = ({ title, description, icon, onExport, loading }) => (
  <Card className="h-full">
    <div className="flex items-start justify-between">
      <div>
        <div className="flex items-center gap-2 mb-2">
          {icon}
          <span className="font-medium">{title}</span>
        </div>
        <p className="text-gray-500 text-sm mb-4">{description}</p>
        <Button type="primary" icon={<DownloadOutlined />} onClick={onExport} loading={loading} size="small">
          导出 CSV
        </Button>
      </div>
    </div>
  </Card>
);

export function AdminExportPanel(): JSX.Element {
  const exportUsersMutation = useExportUsers();
  const exportPostsMutation = useExportPosts();
  const exportNewsMutation = useExportNews();
  const exportLawfirmsMutation = useExportLawfirms();

  return (
    <div className="space-y-6">
      <Title level={4}>数据导出</Title>
      <Space direction="vertical" size="middle" className="w-full">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <ExportCard
            title="导出用户数据"
            description="导出所有用户的基本信息，包含用户名、邮箱、角色等字段"
            icon={<TeamOutlined />}
            onExport={() => exportUsersMutation.mutate()}
            loading={exportUsersMutation.isPending}
          />
          <ExportCard
            title="导出帖子数据"
            description="导出论坛所有帖子的标题、作者、浏览量等信息"
            icon={<FileTextOutlined />}
            onExport={() => exportPostsMutation.mutate()}
            loading={exportPostsMutation.isPending}
          />
          <ExportCard
            title="导出新闻数据"
            description="导出新闻资讯的标题、分类、浏览量等统计信息"
            icon={<DashboardOutlined />}
            onExport={() => exportNewsMutation.mutate()}
            loading={exportNewsMutation.isPending}
          />
          <ExportCard
            title="导出律所数据"
            description="导出所有律所的名称、地址、评分等信息"
            icon={<DashboardOutlined />}
            onExport={() => exportLawfirmsMutation.mutate()}
            loading={exportLawfirmsMutation.isPending}
          />
        </div>
      </Space>
    </div>
  );
}
