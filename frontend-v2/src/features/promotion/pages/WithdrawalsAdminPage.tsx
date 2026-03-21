/**
 * Withdrawals Admin Page
 * 提现管理页面（管理员用）
 */

import { useState } from 'react';
import type { LucideIcon } from 'lucide-react';
import { CreditCard, Download, Search, CheckCircle, XCircle, Clock, Eye } from 'lucide-react';

import { Badge } from '@/components/ui/Badge';
import { Button } from '@/components/ui/Button';
import { Card } from '@/components/ui/Card';
import { Input } from '@/components/ui/Input';
import { Pagination } from '@/components/ui/Pagination';

import {
  useWithdrawalsAdmin,
  useReviewWithdrawal,
  useExportWithdrawals,
} from '../hooks/useWithdrawals';
import type { WithdrawalItem, WithdrawalStatus } from '../types';

interface FilterItem {
  value: WithdrawalStatus | '';
  label: string;
  icon: LucideIcon;
}

const FILTER_ITEMS: FilterItem[] = [
  { value: 'pending', label: '待审核', icon: Clock },
  { value: 'approved', label: '已通过', icon: CheckCircle },
  { value: 'rejected', label: '已拒绝', icon: XCircle },
  { value: '', label: '全部', icon: CreditCard },
];

/**
 * 格式化金额
 */
function formatMoney(amount: number): string {
  return `¥${amount.toFixed(2)}`;
}

/**
 * 提现管理页面
 */
export function WithdrawalsAdminPage(): JSX.Element {
  const [page, setPage] = useState(1);
  const [pageSize] = useState(20);
  const [statusFilter, setStatusFilter] = useState<WithdrawalStatus | ''>('pending');
  const [keyword, setKeyword] = useState('');
  const [selectedWithdrawal, setSelectedWithdrawal] = useState<WithdrawalItem | null>(null);
  const [isDetailModalOpen, setIsDetailModalOpen] = useState(false);
  const [isReviewModalOpen, setIsReviewModalOpen] = useState(false);
  const [reviewAction, setReviewAction] = useState<'approve' | 'reject'>('approve');
  const [rejectReason, setRejectReason] = useState('');

  // 数据查询
  const { data: withdrawalsData, isLoading } = useWithdrawalsAdmin({
    page,
    pageSize,
    status: statusFilter || undefined,
    keyword: keyword || undefined,
  });

  // Mutations
  const reviewMutation = useReviewWithdrawal();
  const exportMutation = useExportWithdrawals();

  const withdrawals = withdrawalsData?.items ?? [];
  const total = withdrawalsData?.total ?? 0;
  const stats = withdrawalsData?.stats;
  const totalPages = Math.ceil(total / pageSize);

  // 处理查看详情
  const handleViewDetail = (withdrawal: WithdrawalItem): void => {
    setSelectedWithdrawal(withdrawal);
    setIsDetailModalOpen(true);
  };

  // 处理审核
  const handleReview = (withdrawal: WithdrawalItem, action: 'approve' | 'reject'): void => {
    setSelectedWithdrawal(withdrawal);
    setReviewAction(action);
    setRejectReason('');
    setIsReviewModalOpen(true);
  };

  // 提交审核
  const handleSubmitReview = (): void => {
    if (!selectedWithdrawal) return;
    reviewMutation.mutate(
      {
        id: selectedWithdrawal.id,
        request: {
          approved: reviewAction === 'approve',
          rejectReason: reviewAction === 'reject' ? rejectReason : undefined,
        },
      },
      {
        onSuccess: () => {
          setIsReviewModalOpen(false);
          setSelectedWithdrawal(null);
        },
      }
    );
  };

  // 处理导出
  const handleExport = (): void => {
    exportMutation.mutate({
      status: statusFilter || undefined,
      keyword: keyword || undefined,
    });
  };

  const getStatusBadge = (status: string): { label: string; variant: 'warning' | 'success' | 'danger' | 'primary' | 'default' } => {
    switch (status) {
      case 'pending':
        return { label: '待审核', variant: 'warning' };
      case 'approved':
        return { label: '已通过', variant: 'success' };
      case 'rejected':
        return { label: '已拒绝', variant: 'danger' };
      case 'completed':
        return { label: '已完成', variant: 'primary' };
      default:
        return { label: '未知', variant: 'default' };
    }
  };

  return (
    <div className="container mx-auto py-6">
      {/* 页面头部 */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">提现管理</h1>
          <p className="text-slate-600 mt-1">审核和管理律师提现申请</p>
        </div>
        <Button onClick={handleExport} disabled={exportMutation.isPending}>
          <Download className="h-4 w-4 mr-1" />
          {exportMutation.isPending ? '导出中...' : '导出记录'}
        </Button>
      </div>

      {/* 统计卡片 */}
      {stats && (
        <div className="grid grid-cols-2 md:grid-cols-5 gap-4 mb-6">
          <Card className="p-4">
            <p className="text-sm text-slate-500">全部申请</p>
            <p className="text-2xl font-bold text-slate-900">{stats.totalCount}</p>
            <p className="text-sm text-slate-600">{formatMoney(stats.totalAmount)}</p>
          </Card>
          <Card className="p-4">
            <p className="text-sm text-slate-500">待审核</p>
            <p className="text-2xl font-bold text-orange-600">{stats.pendingCount}</p>
            <p className="text-sm text-slate-600">{formatMoney(stats.pendingAmount)}</p>
          </Card>
          <Card className="p-4">
            <p className="text-sm text-slate-500">已通过</p>
            <p className="text-2xl font-bold text-green-600">{stats.approvedCount}</p>
            <p className="text-sm text-slate-600">{formatMoney(stats.approvedAmount)}</p>
          </Card>
          <Card className="p-4">
            <p className="text-sm text-slate-500">已拒绝</p>
            <p className="text-2xl font-bold text-red-600">{stats.rejectedCount}</p>
            <p className="text-sm text-slate-600">{formatMoney(stats.rejectedAmount)}</p>
          </Card>
          <Card className="p-4">
            <p className="text-sm text-slate-500">已完成</p>
            <p className="text-2xl font-bold text-blue-600">{stats.completedCount}</p>
            <p className="text-sm text-slate-600">{formatMoney(stats.completedAmount)}</p>
          </Card>
        </div>
      )}

      {/* 筛选栏 */}
      <Card className="mb-6">
        <div className="p-4 flex flex-wrap items-center gap-4">
          <div className="flex items-center gap-2">
            <CreditCard className="h-4 w-4 text-slate-500" />
            <span className="text-sm text-slate-700">状态筛选：</span>
          </div>
          <div className="flex gap-2">
            {FILTER_ITEMS.map((item) => (
              <Button
                key={item.value}
                variant={statusFilter === item.value ? 'primary' : 'ghost'}
                size="sm"
                onClick={() => {
                  setStatusFilter(item.value);
                  setPage(1);
                }}
              >
                <item.icon className="h-4 w-4 mr-1" />
                {item.label}
              </Button>
            ))}
          </div>
          <div className="flex-1 min-w-[200px] ml-auto flex gap-2">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
              <Input
                placeholder="搜索律师姓名、申请号..."
                value={keyword}
                onChange={(e: React.ChangeEvent<HTMLInputElement>) => {
                  setKeyword(e.target.value);
                  setPage(1);
                }}
                className="pl-10"
              />
            </div>
          </div>
        </div>
      </Card>

      {/* 提现列表 */}
      <Card>
        {isLoading ? (
          <div className="p-6 space-y-4">
            {Array.from({ length: 5 }).map((_, i) => (
              <div key={i} className="h-24 bg-slate-100 rounded animate-pulse" />
            ))}
          </div>
        ) : (
          <>
            <div className="divide-y divide-slate-200">
              {withdrawals.map((withdrawal) => {
                const status = getStatusBadge(withdrawal.status);
                return (
                  <div key={withdrawal.id} className="p-4 hover:bg-slate-50">
                    <div className="flex items-start justify-between">
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 mb-2">
                          <h3 className="font-medium text-slate-900">
                            {withdrawal.lawyerName ?? '未知律师'}
                          </h3>
                          <Badge variant={status.variant} size="sm">
                            {status.label}
                          </Badge>
                          <span className="text-xs text-slate-400">
                            {withdrawal.requestNo}
                          </span>
                        </div>
                        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm text-slate-500">
                          <div>
                            <span className="text-slate-400">申请金额：</span>
                            <span className="font-medium text-slate-700">
                              {formatMoney(withdrawal.amount)}
                            </span>
                          </div>
                          <div>
                            <span className="text-slate-400">手续费：</span>
                            {formatMoney(withdrawal.fee)}
                          </div>
                          <div>
                            <span className="text-slate-400">实际到账：</span>
                            <span className="font-medium text-green-600">
                              {formatMoney(withdrawal.actualAmount)}
                            </span>
                          </div>
                          <div>
                            <span className="text-slate-400">提现方式：</span>
                            {withdrawal.withdrawMethod}
                          </div>
                        </div>
                        <div className="mt-2 text-sm text-slate-500">
                          <span className="text-slate-400">账户：</span>
                          {withdrawal.accountInfoMasked}
                          <span className="mx-2">·</span>
                          <span className="text-slate-400">申请时间：</span>
                          {new Date(withdrawal.createdAt).toLocaleString('zh-CN')}
                        </div>
                        {withdrawal.rejectReason && (
                          <div className="mt-2 text-sm text-red-600">
                            <span className="text-slate-400">拒绝原因：</span>
                            {withdrawal.rejectReason}
                          </div>
                        )}
                        {withdrawal.remark && (
                          <div className="mt-2 text-sm text-slate-600">
                            <span className="text-slate-400">备注：</span>
                            {withdrawal.remark}
                          </div>
                        )}
                      </div>
                      <div className="flex items-center gap-2 ml-4">
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleViewDetail(withdrawal)}
                          title="查看详情"
                        >
                          <Eye className="h-4 w-4" />
                        </Button>
                        {withdrawal.status === 'pending' && (
                          <>
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => handleReview(withdrawal, 'approve')}
                              title="通过"
                            >
                              <CheckCircle className="h-4 w-4 text-green-500" />
                            </Button>
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => handleReview(withdrawal, 'reject')}
                              title="拒绝"
                            >
                              <XCircle className="h-4 w-4 text-red-500" />
                            </Button>
                          </>
                        )}
                      </div>
                    </div>
                  </div>
                );
              })}
              {!withdrawals.length && (
                <div className="p-10 text-center text-slate-500">
                  <CreditCard className="h-12 w-12 mx-auto mb-4 text-slate-300" />
                  <p>暂无提现申请</p>
                  <p className="text-sm mt-1">当有律师提交提现申请后会显示在这里</p>
                </div>
              )}
            </div>
            {totalPages > 1 && (
              <div className="p-4 border-t border-slate-200">
                <Pagination
                  currentPage={page}
                  totalPages={totalPages}
                  onPageChange={setPage}
                />
              </div>
            )}
          </>
        )}
      </Card>

      {/* 详情弹窗 */}
      {isDetailModalOpen && selectedWithdrawal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl w-full max-w-2xl mx-4 max-h-[90vh] overflow-y-auto">
            <div className="p-6 border-b border-slate-200">
              <h2 className="text-lg font-semibold">提现详情</h2>
            </div>
            <div className="p-6 space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm text-slate-500 mb-1">申请号</label>
                  <p className="font-medium">{selectedWithdrawal.requestNo}</p>
                </div>
                <div>
                  <label className="block text-sm text-slate-500 mb-1">律师</label>
                  <p className="font-medium">{selectedWithdrawal.lawyerName ?? '未知'}</p>
                </div>
                <div>
                  <label className="block text-sm text-slate-500 mb-1">申请金额</label>
                  <p className="font-medium text-lg">{formatMoney(selectedWithdrawal.amount)}</p>
                </div>
                <div>
                  <label className="block text-sm text-slate-500 mb-1">手续费</label>
                  <p className="font-medium">{formatMoney(selectedWithdrawal.fee)}</p>
                </div>
                <div>
                  <label className="block text-sm text-slate-500 mb-1">实际到账</label>
                  <p className="font-medium text-green-600">{formatMoney(selectedWithdrawal.actualAmount)}</p>
                </div>
                <div>
                  <label className="block text-sm text-slate-500 mb-1">提现方式</label>
                  <p className="font-medium">{selectedWithdrawal.withdrawMethod}</p>
                </div>
              </div>
              <div>
                <label className="block text-sm text-slate-500 mb-1">账户信息</label>
                <p className="font-medium">{selectedWithdrawal.accountInfoMasked}</p>
              </div>
              <div>
                <label className="block text-sm text-slate-500 mb-1">申请时间</label>
                <p className="font-medium">
                  {new Date(selectedWithdrawal.createdAt).toLocaleString('zh-CN')}
                </p>
              </div>
              {selectedWithdrawal.reviewedAt && (
                <div>
                  <label className="block text-sm text-slate-500 mb-1">审核时间</label>
                  <p className="font-medium">
                    {new Date(selectedWithdrawal.reviewedAt).toLocaleString('zh-CN')}
                  </p>
                </div>
              )}
              {selectedWithdrawal.rejectReason && (
                <div>
                  <label className="block text-sm text-slate-500 mb-1">拒绝原因</label>
                  <p className="text-red-600">{selectedWithdrawal.rejectReason}</p>
                </div>
              )}
              {selectedWithdrawal.remark && (
                <div>
                  <label className="block text-sm text-slate-500 mb-1">备注</label>
                  <p className="text-slate-600">{selectedWithdrawal.remark}</p>
                </div>
              )}
            </div>
            <div className="p-6 border-t border-slate-200 flex justify-end gap-3">
              <Button onClick={() => setIsDetailModalOpen(false)}>关闭</Button>
            </div>
          </div>
        </div>
      )}

      {/* 审核弹窗 */}
      {isReviewModalOpen && selectedWithdrawal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl w-full max-w-lg mx-4">
            <div className="p-6 border-b border-slate-200">
              <h2 className="text-lg font-semibold">
                {reviewAction === 'approve' ? '通过提现申请' : '拒绝提现申请'}
              </h2>
            </div>
            <div className="p-6 space-y-4">
              <div className="bg-slate-50 p-4 rounded-lg">
                <p className="text-sm text-slate-500">律师</p>
                <p className="font-medium">{selectedWithdrawal.lawyerName ?? '未知'}</p>
                <p className="text-sm text-slate-500 mt-2">申请金额</p>
                <p className="font-medium text-lg">{formatMoney(selectedWithdrawal.amount)}</p>
              </div>
              {reviewAction === 'reject' && (
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1">
                    拒绝原因
                  </label>
                  <textarea
                    value={rejectReason}
                    onChange={(e: React.ChangeEvent<HTMLTextAreaElement>) => setRejectReason(e.target.value)}
                    className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    rows={3}
                    placeholder="请输入拒绝原因..."
                  />
                </div>
              )}
            </div>
            <div className="p-6 border-t border-slate-200 flex justify-end gap-3">
              <Button variant="ghost" onClick={() => setIsReviewModalOpen(false)}>
                取消
              </Button>
              <Button
                variant={reviewAction === 'approve' ? 'primary' : 'danger'}
                onClick={handleSubmitReview}
                disabled={reviewAction === 'reject' && !rejectReason.trim()}
              >
                {reviewAction === 'approve' ? '确认通过' : '确认拒绝'}
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
