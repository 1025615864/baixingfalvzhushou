/**
 * AI配置表格组件
 */

import React from 'react';
import { Table, Tag, Button, Space, Tooltip, Badge, Switch, Popconfirm } from 'antd';
import {
  EditOutlined,
  DeleteOutlined,
  ApiOutlined,
  HeartOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined,
  ExclamationCircleOutlined,
  QuestionCircleOutlined,
} from '@ant-design/icons';
import type { ColumnsType } from 'antd/es/table';

import type { AIConfigTableProps, AIModelConfigItem, HealthStatus } from '../types/ai-config';

/**
 * 获取健康状态标签
 */
const getHealthStatusTag = (status: HealthStatus) => {
  const statusConfig: Record<HealthStatus, { color: string; icon: React.ReactNode; text: string }> = {
    healthy: { color: 'success', icon: <CheckCircleOutlined />, text: '健康' },
    degraded: { color: 'warning', icon: <ExclamationCircleOutlined />, text: '降级' },
    unhealthy: { color: 'error', icon: <CloseCircleOutlined />, text: '不健康' },
    unknown: { color: 'default', icon: <QuestionCircleOutlined />, text: '未知' },
  };

  const config = statusConfig[status] || statusConfig.unknown;
  return (
    <Tag color={config.color} icon={config.icon}>
      {config.text}
    </Tag>
  );
};

/**
 * 获取提供商标签
 */
const getProviderTag = (provider: string) => {
  const providerColors: Record<string, string> = {
    openai: 'green',
    deepseek: 'blue',
    anthropic: 'purple',
    qwen: 'orange',
    zhipu: 'cyan',
  };

  return (
    <Tag color={providerColors[provider] || 'default'}>
      {provider.toUpperCase()}
    </Tag>
  );
};

/**
 * AI配置表格组件
 */
export const AIConfigTable: React.FC<AIConfigTableProps> = ({
  configs,
  loading,
  onEdit,
  onDelete,
  onToggleEnabled,
  onTest,
  onHealthCheck,
  testingIds,
  healthCheckingIds,
}) => {
  const columns: ColumnsType<AIModelConfigItem> = [
    {
      title: 'ID',
      dataIndex: 'id',
      key: 'id',
      width: 60,
    },
    {
      title: '配置名称',
      dataIndex: 'name',
      key: 'name',
      width: 150,
      render: (text: string, record) => (
        <Space>
          {text}
          {record.is_primary && (
            <Tag color="gold">主配置</Tag>
          )}
        </Space>
      ),
    },
    {
      title: '提供商',
      dataIndex: 'provider',
      key: 'provider',
      width: 100,
      render: (provider: string) => getProviderTag(provider),
    },
    {
      title: '模型ID',
      dataIndex: 'model_id',
      key: 'model_id',
      width: 150,
      ellipsis: true,
    },
    {
      title: '状态',
      dataIndex: 'enabled',
      key: 'enabled',
      width: 80,
      render: (enabled: boolean, record) => (
        <Switch
          checked={enabled}
          onChange={() => onToggleEnabled(record.id, enabled)}
          size="small"
        />
      ),
    },
    {
      title: '健康状态',
      dataIndex: 'health_status',
      key: 'health_status',
      width: 100,
      render: (status: HealthStatus) => getHealthStatusTag(status),
    },
    {
      title: '权重',
      dataIndex: 'weight',
      key: 'weight',
      width: 70,
      sorter: (a, b) => a.weight - b.weight,
    },
    {
      title: '优先级',
      dataIndex: 'priority',
      key: 'priority',
      width: 70,
      sorter: (a, b) => a.priority - b.priority,
    },
    {
      title: '调用统计',
      key: 'stats',
      width: 120,
      render: (_: unknown, record: AIModelConfigItem) => (
        <div className="text-xs">
          <div>
            <Badge status="processing" />
            调用: {record.call_count}
          </div>
          <div>
            <Badge status="error" />
            错误: {record.error_count}
          </div>
        </div>
      ),
    },
    {
      title: '最后使用',
      dataIndex: 'last_used_at',
      key: 'last_used_at',
      width: 140,
      render: (date: string | null) =>
        date ? new Date(date).toLocaleString('zh-CN', {
          month: '2-digit',
          day: '2-digit',
          hour: '2-digit',
          minute: '2-digit',
        }) : '-',
    },
    {
      title: 'API Key',
      dataIndex: 'api_key_configured',
      key: 'api_key_configured',
      width: 80,
      render: (configured: boolean) =>
        configured ? (
          <Tag color="green">已配置</Tag>
        ) : (
          <Tag color="red">未配置</Tag>
        ),
    },
    {
      title: '操作',
      key: 'actions',
      fixed: 'right',
      width: 200,
      render: (_: unknown, record: AIModelConfigItem) => (
        <Space size="small">
          <Tooltip title="编辑">
            <Button
              type="text"
              size="small"
              icon={<EditOutlined />}
              onClick={() => onEdit(record)}
            />
          </Tooltip>
          <Tooltip title="测试连接">
            <Button
              type="text"
              size="small"
              icon={<ApiOutlined />}
              loading={testingIds.has(record.id)}
              onClick={() => onTest(record.id)}
            />
          </Tooltip>
          <Tooltip title="健康检查">
            <Button
              type="text"
              size="small"
              icon={<HeartOutlined />}
              loading={healthCheckingIds.has(record.id)}
              onClick={() => onHealthCheck(record.id)}
            />
          </Tooltip>
          <Popconfirm
            title="确定要删除此配置吗？"
            description="删除后无法恢复"
            onConfirm={() => onDelete(record.id)}
            okText="确定"
            cancelText="取消"
          >
            <Tooltip title="删除">
              <Button
                type="text"
                size="small"
                danger
                icon={<DeleteOutlined />}
              />
            </Tooltip>
          </Popconfirm>
        </Space>
      ),
    },
  ];

  return (
    <Table
      columns={columns}
      dataSource={configs}
      rowKey="id"
      loading={loading}
      scroll={{ x: 1400 }}
      pagination={{
        defaultPageSize: 10,
        showSizeChanger: true,
        showTotal: (total) => `共 ${total} 条`,
      }}
      size="small"
    />
  );
};
