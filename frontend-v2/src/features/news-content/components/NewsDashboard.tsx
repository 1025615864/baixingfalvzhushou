/**
 * News Dashboard Component
 * 新闻内容管理仪表板
 */

import { useState, memo } from 'react';
import { Card, Table, Button, Tag, Space, Input, Select, message, Modal } from 'antd';

import { useArticles, useDeleteArticle, usePublishArticle, useArchiveArticle } from '../hooks';
import type { ArticleEditor } from '../types';

interface NewsDashboardProps {
  onEdit?: (id: string) => void;
  onCreate?: () => void;
}

export const NewsDashboard = memo(function NewsDashboard({ onEdit, onCreate }: NewsDashboardProps) {
  const [params, setParams] = useState({
    page: 1,
    pageSize: 10,
    status: undefined as 'draft' | 'published' | 'archived' | undefined,
    keyword: '',
  });

  const { data, isLoading } = useArticles(params);
  const deleteArticleMutation = useDeleteArticle();
  const publishArticleMutation = usePublishArticle();
  const archiveArticleMutation = useArchiveArticle();

  const handleDelete = (id: string) => {
    Modal.confirm({
      title: '确认删除',
      content: '确定要删除这篇文章吗？此操作不可恢复。',
      onOk: () => {
        void deleteArticleMutation.mutateAsync(id).then(() => {
          void message.success('删除成功');
        }).catch(() => {
          void message.error('删除失败');
        });
      },
    });
  };

  const handlePublish = (id: string) => {
    void publishArticleMutation.mutateAsync(id).then(() => {
      void message.success('发布成功');
    }).catch(() => {
      void message.error('发布失败');
    });
  };

  const handleArchive = (id: string) => {
    void archiveArticleMutation.mutateAsync(id).then(() => {
      void message.success('归档成功');
    }).catch(() => {
      void message.error('归档失败');
    });
  };

  const columns = [
    {
      title: '标题',
      dataIndex: 'title',
      key: 'title',
      render: (title: string, record: ArticleEditor) => (
        <div>
          <div className="font-medium">{title}</div>
          <div className="text-sm text-gray-500">
            {record.categoryName && <Tag>{record.categoryName}</Tag>}
            {record.tags?.slice(0, 3).map((tag) => (
              <Tag key={tag} color="blue">{tag}</Tag>
            ))}
          </div>
        </div>
      ),
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      render: (status: string) => {
        const colors: Record<string, string> = {
          draft: 'orange',
          published: 'green',
          archived: 'default',
        };
        return <Tag color={colors[status]}>{status === 'draft' ? '草稿' : status === 'published' ? '已发布' : '已归档'}</Tag>;
      },
    },
    {
      title: '数据',
      key: 'stats',
      render: (_: unknown, record: ArticleEditor) => (
        <Space size="small">
          <span>👁 {record.viewCount || 0}</span>
          <span>❤️ {record.likeCount || 0}</span>
          <span>💬 {record.commentCount || 0}</span>
        </Space>
      ),
    },
    {
      title: '更新时间',
      dataIndex: 'updatedAt',
      key: 'updatedAt',
      render: (date: string) => new Date(date).toLocaleString(),
    },
    {
      title: '操作',
      key: 'actions',
      render: (_: unknown, record: ArticleEditor) => (
        <Space size="small">
          <Button size="small" onClick={() => onEdit?.(record.id)}>
            查看
          </Button>
          <Button size="small" onClick={() => onEdit?.(record.id)}>
            编辑
          </Button>
          {record.status === 'draft' && (
            <Button size="small" type="primary" onClick={() => handlePublish(record.id)}>
              发布
            </Button>
          )}
          {record.status === 'published' && (
            <Button size="small" onClick={() => handleArchive(record.id)}>
              归档
            </Button>
          )}
          <Button size="small" danger onClick={() => handleDelete(record.id)}>
            删除
          </Button>
        </Space>
      ),
    },
  ];

  return (
    <div className="news-dashboard">
      <Card
        title="新闻内容管理"
        extra={
          <Button type="primary" onClick={onCreate}>
            新建文章
          </Button>
        }
      >
        <div className="filter-section mb-4 flex gap-4">
          <Input
            placeholder="搜索标题..."
            value={params.keyword}
            onChange={(e) => setParams((prev) => ({ ...prev, keyword: e.target.value }))}
            style={{ width: 200 }}
          />
          <Select
            placeholder="状态筛选"
            value={params.status}
            onChange={(status) => setParams((prev) => ({ ...prev, status }))}
            allowClear
            style={{ width: 120 }}
            options={[
              { value: 'draft', label: '草稿' },
              { value: 'published', label: '已发布' },
              { value: 'archived', label: '已归档' },
            ]}
          />
        </div>

        <Table
          columns={columns}
          dataSource={data?.items}
          loading={isLoading}
          rowKey="id"
          pagination={{
            current: params.page,
            pageSize: params.pageSize,
            total: data?.total || 0,
            onChange: (page, pageSize) => setParams((prev) => ({ ...prev, page, pageSize })),
          }}
        />
      </Card>
    </div>
  );
});
