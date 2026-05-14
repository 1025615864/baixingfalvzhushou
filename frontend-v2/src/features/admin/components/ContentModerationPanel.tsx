import { Suspense, lazy } from 'react';
import { Card, Typography, Tag, Tabs } from 'antd';
import { Shield, FileText, MessageSquare, Star, Scale } from 'lucide-react';

const { Title, Text } = Typography;

const LazyForumContentModeration = lazy(() =>
  import('@/features/forum-admin/components/ContentModeration').then(m => ({ default: m.ContentModeration }))
);

function ModerationSectionSkeleton(): JSX.Element {
  return (
    <div className="space-y-3">
      {[1, 2, 3, 4].map(i => (
        <div key={i} className="h-20 animate-pulse rounded-lg bg-slate-100" />
      ))}
    </div>
  );
}

const contentTypeIcons: Record<string, React.ReactNode> = {
  post: <FileText className="w-4 h-4" />,
  comment: <MessageSquare className="w-4 h-4" />,
  review: <Star className="w-4 h-4" />,
  lawyer: <Scale className="w-4 h-4" />,
};

export function ContentModerationPanel(): JSX.Element {
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Shield className="w-6 h-6 text-blue-600" />
          <Title level={4} className="!mb-0">内容审核</Title>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        {[
          { label: '待审帖子', count: 5, color: 'orange' },
          { label: '待审评论', count: 3, color: 'red' },
          { label: '待审评价', count: 2, color: 'purple' },
          { label: '待审认证', count: 3, color: 'blue' },
        ].map(item => (
          <Card key={item.label} className="text-center" size="small">
            <Text className="text-gray-500 text-sm">{item.label}</Text>
            <div className={`text-2xl font-bold text-${item.color}-600`}>{item.count}</div>
          </Card>
        ))}
      </div>

      <Card title="审核队列" className="mt-4">
        <Suspense fallback={<ModerationSectionSkeleton />}>
          <LazyForumContentModeration />
        </Suspense>
      </Card>

      <Card title="审核规则" className="mt-4">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {[
            { name: '敏感词过滤', category: 'keyword_filter', enabled: true, severity: 'high' },
            { name: '联系方式检测', category: 'contact_filter', enabled: true, severity: 'high' },
            { name: '广告推广检测', category: 'ad_filter', enabled: true, severity: 'medium' },
            { name: '执业资质审核', category: 'lawyer_verify', enabled: true, severity: 'high' },
            { name: '虚假评价检测', category: 'review_filter', enabled: true, severity: 'medium' },
            { name: '发布频率限制', category: 'rate_limit', enabled: true, severity: 'low' },
          ].map(rule => (
            <Card key={rule.category} size="small" className="hover:shadow-md transition-shadow">
              <div className="flex items-start justify-between">
                <div>
                  <Text className="font-medium text-sm block">{rule.name}</Text>
                  <Text className="text-xs text-gray-400">{rule.category}</Text>
                </div>
                <Tag color={rule.enabled ? 'green' : 'default'}>
                  {rule.enabled ? '已启用' : '已禁用'}
                </Tag>
              </div>
            </Card>
          ))}
        </div>
      </Card>
    </div>
  );
}