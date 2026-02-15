/**
 * ContentModeration - 内容审核组件
 */

import { useState } from 'react';

import type { ModerationItem, ModerationAction, ContentType, ModerationStatus, ReportReason } from '../types';
import {
  useModerationQueue,
  useModerateContent,
  useBatchModerate,
  useModerationRecords,
} from '../hooks/useForumAdmin';

const actionLabels: Record<ModerationAction, string> = {
  approve: '通过',
  reject: '拒绝',
  escalate: '升级',
  ignore: '忽略',
};

const actionColors: Record<ModerationAction, string> = {
  approve: 'bg-green-100 text-green-800 hover:bg-green-200',
  reject: 'bg-red-100 text-red-800 hover:bg-red-200',
  escalate: 'bg-orange-100 text-orange-800 hover:bg-orange-200',
  ignore: 'bg-gray-100 text-gray-800 hover:bg-gray-200',
};

const statusLabels: Record<ModerationStatus, string> = {
  pending: '待审核',
  approved: '已通过',
  rejected: '已拒绝',
  auto_approved: '自动通过',
};

const statusColors: Record<ModerationStatus, string> = {
  pending: 'bg-yellow-100 text-yellow-800',
  approved: 'bg-green-100 text-green-800',
  rejected: 'bg-red-100 text-red-800',
  auto_approved: 'bg-blue-100 text-blue-800',
};

const contentTypeLabels: Record<ContentType, string> = {
  post: '帖子',
  comment: '评论',
  reply: '回复',
};

const reportReasonLabels: Record<ReportReason, string> = {
  spam: '垃圾信息',
  harassment: '骚扰',
  inappropriate: '不当内容',
  misinformation: '虚假信息',
  copyright: '版权问题',
  violence: '暴力内容',
  other: '其他',
};

/**
 * 内容审核组件
 */
export function ContentModeration(): JSX.Element {
  const [selectedStatus, setSelectedStatus] = useState<ModerationStatus | undefined>('pending');
  const [selectedType, setSelectedType] = useState<ContentType | undefined>();
  const [selectedItems, setSelectedItems] = useState<Set<number>>(new Set());
  const [processingItem, setProcessingItem] = useState<ModerationItem | null>(null);
  const [moderationReason, setModerationReason] = useState<string>('');
  const [showRecords, setShowRecords] = useState<boolean>(false);

  const { data: queueData, isLoading: isLoadingQueue, error: queueError } = useModerationQueue({
    status: selectedStatus,
    contentType: selectedType,
    limit: 50,
  });

  const { data: records, isLoading: isLoadingRecords } = useModerationRecords({
    contentType: selectedType,
    limit: 20,
  });

  const moderateMutation = useModerateContent();
  const batchModerateMutation = useBatchModerate();

  const handleSelectItem = (itemId: number, selected: boolean): void => {
    const newSelected = new Set(selectedItems);
    if (selected) {
      newSelected.add(itemId);
    } else {
      newSelected.delete(itemId);
    }
    setSelectedItems(newSelected);
  };

  const handleSelectAll = (): void => {
    if (!queueData?.items) return;
    if (selectedItems.size === queueData.items.length) {
      setSelectedItems(new Set());
    } else {
      setSelectedItems(new Set(queueData.items.map(item => item.id)));
    }
  };

  const handleModerate = async (action: ModerationAction): Promise<void> => {
    if (!processingItem) return;

    await moderateMutation.mutateAsync({
      itemId: processingItem.id,
      action,
      reason: moderationReason,
    });

    setProcessingItem(null);
    setModerationReason('');
  };

  const handleBatchModerate = async (action: ModerationAction): Promise<void> => {
    if (selectedItems.size === 0) return;

    await batchModerateMutation.mutateAsync({
      itemIds: Array.from(selectedItems),
      action,
      reason: moderationReason,
    });

    setSelectedItems(new Set());
    setModerationReason('');
  };

  const truncateContent = (content: string, maxLength: number = 100): string => {
    if (content.length <= maxLength) return content;
    return content.slice(0, maxLength) + '...';
  };

  if (isLoadingQueue) {
    return (
      <div className="p-6 bg-white rounded-lg shadow-sm">
        <div className="animate-pulse space-y-4">
          <div className="h-4 bg-gray-200 rounded w-1/4" />
          <div className="space-y-2">
            <div className="h-16 bg-gray-200 rounded" />
            <div className="h-16 bg-gray-200 rounded" />
            <div className="h-16 bg-gray-200 rounded" />
          </div>
        </div>
      </div>
    );
  }

  if (queueError) {
    return (
      <div className="p-6 bg-white rounded-lg shadow-sm">
        <div className="text-red-500">加载审核队列失败</div>
      </div>
    );
  }

  return (
    <div className="p-6 bg-white rounded-lg shadow-sm">
      {/* 头部 */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-xl font-semibold text-gray-900">内容审核</h2>
          <p className="text-sm text-gray-500 mt-1">
            待审核: {queueData?.pendingCount || 0} 条 | 当前显示: {queueData?.items.length || 0} 条
          </p>
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={() => setShowRecords(!showRecords)}
            className="px-4 py-2 text-sm font-medium text-gray-600 bg-gray-100 rounded-md hover:bg-gray-200 transition-colors"
          >
            {showRecords ? '隐藏记录' : '审核记录'}
          </button>
        </div>
      </div>

      {/* 筛选器 */}
      <div className="flex flex-wrap items-center gap-4 mb-6">
        <div className="flex items-center gap-2">
          <label className="text-sm font-medium text-gray-700">状态:</label>
          <select
            value={selectedStatus || ''}
            onChange={(e) => setSelectedStatus(e.target.value as ModerationStatus || undefined)}
            className="px-3 py-1.5 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="">全部</option>
            <option value="pending">待审核</option>
            <option value="approved">已通过</option>
            <option value="rejected">已拒绝</option>
          </select>
        </div>
        <div className="flex items-center gap-2">
          <label className="text-sm font-medium text-gray-700">类型:</label>
          <select
            value={selectedType || ''}
            onChange={(e) => setSelectedType(e.target.value as ContentType || undefined)}
            className="px-3 py-1.5 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="">全部</option>
            <option value="post">帖子</option>
            <option value="comment">评论</option>
            <option value="reply">回复</option>
          </select>
        </div>
      </div>

      {/* 批量操作 */}
      {selectedItems.size > 0 && (
        <div className="flex items-center gap-3 mb-4 p-3 bg-blue-50 rounded-lg">
          <span className="text-sm text-blue-800">已选择 {selectedItems.size} 项</span>
          <div className="flex-1" />
          <input
            type="text"
            value={moderationReason}
            onChange={(e) => setModerationReason(e.target.value)}
            placeholder="批量操作原因（可选）"
            className="px-3 py-1.5 border border-gray-300 rounded-md text-sm w-48 focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
          <button
            onClick={() => void handleBatchModerate('approve')}
            disabled={batchModerateMutation.isPending}
            className="px-3 py-1.5 text-sm font-medium text-green-700 bg-green-100 rounded hover:bg-green-200 transition-colors disabled:opacity-50"
          >
            批量通过
          </button>
          <button
            onClick={() => void handleBatchModerate('reject')}
            disabled={batchModerateMutation.isPending}
            className="px-3 py-1.5 text-sm font-medium text-red-700 bg-red-100 rounded hover:bg-red-200 transition-colors disabled:opacity-50"
          >
            批量拒绝
          </button>
          <button
            onClick={() => setSelectedItems(new Set())}
            className="px-3 py-1.5 text-sm text-gray-600 hover:text-gray-800"
          >
            取消
          </button>
        </div>
      )}

      {/* 审核队列 */}
      {!showRecords ? (
        <div className="space-y-4">
          {queueData?.items.length === 0 ? (
            <div className="text-center py-12 text-gray-500">
              <p className="text-lg mb-2">🎉 太棒了！</p>
              <p>当前没有待审核的内容</p>
            </div>
          ) : (
            <>
              <div className="flex items-center gap-3 mb-2">
                <input
                  type="checkbox"
                  checked={queueData?.items.length === selectedItems.size && queueData?.items.length > 0}
                  onChange={handleSelectAll}
                  className="w-4 h-4 text-blue-600 rounded border-gray-300 focus:ring-blue-500"
                />
                <span className="text-sm text-gray-600">全选</span>
              </div>
              {queueData?.items.map((item) => (
                <div
                  key={item.id}
                  className={`p-4 border rounded-lg transition-colors ${selectedItems.has(item.id) ? 'border-blue-500 bg-blue-50' : 'border-gray-200 hover:border-gray-300'}`}
                >
                  <div className="flex items-start gap-4">
                    <input
                      type="checkbox"
                      checked={selectedItems.has(item.id)}
                      onChange={(e) => handleSelectItem(item.id, e.target.checked)}
                      className="w-4 h-4 text-blue-600 rounded border-gray-300 focus:ring-blue-500 mt-1"
                    />
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-2">
                        <span className={`px-2 py-0.5 text-xs font-semibold rounded ${statusColors[item.status]}`}>
                          {statusLabels[item.status]}
                        </span>
                        <span className="px-2 py-0.5 text-xs font-medium bg-gray-100 text-gray-700 rounded">
                          {contentTypeLabels[item.contentType]}
                        </span>
                        {item.categoryName && (
                          <span className="text-xs text-gray-500">板块: {item.categoryName}</span>
                        )}
                        {item.aiScore !== undefined && (
                          <span className={`text-xs px-2 py-0.5 rounded ${item.aiScore > 0.7 ? 'bg-red-100 text-red-700' : item.aiScore > 0.4 ? 'bg-yellow-100 text-yellow-700' : 'bg-green-100 text-green-700'}`}>
                            AI评分: {(item.aiScore * 100).toFixed(0)}%
                          </span>
                        )}
                      </div>
                      <p className="text-gray-800 mb-3">{truncateContent(item.content)}</p>
                      <div className="flex items-center gap-4 text-sm text-gray-500">
                        <div className="flex items-center gap-2">
                          {item.authorAvatar ? (
                            <img src={item.authorAvatar} alt={item.authorName} className="w-6 h-6 rounded-full" />
                          ) : (
                            <div className="w-6 h-6 rounded-full bg-blue-100 flex items-center justify-center text-blue-600 text-xs font-medium">
                              {item.authorName.charAt(0)}
                            </div>
                          )}
                          <span>{item.authorName}</span>
                        </div>
                        <span>{new Date(item.createdAt).toLocaleString('zh-CN')}</span>
                        {item.reportCount > 0 && (
                          <span className="text-red-600">
                            被举报 {item.reportCount} 次
                          </span>
                        )}
                      </div>
                      {item.reportReasons.length > 0 && (
                        <div className="flex flex-wrap gap-2 mt-2">
                          {item.reportReasons.map((reason) => (
                            <span key={reason} className="px-2 py-0.5 text-xs bg-red-50 text-red-700 rounded">
                              {reportReasonLabels[reason]}
                            </span>
                          ))}
                        </div>
                      )}
                    </div>
                    <div className="flex flex-col gap-2">
                      <button
                        onClick={() => setProcessingItem(item)}
                        className="px-4 py-2 text-sm font-medium text-blue-600 bg-blue-50 rounded hover:bg-blue-100 transition-colors"
                      >
                        审核
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </>
          )}
        </div>
      ) : (
        /* 审核记录 */
        <div className="space-y-4">
          {isLoadingRecords ? (
            <div className="animate-pulse space-y-2">
              <div className="h-12 bg-gray-200 rounded" />
              <div className="h-12 bg-gray-200 rounded" />
              <div className="h-12 bg-gray-200 rounded" />
            </div>
          ) : records?.length === 0 ? (
            <div className="text-center py-12 text-gray-500">
              <p>暂无审核记录</p>
            </div>
          ) : (
            <table className="w-full text-left">
              <thead>
                <tr className="border-b border-gray-200">
                  <th className="pb-3 font-medium text-gray-700">类型</th>
                  <th className="pb-3 font-medium text-gray-700">内容预览</th>
                  <th className="pb-3 font-medium text-gray-700">操作</th>
                  <th className="pb-3 font-medium text-gray-700">处理人</th>
                  <th className="pb-3 font-medium text-gray-700">处理时间</th>
                </tr>
              </thead>
              <tbody>
                {records?.map((record) => (
                  <tr key={record.id} className="border-b border-gray-100 last:border-0">
                    <td className="py-3">
                      <span className="px-2 py-0.5 text-xs font-medium bg-gray-100 text-gray-700 rounded">
                        {contentTypeLabels[record.contentType]}
                      </span>
                    </td>
                    <td className="py-3 text-gray-700 max-w-xs truncate">
                      {record.contentPreview}
                    </td>
                    <td className="py-3">
                      <span className={`px-2 py-0.5 text-xs font-semibold rounded ${actionColors[record.action]}`}>
                        {actionLabels[record.action]}
                      </span>
                    </td>
                    <td className="py-3 text-gray-600">{record.handledByName}</td>
                    <td className="py-3 text-gray-500 text-sm">
                      {new Date(record.handledAt).toLocaleString('zh-CN')}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      )}

      {/* 审核弹窗 */}
      {processingItem && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-lg max-h-[90vh] overflow-y-auto">
            <h3 className="text-lg font-semibold mb-4">内容审核</h3>
            <div className="mb-4 p-3 bg-gray-50 rounded-lg">
              <div className="flex items-center gap-2 mb-2">
                <span className="px-2 py-0.5 text-xs font-medium bg-gray-100 text-gray-700 rounded">
                  {contentTypeLabels[processingItem.contentType]}
                </span>
                <span className="text-sm text-gray-500">{processingItem.authorName}</span>
              </div>
              <p className="text-gray-800 whitespace-pre-wrap">{processingItem.content}</p>
            </div>
            {processingItem.aiSuggestion && (
              <div className="mb-4 p-3 bg-blue-50 rounded-lg">
                <p className="text-sm text-blue-800">
                  <span className="font-medium">AI 建议:</span> {actionLabels[processingItem.aiSuggestion]}
                </p>
              </div>
            )}
            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 mb-1">审核原因（可选）</label>
              <textarea
                value={moderationReason}
                onChange={(e) => setModerationReason(e.target.value)}
                placeholder="请输入审核原因或备注"
                rows={3}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
            <div className="grid grid-cols-2 gap-3">
              <button
                onClick={() => void handleModerate('approve')}
                disabled={moderateMutation.isPending}
                className="px-4 py-2 text-sm font-medium text-green-700 bg-green-100 rounded-md hover:bg-green-200 transition-colors disabled:opacity-50"
              >
                {moderateMutation.isPending ? '处理中...' : '✓ 通过'}
              </button>
              <button
                onClick={() => void handleModerate('reject')}
                disabled={moderateMutation.isPending}
                className="px-4 py-2 text-sm font-medium text-red-700 bg-red-100 rounded-md hover:bg-red-200 transition-colors disabled:opacity-50"
              >
                {moderateMutation.isPending ? '处理中...' : '✗ 拒绝'}
              </button>
              <button
                onClick={() => void handleModerate('escalate')}
                disabled={moderateMutation.isPending}
                className="px-4 py-2 text-sm font-medium text-orange-700 bg-orange-100 rounded-md hover:bg-orange-200 transition-colors disabled:opacity-50"
              >
                {moderateMutation.isPending ? '处理中...' : '↑ 升级'}
              </button>
              <button
                onClick={() => void handleModerate('ignore')}
                disabled={moderateMutation.isPending}
                className="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 rounded-md hover:bg-gray-200 transition-colors disabled:opacity-50"
              >
                {moderateMutation.isPending ? '处理中...' : '− 忽略'}
              </button>
            </div>
            <div className="flex justify-end mt-4">
              <button
                onClick={() => {
                  setProcessingItem(null);
                  setModerationReason('');
                }}
                className="px-4 py-2 text-sm font-medium text-gray-600 hover:text-gray-800 transition-colors"
              >
                取消
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}