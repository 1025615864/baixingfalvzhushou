/**
 * Lawyer Verification Admin Page
 * 律师认证管理页面（管理员用）
 */

import { useState } from 'react';
import type { LucideIcon } from 'lucide-react';
import { CheckCircle, XCircle, Clock, Shield, Search, Eye } from 'lucide-react';

import { Badge } from '@/components/ui/Badge';
import { Button } from '@/components/ui/Button';
import { Card } from '@/components/ui/Card';
import { Input } from '@/components/ui/Input';
import { Pagination } from '@/components/ui/Pagination';

import { useVerificationAdmin, useReviewVerification } from '../hooks/useVerification';
import type { LawyerVerification } from '../types';

interface FilterItem {
  value: 'pending' | 'approved' | 'rejected' | '';
  label: string;
  icon: LucideIcon;
}

const FILTER_ITEMS: FilterItem[] = [
  { value: 'pending', label: '待审核', icon: Clock },
  { value: 'approved', label: '已通过', icon: CheckCircle },
  { value: 'rejected', label: '已拒绝', icon: XCircle },
  { value: '', label: '全部', icon: Shield },
];

/**
 * 律师认证管理页面
 */
export function LawyerVerificationAdminPage(): JSX.Element {
  const [page, setPage] = useState(1);
  const [pageSize] = useState(20);
  const [statusFilter, setStatusFilter] = useState<'pending' | 'approved' | 'rejected' | ''>('pending');
  const [keyword, setKeyword] = useState('');
  const [selectedVerification, setSelectedVerification] = useState<LawyerVerification | null>(null);
  const [isDetailModalOpen, setIsDetailModalOpen] = useState(false);
  const [isReviewModalOpen, setIsReviewModalOpen] = useState(false);
  const [reviewAction, setReviewAction] = useState<'approve' | 'reject'>('approve');
  const [rejectReason, setRejectReason] = useState('');

  // 数据查询
  const { data: verificationsData, isLoading } = useVerificationAdmin({
    page,
    pageSize,
    status: statusFilter || undefined,
    keyword: keyword || undefined,
  });

  // Mutations
  const reviewMutation = useReviewVerification();

  const verifications = verificationsData?.items ?? [];
  const total = verificationsData?.total ?? 0;
  const totalPages = Math.ceil(total / pageSize);

  // 处理查看详情
  const handleViewDetail = (verification: LawyerVerification): void => {
    setSelectedVerification(verification);
    setIsDetailModalOpen(true);
  };

  // 处理审核
  const handleReview = (verification: LawyerVerification, action: 'approve' | 'reject'): void => {
    setSelectedVerification(verification);
    setReviewAction(action);
    setRejectReason('');
    setIsReviewModalOpen(true);
  };

  // 提交审核
  const handleSubmitReview = (): void => {
    if (!selectedVerification) return;
    reviewMutation.mutate(
      {
        id: selectedVerification.id,
        request: {
          approved: reviewAction === 'approve',
          rejectReason: reviewAction === 'reject' ? rejectReason : undefined,
        },
      },
      {
        onSuccess: () => {
          setIsReviewModalOpen(false);
          setSelectedVerification(null);
        },
      }
    );
  };

  const getStatusBadge = (status: string): { label: string; variant: 'warning' | 'success' | 'danger' | 'default' } => {
    switch (status) {
      case 'pending':
        return { label: '待审核', variant: 'warning' };
      case 'approved':
        return { label: '已通过', variant: 'success' };
      case 'rejected':
        return { label: '已拒绝', variant: 'danger' };
      default:
        return { label: '未知', variant: 'default' };
    }
  };

  return (
    <div className="container mx-auto py-6">
      {/* 页面头部 */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">律师认证管理</h1>
          <p className="text-slate-600 mt-1">审核和管理律师认证申请</p>
        </div>
      </div>

      {/* 筛选栏 */}
      <Card className="mb-6">
        <div className="p-4 flex flex-wrap items-center gap-4">
          <div className="flex items-center gap-2">
            <Shield className="h-4 w-4 text-slate-500" />
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
          <div className="flex-1 min-w-[200px] ml-auto">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
              <Input
                placeholder="搜索律师姓名、律所..."
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

      {/* 认证列表 */}
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
              {verifications.map((verification) => {
                const status = getStatusBadge(verification.status);
                return (
                  <div key={verification.id} className="p-4 hover:bg-slate-50">
                    <div className="flex items-start justify-between">
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 mb-2">
                          <h3 className="font-medium text-slate-900">
                            {verification.realName}
                          </h3>
                          <Badge variant={status.variant} size="sm">
                            {status.label}
                          </Badge>
                        </div>
                        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm text-slate-500">
                          <div>
                            <span className="text-slate-400">执业证号：</span>
                            {verification.licenseNo}
                          </div>
                          <div>
                            <span className="text-slate-400">所属律所：</span>
                            {verification.firmName}
                          </div>
                          <div>
                            <span className="text-slate-400">执业年限：</span>
                            {verification.experienceYears} 年
                          </div>
                          <div>
                            <span className="text-slate-400">申请时间：</span>
                            {new Date(verification.createdAt).toLocaleDateString('zh-CN')}
                          </div>
                        </div>
                        {verification.specialties && (
                          <div className="mt-2 text-sm">
                            <span className="text-slate-400">专业领域：</span>
                            <span className="text-slate-600">{verification.specialties}</span>
                          </div>
                        )}
                        {verification.rejectReason && (
                          <div className="mt-2 text-sm text-red-600">
                            <span className="text-slate-400">审核意见：</span>
                            {verification.rejectReason}
                          </div>
                        )}
                      </div>
                      <div className="flex items-center gap-2 ml-4">
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleViewDetail(verification)}
                          title="查看详情"
                        >
                          <Eye className="h-4 w-4" />
                        </Button>
                        {verification.status === 'pending' && (
                          <>
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => handleReview(verification, 'approve')}
                              title="通过"
                            >
                              <CheckCircle className="h-4 w-4 text-green-500" />
                            </Button>
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => handleReview(verification, 'reject')}
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
              {!verifications.length && (
                <div className="p-10 text-center text-slate-500">
                  <Shield className="h-12 w-12 mx-auto mb-4 text-slate-300" />
                  <p>暂无认证申请</p>
                  <p className="text-sm mt-1">当有律师提交认证申请后会显示在这里</p>
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
      {isDetailModalOpen && selectedVerification && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl w-full max-w-2xl mx-4 max-h-[90vh] overflow-y-auto">
            <div className="p-6 border-b border-slate-200">
              <h2 className="text-lg font-semibold">认证详情</h2>
            </div>
            <div className="p-6 space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm text-slate-500 mb-1">真实姓名</label>
                  <p className="font-medium">{selectedVerification.realName}</p>
                </div>
                <div>
                  <label className="block text-sm text-slate-500 mb-1">身份证号</label>
                  <p className="font-medium">{selectedVerification.idCardNo}</p>
                </div>
                <div>
                  <label className="block text-sm text-slate-500 mb-1">执业证号</label>
                  <p className="font-medium">{selectedVerification.licenseNo}</p>
                </div>
                <div>
                  <label className="block text-sm text-slate-500 mb-1">所属律所</label>
                  <p className="font-medium">{selectedVerification.firmName}</p>
                </div>
                <div>
                  <label className="block text-sm text-slate-500 mb-1">执业年限</label>
                  <p className="font-medium">{selectedVerification.experienceYears} 年</p>
                </div>
                <div>
                  <label className="block text-sm text-slate-500 mb-1">申请时间</label>
                  <p className="font-medium">
                    {new Date(selectedVerification.createdAt).toLocaleString('zh-CN')}
                  </p>
                </div>
              </div>
              {selectedVerification.specialties && (
                <div>
                  <label className="block text-sm text-slate-500 mb-1">专业领域</label>
                  <p className="font-medium">{selectedVerification.specialties}</p>
                </div>
              )}
              {selectedVerification.rejectReason && (
                <div>
                  <label className="block text-sm text-slate-500 mb-1">审核意见</label>
                  <p className="text-red-600">{selectedVerification.rejectReason}</p>
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
      {isReviewModalOpen && selectedVerification && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl w-full max-w-lg mx-4">
            <div className="p-6 border-b border-slate-200">
              <h2 className="text-lg font-semibold">
                {reviewAction === 'approve' ? '通过认证' : '拒绝认证'}
              </h2>
            </div>
            <div className="p-6 space-y-4">
              <p className="text-slate-600">
                确定要{reviewAction === 'approve' ? '通过' : '拒绝'}
                <span className="font-medium text-slate-900"> {selectedVerification.realName} </span>
                的律师认证申请吗？
              </p>
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
