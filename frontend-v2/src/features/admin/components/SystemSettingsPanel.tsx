import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Card, Typography, Switch, Button, Tag, Input, Space, message, Tabs } from 'antd';
import {
  Settings, Save, Bell, Shield, Globe, Database,
  RefreshCw, Mail, Key, Lock
} from 'lucide-react';
import { apiClient } from '@/shared/lib/api/client';

const { Title, Text } = Typography;

interface SystemConfig {
  site_name: string;
  site_description: string;
  contact_email: string;
  maintenance_mode: boolean;
  registration_enabled: boolean;
  ai_consultation_enabled: boolean;
  max_upload_size_mb: number;
  session_timeout_minutes: number;
  rate_limit_per_minute: number;
  notification_email_enabled: boolean;
  sms_enabled: boolean;
  wechat_notification_enabled: boolean;
}

async function fetchSystemConfig(): Promise<SystemConfig> {
  const { data } = await apiClient.get<{ data: SystemConfig }>('/v1/admin/settings');
  return (data as unknown as { data: SystemConfig }).data ?? (data as unknown as SystemConfig);
}

async function updateSystemConfig(config: Partial<SystemConfig>): Promise<SystemConfig> {
  const { data } = await apiClient.put<{ data: SystemConfig }>('/v1/admin/settings', config);
  return (data as unknown as { data: SystemConfig }).data ?? (data as unknown as SystemConfig);
}

export function SystemSettingsPanel(): JSX.Element {
  const queryClient = useQueryClient();
  const [activeTab, setActiveTab] = useState('basic');

  const { data: config, isLoading } = useQuery({
    queryKey: ['admin', 'system-config'],
    queryFn: fetchSystemConfig,
  });

  const updateMutation = useMutation({
    mutationFn: updateSystemConfig,
    onSuccess: () => {
      message.success('设置已保存');
      void queryClient.invalidateQueries({ queryKey: ['admin', 'system-config'] });
    },
  });

  const handleToggle = (key: keyof SystemConfig) => {
    if (!config) return;
    updateMutation.mutate({ [key]: !config[key] });
  };

  const defaultConfig: SystemConfig = {
    site_name: '百姓法律助手',
    site_description: '您的随身法律顾问',
    contact_email: 'admin@baixingfalv.com',
    maintenance_mode: false,
    registration_enabled: true,
    ai_consultation_enabled: true,
    max_upload_size_mb: 10,
    session_timeout_minutes: 30,
    rate_limit_per_minute: 60,
    notification_email_enabled: true,
    sms_enabled: false,
    wechat_notification_enabled: true,
  };

  const cfg = config ?? defaultConfig;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Settings className="w-6 h-6 text-blue-600" />
          <Title level={4} className="!mb-0">系统设置</Title>
        </div>
        <Button
          type="primary"
          icon={<Save className="w-4 h-4" />}
          loading={updateMutation.isPending}
          onClick={() => updateMutation.mutate(cfg)}
        >
          保存设置
        </Button>
      </div>

      <Tabs
        activeKey={activeTab}
        onChange={setActiveTab}
        items={[
          {
            key: 'basic',
            label: <span className="flex items-center gap-2"><Globe className="w-4 h-4" />基本设置</span>,
            children: (
              <div className="space-y-4 pt-4">
                <Card size="small" title="站点信息" className="hover:shadow-sm">
                  <div className="space-y-3">
                    <div>
                      <Text className="text-sm font-medium text-gray-600 block mb-1">站点名称</Text>
                      <Input defaultValue={cfg.site_name} className="max-w-md" />
                    </div>
                    <div>
                      <Text className="text-sm font-medium text-gray-600 block mb-1">站点描述</Text>
                      <Input defaultValue={cfg.site_description} className="max-w-md" />
                    </div>
                    <div>
                      <Text className="text-sm font-medium text-gray-600 block mb-1">
                        <Mail className="w-3.5 h-3.5 inline mr-1" />联系邮箱
                      </Text>
                      <Input defaultValue={cfg.contact_email} className="max-w-md" />
                    </div>
                  </div>
                </Card>

                <Card size="small" title="功能开关">
                  <div className="space-y-3">
                    {[
                      { key: 'maintenance_mode' as const, label: '维护模式', desc: '启用后仅管理员可访问' },
                      { key: 'registration_enabled' as const, label: '用户注册', desc: '允许新用户注册' },
                      { key: 'ai_consultation_enabled' as const, label: 'AI 咨询', desc: '启用 AI 法律咨询服务' },
                    ].map(item => (
                      <div key={item.key} className="flex items-center justify-between py-2 border-b border-gray-100 last:border-0">
                        <div>
                          <Text className="font-medium text-gray-900">{item.label}</Text>
                          <Text className="text-xs text-gray-400 block">{item.desc}</Text>
                        </div>
                        <Switch
                          checked={cfg[item.key]}
                          onChange={() => handleToggle(item.key)}
                          loading={updateMutation.isPending}
                        />
                      </div>
                    ))}
                  </div>
                </Card>

                <Card size="small" title="上传限制">
                  <div className="space-y-3">
                    <div>
                      <Text className="text-sm font-medium text-gray-600 block mb-1">最大上传大小 (MB)</Text>
                      <Input type="number" defaultValue={cfg.max_upload_size_mb} className="max-w-xs" min={1} max={100} />
                    </div>
                  </div>
                </Card>
              </div>
            ),
          },
          {
            key: 'security',
            label: <span className="flex items-center gap-2"><Shield className="w-4 h-4" />安全设置</span>,
            children: (
              <div className="space-y-4 pt-4">
                <Card size="small" title="会话与限流">
                  <div className="space-y-3">
                    <div>
                      <Text className="text-sm font-medium text-gray-600 block mb-1">会话超时时间 (分钟)</Text>
                      <Input type="number" defaultValue={cfg.session_timeout_minutes} className="max-w-xs" min={5} max={1440} />
                    </div>
                    <div>
                      <Text className="text-sm font-medium text-gray-600 block mb-1">API 速率限制 (次/分钟)</Text>
                      <Input type="number" defaultValue={cfg.rate_limit_per_minute} className="max-w-xs" min={10} max={1000} />
                    </div>
                  </div>
                </Card>

                <Card size="small" title="密码策略">
                  <div className="space-y-3">
                    <div className="flex items-center justify-between py-2">
                      <div>
                        <Text className="font-medium text-gray-900">强制密码复杂度</Text>
                        <Text className="text-xs text-gray-400 block">要求包含大小写字母、数字和特殊字符</Text>
                      </div>
                      <Switch defaultChecked />
                    </div>
                    <div className="flex items-center justify-between py-2">
                      <div>
                        <Text className="font-medium text-gray-900">登录失败锁定</Text>
                        <Text className="text-xs text-gray-400 block">5次失败后锁定账户30分钟</Text>
                      </div>
                      <Switch defaultChecked />
                    </div>
                  </div>
                </Card>
              </div>
            ),
          },
          {
            key: 'notification',
            label: <span className="flex items-center gap-2"><Bell className="w-4 h-4" />通知设置</span>,
            children: (
              <div className="space-y-4 pt-4">
                <Card size="small" title="通知渠道">
                  <div className="space-y-3">
                    {[
                      { key: 'notification_email_enabled' as const, label: '邮件通知', desc: '通过邮件发送系统通知' },
                      { key: 'sms_enabled' as const, label: '短信通知', desc: '通过短信发送重要通知' },
                      { key: 'wechat_notification_enabled' as const, label: '微信通知', desc: '通过微信公众号推送通知' },
                    ].map(item => (
                      <div key={item.key} className="flex items-center justify-between py-2 border-b border-gray-100 last:border-0">
                        <div>
                          <Text className="font-medium text-gray-900">{item.label}</Text>
                          <Text className="text-xs text-gray-400 block">{item.desc}</Text>
                        </div>
                        <Switch
                          checked={cfg[item.key]}
                          onChange={() => handleToggle(item.key)}
                          loading={updateMutation.isPending}
                        />
                      </div>
                    ))}
                  </div>
                </Card>
              </div>
            ),
          },
          {
            key: 'database',
            label: <span className="flex items-center gap-2"><Database className="w-4 h-4" />数据维护</span>,
            children: (
              <div className="space-y-4 pt-4">
                <Card size="small" title="数据操作">
                  <div className="space-y-4">
                    <div className="p-4 bg-yellow-50 rounded-lg border border-yellow-200">
                      <Text className="text-yellow-800 font-medium flex items-center gap-2">
                        <Lock className="w-4 h-4" /> 谨慎操作
                      </Text>
                      <Text className="text-yellow-600 text-sm block mt-1">
                        以下操作不可逆，请在操作前确保已备份数据
                      </Text>
                    </div>
                    <Space direction="vertical" className="w-full">
                      <Button icon={<RefreshCw className="w-4 h-4" />} block>
                        清理过期会话数据
                      </Button>
                      <Button icon={<RefreshCw className="w-4 h-4" />} block>
                        重建搜索索引
                      </Button>
                      <Button icon={<Database className="w-4 h-4" />} block>
                        导出完整备份
                      </Button>
                    </Space>
                  </div>
                </Card>
              </div>
            ),
          },
        ]}
      />
    </div>
  );
}