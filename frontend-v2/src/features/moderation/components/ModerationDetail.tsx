/**
 * ModerationDetail - 审核详情组件
 *
 * 展示单个审核项的详细信息，支持内容预览、历史记录、AI分析等
 */

import React, { useState, useCallback } from 'react';
import {
  Drawer,
  Card,
  Tabs,
  Space,
  Tag,
  Button,
  Typography,
  Alert,
  Timeline,
  Radio,
  Input,
  Row,
  Col,
  Badge,
  Empty,
  Spin,
} from 'antd';
import {
  CheckCircleOutlined,
  CloseCircleOutlined,
  EyeOutlined,
  HistoryOutlined,
  RobotOutlined,
  ExclamationCircleOutlined,
  FlagOutlined,
} from '@ant-design/icons';

import type {
  ModerationQueueItem,
  ReviewAction,
  AIReviewResult,
  ModerationRecord,
} from '../types';

import { ContentPreview } from './ContentPreview';

const { Text, Paragraph } = Typography;
const { TextArea } = Input;

/** ModerationDetail组件Props */
export interface ModerationDetailProps {
  /** 当前审核项 */
  item?: ModerationQueueItem;
  /** 是否可见 */
  visible: boolean;
  /** AI审核结果 */
  aiReview?: AIReviewResult;
  /** 审核历史 */
  history?: ModerationRecord[];
  /** 加载状态 */
  loading?: boolean;
  /** 提交审核加载状态 */
  submitting?: boolean;
  /** 关闭回调 */
  onClose: () => void;
  /** 提交审核回调 */
  onSubmit: (action: ReviewAction, reason?: string, note?: string) => void;
}

/** 审核操作选项 */
const reviewOptions: { value: ReviewAction; label: string; color: string; icon: React.ReactNode }[] = [
  {
    value: 'approve',
    label: '通过',
    color: '#52c41a',
    icon: <CheckCircleOutlined />,
  },
  {
    value: 'reject',
    label: '拒绝',
    color: '#ff4d4f',
    icon: <CloseCircleOutlined />,
  },
  {
    value: 'escalate',
    label: '升级',
    color: '#faad14',
    icon: <ExclamationCircleOutlined />,
  },
  {
    value: 'flag',
    label: '标记',
    color: '#1890ff',
    icon: <FlagOutlined />,
  },
];

/** 风险等级颜色映射 */
const riskLevelColorMap = {
  high: 'red',
  medium: 'orange',
  low: 'green',
  none: 'default',
};

/**
 * 格式化日期
 */
function formatDateTime(dateString: string): string {
  const date = new Date(dateString);
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
  });
}

/**
 * 审核详情组件
 */
export const ModerationDetail: React.FC<ModerationDetailProps> = ({
  item,
  visible,
  aiReview,
  history = [],
  loading = false,
  submitting = false,
  onClose,
  onSubmit,
}) => {
  const [selectedAction, setSelectedAction] = useState<ReviewAction>('approve');
  const [reason, setReason] = useState('');
  const [note, setNote] = useState('');

  // 处理提交
  const handleSubmit = useCallback(() => {
    onSubmit(selectedAction, reason || undefined, note || undefined);
    // 重置表单
    setReason('');
    setNote('');
    setSelectedAction('approve');
  }, [selectedAction, reason, note, onSubmit]);

  // 如果没有选中项，显示空状态
  if (!item) {
    return (
      <Drawer
        title="审核详情"
        open={visible}
        onClose={onClose}
        width={800}
      >
        <Empty description="请选择要审核的内容" />
      </Drawer>
    );
  }

  return (
    <Drawer
      title={
        <Space>
          <span>审核详情</span>
          <Tag color={item.riskLevel === 'high' ? 'red' : item.riskLevel === 'medium' ? 'orange' : 'green'}>
            风险
            {item.riskLevel === 'high' ? '高' : item.riskLevel === 'medium' ? '中' : '低'}
          </Tag>
        </Space>
      }
      open={visible}
      onClose={onClose}
      width={900}
      footer={
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <Space>
            <Text type="secondary">审核操作：</Text>
            <Radio.Group
              value={selectedAction}
              onChange={(e) => setSelectedAction(e.target.value as ReviewAction)}
              buttonStyle="solid"
            >
              {reviewOptions.map((option) => (
                <Radio.Button
                  key={option.value}
                  value={option.value}
                  style={{
                    color: selectedAction === option.value ? '#fff' : option.color,
                    backgroundColor: selectedAction === option.value ? option.color : 'transparent',
                    borderColor: option.color,
                  }}
                >
                  <Space>
                    {option.icon}
                    {option.label}
                  </Space>
                </Radio.Button>
              ))}
            </Radio.Group>
          </Space>
          <Space>
            <Button onClick={onClose}>取消</Button>
            <Button
              type="primary"
              loading={submitting}
              onClick={handleSubmit}
              danger={selectedAction === 'reject'}
              style={{
                backgroundColor: reviewOptions.find((o) => o.value === selectedAction)?.color,
                borderColor: reviewOptions.find((o) => o.value === selectedAction)?.color,
              }}
            >
              确认
              {reviewOptions.find((o) => o.value === selectedAction)?.label}
            </Button>
          </Space>
        </div>
      }
    >
      <Spin spinning={loading}>
        <Tabs
          defaultActiveKey="content"
          items={[
            {
              key: 'content',
              label: (
                <Space>
                  <EyeOutlined />
                  内容预览
                </Space>
              ),
              children: (
                <div>
                  {/* AI建议提示 */}
                  {item.aiSuggestion && (
                    <Alert
                      message={
                        <Space>
                          <RobotOutlined />
                          <span>
                            AI 建议
                            {item.aiSuggestion === 'approve'
                              ? '通过'
                              : item.aiSuggestion === 'reject'
                                ? '拒绝'
                                : item.aiSuggestion === 'escalate'
                                  ? '升级'
                                  : '标记'}
                          </span>
                          {item.aiReason && (
                            <Text type="secondary">
                              -
                              {item.aiReason}
                            </Text>
                          )}
                        </Space>
                      }
                      type={
                        item.aiSuggestion === 'approve'
                          ? 'success'
                          : item.aiSuggestion === 'reject'
                            ? 'error'
                            : 'warning'
                      }
                      showIcon
                      style={{ marginBottom: 16 }}
                    />
                  )}

                  <ContentPreview
                    content={{
                      id: item.id,
                      contentId: item.contentId,
                      contentType: item.contentType,
                      title: item.title,
                      content: item.content,
                      author: {
                        id: item.authorId,
                        name: item.authorName,
                        avatar: item.authorAvatar,
                      },
                      createdAt: item.createdAt,
                    }}
                  />

                  {/* 审核备注 */}
                  <Card title="审核备注" style={{ marginTop: 16 }}>
                    <Row gutter={[16, 16]}>
                      <Col span={24}>
                        <TextArea
                          placeholder="请输入审核原因（可选，将通知用户）"
                          value={reason}
                          onChange={(e) => setReason(e.target.value)}
                          rows={2}
                        />
                      </Col>
                      <Col span={24}>
                        <TextArea
                          placeholder="内部备注（仅管理员可见）"
                          value={note}
                          onChange={(e) => setNote(e.target.value)}
                          rows={2}
                        />
                      </Col>
                    </Row>
                  </Card>
                </div>
              ),
            },
            {
              key: 'ai',
              label: (
                <Space>
                  <RobotOutlined />
                  AI 分析
                </Space>
              ),
              children: aiReview ? (
                <div>
                  <Card title="风险评分" style={{ marginBottom: 16 }}>
                    <div style={{ textAlign: 'center', padding: 20 }}>
                      <Badge
                        count={aiReview.riskScore}
                        style={{
                          backgroundColor: riskLevelColorMap[aiReview.riskLevel],
                          fontSize: 24,
                          padding: '10px 20px',
                          height: 50,
                          lineHeight: '30px',
                          borderRadius: 25,
                        }}
                      />
                      <div style={{ marginTop: 16 }}>
                        <Tag color={riskLevelColorMap[aiReview.riskLevel]}>
                          风险等级：
                          {aiReview.riskLevel === 'high'
                            ? '高'
                            : aiReview.riskLevel === 'medium'
                              ? '中'
                              : aiReview.riskLevel === 'low'
                                ? '低'
                                : '无'}
                        </Tag>
                        <Tag color="blue">
                          置信度：
                          {(aiReview.confidence * 100).toFixed(1)}
                          %
                        </Tag>
                      </div>
                    </div>
                  </Card>

                  <Card title="关键词匹配" style={{ marginBottom: 16 }}>
                    {aiReview.keywords.length > 0 ? (
                      <div>
                        {aiReview.keywords.map((keyword, index) => (
                          <Tag
                            key={index}
                            color={
                              keyword.severity === 'high'
                                ? 'red'
                                : keyword.severity === 'medium'
                                  ? 'orange'
                                  : 'default'
                            }
                            style={{ marginBottom: 8 }}
                          >
                            {keyword.keyword}
                            {' '}
                            (
                            {keyword.category}
                            )
                          </Tag>
                        ))}
                      </div>
                    ) : (
                      <Text type="secondary">未检测到敏感关键词</Text>
                    )}
                  </Card>

                  <Card title="分类检测">
                    <Space wrap>
                      {aiReview.categories.map((category, index) => (
                        <Tag key={index} color="blue">
                          {category}
                        </Tag>
                      ))}
                    </Space>
                  </Card>
                </div>
              ) : (
                <Empty description="暂无AI分析数据" />
              ),
            },
            {
              key: 'history',
              label: (
                <Space>
                  <HistoryOutlined />
                  审核历史
                </Space>
              ),
              children: history.length > 0 ? (
                <Timeline mode="left">
                  {history.map((record) => (
                    <Timeline.Item
                      key={record.id}
                      label={formatDateTime(record.reviewedAt)}
                      color={
                        record.action === 'approve'
                          ? 'green'
                          : record.action === 'reject'
                            ? 'red'
                            : record.action === 'escalate'
                              ? 'orange'
                              : 'blue'
                      }
                    >
                      <Card size="small" style={{ marginBottom: 8 }}>
                        <Space direction="vertical" style={{ width: '100%' }}>
                          <Space>
                            <Text strong>
                              {record.action === 'approve'
                                ? '通过'
                                : record.action === 'reject'
                                  ? '拒绝'
                                  : record.action === 'escalate'
                                    ? '升级'
                                    : '标记'}
                            </Text>
                            <Text type="secondary">
                              by
                              {' '}
                              {record.reviewerName}
                            </Text>
                          </Space>
                          {record.reason && (
                            <Paragraph type="secondary" style={{ margin: 0 }}>
                              原因：
                              {record.reason}
                            </Paragraph>
                          )}
                          {record.note && (
                            <Text type="secondary" style={{ fontSize: 12 }}>
                              备注：
                              {record.note}
                            </Text>
                          )}
                        </Space>
                      </Card>
                    </Timeline.Item>
                  ))}
                </Timeline>
              ) : (
                <Empty description="暂无审核历史" />
              ),
            },
          ]}
        />
      </Spin>
    </Drawer>
  );
};

export default ModerationDetail;