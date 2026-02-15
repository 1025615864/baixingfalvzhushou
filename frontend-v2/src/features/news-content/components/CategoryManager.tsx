/**
 * Category Manager Component
 * 新闻分类管理组件
 */

import { useState, memo } from 'react';
import { Card, Table, Button, Input, Modal, Form, message, Tag } from 'antd';

import { useCategories, useCreateCategory, useUpdateCategory, useDeleteCategory } from '../hooks';
import type { NewsCategory } from '../types';

export const CategoryManager = memo(function CategoryManager() {
  const [isModalVisible, setIsModalVisible] = useState(false);
  const [editingCategory, setEditingCategory] = useState<NewsCategory | null>(null);
  const [form] = Form.useForm();

  const { data: categories, isLoading } = useCategories();
  const createCategoryMutation = useCreateCategory();
  const updateCategoryMutation = useUpdateCategory();
  const deleteCategoryMutation = useDeleteCategory();

  const handleCreate = () => {
    setEditingCategory(null);
    form.resetFields();
    setIsModalVisible(true);
  };

  const handleEdit = (category: NewsCategory) => {
    setEditingCategory(category);
    form.setFieldsValue(category);
    setIsModalVisible(true);
  };

  const handleDelete = (id: string) => {
    Modal.confirm({
      title: '确认删除',
      content: '确定要删除这个分类吗？该分类下的文章将变为未分类状态。',
      onOk: () => {
        void deleteCategoryMutation.mutateAsync(id).then(() => {
          void message.success('删除成功');
        }).catch(() => {
          void message.error('删除失败');
        });
      },
    });
  };

  const handleSubmit = () => {
    void form.validateFields().then((values: { name: string; description?: string; icon?: string; sortOrder?: number }) => {
      if (editingCategory) {
        void updateCategoryMutation.mutateAsync({ id: editingCategory.id, data: values }).then(() => {
          void message.success('更新成功');
          setIsModalVisible(false);
        }).catch(() => {
          void message.error('操作失败');
        });
      } else {
        void createCategoryMutation.mutateAsync(values).then(() => {
          void message.success('创建成功');
          setIsModalVisible(false);
        }).catch(() => {
          void message.error('操作失败');
        });
      }
    });
  };

  const columns = [
    {
      title: '排序',
      key: 'sort',
      width: 60,
      render: () => <span className="cursor-move text-gray-400">::</span>,
    },
    {
      title: '名称',
      dataIndex: 'name',
      key: 'name',
      render: (name: string, record: NewsCategory) => (
        <div>
          <span className="font-medium">{name}</span>
          {record.icon && <Tag className="ml-2">{record.icon}</Tag>}
        </div>
      ),
    },
    {
      title: '描述',
      dataIndex: 'description',
      key: 'description',
      ellipsis: true,
    },
    {
      title: '文章数',
      dataIndex: 'articleCount',
      key: 'articleCount',
    },
    {
      title: '状态',
      dataIndex: 'isActive',
      key: 'isActive',
      render: (isActive: boolean) => (
        <Tag color={isActive ? 'green' : 'default'}>{isActive ? '启用' : '禁用'}</Tag>
      ),
    },
    {
      title: '操作',
      key: 'actions',
      render: (_: unknown, record: NewsCategory) => (
        <div className="flex gap-2">
          <Button size="small" onClick={() => handleEdit(record)}>
            编辑
          </Button>
          <Button size="small" danger onClick={() => handleDelete(record.id)}>
            删除
          </Button>
        </div>
      ),
    },
  ];

  return (
    <div className="category-manager">
      <Card
        title="分类管理"
        extra={
          <Button type="primary" onClick={handleCreate}>
            新建分类
          </Button>
        }
      >
        <Table
          columns={columns}
          dataSource={categories}
          loading={isLoading}
          rowKey="id"
          pagination={false}
        />
      </Card>

      <Modal
        title={editingCategory ? '编辑分类' : '新建分类'}
        open={isModalVisible}
        onOk={handleSubmit}
        onCancel={() => setIsModalVisible(false)}
        confirmLoading={createCategoryMutation.isPending || updateCategoryMutation.isPending}
      >
        <Form form={form} layout="vertical">
          <Form.Item
            name="name"
            label="名称"
            rules={[{ required: true, message: '请输入分类名称' }]}
          >
            <Input />
          </Form.Item>
          <Form.Item name="description" label="描述">
            <Input.TextArea rows={3} />
          </Form.Item>
          <Form.Item name="icon" label="图标">
            <Input placeholder="图标标识符" />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
});
