/**
 * AI配置表单组件
 */

import React, { useEffect, useState } from 'react';
import { Modal, Form, Input, Select, InputNumber, Switch, Divider, Alert } from 'antd';

import type {
  AIConfigFormProps,
  CreateAIModelConfigRequest,
  UpdateAIModelConfigRequest,
} from '../types/ai-config';

/**
 * AI配置表单组件
 */
export const AIConfigForm: React.FC<AIConfigFormProps> = ({
  visible,
  config,
  providers,
  onCancel,
  onConfirm,
  loading,
}) => {
  const [form] = Form.useForm();
  const [selectedProvider, setSelectedProvider] = useState<string>('openai');
  const isEdit = !!config;

  // 当config变化时更新表单
  useEffect(() => {
    if (visible) {
      if (config) {
        form.setFieldsValue({
          name: config.name,
          provider: config.provider,
          model_id: config.model_id,
          api_key: '***', // 显示占位符
          base_url: config.base_url,
          enabled: config.enabled,
          weight: config.weight,
          priority: config.priority,
          is_primary: config.is_primary,
          max_tokens: config.max_tokens,
          temperature: config.temperature,
        });
        setSelectedProvider(config.provider);
      } else {
        form.resetFields();
        form.setFieldsValue({
          provider: 'openai',
          enabled: true,
          weight: 1,
          priority: 0,
          is_primary: false,
        });
        setSelectedProvider('openai');
      }
    }
  }, [visible, config, form]);

  // 获取选中提供商的模型列表
  const getModelsForProvider = () => {
    const provider = providers.find((p) => p.id === selectedProvider);
    return provider?.models || [];
  };

  // 处理提交
  const handleOk = async (): Promise<void> => {
    try {
      const values = await form.validateFields() as Record<string, unknown>;

      // 处理API Key
      const data: Record<string, unknown> = { ...values };
      const apiKey = data.api_key;
      if (typeof apiKey === 'string' && (apiKey === '***' || apiKey.includes('•'))) {
        delete data.api_key; // 保持原值
      }

      if (isEdit) {
        void onConfirm(data as unknown as UpdateAIModelConfigRequest);
      } else {
        void onConfirm(data as unknown as CreateAIModelConfigRequest);
      }
    } catch {
      // 表单验证失败
    }
  };

  // 包装handleOk以避免Promise问题
  const handleOkWrapper = (): void => {
    void handleOk();
  };

  return (
    <Modal
      title={isEdit ? '编辑AI配置' : '添加AI配置'}
      open={visible}
      onCancel={onCancel}
      onOk={handleOkWrapper}
      confirmLoading={loading}
      width={600}
      destroyOnClose
    >
      <Form
        form={form}
        layout="vertical"
        initialValues={{
          provider: 'openai',
          enabled: true,
          weight: 1,
          priority: 0,
          is_primary: false,
        }}
      >
        <Form.Item
          name="name"
          label="配置名称"
          rules={[{ required: true, message: '请输入配置名称' }]}
        >
          <Input placeholder="例如：DeepSeek主配置" />
        </Form.Item>

        <Form.Item
          name="provider"
          label="提供商"
          rules={[{ required: true, message: '请选择提供商' }]}
        >
          <Select
            onChange={(value: string) => {
              setSelectedProvider(value);
              form.setFieldValue('model_id', undefined);
            }}
            options={providers.map((p) => ({
              label: p.name,
              value: p.id,
            }))}
          />
        </Form.Item>

        <Form.Item
          name="model_id"
          label="模型ID"
          rules={[{ required: true, message: '请选择或输入模型ID' }]}
        >
          <Select
            showSearch
            placeholder="选择或输入模型ID"
            optionFilterProp="children"
            filterOption={(input, option) =>
              (option?.label ?? '').toLowerCase().includes(input.toLowerCase())
            }
            options={getModelsForProvider().map((m) => ({
              label: m,
              value: m,
            }))}
            allowClear
          />
        </Form.Item>

        <Form.Item
          name="api_key"
          label="API Key"
          extra={isEdit ? '留空保持原值，输入新值将覆盖' : '请输入API密钥'}
        >
          <Input.Password
            placeholder={isEdit ? '留空保持原值' : '请输入API Key'}
            autoComplete="new-password"
          />
        </Form.Item>

        <Form.Item
          name="base_url"
          label="Base URL"
          extra="可选，用于自定义API端点"
        >
          <Input placeholder="例如：https://api.deepseek.com" />
        </Form.Item>

        <Divider>负载均衡设置</Divider>

        <div className="grid grid-cols-2 gap-4">
          <Form.Item
            name="weight"
            label="权重"
            tooltip="权重越高，被选中的概率越大"
          >
            <InputNumber min={1} max={100} className="w-full" />
          </Form.Item>

          <Form.Item
            name="priority"
            label="优先级"
            tooltip="优先级越高，越优先使用"
          >
            <InputNumber min={0} max={100} className="w-full" />
          </Form.Item>
        </div>

        <div className="grid grid-cols-2 gap-4">
          <Form.Item
            name="enabled"
            label="启用状态"
            valuePropName="checked"
          >
            <Switch checkedChildren="启用" unCheckedChildren="禁用" />
          </Form.Item>

          <Form.Item
            name="is_primary"
            label="设为主配置"
            valuePropName="checked"
            tooltip="主配置会优先被使用"
          >
            <Switch />
          </Form.Item>
        </div>

        <Divider>模型参数</Divider>

        <div className="grid grid-cols-2 gap-4">
          <Form.Item
            name="max_tokens"
            label="最大Token数"
            tooltip="生成内容的最大token数量"
          >
            <InputNumber min={1} max={128000} className="w-full" />
          </Form.Item>

          <Form.Item
            name="temperature"
            label="温度"
            tooltip="控制输出的随机性，0-1之间"
          >
            <InputNumber min={0} max={2} step={0.1} className="w-full" />
          </Form.Item>
        </div>

        {isEdit && (
          <Alert
            message="注意"
            description="修改配置后，新的请求将使用新配置。正在进行中的请求不受影响。"
            type="info"
            showIcon
          />
        )}
      </Form>
    </Modal>
  );
};
