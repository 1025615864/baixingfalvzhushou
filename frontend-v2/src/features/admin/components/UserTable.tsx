/**
 * UserTable 组件 - 用户列表表格
 */

import React, { useState, useCallback } from 'react';
import {
  Table,
  Tag,
  Switch,
  Button,
  Space,
  Input,
  Avatar,
  Tooltip,
} from 'antd';
import {
  EditOutlined,
  SearchOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined,
} from '@ant-design/icons';

import type { UserListItem, UserRole } from '../types';

/** 用户表格Props */
interface UserTableProps {
  users: UserListItem[];
  loading: boolean;
  pagination: {
    current: number;
    pageSize: number;
    total: number;
  };
  onPageChange: (page: number, pageSize: number) => void;
  onToggleActive: (userId: number, currentStatus: boolean) => void;
  onEditRole: (user: UserListItem) => void;
}

/** 角色标签配置 */
const ROLE_CONFIG: Record<UserRole, { color: string; label: string }> = {
  super_admin: { color: 'magenta', label: '超级管理员' },
  admin: { color: 'red', label: '管理员' },
  forum_admin: { color: 'volcano', label: '论坛管理员' },
  news_admin: { color: 'lime', label: '新闻管理员' },
  ai_admin: { color: 'purple', label: 'AI 管理员' },
  lawyer_admin: { color: 'gold', label: '律师管理员' },
  cs_agent: { color: 'cyan', label: '客服' },
  moderator: { color: 'orange', label: '审核员' },
  lawyer: { color: 'blue', label: '律师' },
  user: { color: 'green', label: '普通用户' },
};

/**
 * 用户表格组件
 */
export const UserTable: React.FC<UserTableProps> = ({
  users,
  loading,
  pagination,
  onPageChange,
  onToggleActive,
  onEditRole,
}) => {
  const [searchText, setSearchText] = useState<string>('');

  /** 处理搜索 */
  const handleSearch = useCallback(
    (value: string) => {
      // 搜索时重置到第一页，通过父组件的keyword过滤
      if (value !== searchText) {
        setSearchText(value);
        onPageChange(1, pagination.pageSize);
      }
    },
    [searchText, pagination.pageSize, onPageChange]
  );

  /** 表格列定义 */
  const columns = [
    {
      title: '用户',
      dataIndex: 'username',
      key: 'username',
      render: (_: string, record: UserListItem) => (
        <Space>
          <Avatar
            src={record.avatar || undefined}
            alt={record.username}
            size="small"
          >
            {record.username.charAt(0).toUpperCase()}
          </Avatar>
          <div>
            <div className="font-medium">{record.username}</div>
            <div className="text-xs text-gray-500">{record.email}</div>
          </div>
        </Space>
      ),
    },
    {
      title: '昵称',
      dataIndex: 'nickname',
      key: 'nickname',
      render: (nickname: string | null) => nickname || '-',
    },
    {
      title: '手机号',
      dataIndex: 'phone',
      key: 'phone',
      render: (phone: string | null) => phone || '-',
    },
    {
      title: '角色',
      dataIndex: 'role',
      key: 'role',
      render: (role: UserRole) => (
        <Tag color={ROLE_CONFIG[role].color}>{ROLE_CONFIG[role].label}</Tag>
      ),
    },
    {
      title: '状态',
      key: 'status',
      render: (_: unknown, record: UserListItem) => (
        <Space>
          <Switch
            checked={record.is_active}
            onChange={() => onToggleActive(record.id, record.is_active)}
            checkedChildren="启用"
            unCheckedChildren="禁用"
            size="small"
          />
          {record.is_active ? (
            <Tag icon={<CheckCircleOutlined />} color="success">
              正常
            </Tag>
          ) : (
            <Tag icon={<CloseCircleOutlined />} color="error">
              禁用
            </Tag>
          )}
        </Space>
      ),
    },
    {
      title: '邮箱验证',
      dataIndex: 'email_verified',
      key: 'email_verified',
      render: (verified: boolean) =>
        verified ? (
          <Tag color="success">已验证</Tag>
        ) : (
          <Tag color="default">未验证</Tag>
        ),
    },
    {
      title: '注册时间',
      dataIndex: 'created_at',
      key: 'created_at',
      render: (date: string) => new Date(date).toLocaleString('zh-CN'),
    },
    {
      title: '操作',
      key: 'action',
      fixed: 'right' as const,
      width: 120,
      render: (_: unknown, record: UserListItem) => (
        <Space size="small">
          <Tooltip title="修改角色">
            <Button
              type="link"
              icon={<EditOutlined />}
              onClick={() => onEditRole(record)}
              size="small"
            >
              角色
            </Button>
          </Tooltip>
        </Space>
      ),
    },
  ];

  return (
    <div className="space-y-4">
      {/* 搜索栏 */}
      <div className="flex justify-between items-center">
        <Input.Search
          placeholder="搜索用户名、邮箱或昵称"
          allowClear
          enterButton={<><SearchOutlined /> 搜索</>}
          onSearch={handleSearch}
          style={{ width: 300 }}
        />
        <div className="text-gray-500 text-sm">
          共 <span className="font-medium">{pagination.total}</span> 位用户
        </div>
      </div>

      {/* 用户表格 */}
      <Table
        columns={columns}
        dataSource={users}
        rowKey="id"
        loading={loading}
        pagination={{
          current: pagination.current,
          pageSize: pagination.pageSize,
          total: pagination.total,
          showSizeChanger: true,
          showQuickJumper: true,
          showTotal: (total, range) =>
            `第 ${range[0]}-${range[1]} 条，共 ${total} 条`,
          pageSizeOptions: [10, 20, 50, 100],
        }}
        onChange={(newPagination) =>
          onPageChange(newPagination.current || 1, newPagination.pageSize || 20)
        }
        scroll={{ x: 1000 }}
      />
    </div>
  );
};