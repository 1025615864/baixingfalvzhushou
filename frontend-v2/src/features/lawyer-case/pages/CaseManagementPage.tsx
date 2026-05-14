import { useState } from 'react';
import { Plus, FileText, List } from 'lucide-react';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import { Card } from '@/components/ui/Card';
import { Pagination } from '@/components/ui/Pagination';
import { Loading } from '@/shared/components/Loading';
import { CaseStatsCards } from '../components/CaseStatsCards';
import { CaseCreateDialog } from '../components/CaseCreateDialog';
import { CaseDetail } from '../components/CaseDetail';
import { DispatchPool } from '../components/DispatchPool';
import { useCases, useCaseStats } from '../hooks/useCases';

const STATUS_MAP: Record<string, { label: string; variant: 'success' | 'warning' | 'default' }> = {
  active: { label: '进行中', variant: 'success' },
  closed: { label: '已结案', variant: 'default' },
  archived: { label: '已归档', variant: 'warning' },
};

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

export function CaseManagementPage(): JSX.Element {
  const [page, setPage] = useState(1);
  const [statusFilter, setStatusFilter] = useState<string | undefined>();
  const [showCreate, setShowCreate] = useState(false);
  const [selectedCaseId, setSelectedCaseId] = useState<number | null>(null);
  const [activeTab, setActiveTab] = useState<'cases' | 'pool'>('cases');

  const { data: casesData, isLoading } = useCases({ status: statusFilter, page, pageSize: 10 });
  const { data: statsData, isLoading: statsLoading } = useCaseStats();

  if (selectedCaseId) {
    return <CaseDetail caseId={selectedCaseId} onBack={() => setSelectedCaseId(null)} />;
  }

  const items = (casesData as { data?: { items: Array<{ id: number; caseNo: string; title: string; clientName: string | null; category: string; status: string; priority: number; source: string; createdAt: string }> } })?.data?.items
    ?? (casesData as { items?: Array<{ id: number; caseNo: string; title: string; clientName: string | null; category: string; status: string; priority: number; source: string; createdAt: string }> })?.items
    ?? [];
  const total = (casesData as { data?: { total: number } })?.data?.total ?? (casesData as { total?: number })?.total ?? 0;
  const pageSize = 10;

  const totalPages = Math.ceil(total / pageSize);

  return (
    <div className="max-w-6xl mx-auto px-4 py-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">案件管理</h1>
          <p className="text-sm text-gray-500 mt-1">管理您的案件和抢单</p>
        </div>
        <Button
          variant="primary"
          onClick={() => setShowCreate(true)}
          leftIcon={<Plus className="w-4 h-4" />}
        >
          创建案件
        </Button>
      </div>

      <CaseStatsCards stats={statsData as { activeCount: number; closedCount: number; winRate: number; winCount: number; channelDistribution: Array<{ channel: string; count: number }> } | undefined} isLoading={statsLoading} />

      <div className="flex gap-2 border-b pb-0">
        {[
          { key: 'cases' as const, label: '案件列表', icon: List },
          { key: 'pool' as const, label: '抢单池', icon: FileText },
        ].map((tab) => (
          <button
            key={tab.key}
            onClick={() => setActiveTab(tab.key)}
            className={`flex items-center gap-2 px-4 py-2.5 text-sm font-medium border-b-2 transition-colors -mb-[2px] ${
              activeTab === tab.key
                ? 'border-primary-500 text-primary-600'
                : 'border-transparent text-gray-500 hover:text-gray-700'
            }`}
          >
            <tab.icon className="w-4 h-4" />
            {tab.label}
          </button>
        ))}
      </div>

      {activeTab === 'pool' ? (
        <DispatchPool />
      ) : (
        <>
          <div className="flex items-center gap-2">
            {[
              { value: undefined, label: '全部' },
              { value: 'active', label: '进行中' },
              { value: 'closed', label: '已结案' },
              { value: 'archived', label: '已归档' },
            ].map((f) => (
              <button
                key={f.label}
                onClick={() => { setStatusFilter(f.value); setPage(1); }}
                className={`px-3 py-1.5 rounded-full text-xs font-medium transition-colors ${
                  statusFilter === f.value
                    ? 'bg-primary-100 text-primary-700'
                    : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                }`}
              >
                {f.label}
              </button>
            ))}
          </div>

          {isLoading ? (
            <Loading text="加载案件列表..." />
          ) : items.length === 0 ? (
            <Card padding="lg">
              <div className="text-center py-12 text-gray-400">
                <FileText className="w-12 h-12 mx-auto mb-3" />
                <p className="text-sm">暂无案件</p>
                <p className="text-xs mt-1">点击"创建案件"开始管理您的案件</p>
              </div>
            </Card>
          ) : (
            <div className="space-y-3">
              {items.map((c) => {
                const statusInfo = STATUS_MAP[c.status] ?? { label: c.status, variant: 'default' as const };
                return (
                  <Card
                    key={c.id}
                    padding="md"
                    className="cursor-pointer hover:shadow-md transition-shadow"
                    onClick={() => setSelectedCaseId(c.id)}
                  >
                    <div className="flex items-start justify-between gap-4">
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 mb-1">
                          <Badge variant={statusInfo.variant} size="sm">{statusInfo.label}</Badge>
                          <Badge variant="default" size="sm">
                            {CATEGORY_LABELS[c.category] ?? c.category}
                          </Badge>
                          {c.priority === 1 && (
                            <Badge variant="danger" size="sm">紧急</Badge>
                          )}
                        </div>
                        <h4 className="text-sm font-medium text-gray-900 truncate">{c.title}</h4>
                        <div className="flex items-center gap-3 mt-1.5 text-xs text-gray-400">
                          <span>编号：{c.caseNo}</span>
                          {c.clientName && <span>当事人：{c.clientName}</span>}
                          <span>{new Date(c.createdAt).toLocaleDateString('zh-CN')}</span>
                        </div>
                      </div>
                    </div>
                  </Card>
                );
              })}

              <Pagination
                currentPage={page}
                totalPages={totalPages}
                pageSize={pageSize}
                onPageChange={setPage}
              />
            </div>
          )}
        </>
      )}

      <CaseCreateDialog
        isOpen={showCreate}
        onClose={() => setShowCreate(false)}
        onSuccess={() => setShowCreate(false)}
      />
    </div>
  );
}