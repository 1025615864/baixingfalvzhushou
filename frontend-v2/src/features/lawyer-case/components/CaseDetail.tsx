import { useState } from 'react';
import { ArrowLeft, Calendar, User, Tag, AlertTriangle, Folder } from 'lucide-react';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import { Card } from '@/components/ui/Card';
import { Loading } from '@/shared/components/Loading';
import { CaseTimeline } from './CaseTimeline';
import { useCaseDetail, useAddProgressNode, useCloseCase } from '../hooks/useCases';

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

interface CaseDetailProps {
  caseId: number;
  onBack: () => void;
}

export function CaseDetail({ caseId, onBack }: CaseDetailProps): JSX.Element {
  const { data: caseData, isLoading } = useCaseDetail(caseId);
  const [showAddProgress, setShowAddProgress] = useState(false);
  const [showClose, setShowClose] = useState(false);
  const [progressTitle, setProgressTitle] = useState('');
  const [progressDesc, setProgressDesc] = useState('');
  const [resultType, setResultType] = useState('win');
  const [resultReport, setResultReport] = useState('');

  const addProgressMutation = useAddProgressNode();
  const closeMutation = useCloseCase();

  if (isLoading) {
    return <Loading text="加载案件详情..." />;
  }

  if (!caseData) {
    return (
      <div className="text-center py-12">
        <p className="text-gray-500 mb-4">案件不存在</p>
        <Button variant="outline" onClick={onBack}>返回列表</Button>
      </div>
    );
  }

  const statusInfo = STATUS_MAP[caseData.status] ?? { label: caseData.status, variant: 'default' as const };
  const isActive = caseData.status === 'active';

  const handleAddProgress = () => {
    if (!progressTitle.trim()) return;
    addProgressMutation.mutate(
      {
        caseId,
        data: { title: progressTitle.trim(), description: progressDesc.trim() },
      },
      {
        onSuccess: () => {
          setProgressTitle('');
          setProgressDesc('');
          setShowAddProgress(false);
        },
      }
    );
  };

  const handleClose = () => {
    closeMutation.mutate(
      {
        caseId,
        data: { resultType, resultReport: resultReport.trim() || undefined },
      },
      {
        onSuccess: () => setShowClose(false),
      }
    );
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3">
        <button onClick={onBack} className="p-2 rounded-lg hover:bg-gray-100">
          <ArrowLeft className="w-5 h-5 text-gray-600" />
        </button>
        <h2 className="text-xl font-semibold text-gray-900 flex-1">{caseData.title}</h2>
        <Badge variant={statusInfo.variant}>{statusInfo.label}</Badge>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <Card padding="md">
          <div className="space-y-3">
            <div className="flex items-center gap-2 text-sm">
              <Tag className="w-4 h-4 text-gray-400" />
              <span className="text-gray-500">案件编号：</span>
              <span className="font-mono text-gray-900">{caseData.caseNo}</span>
            </div>
            <div className="flex items-center gap-2 text-sm">
              <Tag className="w-4 h-4 text-gray-400" />
              <span className="text-gray-500">案件类别：</span>
              <span className="text-gray-900">{CATEGORY_LABELS[caseData.category] ?? caseData.category}</span>
            </div>
            {caseData.clientName && (
              <div className="flex items-center gap-2 text-sm">
                <User className="w-4 h-4 text-gray-400" />
                <span className="text-gray-500">当事人：</span>
                <span className="text-gray-900">{caseData.clientName}</span>
              </div>
            )}
            <div className="flex items-center gap-2 text-sm">
              <Calendar className="w-4 h-4 text-gray-400" />
              <span className="text-gray-500">创建时间：</span>
              <span className="text-gray-900">{new Date(caseData.createdAt).toLocaleDateString('zh-CN')}</span>
            </div>
            {caseData.priority === 1 && (
              <Badge variant="danger">
                <AlertTriangle className="w-3 h-3 mr-1" />
                紧急
              </Badge>
            )}
          </div>
        </Card>

        {(caseData.resultType || caseData.resultReport) && (
          <Card padding="md">
            <h3 className="text-sm font-medium text-gray-700 mb-3">结案信息</h3>
            <p className="text-sm text-gray-600">
              结果类型：{caseData.resultType === 'win' ? '胜诉' : caseData.resultType === 'lose' ? '败诉' : caseData.resultType === 'mediation' ? '调解' : caseData.resultType === 'withdrawal' ? '撤诉' : caseData.resultType}
            </p>
            {caseData.resultReport && (
              <p className="text-sm text-gray-600 mt-1">{caseData.resultReport}</p>
            )}
          </Card>
        )}
      </div>

      {isActive && (
        <div className="flex gap-2">
          <Button
            variant="outline"
            size="sm"
            leftIcon={<Folder className="w-3.5 h-3.5" />}
            onClick={() => setShowClose(true)}
          >
            结案归档
          </Button>
        </div>
      )}

      <Card padding="md">
        <CaseTimeline
          nodes={caseData.progressNodes ?? []}
          onAddNode={isActive ? () => setShowAddProgress(true) : undefined}
        />
      </Card>

      {showAddProgress && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
          <div className="w-full max-w-sm bg-white rounded-xl shadow-xl p-6 space-y-4">
            <h3 className="text-lg font-semibold text-gray-900">添加进度</h3>
            <input
              type="text"
              value={progressTitle}
              onChange={(e) => setProgressTitle(e.target.value)}
              placeholder="进度标题"
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 outline-none"
            />
            <textarea
              value={progressDesc}
              onChange={(e) => setProgressDesc(e.target.value)}
              placeholder="进度描述（选填）"
              rows={3}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 outline-none resize-none"
            />
            <div className="flex gap-2">
              <Button variant="outline" fullWidth onClick={() => setShowAddProgress(false)}>取消</Button>
              <Button
                variant="primary"
                fullWidth
                onClick={handleAddProgress}
                disabled={!progressTitle.trim()}
                isLoading={addProgressMutation.isPending}
              >
                确认添加
              </Button>
            </div>
          </div>
        </div>
      )}

      {showClose && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
          <div className="w-full max-w-sm bg-white rounded-xl shadow-xl p-6 space-y-4">
            <h3 className="text-lg font-semibold text-gray-900">结案归档</h3>
            <select
              value={resultType}
              onChange={(e) => setResultType(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 outline-none"
            >
              <option value="win">胜诉</option>
              <option value="lose">败诉</option>
              <option value="mediation">调解</option>
              <option value="withdrawal">撤诉</option>
            </select>
            <textarea
              value={resultReport}
              onChange={(e) => setResultReport(e.target.value)}
              placeholder="结案报告（选填）"
              rows={3}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 outline-none resize-none"
            />
            <div className="flex gap-2">
              <Button variant="outline" fullWidth onClick={() => setShowClose(false)}>取消</Button>
              <Button
                variant="primary"
                fullWidth
                onClick={handleClose}
                isLoading={closeMutation.isPending}
              >
                确认归档
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}