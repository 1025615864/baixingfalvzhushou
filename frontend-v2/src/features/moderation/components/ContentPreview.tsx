/**
 * ContentPreview - 内容预览组件
 *
 * 用于展示待审核内容的完整信息，包括文本内容、附件、作者信息等
 */

import React from 'react';
import { Card, Avatar, Space, Tag, Typography, Divider, Image, Empty } from 'antd';
import {
  UserOutlined,
  ClockCircleOutlined,
  FileTextOutlined,
  PictureOutlined,
  LinkOutlined,
} from '@ant-design/icons';

import type { ContentPreviewData, ContentType } from '../types';

const { Text, Paragraph } = Typography;

/** ContentPreview组件Props */
export interface ContentPreviewProps {
  /** 内容数据 */
  content?: ContentPreviewData;
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

/** 内容类型颜色映射 */
const contentTypeColorMap: Record<ContentType, string> = {
  post: 'blue',
  comment: 'cyan',
  consultation: 'purple',
  document: 'orange',
  news: 'red',
  forum_post: 'green',
  forum_comment: 'lime',
};

/**
 * 格式化日期
 */
function formatDate(dateString: string): string {
  const date = new Date(dateString);
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  });
}

/**
 * 内容预览组件
 */
export const ContentPreview: React.FC<ContentPreviewProps> = ({
  content,
  loading = false,
}) => {
  // 加载中或没有数据时的占位
  if (loading || !content) {
    return (
      <Card loading={loading}>
        <Empty description="选择审核项以查看详情" />
      </Card>
    );
  }

  // 获取附件图标
  const getAttachmentIcon = (type: string) => {
    switch (type) {
      case 'image':
        return <PictureOutlined />;
      case 'link':
        return <LinkOutlined />;
      default:
        return <FileTextOutlined />;
    }
  };

  return (
    <Card
      title={
        <Space>
          <Tag color={contentTypeColorMap[content.contentType]}>
            {contentTypeMap[content.contentType]}
          </Tag>
          {content.title && <Text strong>{content.title}</Text>}
        </Space>
      }
      className="content-preview"
    >
      {/* 作者信息 */}
      <Space align="center" style={{ marginBottom: 16 }}>
        <Avatar
          src={content.author.avatar}
          icon={!content.author.avatar && <UserOutlined />}
          size="large"
        />
        <div>
          <Text strong>{content.author.name}</Text>
          <br />
          <Text type="secondary" style={{ fontSize: 12 }}>
            <ClockCircleOutlined style={{ marginRight: 4 }} />
            {formatDate(content.createdAt)}
          </Text>
        </div>
      </Space>

      <Divider style={{ margin: '12px 0' }} />

      {/* 内容主体 */}
      <div className="content-body" style={{ marginBottom: 16 }}>
        <Paragraph
          style={{
            fontSize: 14,
            lineHeight: 1.8,
            whiteSpace: 'pre-wrap',
          }}
        >
          {content.content}
        </Paragraph>
      </div>

      {/* 上下文信息 */}
      {content.context && (
        <div
          className="content-context"
          style={{
            background: '#f5f5f5',
            padding: 12,
            borderRadius: 8,
            marginBottom: 16,
          }}
        >
          <Text type="secondary" style={{ fontSize: 12, display: 'block', marginBottom: 8 }}>
            上下文
          </Text>
          <Paragraph
            type="secondary"
            style={{
              fontSize: 13,
              margin: 0,
              whiteSpace: 'pre-wrap',
            }}
          >
            {content.context}
          </Paragraph>
        </div>
      )}

      {/* 附件列表 */}
      {content.attachments && content.attachments.length > 0 && (
        <div className="content-attachments">
          <Divider style={{ margin: '12px 0' }} />
          <Text type="secondary" style={{ fontSize: 12, display: 'block', marginBottom: 8 }}>
            附件 ({content.attachments.length})
          </Text>
          <Space wrap>
            {content.attachments.map((attachment) => (
              <Card.Grid
                key={attachment.id}
                style={{
                  width: attachment.type === 'image' ? 120 : 200,
                  padding: 8,
                  textAlign: 'center',
                }}
              >
                {attachment.type === 'image' ? (
                  <Image
                    src={attachment.url}
                    alt={attachment.name}
                    style={{ maxHeight: 100, objectFit: 'cover' }}
                    preview
                  />
                ) : (
                  <a
                    href={attachment.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    style={{ display: 'flex', alignItems: 'center', justifyContent: 'center' }}
                  >
                    <Space direction="vertical" size={4}>
                      {getAttachmentIcon(attachment.type)}
                      <Text style={{ fontSize: 12 }} ellipsis>
                        {attachment.name}
                      </Text>
                    </Space>
                  </a>
                )}
              </Card.Grid>
            ))}
          </Space>
        </div>
      )}
    </Card>
  );
};

export default ContentPreview;