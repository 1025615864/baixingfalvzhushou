import { Clock, Tag, Zap } from 'lucide-react';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import { Card } from '@/components/ui/Card';
import { Loading } from '@/shared/components/Loading';
import { useDispatchPool, useGrabConsultation } from '../hooks/useCases';

const CATEGORY_LABELS: Record<string, string> = {
  civil: '民事纠纷',
  criminal: '刑事辩护',
  contract: '合同纠纷',
  labor: '劳动争议',
  family: '婚姻家庭',
  property: '房产纠纷',
  intellectual: '知识产权',
  corporate: '公司法务',
  other: '其他',
};

export function DispatchPool(): JSX.Element {
  const { data, isLoading } = useDispatchPool();
  const grabMutation = useGrabConsultation();

  if (isLoading) return <Loading text="加载抢单池..." />;

  const items = (data as { data?: { items: Array<{ id: number; category: string; title: string; description: string; createdAt: string }> } })?.data?.items
    ?? (data as { items?: Array<{ id: number; category: string; title: string; description: string; createdAt: string }> })?.items
    ?? [];

  const handleGrab = (consultationId: number) => {
    grabMutation.mutate(consultationId);
  };

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between mb-2">
        <h3 className="text-lg font-semibold text-gray-900">抢单池</h3>
        <Badge variant="warning">
          <Zap className="w-3 h-3 mr-1" />
          {items.length} 个待接单
        </Badge>
      </div>

      {items.length === 0 ? (
        <Card padding="lg">
          <div className="text-center py-8 text-gray-400">
            <Zap className="w-10 h-10 mx-auto mb-2" />
            <p className="text-sm">暂无待接单的咨询</p>
          </div>
        </Card>
      ) : (
        items.map((item) => (
          <Card key={item.id} padding="md" className="hover:shadow-md transition-shadow">
            <div className="flex items-start justify-between gap-4">
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 mb-1">
                  <Badge variant="primary" size="sm">
                    {CATEGORY_LABELS[item.category] ?? item.category}
                  </Badge>
                  <span className="text-xs text-gray-400 flex items-center gap-1">
                    <Clock className="w-3 h-3" />
                    {new Date(item.createdAt).toLocaleDateString('zh-CN')}
                  </span>
                </div>
                <h4 className="text-sm font-medium text-gray-900 truncate">{item.title}</h4>
                {item.description && (
                  <p className="text-xs text-gray-500 mt-1 line-clamp-2">{item.description}</p>
                )}
              </div>
              <Button
                variant="primary"
                size="sm"
                onClick={() => handleGrab(item.id)}
                isLoading={grabMutation.isPending && grabMutation.variables === item.id}
                disabled={grabMutation.isPending}
              >
                抢单
              </Button>
            </div>
          </Card>
        ))
      )}
    </div>
  );
}