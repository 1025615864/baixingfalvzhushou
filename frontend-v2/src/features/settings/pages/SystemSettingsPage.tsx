/**
 * System Settings Page
 * 系统设置页面（管理员用）
 */

import { useState } from 'react';
import { Save, RefreshCw, Server, Shield, Bell, CreditCard, FileText, Users, Globe, Database, Activity } from 'lucide-react';

import { Card, Input, Button, Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui';

import {
  useSystemConfig,
  useUpdateSystemConfig,
  useSystemStatus,
} from '../hooks/useSettings';
import type { SystemConfig } from '../types';

/**
 * 格式化字节大小
 */
function formatBytes(bytes: number): string {
  if (bytes === 0) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(2))} ${sizes[i]}`;
}

/**
 * 格式化运行时间
 */
function formatUptime(seconds: number): string {
  const days = Math.floor(seconds / 86400);
  const hours = Math.floor((seconds % 86400) / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  if (days > 0) return `${days}天 ${hours}小时`;
  if (hours > 0) return `${hours}小时 ${minutes}分钟`;
  return `${minutes}分钟`;
}

/**
 * 系统设置页面
 */
export function SystemSettingsPage(): JSX.Element {
  const [activeTab, setActiveTab] = useState('site');
  const { data: configData, isLoading: configLoading } = useSystemConfig();
  const { data: statusData } = useSystemStatus();
  const updateMutation = useUpdateSystemConfig();

  const config = configData?.config;
  const status = statusData;

  // 本地表单状态
  const [formData, setFormData] = useState<Partial<SystemConfig>>({});

  // 处理保存
  const handleSave = (): void => {
    updateMutation.mutate(formData);
  };

  // 处理字段变更
  const updateField = <K extends keyof SystemConfig>(
    section: K,
    field: keyof SystemConfig[K],
    value: unknown
  ): void => {
    setFormData((prev) => ({
      ...prev,
      [section]: {
        ...(prev[section] ?? config?.[section] ?? {}),
        [field]: value,
      },
    }));
  };

  if (configLoading) {
    return (
      <div className="container mx-auto py-6">
        <div className="animate-pulse space-y-4">
          <div className="h-8 bg-slate-200 rounded w-1/4" />
          <div className="h-96 bg-slate-200 rounded" />
        </div>
      </div>
    );
  }

  return (
    <div className="container mx-auto py-6">
      {/* 页面头部 */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">系统设置</h1>
          <p className="text-slate-600 mt-1">管理平台的系统配置和运行状态</p>
        </div>
        <div className="flex gap-2">
          <Button
            variant="ghost"
            onClick={() => window.location.reload()}
          >
            <RefreshCw className="h-4 w-4 mr-1" />
            刷新
          </Button>
          <Button
            onClick={handleSave}
            disabled={updateMutation.isPending || Object.keys(formData).length === 0}
          >
            <Save className="h-4 w-4 mr-1" />
            {updateMutation.isPending ? '保存中...' : '保存设置'}
          </Button>
        </div>
      </div>

      {/* 系统状态卡片 */}
      {status && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
          <Card className="p-4">
            <div className="flex items-center gap-2 mb-2">
              <Server className="h-5 w-5 text-blue-500" />
              <span className="text-sm text-slate-500">运行时间</span>
            </div>
            <p className="text-xl font-bold text-slate-900">{formatUptime(status.uptime)}</p>
            <p className="text-xs text-slate-500">版本 {status.version}</p>
          </Card>
          <Card className="p-4">
            <div className="flex items-center gap-2 mb-2">
              <Database className="h-5 w-5 text-green-500" />
              <span className="text-sm text-slate-500">数据库</span>
            </div>
            <p className="text-xl font-bold text-slate-900">
              {status.database.connected ? '正常' : '异常'}
            </p>
            <p className="text-xs text-slate-500">延迟 {status.database.latency}ms</p>
          </Card>
          <Card className="p-4">
            <div className="flex items-center gap-2 mb-2">
              <Activity className="h-5 w-5 text-orange-500" />
              <span className="text-sm text-slate-500">内存使用</span>
            </div>
            <p className="text-xl font-bold text-slate-900">
              {((status.memory.used / status.memory.total) * 100).toFixed(1)}%
            </p>
            <p className="text-xs text-slate-500">
              {formatBytes(status.memory.used)} / {formatBytes(status.memory.total)}
            </p>
          </Card>
          <Card className="p-4">
            <div className="flex items-center gap-2 mb-2">
              <Server className="h-5 w-5 text-purple-500" />
              <span className="text-sm text-slate-500">CPU 使用</span>
            </div>
            <p className="text-xl font-bold text-slate-900">{status.cpu.usage.toFixed(1)}%</p>
            <p className="text-xs text-slate-500">{status.cpu.cores} 核心</p>
          </Card>
        </div>
      )}

      {/* 设置标签页 */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="mb-6">
          <TabsTrigger value="site">
            <Globe className="h-4 w-4 mr-1" />
            站点设置
          </TabsTrigger>
          <TabsTrigger value="user">
            <Users className="h-4 w-4 mr-1" />
            用户设置
          </TabsTrigger>
          <TabsTrigger value="consultation">
            <FileText className="h-4 w-4 mr-1" />
            咨询设置
          </TabsTrigger>
          <TabsTrigger value="payment">
            <CreditCard className="h-4 w-4 mr-1" />
            支付设置
          </TabsTrigger>
          <TabsTrigger value="notification">
            <Bell className="h-4 w-4 mr-1" />
            通知设置
          </TabsTrigger>
          <TabsTrigger value="security">
            <Shield className="h-4 w-4 mr-1" />
            安全设置
          </TabsTrigger>
        </TabsList>

        {/* 站点设置 */}
        <TabsContent value="site">
          <Card className="p-6">
            <h2 className="text-lg font-semibold mb-4">站点设置</h2>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">
                  站点名称
                </label>
                <Input
                  value={formData.site?.siteName ?? config?.site.siteName ?? ''}
                  onChange={(e: React.ChangeEvent<HTMLInputElement>) => updateField('site', 'siteName', e.target.value)}
                  placeholder="站点名称"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">
                  站点描述
                </label>
                <Input
                  value={formData.site?.siteDescription ?? config?.site.siteDescription ?? ''}
                  onChange={(e: React.ChangeEvent<HTMLInputElement>) => updateField('site', 'siteDescription', e.target.value)}
                  placeholder="站点描述"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">
                  联系邮箱
                </label>
                <Input
                  type="email"
                  value={formData.site?.contactEmail ?? config?.site.contactEmail ?? ''}
                  onChange={(e: React.ChangeEvent<HTMLInputElement>) => updateField('site', 'contactEmail', e.target.value)}
                  placeholder="contact@example.com"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">
                  联系电话
                </label>
                <Input
                  value={formData.site?.contactPhone ?? config?.site.contactPhone ?? ''}
                  onChange={(e: React.ChangeEvent<HTMLInputElement>) => updateField('site', 'contactPhone', e.target.value)}
                  placeholder="400-xxx-xxxx"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">
                  ICP备案号
                </label>
                <Input
                  value={formData.site?.icp ?? config?.site.icp ?? ''}
                  onChange={(e: React.ChangeEvent<HTMLInputElement>) => updateField('site', 'icp', e.target.value)}
                  placeholder="京ICP备xxxxxxxx号"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">
                  版权信息
                </label>
                <Input
                  value={formData.site?.copyright ?? config?.site.copyright ?? ''}
                  onChange={(e: React.ChangeEvent<HTMLInputElement>) => updateField('site', 'copyright', e.target.value)}
                  placeholder="© 2024 百姓助手"
                />
              </div>
            </div>
          </Card>
        </TabsContent>

        {/* 用户设置 */}
        <TabsContent value="user">
          <Card className="p-6">
            <h2 className="text-lg font-semibold mb-4">用户设置</h2>
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1">
                    默认用户角色
                  </label>
                  <select
                    value={formData.user?.defaultUserRole ?? config?.user.defaultUserRole ?? 'user'}
                    onChange={(e) => updateField('user', 'defaultUserRole', e.target.value)}
                    className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  >
                    <option value="user">普通用户</option>
                    <option value="lawyer">律师</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1">
                    密码最小长度
                  </label>
                  <Input
                    type="number"
                    value={formData.user?.passwordMinLength ?? config?.user.passwordMinLength ?? 8}
                    onChange={(e: React.ChangeEvent<HTMLInputElement>) => updateField('user', 'passwordMinLength', Number(e.target.value))}
                  />
                </div>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1">
                    会话超时（分钟）
                  </label>
                  <Input
                    type="number"
                    value={formData.user?.sessionTimeout ?? config?.user.sessionTimeout ?? 120}
                    onChange={(e: React.ChangeEvent<HTMLInputElement>) => updateField('user', 'sessionTimeout', Number(e.target.value))}
                  />
                </div>
              </div>
              <div className="space-y-2">
                <label className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    checked={formData.user?.allowRegistration ?? config?.user.allowRegistration ?? true}
                    onChange={(e) => updateField('user', 'allowRegistration', e.target.checked)}
                  />
                  <span className="text-sm">允许用户注册</span>
                </label>
                <label className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    checked={formData.user?.requireEmailVerification ?? config?.user.requireEmailVerification ?? false}
                    onChange={(e) => updateField('user', 'requireEmailVerification', e.target.checked)}
                  />
                  <span className="text-sm">需要邮箱验证</span>
                </label>
                <label className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    checked={formData.user?.requirePhoneVerification ?? config?.user.requirePhoneVerification ?? false}
                    onChange={(e) => updateField('user', 'requirePhoneVerification', e.target.checked)}
                  />
                  <span className="text-sm">需要手机验证</span>
                </label>
                <label className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    checked={formData.user?.passwordRequireUppercase ?? config?.user.passwordRequireUppercase ?? false}
                    onChange={(e) => updateField('user', 'passwordRequireUppercase', e.target.checked)}
                  />
                  <span className="text-sm">密码需要包含大写字母</span>
                </label>
                <label className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    checked={formData.user?.passwordRequireNumber ?? config?.user.passwordRequireNumber ?? true}
                    onChange={(e) => updateField('user', 'passwordRequireNumber', e.target.checked)}
                  />
                  <span className="text-sm">密码需要包含数字</span>
                </label>
              </div>
            </div>
          </Card>
        </TabsContent>

        {/* 咨询设置 */}
        <TabsContent value="consultation">
          <Card className="p-6">
            <h2 className="text-lg font-semibold mb-4">咨询设置</h2>
            <div className="space-y-4">
              <div className="grid grid-cols-3 gap-4">
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1">
                    默认价格（元）
                  </label>
                  <Input
                    type="number"
                    value={formData.consultation?.defaultPrice ?? config?.consultation.defaultPrice ?? 0}
                    onChange={(e: React.ChangeEvent<HTMLInputElement>) => updateField('consultation', 'defaultPrice', Number(e.target.value))}
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1">
                    最低价格（元）
                  </label>
                  <Input
                    type="number"
                    value={formData.consultation?.minPrice ?? config?.consultation.minPrice ?? 0}
                    onChange={(e: React.ChangeEvent<HTMLInputElement>) => updateField('consultation', 'minPrice', Number(e.target.value))}
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1">
                    最高价格（元）
                  </label>
                  <Input
                    type="number"
                    value={formData.consultation?.maxPrice ?? config?.consultation.maxPrice ?? 10000}
                    onChange={(e: React.ChangeEvent<HTMLInputElement>) => updateField('consultation', 'maxPrice', Number(e.target.value))}
                  />
                </div>
              </div>
              <div className="grid grid-cols-3 gap-4">
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1">
                    律师佣金比例（%）
                  </label>
                  <Input
                    type="number"
                    value={formData.consultation?.lawyerCommissionRate ?? config?.consultation.lawyerCommissionRate ?? 70}
                    onChange={(e: React.ChangeEvent<HTMLInputElement>) => updateField('consultation', 'lawyerCommissionRate', Number(e.target.value))}
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1">
                    平台佣金比例（%）
                  </label>
                  <Input
                    type="number"
                    value={formData.consultation?.platformCommissionRate ?? config?.consultation.platformCommissionRate ?? 30}
                    onChange={(e: React.ChangeEvent<HTMLInputElement>) => updateField('consultation', 'platformCommissionRate', Number(e.target.value))}
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1">
                    自动完成时间（小时）
                  </label>
                  <Input
                    type="number"
                    value={formData.consultation?.autoCompleteHours ?? config?.consultation.autoCompleteHours ?? 48}
                    onChange={(e: React.ChangeEvent<HTMLInputElement>) => updateField('consultation', 'autoCompleteHours', Number(e.target.value))}
                  />
                </div>
              </div>
              <div className="space-y-2">
                <label className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    checked={formData.consultation?.enableConsultation ?? config?.consultation.enableConsultation ?? true}
                    onChange={(e) => updateField('consultation', 'enableConsultation', e.target.checked)}
                  />
                  <span className="text-sm">启用咨询功能</span>
                </label>
                <label className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    checked={formData.consultation?.requirePayment ?? config?.consultation.requirePayment ?? true}
                    onChange={(e) => updateField('consultation', 'requirePayment', e.target.checked)}
                  />
                  <span className="text-sm">需要支付</span>
                </label>
              </div>
            </div>
          </Card>
        </TabsContent>

        {/* 支付设置 */}
        <TabsContent value="payment">
          <Card className="p-6">
            <h2 className="text-lg font-semibold mb-4">支付设置</h2>
            <div className="space-y-4">
              <div className="grid grid-cols-3 gap-4">
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1">
                    最低提现金额（元）
                  </label>
                  <Input
                    type="number"
                    value={formData.payment?.minWithdrawalAmount ?? config?.payment.minWithdrawalAmount ?? 100}
                    onChange={(e: React.ChangeEvent<HTMLInputElement>) => updateField('payment', 'minWithdrawalAmount', Number(e.target.value))}
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1">
                    提现手续费（%）
                  </label>
                  <Input
                    type="number"
                    value={formData.payment?.withdrawalFeeRate ?? config?.payment.withdrawalFeeRate ?? 0}
                    onChange={(e: React.ChangeEvent<HTMLInputElement>) => updateField('payment', 'withdrawalFeeRate', Number(e.target.value))}
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1">
                    提现处理天数
                  </label>
                  <Input
                    type="number"
                    value={formData.payment?.withdrawalProcessingDays ?? config?.payment.withdrawalProcessingDays ?? 3}
                    onChange={(e: React.ChangeEvent<HTMLInputElement>) => updateField('payment', 'withdrawalProcessingDays', Number(e.target.value))}
                  />
                </div>
              </div>
              <div className="space-y-2">
                <label className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    checked={formData.payment?.enableAlipay ?? config?.payment.enableAlipay ?? true}
                    onChange={(e) => updateField('payment', 'enableAlipay', e.target.checked)}
                  />
                  <span className="text-sm">启用支付宝</span>
                </label>
                <label className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    checked={formData.payment?.enableWechatPay ?? config?.payment.enableWechatPay ?? true}
                    onChange={(e) => updateField('payment', 'enableWechatPay', e.target.checked)}
                  />
                  <span className="text-sm">启用微信支付</span>
                </label>
                <label className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    checked={formData.payment?.enableBalance ?? config?.payment.enableBalance ?? true}
                    onChange={(e) => updateField('payment', 'enableBalance', e.target.checked)}
                  />
                  <span className="text-sm">启用余额支付</span>
                </label>
              </div>
            </div>
          </Card>
        </TabsContent>

        {/* 通知设置 */}
        <TabsContent value="notification">
          <Card className="p-6">
            <h2 className="text-lg font-semibold mb-4">通知设置</h2>
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1">
                    发件人邮箱
                  </label>
                  <Input
                    type="email"
                    value={formData.notification?.emailFrom ?? config?.notification.emailFrom ?? ''}
                    onChange={(e: React.ChangeEvent<HTMLInputElement>) => updateField('notification', 'emailFrom', e.target.value)}
                    placeholder="noreply@example.com"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1">
                    短信服务商
                  </label>
                  <Input
                    value={formData.notification?.smsProvider ?? config?.notification.smsProvider ?? ''}
                    onChange={(e: React.ChangeEvent<HTMLInputElement>) => updateField('notification', 'smsProvider', e.target.value)}
                    placeholder="阿里云短信"
                  />
                </div>
              </div>
              <div className="space-y-2">
                <label className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    checked={formData.notification?.enableEmailNotification ?? config?.notification.enableEmailNotification ?? true}
                    onChange={(e) => updateField('notification', 'enableEmailNotification', e.target.checked)}
                  />
                  <span className="text-sm">启用邮件通知</span>
                </label>
                <label className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    checked={formData.notification?.enableSmsNotification ?? config?.notification.enableSmsNotification ?? false}
                    onChange={(e) => updateField('notification', 'enableSmsNotification', e.target.checked)}
                  />
                  <span className="text-sm">启用短信通知</span>
                </label>
                <label className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    checked={formData.notification?.enablePushNotification ?? config?.notification.enablePushNotification ?? true}
                    onChange={(e) => updateField('notification', 'enablePushNotification', e.target.checked)}
                  />
                  <span className="text-sm">启用推送通知</span>
                </label>
              </div>
            </div>
          </Card>
        </TabsContent>

        {/* 安全设置 */}
        <TabsContent value="security">
          <Card className="p-6">
            <h2 className="text-lg font-semibold mb-4">安全设置</h2>
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1">
                    最大登录尝试次数
                  </label>
                  <Input
                    type="number"
                    value={formData.security?.maxLoginAttempts ?? config?.security.maxLoginAttempts ?? 5}
                    onChange={(e: React.ChangeEvent<HTMLInputElement>) => updateField('security', 'maxLoginAttempts', Number(e.target.value))}
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1">
                    锁定时间（分钟）
                  </label>
                  <Input
                    type="number"
                    value={formData.security?.lockoutDuration ?? config?.security.lockoutDuration ?? 30}
                    onChange={(e: React.ChangeEvent<HTMLInputElement>) => updateField('security', 'lockoutDuration', Number(e.target.value))}
                  />
                </div>
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">
                  IP 白名单（每行一个）
                </label>
                <textarea
                  value={(formData.security?.ipWhitelist ?? config?.security.ipWhitelist ?? []).join('\n')}
                  onChange={(e: React.ChangeEvent<HTMLTextAreaElement>) => updateField('security', 'ipWhitelist', e.target.value.split('\n').filter(Boolean))}
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  rows={4}
                  placeholder="192.168.1.1&#10;10.0.0.0/8"
                />
              </div>
              <div className="space-y-2">
                <label className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    checked={formData.security?.enableCaptcha ?? config?.security.enableCaptcha ?? true}
                    onChange={(e) => updateField('security', 'enableCaptcha', e.target.checked)}
                  />
                  <span className="text-sm">启用验证码</span>
                </label>
                <label className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    checked={formData.security?.enableIpWhitelist ?? config?.security.enableIpWhitelist ?? false}
                    onChange={(e) => updateField('security', 'enableIpWhitelist', e.target.checked)}
                  />
                  <span className="text-sm">启用 IP 白名单</span>
                </label>
                <label className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    checked={formData.security?.enableAuditLog ?? config?.security.enableAuditLog ?? true}
                    onChange={(e) => updateField('security', 'enableAuditLog', e.target.checked)}
                  />
                  <span className="text-sm">启用审计日志</span>
                </label>
              </div>
            </div>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
