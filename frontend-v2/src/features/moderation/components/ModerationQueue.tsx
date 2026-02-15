/**
 * ModerationQueue - 审核队列组件
 *
 * 展示待审核内容列表，支持筛选、排序、批量操作等功能
 */

import React, { useCallback } from 'react';
import {
  Table,
  Card,
  Space,
  Tag,
  Button,
  Checkbox,
  Dropdown,
  Menu,
  Typography,
  Tooltip,
  Badge,
  Empty,
  Alert,
} from 'antd';
import {
  CheckCircleOutlined,
  CloseCircleOutlined,
  EyeOutlined,
  FilterOutlined,
  MoreOutlined,
  FlagOutlined,
  ExclamationCircleOutlined,
  RobotOutlined,
} from '@ant-design/icons';

import type { ModerationQueueItem, ContentType, RiskLevel, ReviewAction } from '../types';

const { Text, Paragraph } = Typography;

/** ModerationQueue组件Props */
export interface ModerationQueueProps {
  /** 队列数据 */
  items: ModerationQueueItem[];
  /** 总数 */
  total: number;
  /** 选中项 */
  selectedItems: string[];
  /** 加载状态 */
  loading?: boolean;
  /** 当前页 */
  page: number;
  /** 每页条数 */
  pageSize: number;
  /** 选择变更回调 */
  onSelectionChange: (selectedIds: string[]) => void;
  /** 查看详情回调 */
  onViewDetail: (item: ModerationQueueItem) => void;
  /** 审核回调 */
  onReview: (item: ModerationQueueItem, action: ReviewAction) => void;
  /** 批量审核回调 */
  onBatchReview: (action: ReviewAction) => void;
  /** 分页变更回调 */
  onPageChange: (page: number, pageSize: number) => void;
}

/** 内容类型映射 */
const contentTypeMap: Record<ContentType, { label: string; color: string }> = {
  post: { label: '帖子', color: 'blue' },
  comment: { label: '评论', color: 'cyan' },
  consultation: { label: '咨询', color: 'purple' },
  document: { label: '文档', color: 'orange' },
  news: { label: '新闻', color: 'red' },
  forum_post: { label: '论坛帖', color: 'green' },
  forum_comment: { label: '论坛回复', color: 'lime' },
};

/** 风险等级映射 */
const riskLevelMap: Record<RiskLevel, { label: string; color: string }> = {
  high: { label: '高', color: 'red' },
  medium: { label: '中', color: 'orange' },
  low: { label: '低', color: 'green' },
  none: { label: '无', color: 'default' },
};

/** AI建议映射 */
const aiSuggestionMap: Record<ReviewAction, { label: string; color: string; icon: React.ReactNode }> = {
  approve: { label: '通过', color: 'success', icon: <CheckCircleOutlined /> },
  reject: { label: '拒绝', color: 'error', icon: <CloseCircleOutlined /> },
  escalate: { label: '升级', color: 'warning', icon: <ExclamationCircleOutlined /> },
  flag: { label: '标记', color: 'default', icon: <FlagOutlined /> },
};

/**
 * 格式化日期
 */
function formatDate(dateString: string): string {
  const date = new Date(dateString);
  const now = new Date();
  const diff = now.getTime() - date.getTime();
  const minutes = Math.floor(diff / 60000);
  const hours = Math.floor(diff / 3600000);
  const days = Math.floor(diff / 86400000);

  if (minutes < 1) return '刚刚';
  if (minutes < 60) return `${minutes}分钟前`;
  if (hours < 24) return `${hours}小时前`;
  if (days < 7) return `${days}天前`;
  return date.toLocaleDateString('zh-CN');
}

/**
 * 审核队列组件
 */
export const ModerationQueue: React.FC<ModerationQueueProps> = ({
  items,
  total,
  selectedItems,
  loading = false,
  page,
  pageSize,
  onSelectionChange,
  onViewDetail,
  onReview,
  onBatchReview,
  onPageChange,
}) => {
  // 处理单选
  const handleSelect = useCallback(
    (id: string, checked: boolean) => {
      if (checked) {
        onSelectionChange([...selectedItems, id]);
      } else {
        onSelectionChange(selectedItems.filter((item) => item !== id));
      }
    },
    [selectedItems, onSelectionChange]
  );

  // 处理全选
  const handleSelectAll = useCallback(
    (checked: boolean) => {
      if (checked) {
        onSelectionChange(items.map((item) => item.id));
      } else {
        onSelectionChange([]);
      }
    },
    [items, onSelectionChange]
  );

  // 表格列定义
  const columns = [
    {
      title: (
        <Checkbox
          indeterminate={selectedItems.length > 0 && selectedItems.length < items.length}
          checked={selectedItems.length === items.length && items.length > 0}
          onChange={(e) => handleSelectAll(e.target.checked)}
        />
      ),
      key: 'selection',
      width: 50,
      render: (_: unknown, record: ModerationQueueItem) => (
        <Checkbox
          checked={selectedItems.includes(record.id)}
          onChange={(e) => handleSelect(record.id, e.target.checked)}
        />
      ),
    },
    {
      title: '内容类型',
      key: 'contentType',
      width: 100,
      render: (_: unknown, record: ModerationQueueItem) => (
        <Tag color={contentTypeMap[record.contentType].color}>
          {contentTypeMap[record.contentType].label}
        </Tag>
      ),
    },
    {
      title: '内容摘要',
      key: 'content',
      render: (_: unknown, record: ModerationQueueItem) => (
        <div style={{ maxWidth: 400 }}>
          {record.title && (
            <Text strong style={{ display: 'block', marginBottom: 4 }}>
              {record.title}
            </Text>
          )}
          <Paragraph
            ellipsis={{ rows: 2 }}
            style={{ margin: 0, fontSize: 13 }}
          >
            {record.content}
          </Paragraph>
        </div>
      ),
    },
    {
      title: '作者',
      key: 'author',
      width: 120,
      render: (_: unknown, record: ModerationQueueItem) => (
        <Text>{record.authorName}</Text>
      ),
    },
    {
      title: '风险等级',
      key: 'riskLevel',
      width: 100,
      render: (_: unknown, record: ModerationQueueItem) => (
        <Badge
          status={record.riskLevel === 'high' ? 'error' : record.riskLevel === 'medium' ? 'warning' : 'default'}
          text={
            <Tag color={riskLevelMap[record.riskLevel].color}>
              {riskLevelMap[record.riskLevel].label}
              {' '}
              ({record.riskScore})
            </Tag>
          }
        />
      ),
    },
    {
      title: 'AI建议',
      key: 'aiSuggestion',
      width: 100,
      render: (_: unknown, record: ModerationQueueItem) => {
        if (!record.aiSuggestion) return '-';
        const suggestion = aiSuggestionMap[record.aiSuggestion];
        return (
          <Tooltip title={record.aiReason || 'AI自动分析建议'}>
            <Tag
              color={suggestion.color}
              icon={<RobotOutlined style={{ marginRight: 4 }} />}
            >
              {suggestion.label}
            </Tag>
          </Tooltip>
        );
      },
    },
    {
      title: '提交时间',
      key: 'submittedAt',
      width: 120,
      render: (_: unknown, record: ModerationQueueItem) => (
        <Text type="secondary" style={{ fontSize: 12 }}>
          {formatDate(record.submittedAt)}
        </Text>
      ),
    },
    {
      title: '操作',
      key: 'actions',
      width: 200,
      fixed: 'right' as const,
      render: (_: unknown, record: ModerationQueueItem) => (
        <Space size="small">
          <Tooltip title="查看详情">
            <Button
              type="text"
              icon={<EyeOutlined />}
              onClick={() => {
                onViewDetail(record);
              }}
            />
          </Tooltip>
          <Tooltip title="通过">
            <Button
              type="text"
              style={{ color: '#52c41a' }}
              icon={<CheckCircleOutlined />}
              onClick={() => onReview(record, 'approve')}
            />
          </Tooltip>
          <Tooltip title="拒绝">
            <Button
              type="text"
              danger
              icon={<CloseCircleOutlined />}
              onClick={() => onReview(record, 'reject')}
            />
          </Tooltip>
          <Dropdown
            overlay={
              <Menu>
                <Menu.Item
                  key="escalate"
                  icon={<ExclamationCircleOutlined />}
                  onClick={() => onReview(record, 'escalate')}
                >
                  升级处理
                </Menu.Item>
                <Menu.Item
                  key="flag"
                  icon={<FlagOutlined />}
                  onClick={() => onReview(record, 'flag')}
                >
                  标记关注
                </Menu.Item>
              </Menu>
            }
          >
            <Button type="text" icon={<MoreOutlined />} />
          </Dropdown>
        </Space>
      ),
    },
  ];

  // 批量操作菜单
  const batchActionMenu = (
    <Menu>
      <Menu.Item
        key="approve"
        icon={<CheckCircleOutlined style={{ color: '#52c41a' }} />}
        onClick={() => onBatchReview('approve')}
      >
        批量通过
      </Menu.Item>
      <Menu.Item
        key="reject"
        icon={<CloseCircleOutlined style={{ color: '#ff4d4f' }} />}
        onClick={() => onBatchReview('reject')}
      >
        批量拒绝
      </Menu.Item>
      <Menu.Divider />
      <Menu.Item
        key="escalate"
        icon={<ExclamationCircleOutlined />}
        onClick={() => onBatchReview('escalate')}
      >
        批量升级
      </Menu.Item>
    </Menu>
  );

  return (
    <Card
      className="moderation-queue"
      title={
        <Space>
          <span>审核队列</span>
          <Badge count={total} showZero overflowCount={999} />
        </Space>
      }
      extra={
        <Space>
          <Button icon={<FilterOutlined />}>筛选</Button>
          {selectedItems.length > 0 && (
            <Dropdown overlay={batchActionMenu}>
              <Button type="primary">
                批量操作 (
                {selectedItems.length}
                )
              </Button>
            </Dropdown>
          )}
        </Space>
      }
    >
      {selectedItems.length > 0 && (
        <Alert
          message={
            <Space>
              <span>
                已选择
                {' '}
                <strong>{selectedItems.length}</strong>
                {' '}
                项
              </span>
              <Button type="link" size="small" onClick={() => onSelectionChange([])}>
                取消选择
              </Button>
            </Space>
          }
          type="info"
          showIcon
          style={{ marginBottom: 16 }}
        />
      )}

      <Table
        columns={columns}
        dataSource={items}
        rowKey="id"
        loading={loading}
        pagination={{
          current: page,
          pageSize,
          total,
          showSizeChanger: true,
          showQuickJumper: true,
          showTotal: (totalCount) => `共 ${totalCount} 条`,
          onChange: onPageChange,
        }}
        scroll={{ x: 1200 }}
        locale={{
          emptyText: (
            <Empty
              image={Empty.PRESENTED_IMAGE_SIMPLE}
              description="暂无待审核内容"
            />
          ),
        }}
      />
    </Card>
  );
};

export default ModerationQueue;