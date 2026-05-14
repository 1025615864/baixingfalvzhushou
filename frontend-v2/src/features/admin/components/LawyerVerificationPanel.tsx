import { Suspense, lazy } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Card, Typography, Tag, Button, Space } from 'antd';
import { Scale, CheckCircle, XCircle, Clock, Eye, Search } from 'lucide-react';
import { apiClient } from '@/shared/lib/api/client';

const { Title, Text } = Typography;

interface VerificationItem {
  id: string | number;
  lawyerName: string;
  certificateNo: string;
  lawFirm: string;
  years: number;
  specialties: string;
  status: 'pending' | 'approved' | 'rejected';
  submittedAt: string;
  documents: string[];
}

interface VerificationStats {
  pending: number;
  approved: number;
  rejected: number;
  total: number;
}

async function fetchLawyerVerifications(params: {
  status?: string;
  page?: number;
  pageSize?: number;
} = {}): Promise<{ items: VerificationItem[]; total: number }> {
  const { data } = await apiClient.get('/verification', { params });
  const d = (data as { data: { items: VerificationItem[]; total: number } }).data;
  return d ?? { items: [], total: 0 };
}

function VerificationSkeleton(): JSX.Element {
  return (
    <div className="space-y-3">
      {[1, 2, 3, 4].map(i => (
        <div key={i} className="h-24 animate-pulse rounded-lg bg-slate-100" />
      ))}
    </div>
  );
}

const statusConfig: Record<string, { label: string; color: string }> = {
  pending: { label: '待审核', color: 'orange' },
  approved: { label: '已通过', color: 'green' },
  rejected: { label: '已拒绝', color: 'red' },
};

export function LawyerVerificationPanel(): JSX.Element {
  const { data, isLoading } = useQuery({
    queryKey: ['admin', 'lawyer-verifications'],
    queryFn: () => fetchLawyerVerifications({ pageSize: 50 }),
  });

  const items = data?.items ?? [];

  const stats: VerificationStats = {
    pending: items.filter(i => i.status === 'pending').length,
    approved: items.filter(i => i.status === 'approved').length,
    rejected: items.filter(i => i.status === 'rejected').length,
    total: items.length,
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Scale className="w-6 h-6 text-blue-600" />
          <Title level={4} className="!mb-0">律师认证管理</Title>
        </div>
        <div className="relative">
          <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
          <input
            type="text"
            placeholder="搜索律师姓名或执业证号..."
            className="pl-9 pr-4 py-2 border border-gray-300 rounded-lg text-sm w-64 focus:ring-2 focus:ring-primary-500 outline-none"
          />
        </div>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {[
          { label: '待审核', count: stats.pending, icon: Clock, color: 'text-orange-600' },
          { label: '已通过', count: stats.approved, icon: CheckCircle, color: 'text-green-600' },
          { label: '已拒绝', count: stats.rejected, icon: XCircle, color: 'text-red-600' },
          { label: '总申请', count: stats.total, icon: Scale, color: 'text-blue-600' },
        ].map(item => (
          <Card key={item.label} className="h-full">
            <div className="flex items-center gap-3">
              <div className={`p-2.5 rounded-lg ${item.color.replace('text-', 'bg-').replace('600', '50')}`}>
                <item.icon className={`w-5 h-5 ${item.color}`} />
              </div>
              <div>
                <Text className="text-gray-500 text-xs">{item.label}</Text>
                <div className="text-xl font-bold text-gray-900">{item.count}</div>
              </div>
            </div>
          </Card>
        ))}
      </div>

      <Card title="认证申请列表">
        {isLoading ? (
          <VerificationSkeleton />
        ) : items.length === 0 ? (
          <div className="text-center py-12 text-gray-400">
            <Scale className="w-12 h-12 mx-auto mb-3" />
            <Text className="block">暂无认证申请</Text>
          </div>
        ) : (
          <div className="space-y-3">
            {items.map(item => {
              const cfg = statusConfig[item.status] ?? { label: item.status, color: 'default' };
              return (
                <Card key={item.id} size="small" className="hover:shadow-md transition-shadow">
                  <div className="flex items-start justify-between gap-4">
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-3 mb-2">
                        <Text className="font-medium text-gray-900">{item.lawyerName}</Text>
                        <Tag color={cfg.color}>{cfg.label}</Tag>
                      </div>
                      <div className="grid grid-cols-2 gap-x-6 gap-y-1 text-sm">
                        <Text className="text-gray-500">
                          执业证号：<span className="font-mono text-gray-700">{item.certificateNo}</span>
                        </Text>
                        <Text className="text-gray-500">
                          执业机构：<span className="text-gray-700">{item.lawFirm}</span>
                        </Text>
                        <Text className="text-gray-500">
                          执业年限：<span className="text-gray-700">{item.years}年</span>
                        </Text>
                        <Text className="text-gray-500">
                          擅长领域：<span className="text-gray-700">{item.specialties}</span>
                        </Text>
                      </div>
                      <div className="flex items-center gap-2 mt-2">
                        <Text className="text-xs text-gray-400 flex items-center gap-1">
                          <Clock className="w-3 h-3" />
                          {new Date(item.submittedAt).toLocaleString('zh-CN')}
                        </Text>
                        {item.documents && item.documents.length > 0 && (
                          <Tag color="blue" className="flex items-center gap-1">
                            <Eye className="w-3 h-3" />
                            {item.documents.length} 个附件
                          </Tag>
                        )}
                      </div>
                    </div>
                    {item.status === 'pending' && (
                      <Space>
                        <Button
                          type="primary"
                          size="small"
                          icon={<CheckCircle className="w-3.5 h-3.5" />}
                        >
                          通过
                        </Button>
                        <Button
                          danger
                          size="small"
                          icon={<XCircle className="w-3.5 h-3.5" />}
                        >
                          拒绝
                        </Button>
                      </Space>
                    )}
                  </div>
                </Card>
              );
            })}
          </div>
        )}
      </Card>
    </div>
  );
}