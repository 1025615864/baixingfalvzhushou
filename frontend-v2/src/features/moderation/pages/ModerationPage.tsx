/**
 * ModerationPage - 内容审核中心页面
 *
 * 管理员进行内容审核的主页面，包含队列、记录、统计三个主要视图
 */

import React, { Suspense, lazy, useState, useCallback } from 'react';
import {
  Layout,
  Tabs,
  Card,
  Space,
  Button,
  message,
  Modal,
  Badge,
} from 'antd';
import {
  AuditOutlined,
  HistoryOutlined,
  BarChartOutlined,
  ReloadOutlined,
} from '@ant-design/icons';

import { useModerationManager } from '../hooks/useModeration';
import type { ModerationQueueItem, ReviewAction } from '../types';

const LazyModerationQueue = lazy(() =>
  import('../components/ModerationQueue').then((module) => ({
    default: module.ModerationQueue,
  }))
);

const LazyModerationDetail = lazy(() =>
  import('../components/ModerationDetail').then((module) => ({
    default: module.ModerationDetail,
  }))
);

const LazyModerationStats = lazy(() =>
  import('../components/ModerationStats').then((module) => ({
    default: module.ModerationStats,
  }))
);

const LazyQuickReviewModal = lazy(() =>
  import('../components/QuickReviewModal').then((module) => ({
    default: module.QuickReviewModal,
  }))
);

const { Content } = Layout;

function ModerationSectionSkeleton({ rows = 3 }: { rows?: number }): JSX.Element {
  return (
    <div className="space-y-4">
      {Array.from({ length: rows }).map((_, index) => (
        <div key={index} className="h-24 animate-pulse rounded-lg bg-slate-100" />
      ))}
    </div>
  );
}

/**
 * 内容审核中心页面
 */
export const ModerationPage: React.FC = () => {
  // 视图状态
  const [activeTab, setActiveTab] = useState('queue');

  // 审核详情抽屉状态
  const [selectedItem, setSelectedItem] = useState<ModerationQueueItem | undefined>();
  const [detailVisible, setDetailVisible] = useState(false);

  // 快速审核弹窗状态
  const [quickReviewVisible, setQuickReviewVisible] = useState(false);
  const [quickReviewItem, setQuickReviewItem] = useState<ModerationQueueItem | undefined>();
  const [quickReviewAction, setQuickReviewAction] = useState<ReviewAction>('approve');
  const [quickReviewReason, setQuickReviewReason] = useState('');
  const [quickReviewNote, setQuickReviewNote] = useState('');

  // 审核管理 Hook
  const {
    queueItems,
    queueTotal,
    isLoadingQueue,
    stats,
    isLoadingStats,
    queueFilters,
    selectedItems,
    toggleSelectAll,
    clearSelection,
    setQueuePage,
    handleReview,
    handleBatchReview,
    isSubmitting,
    refreshAll,
  } = useModerationManager(activeTab as 'queue' | 'records' | 'stats');

  // 查看详情
  const handleViewDetail = useCallback((item: ModerationQueueItem) => {
    setSelectedItem(item);
    setDetailVisible(true);
  }, []);

  // 关闭详情
  const handleCloseDetail = useCallback(() => {
    setDetailVisible(false);
    setSelectedItem(undefined);
  }, []);

  // 提交单个审核
  const handleSubmitReview = useCallback(
    (action: ReviewAction, reason?: string, note?: string): void => {
      if (!selectedItem) return;

      handleReview(selectedItem.id, action, reason, note)
        .then(() => {
          void message.success('审核提交成功');
          handleCloseDetail();
        })
        .catch((error: unknown) => {
          void message.error(error instanceof Error ? error.message : '审核提交失败');
        });
    },
    [selectedItem, handleReview, handleCloseDetail]
  );

  // 打开快速审核弹窗
  const handleOpenQuickReview = useCallback((item: ModerationQueueItem, action: ReviewAction) => {
    setQuickReviewItem(item);
    setQuickReviewAction(action);
    setQuickReviewReason('');
    setQuickReviewNote('');
    setQuickReviewVisible(true);
  }, []);

  // 提交快速审核
  const handleSubmitQuickReview = useCallback(() => {
    if (!quickReviewItem) return;

    handleReview(
      quickReviewItem.id,
      quickReviewAction,
      quickReviewReason || undefined,
      quickReviewNote || undefined
    )
      .then(() => {
        void message.success('审核提交成功');
        setQuickReviewVisible(false);
        setQuickReviewItem(undefined);
      })
      .catch((error: unknown) => {
        void message.error(error instanceof Error ? error.message : '审核提交失败');
      });
  }, [quickReviewItem, quickReviewAction, quickReviewReason, quickReviewNote, handleReview]);

  // 提交批量审核
  const handleSubmitBatchReview = useCallback(
    (action: ReviewAction) => {
      if (selectedItems.length === 0) {
        void message.warning('请先选择要审核的项目');
        return;
      }

      Modal.confirm({
        title: '确认批量审核',
        content: (
          <div>
            确定要对选中的
            {' '}
            <strong>{selectedItems.length}</strong>
            {' '}
            项内容进行
            {action === 'approve' ? '通过' : action === 'reject' ? '拒绝' : '升级处理'}
            操作吗？
          </div>
        ),
        onOk: () => {
          handleBatchReview(action)
            .then(() => {
              void message.success('批量审核提交成功');
              clearSelection();
            })
            .catch((error: unknown) => {
              void message.error(error instanceof Error ? error.message : '批量审核提交失败');
            });
        },
      });
    },
    [selectedItems, handleBatchReview, clearSelection]
  );

  // 刷新数据
  const handleRefresh = useCallback(() => {
    void refreshAll();
    void message.success('数据已刷新');
  }, [refreshAll]);

  return (
    <Layout className="moderation-page" style={{ minHeight: '100vh', padding: 24 }}>
      <Content>
        <Card
          title={
            <Space>
              <AuditOutlined />
              <span>内容审核中心</span>
            </Space>
          }
          extra={
            <Button icon={<ReloadOutlined />} onClick={handleRefresh}>
              刷新
            </Button>
          }
        >
          <Tabs
            activeKey={activeTab}
            onChange={setActiveTab}
            destroyInactiveTabPane
            items={[
              {
                key: 'queue',
                label: (
                  <span>
                    <AuditOutlined />
                    审核队列
                    <Badge
                      count={stats?.totalPending || 0}
                      style={{ marginLeft: 8 }}
                      overflowCount={99}
                    />
                  </span>
                ),
                children: (
                  <Suspense fallback={<ModerationSectionSkeleton rows={4} />}>
                    <LazyModerationQueue
                      items={queueItems}
                      total={queueTotal}
                      selectedItems={selectedItems}
                      loading={isLoadingQueue}
                      page={queueFilters.page || 1}
                      pageSize={queueFilters.pageSize || 20}
                      onSelectionChange={(ids) => {
                        // 清空选择后重新设置
                        if (ids.length === 0) {
                          clearSelection();
                        } else {
                          // 使用 toggleSelectAll 来处理全选
                          const currentIds = queueItems.map((item) => item.id);
                          if (ids.length === currentIds.length) {
                            toggleSelectAll(currentIds);
                          }
                        }
                      }}
                      onViewDetail={handleViewDetail}
                      onReview={handleOpenQuickReview}
                      onBatchReview={handleSubmitBatchReview}
                      onPageChange={setQueuePage}
                    />
                  </Suspense>
                ),
              },
              {
                key: 'records',
                label: (
                  <span>
                    <HistoryOutlined />
                    审核记录
                  </span>
                ),
                children: (
                  <div>
                    <h3>审核记录</h3>
                    <p>请在审核队列中完成审核操作</p>
                  </div>
                ),
              },
              {
                key: 'stats',
                label: (
                  <span>
                    <BarChartOutlined />
                    审核统计
                  </span>
                ),
                children: (
                  <Suspense fallback={<ModerationSectionSkeleton rows={3} />}>
                    <LazyModerationStats stats={stats} loading={isLoadingStats} />
                  </Suspense>
                ),
              },
            ]}
          />
        </Card>

        {/* 审核详情抽屉 */}
        {(detailVisible || selectedItem) && (
          <Suspense fallback={null}>
            <LazyModerationDetail
              item={selectedItem}
              visible={detailVisible}
              onClose={handleCloseDetail}
              onSubmit={handleSubmitReview}
              submitting={isSubmitting}
            />
          </Suspense>
        )}

        {/* 快速审核弹窗 */}
        {quickReviewVisible && (
          <Suspense fallback={null}>
            <LazyQuickReviewModal
              visible={quickReviewVisible}
              item={quickReviewItem}
              action={quickReviewAction}
              reason={quickReviewReason}
              note={quickReviewNote}
              submitting={isSubmitting}
              onActionChange={setQuickReviewAction}
              onReasonChange={setQuickReviewReason}
              onNoteChange={setQuickReviewNote}
              onSubmit={handleSubmitQuickReview}
              onCancel={() => setQuickReviewVisible(false)}
            />
          </Suspense>
        )}
      </Content>
    </Layout>
  );
};

export default ModerationPage;