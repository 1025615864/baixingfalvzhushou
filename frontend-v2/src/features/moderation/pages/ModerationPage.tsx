/**
 * ModerationPage - 内容审核中心页面
 *
 * 管理员进行内容审核的主页面，包含队列、记录、统计三个主要视图
 */

import React, { useState, useCallback } from 'react';
import {
  Layout,
  Tabs,
  Card,
  Space,
  Button,
  message,
  Modal,
  Radio,
  Input,
  Badge,
} from 'antd';
import {
  AuditOutlined,
  HistoryOutlined,
  BarChartOutlined,
  ReloadOutlined,
} from '@ant-design/icons';

import { useModerationManager } from '../hooks/useModeration';
import { ModerationQueue } from '../components/ModerationQueue';
import { ModerationDetail } from '../components/ModerationDetail';
import { ModerationStats } from '../components/ModerationStats';
import type { ModerationQueueItem, ReviewAction } from '../types';

const { Content } = Layout;
const { TextArea } = Input;

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
  } = useModerationManager();

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
                  <ModerationQueue
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
                  <ModerationStats stats={stats} loading={isLoadingStats} />
                ),
              },
            ]}
          />
        </Card>

        {/* 审核详情抽屉 */}
        <ModerationDetail
          item={selectedItem}
          visible={detailVisible}
          onClose={handleCloseDetail}
          onSubmit={handleSubmitReview}
          submitting={isSubmitting}
        />

        {/* 快速审核弹窗 */}
        <Modal
          title="确认审核操作"
          open={quickReviewVisible}
          onOk={handleSubmitQuickReview}
          onCancel={() => setQuickReviewVisible(false)}
          confirmLoading={isSubmitting}
          okText="确认"
          cancelText="取消"
          okButtonProps={{
            danger: quickReviewAction === 'reject',
          }}
        >
          {quickReviewItem && (
            <div>
              <p>
                <strong>内容类型：</strong>
                {quickReviewItem.contentType}
              </p>
              <p>
                <strong>内容摘要：</strong>
                {quickReviewItem.content.substring(0, 100)}
                {quickReviewItem.content.length > 100 ? '...' : ''}
              </p>
              <p>
                <strong>审核操作：</strong>
                <Radio.Group
                  value={quickReviewAction}
                  onChange={(e) => setQuickReviewAction(e.target.value as ReviewAction)}
                >
                  <Radio value="approve">通过</Radio>
                  <Radio value="reject">拒绝</Radio>
                  <Radio value="escalate">升级</Radio>
                </Radio.Group>
              </p>
              <div style={{ marginTop: 16 }}>
                <p>审核原因（可选）：</p>
                <TextArea
                  value={quickReviewReason}
                  onChange={(e) => setQuickReviewReason(e.target.value)}
                  placeholder="请输入审核原因，将通知用户"
                  rows={3}
                />
              </div>
              <div style={{ marginTop: 16 }}>
                <p>内部备注（仅管理员可见）：</p>
                <TextArea
                  value={quickReviewNote}
                  onChange={(e) => setQuickReviewNote(e.target.value)}
                  placeholder="请输入内部备注"
                  rows={2}
                />
              </div>
            </div>
          )}
        </Modal>
      </Content>
    </Layout>
  );
};

export default ModerationPage;