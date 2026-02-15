/**
 * UserEditDialog 组件 - 用户编辑对话框
 */

import React, { useState, useEffect } from 'react';
import {
  Modal,
  Select,
  Form,
  Space,
  Avatar,
  Typography,
  Tag,
} from 'antd';
import {
  UserOutlined,
  SafetyCertificateOutlined,
} from '@ant-design/icons';

import type { UserListItem, UserRole } from '../types';

const { Text } = Typography;

/** 角色选项配置 */
const ROLE_OPTIONS: { value: UserRole; label: string; color: string; description: string }[] = [
  {
    value: 'user',
    label: '普通用户',
    color: 'green',
    description: '拥有基本功能权限',
  },
  {
    value: 'lawyer',
    label: '律师',
    color: 'blue',
    description: '可接受咨询、管理案件',
  },
  {
    value: 'admin',
    label: '管理员',
    color: 'red',
    description: '拥有全部管理权限',
  },
];

/** 用户编辑对话框Props */
interface UserEditDialogProps {
  user: UserListItem | null;
  visible: boolean;
  onCancel: () => void;
  onConfirm: (userId: number, role: UserRole) => void;
  loading: boolean;
}

/**
 * 用户编辑对话框组件
 */
export const UserEditDialog: React.FC<UserEditDialogProps> = ({
  user,
  visible,
  onCancel,
  onConfirm,
  loading,
}) => {
  const [selectedRole, setSelectedRole] = useState<UserRole>('user');

  // 当用户变化时，更新选中的角色
  useEffect(() => {
    if (user) {
      setSelectedRole(user.role);
    }
  }, [user]);

  /** 处理确认 */
  const handleConfirm = () => {
    if (user) {
      onConfirm(user.id, selectedRole);
    }
  };

  /** 处理取消 */
  const handleCancel = () => {
    if (user) {
      setSelectedRole(user.role); // 重置为原始角色
    }
    onCancel();
  };

  if (!user) return null;

  return (
    <Modal
      title={
        <Space>
          <SafetyCertificateOutlined />
          <span>修改用户角色</span>
        </Space>
      }
      open={visible}
      onOk={handleConfirm}
      onCancel={handleCancel}
      confirmLoading={loading}
      okText="确认修改"
      cancelText="取消"
      width={480}
    >
      <div className="py-4">
        {/* 用户信息卡片 */}
        <div className="bg-gray-50 p-4 rounded-lg mb-4">
          <Space size="large">
            <Avatar
              src={user.avatar || undefined}
              size={64}
              icon={<UserOutlined />}
            >
              {user.username.charAt(0).toUpperCase()}
            </Avatar>
            <div>
              <div className="text-lg font-medium">{user.username}</div>
              <div className="text-gray-500">{user.email}</div>
              <div className="mt-2">
                <Tag color={user.is_active ? 'success' : 'error'}>
                  {user.is_active ? '正常' : '已禁用'}
                </Tag>
                <Tag color={user.email_verified ? 'success' : 'default'}>
                  {user.email_verified ? '已验证' : '未验证'}
                </Tag>
              </div>
            </div>
          </Space>
        </div>

        {/* 角色选择表单 */}
        <Form layout="vertical">
          <Form.Item
            label={<span className="font-medium">选择新角色</span>}
            required
          >
            <Select<UserRole>
              value={selectedRole}
              onChange={setSelectedRole}
              style={{ width: '100%' }}
              size="large"
              options={ROLE_OPTIONS.map((role) => ({
                value: role.value,
                label: (
                  <Space direction="vertical" size={0} style={{ padding: '4px 0' }}>
                    <Space>
                      <Tag color={role.color}>{role.label}</Tag>
                      {user.role === role.value && (
                        <Tag color="default">当前角色</Tag>
                      )}
                    </Space>
                    <Text type="secondary" style={{ fontSize: '12px' }}>
                      {role.description}
                    </Text>
                  </Space>
                ),
              }))}
            />
          </Form.Item>
        </Form>

        {/* 警告提示 */}
        {selectedRole !== user.role && (
          <div className="bg-yellow-50 border border-yellow-200 rounded p-3 mt-4">
            <Text type="warning" style={{ fontSize: '13px' }}>
              警告：修改角色后，用户的权限将立即发生变化。请谨慎操作。
            </Text>
          </div>
        )}
      </div>
    </Modal>
  );
};