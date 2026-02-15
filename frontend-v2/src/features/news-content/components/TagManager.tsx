/**
 * Tag Manager Component
 * 新闻标签管理组件
 */

import { useState, memo } from 'react';
import { Card, Table, Button, Input, Modal, Form, message, Tag, Popconfirm } from 'antd';

import { useTags, useCreateTag, useUpdateTag, useDeleteTag } from '../hooks';
import type { NewsTag } from '../types';

export const TagManager = memo(function TagManager() {
  const [isModalVisible, setIsModalVisible] = useState(false);
  const [editingTag, setEditingTag] = useState<NewsTag | null>(null);
  const [form] = Form.useForm();
  const [keyword, setKeyword] = useState('');

  const { data, isLoading, refetch } = useTags({ keyword: keyword || undefined });
  const createTagMutation = useCreateTag();
  const updateTagMutation = useUpdateTag();
  const deleteTagMutation = useDeleteTag();

  const handleCreate = () => {
    setEditingTag(null);
    form.resetFields();
    setIsModalVisible(true);
  };

  const handleEdit = (tag: NewsTag) => {
    setEditingTag(tag);
    form.setFieldsValue(tag);
    setIsModalVisible(true);
  };

  const handleDelete = (id: string) => {
    void deleteTagMutation.mutateAsync(id).then(() => {
      void message.success('删除成功');
    }).catch(() => {
      void message.error('删除失败');
    });
  };

  const handleSubmit = () => {
    void form.validateFields().then((values: { name: string; slug?: string; description?: string }) => {
      const promise = editingTag
        ? updateTagMutation.mutateAsync({ id: editingTag.id, data: values })
        : createTagMutation.mutateAsync(values);
      promise.then(() => {
        void message.success(editingTag ? '更新成功' : '创建成功');
        setIsModalVisible(false);
        void refetch();
      }).catch(() => {
        void message.error('操作失败');
      });
    });
  };

  const columns = [
    {
      title: '名称',
      dataIndex: 'name',
      key: 'name',
      render: (name: string) => <Tag color="blue">{name}</Tag>,
    },
    {
      title: 'Slug',
      dataIndex: 'slug',
      key: 'slug',
    },
    {
      title: '使用次数',
      dataIndex: 'count',
      key: 'count',
    },
    {
      title: '描述',
      dataIndex: 'description',
      key: 'description',
      ellipsis: true,
    },
    {
      title: '操作',
      key: 'actions',
      render: (_: unknown, record: NewsTag) => (
        <div className="flex gap-2">
          <Button size="small" onClick={() => handleEdit(record)}>
            编辑
          </Button>
          <Popconfirm
            title="确认删除"
            description="确定要删除这个标签吗？"
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
    <div className="tag-manager">
      <Card
        title="标签管理"
        extra={
          <Button type="primary" onClick={handleCreate}>
            新建标签
          </Button>
        }
      >
        <div className="mb-4">
          <Input
            placeholder="搜索标签..."
            value={keyword}
            onChange={(e) => setKeyword(e.target.value)}
            style={{ width: 200 }}
            onPressEnter={() => void refetch()}
          />
        </div>
        <Table
          columns={columns}
          dataSource={data?.items}
          loading={isLoading}
          rowKey="id"
          pagination={{
            total: data?.total,
            pageSize: 10,
          }}
        />
      </Card>

      <Modal
        title={editingTag ? '编辑标签' : '新建标签'}
        open={isModalVisible}
        onOk={handleSubmit}
        onCancel={() => setIsModalVisible(false)}
        confirmLoading={createTagMutation.isPending || updateTagMutation.isPending}
      >
        <Form form={form} layout="vertical">
          <Form.Item
            name="name"
            label="名称"
            rules={[{ required: true, message: '请输入标签名称' }]}
          >
            <Input />
          </Form.Item>
          <Form.Item name="slug" label="Slug">
            <Input placeholder="URL 友好的标识符" />
          </Form.Item>
          <Form.Item name="description" label="描述">
            <Input.TextArea rows={3} />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
});
