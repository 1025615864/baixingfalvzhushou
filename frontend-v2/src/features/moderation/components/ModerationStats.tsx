/**
 * ModerationStats - 审核统计组件
 *
 * 展示内容审核的各项统计数据，包括待审核数量、已审核数量、通过率等
 */

import React from 'react';
import {
  Card,
  Row,
  Col,
  Statistic,
  Progress,
  List,
  Tag,
  Typography,
  Empty,
  Spin,
  Timeline,
} from 'antd';
import {
  CheckCircleOutlined,
  CloseCircleOutlined,
  WarningOutlined,
  ClockCircleOutlined,
  BarChartOutlined,
  FileSearchOutlined,
} from '@ant-design/icons';

import type {
  ModerationStats as ModerationStatsData,
  ContentType,
  RiskLevel,
} from '../types';

const { Text } = Typography;

/** ModerationStats组件Props */
export interface ModerationStatsProps {
  /** 统计数据 */
  stats?: ModerationStatsData;
  /** 加载状态 */
  loading?: boolean;
}

/** 内容类型映射 */
const contentTypeMap: Record<ContentType, string> = {
  post: '帖子',
  comment: '评论',
  consultation: '咨询',
  document: '文档',
  news: '新闻',
  forum_post: '论坛帖子',
  forum_comment: '论坛回复',
};

/** 风险等级映射 */
const riskLevelMap: Record<RiskLevel, { label: string; color: string }> = {
  high: { label: '高风险', color: '#ff4d4f' },
  medium: { label: '中风险', color: '#faad14' },
  low: { label: '低风险', color: '#52c41a' },
  none: { label: '无风险', color: '#d9d9d9' },
};

/**
 * 审核统计组件
 */
export const ModerationStats: React.FC<ModerationStatsProps> = ({
  stats,
  loading = false,
}) => {
  // 加载状态
  if (loading) {
    return (
      <Card>
        <div style={{ textAlign: 'center', padding: 40 }}>
          <Spin tip="加载统计中..." />
        </div>
      </Card>
    );
  }

  // 无数据状态
  if (!stats) {
    return (
      <Card>
        <Empty description="暂无统计数据" />
      </Card>
    );
  }

  // 计算通过率
  const passRate = stats.totalReviewed > 0
    ? Math.round((stats.totalApproved / stats.totalReviewed) * 100)
    : 0;

  // 风险等级分布数据
  const riskLevelData = Object.entries(stats.byRiskLevel).map(([level, count]) => ({
    level: level as RiskLevel,
    count,
    ...riskLevelMap[level as RiskLevel],
  }));

  // 内容类型分布数据
  const contentTypeData = Object.entries(stats.byContentType).map(([type, data]) => ({
    type: type as ContentType,
    name: contentTypeMap[type as ContentType],
    ...data,
    total: data.pending + data.approved + data.rejected,
  }));

  return (
    <div className="moderation-stats">
      {/* 概览统计卡片 */}
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col xs={12} sm={8} md={6}>
          <Card>
            <Statistic
              title="待审核"
              value={stats.totalPending}
              valueStyle={{ color: '#faad14' }}
              prefix={<ClockCircleOutlined />}
            />
            <Text type="secondary" style={{ fontSize: 12 }}>
              今日新增:
              {' '}
              {stats.todayPending}
            </Text>
          </Card>
        </Col>
        <Col xs={12} sm={8} md={6}>
          <Card>
            <Statistic
              title="已审核"
              value={stats.totalReviewed}
              valueStyle={{ color: '#1890ff' }}
              prefix={<FileSearchOutlined />}
            />
            <Text type="secondary" style={{ fontSize: 12 }}>
              今日:
              {' '}
              {stats.todayReviewed}
            </Text>
          </Card>
        </Col>
        <Col xs={12} sm={8} md={6}>
          <Card>
            <Statistic
              title="已通过"
              value={stats.totalApproved}
              valueStyle={{ color: '#52c41a' }}
              prefix={<CheckCircleOutlined />}
            />
            <Text type="secondary" style={{ fontSize: 12 }}>
              今日:
              {' '}
              {stats.todayApproved}
            </Text>
          </Card>
        </Col>
        <Col xs={12} sm={8} md={6}>
          <Card>
            <Statistic
              title="已拒绝"
              value={stats.totalRejected}
              valueStyle={{ color: '#ff4d4f' }}
              prefix={<CloseCircleOutlined />}
            />
            <Text type="secondary" style={{ fontSize: 12 }}>
              今日:
              {' '}
              {stats.todayRejected}
            </Text>
          </Card>
        </Col>
      </Row>

      {/* 通过率和平均处理时间 */}
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col xs={24} sm={12}>
          <Card title={<><BarChartOutlined /> 通过率</>}>
            <div style={{ textAlign: 'center' }}>
              <Progress
                type="circle"
                percent={passRate}
                strokeColor={passRate >= 80 ? '#52c41a' : passRate >= 50 ? '#faad14' : '#ff4d4f'}
                format={(percent) => (
                  <span style={{ fontSize: 24, fontWeight: 'bold' }}>{percent}%</span>
                )}
                width={120}
              />
              <div style={{ marginTop: 16 }}>
                <Text type="secondary">
                  已审核
                  {' '}
                  {stats.totalReviewed}
                  {' '}
                  条，通过
                  {' '}
                  {stats.totalApproved}
                  {' '}
                  条
                </Text>
              </div>
            </div>
          </Card>
        </Col>
        <Col xs={24} sm={12}>
          <Card title={<><ClockCircleOutlined /> 平均处理时间</>}>
            <div style={{ textAlign: 'center', padding: '20px 0' }}>
              <div style={{ fontSize: 36, fontWeight: 'bold', color: '#1890ff' }}>
                {Math.round(stats.averageProcessingTime)}
                <span style={{ fontSize: 16, fontWeight: 'normal', marginLeft: 4 }}>秒</span>
              </div>
              <Text type="secondary">
                每篇内容的平均审核时长
              </Text>
            </div>
          </Card>
        </Col>
      </Row>

      {/* 风险等级分布 */}
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col xs={24} md={12}>
          <Card title={<><WarningOutlined /> 风险等级分布</>}>
            <List
              dataSource={riskLevelData}
              renderItem={(item) => (
                <List.Item>
                  <div style={{ display: 'flex', alignItems: 'center', width: '100%' }}>
                    <Tag color={item.color} style={{ minWidth: 70, textAlign: 'center' }}>
                      {item.label}
                    </Tag>
                    <Progress
                      percent={Math.round((item.count / Math.max(stats.totalPending, 1)) * 100)}
                      strokeColor={item.color}
                      showInfo={false}
                      style={{ flex: 1, margin: '0 16px' }}
                    />
                    <Text strong>{item.count}</Text>
                  </div>
                </List.Item>
              )}
            />
          </Card>
        </Col>
        <Col xs={24} md={12}>
          <Card title={<><FileSearchOutlined /> 内容类型分布</>}>
            <List
              dataSource={contentTypeData}
              renderItem={(item) => (
                <List.Item>
                  <div style={{ display: 'flex', alignItems: 'center', width: '100%' }}>
                    <Text style={{ minWidth: 80 }}>{item.name}</Text>
                    <div style={{ flex: 1, margin: '0 16px', display: 'flex', gap: 4 }}>
                      <Tag color="warning" style={{ flex: item.pending }}>{item.pending}</Tag>
                      <Tag color="success" style={{ flex: item.approved }}>{item.approved}</Tag>
                      <Tag color="error" style={{ flex: item.rejected }}>{item.rejected}</Tag>
                    </div>
                    <Text strong>{item.total}</Text>
                  </div>
                </List.Item>
              )}
            />
          </Card>
        </Col>
      </Row>

      {/* 审核趋势时间线 */}
      {stats.trend.length > 0 && (
        <Card title="审核趋势（近7天）" style={{ marginBottom: 24 }}>
          <Timeline mode="alternate">
            {stats.trend.slice(-7).map((item) => (
              <Timeline.Item key={item.date}>
                <div style={{ padding: '8px 16px', background: '#f5f5f5', borderRadius: 8 }}>
                  <Text strong>{item.date}</Text>
                  <div style={{ marginTop: 8 }}>
                    <Tag color="blue">
                      已审核:
                      {item.reviewed}
                    </Tag>
                    <Tag color="green">
                      通过:
                      {item.approved}
                    </Tag>
                    <Tag color="red">
                      拒绝:
                      {item.rejected}
                    </Tag>
                  </div>
                </div>
              </Timeline.Item>
            ))}
          </Timeline>
        </Card>
      )}
    </div>
  );
};

export default ModerationStats;