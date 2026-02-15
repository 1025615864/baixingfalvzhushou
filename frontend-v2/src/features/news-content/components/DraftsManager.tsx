/**
 * Drafts Manager Component
 * 草稿管理组件
 */

import { useState, memo } from 'react';
import { Card, Table, Button, Tag, message, Popconfirm, Empty } from 'antd';

import { useDrafts, useDeleteDraft } from '../hooks';
import type { ArticleDraft } from '../types';

interface DraftsManagerProps {
  onEdit?: (id: string) => void;
}

export const DraftsManager = memo(function DraftsManager({ onEdit }: DraftsManagerProps) {
  const [params, setParams] = useState({ page: 1, pageSize: 10 });

  const { data, isLoading, refetch } = useDrafts(params);
  const deleteDraftMutation = useDeleteDraft();

  const handleDelete = (id: string) => {
    void deleteDraftMutation.mutateAsync(id).then(() => {
      void message.success('删除成功');
      void refetch();
    }).catch(() => {
      void message.error('删除失败');
    });
  };

  const columns = [
    {
      title: '标题',
      dataIndex: 'title',
      key: 'title',
      render: (title: string, record: ArticleDraft) => (
        <div>
          <div className="font-medium">{title || '无标题'}</div>
          <div className="text-sm text-gray-500">
            <span className="flex items-center gap-1">
              自动保存: {new Date(record.autoSavedAt).toLocaleString()}
            </span>
          </div>
        </div>
      ),
    },
    {
      title: '标签',
      dataIndex: 'tags',
      key: 'tags',
      render: (tags: string[]) => (
        <div className="flex flex-wrap gap-1">
          {tags?.slice(0, 3).map((tag) => (
            <Tag key={tag} color="orange">{tag}</Tag>
          ))}
          {tags && tags.length > 3 && <Tag>+{tags.length - 3}</Tag>}
        </div>
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
      render: (_: unknown, record: ArticleDraft) => (
        <div className="flex gap-2">
          <Button size="small" onClick={() => onEdit?.(record.id)}>
            继续编辑
          </Button>
          <Popconfirm
            title="确认删除"
            description="确定要删除这个草稿吗？"
            onConfirm={() => handleDelete(record.id)}
          >
            <Button size="small" danger>
              删除
            </Button>
          </Popconfirm>
        </div>
      ),
    },
  ];

  return (
    <div className="drafts-manager">
      <Card
        title="草稿管理"
        extra={
          <Button onClick={() => onEdit?.('')}>
            新建草稿
          </Button>
        }
      >
        {data?.items && data.items.length > 0 ? (
          <Table
            columns={columns}
            dataSource={data.items}
            loading={isLoading}
            rowKey="id"
            pagination={{
              current: params.page,
              pageSize: params.pageSize,
              total: data.total,
              onChange: (page, pageSize) => setParams((prev) => ({ ...prev, page, pageSize })),
            }}
          />
        ) : (
          <Empty description="暂无草稿" />
        )}
      </Card>
    </div>
  );
});
