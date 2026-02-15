/**
 * StatsCards 组件 - 统计卡片
 */

import React from 'react';
import { Card, Row, Col, Statistic, Skeleton } from 'antd';
import {
  UserOutlined,
  FileTextOutlined,
  ReadOutlined,
  BankOutlined,
  CommentOutlined,
  CustomerServiceOutlined,
} from '@ant-design/icons';

import type { AdminStats } from '../types';

/** 统计卡片Props */
interface StatsCardsProps {
  stats: AdminStats | null;
  loading: boolean;
}

/** 统计项配置 */
const STAT_CONFIG = [
  {
    key: 'users',
    title: '总用户数',
    icon: <UserOutlined style={{ color: '#1890ff' }} />,
    color: '#e6f7ff',
    borderColor: '#91d5ff',
  },
  {
    key: 'news',
    title: '新闻数量',
    icon: <FileTextOutlined style={{ color: '#52c41a' }} />,
    color: '#f6ffed',
    borderColor: '#b7eb8f',
  },
  {
    key: 'posts',
    title: '帖子数量',
    icon: <ReadOutlined style={{ color: '#faad14' }} />,
    color: '#fffbe6',
    borderColor: '#ffe58f',
  },
  {
    key: 'lawfirms',
    title: '律所数量',
    icon: <BankOutlined style={{ color: '#722ed1' }} />,
    color: '#f9f0ff',
    borderColor: '#d3adf7',
  },
  {
    key: 'comments',
    title: '评论数量',
    icon: <CommentOutlined style={{ color: '#eb2f96' }} />,
    color: '#fff0f6',
    borderColor: '#ffadd2',
  },
  {
    key: 'consultations',
    title: '咨询数量',
    icon: <CustomerServiceOutlined style={{ color: '#13c2c2' }} />,
    color: '#e6fffb',
    borderColor: '#87e8de',
  },
] as const;

/**
 * 格式化数字（大于1000显示为k）
 */
function formatNumber(num: number): string {
  if (num >= 1000000) {
    return `${(num / 1000000).toFixed(1)}M`;
  }
  if (num >= 1000) {
    return `${(num / 1000).toFixed(1)}K`;
  }
  return num.toString();
}

/**
 * 统计卡片组件
 */
export const StatsCards: React.FC<StatsCardsProps> = ({ stats, loading }) => {
  return (
    <Row gutter={[16, 16]}>
      {STAT_CONFIG.map((config) => (
        <Col xs={24} sm={12} lg={8} xl={4} key={config.key}>
          <Card
            bodyStyle={{ padding: '20px 24px' }}
            style={{
              backgroundColor: config.color,
              borderColor: config.borderColor,
              borderWidth: 1,
              borderStyle: 'solid',
            }}
          >
            {loading || !stats ? (
              <Skeleton active paragraph={false} title={{ width: '80%' }} />
            ) : (
              <Statistic
                title={
                  <span style={{ color: 'rgba(0, 0, 0, 0.45)' }}>
                    {config.title}
                  </span>
                }
                value={stats[config.key as keyof AdminStats]}
                prefix={config.icon}
                formatter={(value) => formatNumber(Number(value))}
                valueStyle={{ color: 'rgba(0, 0, 0, 0.85)', fontWeight: 600 }}
              />
            )}
          </Card>
        </Col>
      ))}
    </Row>
  );
};