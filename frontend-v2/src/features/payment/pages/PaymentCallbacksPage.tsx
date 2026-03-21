/**
 * Payment Callbacks Page
 * 支付回调管理页面（管理员用）
 */

import { useState } from 'react';
import { Search, RefreshCw, CheckCircle, XCircle, Eye } from 'lucide-react';

import { Badge } from '@/components/ui/Badge';
import { Button } from '@/components/ui/Button';
import { Card } from '@/components/ui/Card';
import { Input } from '@/components/ui/Input';
import { Pagination } from '@/components/ui/Pagination';

import {
  usePaymentCallbacks,
  useRetryPaymentCallback,
  useProcessPaymentCallback,
} from '../hooks/usePaymentCallbacks';
import type { PaymentCallback, CallbackStatus, CallbackSource } from '../types';

const STATUS_FILTERS: { value: CallbackStatus | ''; label: string }[] = [
  { value: 'pending', label: '待处理' },
  { value: 'success', label: '成功' },
  { value: 'failed', label: '失败' },
  { value: 'retrying', label: '重试中' },
  { value: '', label: '全部' },
];

const SOURCE_OPTIONS: { value: CallbackSource | ''; label: string }[] = [
  { value: 'alipay', label: '支付宝' },
  { value: 'wechat', label: '微信支付' },
  { value: 'system', label: '系统' },
  { value: '', label: '全部来源' },
];

/**
 * 支付回调管理页面
 */
export function PaymentCallbacksPage(): JSX.Element {
  const [page, setPage] = useState(1);
  const [pageSize] = useState(20);
  const [statusFilter, setStatusFilter] = useState<CallbackStatus | ''>('');
  const [sourceFilter, setSourceFilter] = useState<CallbackSource | ''>('');
  const [orderNo, setOrderNo] = useState('');
  const [selectedCallback, setSelectedCallback] = useState<PaymentCallback | null>(null);
  const [isDetailModalOpen, setIsDetailModalOpen] = useState(false);
  const [isProcessModalOpen, setIsProcessModalOpen] = useState(false);
  const [processAction, setProcessAction] = useState<'success' | 'fail'>('success');
  const [processNote, setProcessNote] = useState('');

  const { data: callbacksData, isLoading } = usePaymentCallbacks({
    page,
    pageSize,
    status: statusFilter || undefined,
    source: sourceFilter || undefined,
    orderNo: orderNo || undefined,
  });

  const retryMutation = useRetryPaymentCallback();
  const processMutation = useProcessPaymentCallback();

  const callbacks = callbacksData?.items ?? [];
  const stats = callbacksData?.stats;
  const totalPages = Math.ceil((callbacksData?.total ?? 0) / pageSize);

  const handleViewDetail = (callback: PaymentCallback): void => {
    setSelectedCallback(callback);
    setIsDetailModalOpen(true);
  };

  const handleRetry = (id: string): void => {
    retryMutation.mutate(id);
  };

  const handleProcess = (callback: PaymentCallback, action: 'success' | 'fail'): void => {
    setSelectedCallback(callback);
    setProcessAction(action);
    setProcessNote('');
    setIsProcessModalOpen(true);
  };

  const handleSubmitProcess = (): void => {
    if (!selectedCallback) return;
    processMutation.mutate(
      {
        id: selectedCallback.id,
        success: processAction === 'success',
        note: processNote,
      },
      {
        onSuccess: () => {
          setIsProcessModalOpen(false);
          setSelectedCallback(null);
        },
      }
    );
  };

  const getStatusBadge = (status: string): { label: string; variant: 'warning' | 'success' | 'danger' | 'primary' | 'default' } => {
    switch (status) {
      case 'pending':
        return { label: '待处理', variant: 'warning' };
      case 'success':
        return { label: '成功', variant: 'success' };
      case 'failed':
        return { label: '失败', variant: 'danger' };
      case 'retrying':
        return { label: '重试中', variant: 'primary' };
      default:
        return { label: '未知', variant: 'default' };
    }
  };

  const getSourceLabel = (source: string): string => {
    switch (source) {
      case 'alipay':
        return '支付宝';
      case 'wechat':
        return '微信支付';
      case 'system':
        return '系统';
      default:
        return source;
    }
  };

  return (
    <div className="container mx-auto py-6">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">支付回调管理</h1>
          <p className="text-slate-600 mt-1">监控和管理支付回调记录</p>
        </div>
      </div>

      {stats && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
          <Card className="p-4">
            <p className="text-sm text-slate-500">全部回调</p>
            <p className="text-2xl font-bold text-slate-900">{stats.totalCount}</p>
          </Card>
          <Card className="p-4">
            <p className="text-sm text-slate-500">待处理</p>
            <p className="text-2xl font-bold text-orange-600">{stats.pendingCount}</p>
          </Card>
          <Card className="p-4">
            <p className="text-sm text-slate-500">成功</p>
            <p className="text-2xl font-bold text-green-600">{stats.successCount}</p>
          </Card>
          <Card className="p-4">
            <p className="text-sm text-slate-500">失败</p>
            <p className="text-2xl font-bold text-red-600">{stats.failedCount}</p>
          </Card>
        </div>
      )}

      <Card className="mb-6">
        <div className="p-4 space-y-4">
          <div className="flex flex-wrap items-center gap-4">
            <div className="flex items-center gap-2">
              <span className="text-sm text-slate-700">状态：</span>
              <div className="flex gap-2">
                {STATUS_FILTERS.map((item) => (
                  <Button
                    key={item.value}
                    variant={statusFilter === item.value ? 'primary' : 'ghost'}
                    size="sm"
                    onClick={() => {
                      setStatusFilter(item.value);
                      setPage(1);
                    }}
                  >
                    {item.label}
                  </Button>
                ))}
              </div>
            </div>
          </div>
          <div className="flex flex-wrap items-center gap-4">
            <div className="flex items-center gap-2">
              <span className="text-sm text-slate-700">来源：</span>
              <select
                value={sourceFilter}
                onChange={(e) => {
                  setSourceFilter(e.currentTarget.value as CallbackSource | '');
                  setPage(1);
                }}
                className="px-3 py-1.5 border border-slate-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              >
                {SOURCE_OPTIONS.map((item) => (
                  <option key={item.value} value={item.value}>
                    {item.label}
                  </option>
                ))}
              </select>
            </div>
            <div className="flex-1 min-w-[200px] ml-auto">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
                <Input
                  placeholder="搜索订单号..."
                  value={orderNo}
                  onChange={(e: React.ChangeEvent<HTMLInputElement>) => {
                    setOrderNo(e.currentTarget.value);
                    setPage(1);
                  }}
                  className="pl-10"
                />
              </div>
            </div>
          </div>
        </div>
      </Card>

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
              {callbacks.map((callback) => {
                const status = getStatusBadge(callback.status);
                return (
                  <div key={callback.id} className="p-4 hover:bg-slate-50">
                    <div className="flex items-start justify-between">
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 mb-2">
                          <Badge variant={status.variant} size="sm">
                            {status.label}
                          </Badge>
                          <span className="text-sm text-slate-600">
                            {getSourceLabel(callback.source)}
                          </span>
                          <span className="text-xs text-slate-400">
                            订单: {callback.orderNo}
                          </span>
                          {callback.tradeNo && (
                            <span className="text-xs text-slate-400">
                              流水: {callback.tradeNo}
                            </span>
                          )}
                        </div>
                        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm text-slate-500">
                          <div>
                            <span className="text-slate-400">重试次数：</span>
                            {callback.retryCount}/{callback.maxRetries}
                          </div>
                          <div>
                            <span className="text-slate-400">IP地址：</span>
                            {callback.ipAddress ?? '-'}
                          </div>
                          <div>
                            <span className="text-slate-400">创建时间：</span>
                            {new Date(callback.createdAt).toLocaleString('zh-CN')}
                          </div>
                          <div>
                            <span className="text-slate-400">处理时间：</span>
                            {callback.processedAt
                              ? new Date(callback.processedAt).toLocaleString('zh-CN')
                              : '-'}
                          </div>
                        </div>
                        {callback.errorMessage && (
                          <div className="mt-2 text-sm text-red-600">
                            {callback.errorMessage}
                          </div>
                        )}
                      </div>
                      <div className="flex items-center gap-2 ml-4">
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleViewDetail(callback)}
                          title="查看详情"
                        >
                          <Eye className="h-4 w-4" />
                        </Button>
                        {callback.status === 'failed' && callback.retryCount < callback.maxRetries && (
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => handleRetry(callback.id)}
                            disabled={retryMutation.isPending}
                            title="重试"
                          >
                            <RefreshCw className={`h-4 w-4 ${retryMutation.isPending ? 'animate-spin' : ''}`} />
                          </Button>
                        )}
                        {callback.status === 'pending' && (
                          <>
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => handleProcess(callback, 'success')}
                              title="标记成功"
                            >
                              <CheckCircle className="h-4 w-4 text-green-500" />
                            </Button>
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => handleProcess(callback, 'fail')}
                              title="标记失败"
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
              {!callbacks.length && (
                <div className="p-10 text-center text-slate-500">
                  <p>暂无回调记录</p>
                  <p className="text-sm mt-1">当有支付回调时会显示在这里</p>
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

      {isDetailModalOpen && selectedCallback && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl w-full max-w-3xl mx-4 max-h-[90vh] overflow-y-auto">
            <div className="p-6 border-b border-slate-200">
              <h2 className="text-lg font-semibold">回调详情</h2>
            </div>
            <div className="p-6 space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm text-slate-500 mb-1">订单号</label>
                  <p className="font-medium">{selectedCallback.orderNo}</p>
                </div>
                <div>
                  <label className="block text-sm text-slate-500 mb-1">流水号</label>
                  <p className="font-medium">{selectedCallback.tradeNo ?? '-'}</p>
                </div>
                <div>
                  <label className="block text-sm text-slate-500 mb-1">来源</label>
                  <p className="font-medium">{getSourceLabel(selectedCallback.source)}</p>
                </div>
                <div>
                  <label className="block text-sm text-slate-500 mb-1">状态</label>
                  <Badge variant={getStatusBadge(selectedCallback.status).variant}>
                    {getStatusBadge(selectedCallback.status).label}
                  </Badge>
                </div>
              </div>
              <div>
                <label className="block text-sm text-slate-500 mb-1">请求数据 (Payload)</label>
                <pre className="bg-slate-50 p-3 rounded-lg text-xs overflow-auto max-h-48">
                  {selectedCallback.payload}
                </pre>
              </div>
              {selectedCallback.response && (
                <div>
                  <label className="block text-sm text-slate-500 mb-1">响应数据 (Response)</label>
                  <pre className="bg-slate-50 p-3 rounded-lg text-xs overflow-auto max-h-48">
                    {selectedCallback.response}
                  </pre>
                </div>
              )}
            </div>
            <div className="p-6 border-t border-slate-200 flex justify-end gap-3">
              <Button onClick={() => setIsDetailModalOpen(false)}>关闭</Button>
            </div>
          </div>
        </div>
      )}

      {isProcessModalOpen && selectedCallback && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl w-full max-w-lg mx-4">
            <div className="p-6 border-b border-slate-200">
              <h2 className="text-lg font-semibold">
                {processAction === 'success' ? '标记回调成功' : '标记回调失败'}
              </h2>
            </div>
            <div className="p-6 space-y-4">
              <div className="bg-slate-50 p-4 rounded-lg">
                <p className="text-sm text-slate-500">订单号</p>
                <p className="font-medium">{selectedCallback.orderNo}</p>
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">
                  备注
                </label>
                <textarea
                  value={processNote}
                  onChange={(e) => setProcessNote(e.currentTarget.value)}
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  rows={3}
                  placeholder="请输入处理备注..."
                />
              </div>
            </div>
            <div className="p-6 border-t border-slate-200 flex justify-end gap-3">
              <Button variant="ghost" onClick={() => setIsProcessModalOpen(false)}>
                取消
              </Button>
              <Button
                variant={processAction === 'success' ? 'primary' : 'danger'}
                onClick={handleSubmitProcess}
                disabled={processMutation.isPending}
              >
                {processMutation.isPending ? '处理中...' : '确认'}
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
