/**
 * UserSettingsPage - 用户设置页面
 * 
 * 功能：账户设置、隐私设置、通知设置、密码修改
 */

import { useState, useEffect } from 'react';
import {
  Bell,
  Lock,
  Shield,
  Globe,
  Smartphone,
  Mail,
  Moon,
  Sun,
  Monitor,
} from 'lucide-react';

import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/Card';
import { Input } from '@/components/ui/Input';
import { Button } from '@/components/ui/Button';
import { useToast } from '@/components/ui/useToast';

import type { UserSettings as UserSettingsType, UpdateSettingsDTO } from '../types';
import { useUserSettings, useUpdateUserSettings, useChangePassword } from '../hooks/useUserSettings';

/**
 * 通知设置项
 */
function NotificationSettings({
  settings,
  onChange,
}: {
  settings: UserSettingsType;
  onChange: (changes: UpdateSettingsDTO) => void;
}): JSX.Element {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Bell className="w-5 h-5" />
          通知设置
        </CardTitle>
        <CardDescription>管理您希望接收的通知类型</CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* 邮件通知 */}
        <div className="flex items-center justify-between py-3 border-b border-gray-100">
          <div className="flex items-center gap-3">
            <Mail className="w-5 h-5 text-gray-400" />
            <div>
              <p className="font-medium text-gray-900">邮件通知</p>
              <p className="text-sm text-gray-500">接收账户活动、系统通知等邮件</p>
            </div>
          </div>
          <label className="relative inline-flex items-center cursor-pointer">
            <input
              type="checkbox"
              checked={settings.emailNotifications}
              onChange={(e) => { void onChange({ emailNotifications: e.target.checked }); }}
              className="sr-only peer"
            />
            <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
          </label>
        </div>

        {/* 短信通知 */}
        <div className="flex items-center justify-between py-3 border-b border-gray-100">
          <div className="flex items-center gap-3">
            <Smartphone className="w-5 h-5 text-gray-400" />
            <div>
              <p className="font-medium text-gray-900">短信通知</p>
              <p className="text-sm text-gray-500">接收重要账户变动的短信提醒</p>
            </div>
          </div>
          <label className="relative inline-flex items-center cursor-pointer">
            <input
              type="checkbox"
              checked={settings.smsNotifications}
              onChange={(e) => { void onChange({ smsNotifications: e.target.checked }); }}
              className="sr-only peer"
            />
            <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
          </label>
        </div>

        {/* 订阅通讯 */}
        <div className="flex items-center justify-between py-3">
          <div className="flex items-center gap-3">
            <Globe className="w-5 h-5 text-gray-400" />
            <div>
              <p className="font-medium text-gray-900">订阅通讯</p>
              <p className="text-sm text-gray-500">接收产品更新、功能介绍等资讯</p>
            </div>
          </div>
          <label className="relative inline-flex items-center cursor-pointer">
            <input
              type="checkbox"
              checked={settings.newsletter}
              onChange={(e) => { void onChange({ newsletter: e.target.checked }); }}
              className="sr-only peer"
            />
            <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
          </label>
        </div>
      </CardContent>
    </Card>
  );
}

/**
 * 隐私设置项
 */
function PrivacySettings({
  settings,
  onChange,
}: {
  settings: UserSettingsType;
  onChange: (changes: UpdateSettingsDTO) => void;
}): JSX.Element {
  const privacyOptions = [
    { value: 'public' as const, label: '公开', description: '所有人可见您的资料' },
    { value: 'friends' as const, label: '好友可见', description: '仅好友可见您的资料' },
    { value: 'private' as const, label: '私密', description: '仅自己可见' },
  ];

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Shield className="w-5 h-5" />
          隐私设置
        </CardTitle>
        <CardDescription>控制您的个人资料可见范围</CardDescription>
      </CardHeader>
      <CardContent className="space-y-3">
        {privacyOptions.map((option) => (
          <label
            key={option.value}
            className={`flex items-start gap-3 p-4 rounded-xl border-2 cursor-pointer transition-all ${
              settings.privacy === option.value
                ? 'border-blue-500 bg-blue-50'
                : 'border-gray-200 hover:border-gray-300'
            }`}
          >
            <input
              type="radio"
              name="privacy"
              value={option.value}
              checked={settings.privacy === option.value}
              onChange={(e) => { void onChange({ privacy: e.target.value as UserSettingsType['privacy'] }); }}
              className="mt-1 w-4 h-4 text-blue-600"
            />
            <div className="flex-1">
              <p className="font-medium text-gray-900">{option.label}</p>
              <p className="text-sm text-gray-500 mt-1">{option.description}</p>
            </div>
          </label>
        ))}
      </CardContent>
    </Card>
  );
}

/**
 * 外观设置项
 */
function AppearanceSettings({
  settings,
  onChange,
}: {
  settings: UserSettingsType;
  onChange: (changes: UpdateSettingsDTO) => void;
}): JSX.Element {
  const themeOptions = [
    { value: 'light' as const, label: '浅色', icon: Sun },
    { value: 'dark' as const, label: '深色', icon: Moon },
    { value: 'auto' as const, label: '自动', icon: Monitor },
  ];

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          外观设置
        </CardTitle>
        <CardDescription>选择您的界面主题</CardDescription>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-3 gap-3">
          {themeOptions.map((option) => {
            const Icon = option.icon;
            return (
              <label
                key={option.value}
                className={`flex flex-col items-center gap-2 p-4 rounded-xl border-2 cursor-pointer transition-all ${
                  settings.theme === option.value
                    ? 'border-blue-500 bg-blue-50'
                    : 'border-gray-200 hover:border-gray-300'
                }`}
              >
                <input
                  type="radio"
                  name="theme"
                  value={option.value}
                  checked={settings.theme === option.value}
                  onChange={(e) => { void onChange({ theme: e.target.value as UserSettingsType['theme'] }); }}
                  className="sr-only"
                />
                <Icon className={`w-6 h-6 ${settings.theme === option.value ? 'text-blue-600' : 'text-gray-400'}`} />
                <span className={`text-sm font-medium ${settings.theme === option.value ? 'text-blue-600' : 'text-gray-600'}`}>
                  {option.label}
                </span>
              </label>
            );
          })}
        </div>
      </CardContent>
    </Card>
  );
}

/**
 * 密码修改表单
 */
function ChangePasswordForm(): JSX.Element {
  const toast = useToast();
  const changePassword = useChangePassword();

  const [formData, setFormData] = useState({
    currentPassword: '',
    newPassword: '',
    confirmPassword: '',
  });
  const [errors, setErrors] = useState<Record<string, string>>({});

  const validate = (): boolean => {
    const newErrors: Record<string, string> = {};

    if (!formData.currentPassword) {
      newErrors.currentPassword = '请输入当前密码';
    }

    if (!formData.newPassword) {
      newErrors.newPassword = '请输入新密码';
    } else if (formData.newPassword.length < 8) {
      newErrors.newPassword = '密码长度至少 8 位';
    }

    if (formData.newPassword !== formData.confirmPassword) {
      newErrors.confirmPassword = '两次输入的密码不一致';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent): Promise<void> => {
    e.preventDefault();

    if (!validate()) return;

    try {
      await changePassword.mutateAsync({
        currentPassword: formData.currentPassword,
        newPassword: formData.newPassword,
      });
      toast.success('密码修改成功');
      setFormData({ currentPassword: '', newPassword: '', confirmPassword: '' });
    } catch (err) {
      toast.error(err instanceof Error ? err.message : '密码修改失败');
    }
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Lock className="w-5 h-5" />
          修改密码
        </CardTitle>
        <CardDescription>定期修改密码可以提高账户安全性</CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={(e) => void handleSubmit(e)} className="space-y-4">
          <Input
            label="当前密码"
            type="password"
            value={formData.currentPassword}
            onChange={(e) => setFormData({ ...formData, currentPassword: e.target.value })}
            error={errors.currentPassword}
            placeholder="请输入当前密码"
          />
          <Input
            label="新密码"
            type="password"
            value={formData.newPassword}
            onChange={(e) => setFormData({ ...formData, newPassword: e.target.value })}
            error={errors.newPassword}
            placeholder="请输入新密码（至少 8 位）"
          />
          <Input
            label="确认新密码"
            type="password"
            value={formData.confirmPassword}
            onChange={(e) => setFormData({ ...formData, confirmPassword: e.target.value })}
            error={errors.confirmPassword}
            placeholder="请再次输入新密码"
          />
          <div className="flex justify-end pt-2">
            <Button
              type="submit"
              variant="primary"
              isLoading={changePassword.isPending}
              disabled={changePassword.isPending}
            >
              {changePassword.isPending ? '修改中...' : '修改密码'}
            </Button>
          </div>
        </form>
      </CardContent>
    </Card>
  );
}

/**
 * 用户设置页面
 */
export function UserSettingsPage(): JSX.Element {
  const toast = useToast();
  const { data: settings, isLoading, error } = useUserSettings();
  const updateSettings = useUpdateUserSettings();

  const [localSettings, setLocalSettings] = useState<UserSettingsType>({
    emailNotifications: true,
    smsNotifications: false,
    newsletter: false,
    language: 'zh-CN',
    theme: 'light',
    privacy: 'public',
  });

  // 同步远程数据
  useEffect(() => {
    if (settings) {
      setLocalSettings(settings);
    }
  }, [settings]);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="text-center">
          <div className="w-12 h-12 border-4 border-blue-500 border-t-transparent rounded-full animate-spin mx-auto mb-4" />
          <p className="text-gray-500">加载中...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <Card className="max-w-md">
          <CardContent className="pt-6">
            <div className="text-center">
              <p className="text-red-500 mb-4">加载设置失败</p>
              <Button variant="primary" onClick={() => window.location.reload()}>
                重新加载
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  const handleSettingsChange = (changes: UpdateSettingsDTO): void => {
    // 先更新本地状态
    setLocalSettings((prev) => ({ ...prev, ...changes }));

    // 异步保存设置
    void (async () => {
      try {
        await updateSettings.mutateAsync(changes);
        toast.success('设置已保存');
      } catch (err) {
        toast.error(err instanceof Error ? err.message : '保存失败');
        // 恢复原设置
        if (settings) {
          setLocalSettings(settings);
        }
      }
    })();
  };

  return (
    <div className="max-w-4xl mx-auto">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-gray-900">账户设置</h1>
        <p className="text-gray-500 mt-1">管理您的通知、隐私和安全设置</p>
      </div>

      <div className="grid gap-6">
        {/* 通知设置 */}
        <NotificationSettings
          settings={localSettings}
          onChange={handleSettingsChange}
        />

        {/* 隐私设置 */}
        <PrivacySettings
          settings={localSettings}
          onChange={handleSettingsChange}
        />

        {/* 外观设置 */}
        <AppearanceSettings
          settings={localSettings}
          onChange={handleSettingsChange}
        />

        {/* 密码修改 */}
        <ChangePasswordForm />
      </div>
    </div>
  );
}

export default UserSettingsPage;
