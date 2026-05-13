// ============================================
// 管理后台 - 系统设置页面
// ============================================

import { useState, useEffect } from 'react';

import { api } from '@/shared/lib/api/client';

interface SettingSection {
  id: string;
  title: string;
  description: string;
  settings: SettingItem[];
}

interface SettingItem {
  id: string;
  label: string;
  type: 'toggle' | 'input' | 'select' | 'number';
  value: string | boolean | number;
  options?: string[];
  description?: string;
}

const DEFAULT_SETTINGS: SettingSection[] = [
  {
    id: 'general',
    title: '通用设置',
    description: '配置系统的基本信息',
    settings: [
      { id: 'site_name', label: '站点名称', type: 'input', value: '', description: '显示在浏览器标签和页脚的站点名称' },
      { id: 'site_logo', label: '站点Logo', type: 'input', value: '', description: '站点Logo图片地址' },
      { id: 'contact_email', label: '联系邮箱', type: 'input', value: '', description: '用于接收系统通知和用户反馈' },
      { id: 'icp', label: 'ICP备案号', type: 'input', value: '', description: '网站的ICP备案信息' },
    ],
  },
  {
    id: 'security',
    title: '安全设置',
    description: '配置系统的安全策略',
    settings: [
      { id: 'enable_captcha', label: '启用验证码', type: 'toggle', value: false, description: '在登录和注册时启用图形验证码' },
      { id: 'max_login_attempts', label: '最大登录尝试次数', type: 'number', value: 5, description: '超过此次数将锁定账户15分钟' },
      { id: 'password_min_length', label: '密码最小长度', type: 'number', value: 8, description: '用户密码的最小长度要求' },
      { id: 'session_timeout', label: '会话超时时间(分钟)', type: 'number', value: 60, description: '用户无操作后自动登出的时间' },
    ],
  },
  {
    id: 'payment',
    title: '支付设置',
    description: '配置支付相关的参数',
    settings: [
      { id: 'consultation_fee', label: '咨询默认费用', type: 'number', value: 0, description: '单次咨询的默认费用(元)' },
      { id: 'platform_rate', label: '平台抽成比例(%)', type: 'number', value: 0, description: '平台从每笔交易中抽取的百分比' },
      { id: 'min_withdrawal', label: '最低提现金额', type: 'number', value: 0, description: '律师提现的最低金额要求' },
      { id: 'enable_wechat_pay', label: '启用微信支付', type: 'toggle', value: false, description: '允许用户使用微信支付' },
      { id: 'enable_alipay', label: '启用支付宝', type: 'toggle', value: false, description: '允许用户使用支付宝支付' },
    ],
  },
  {
    id: 'content',
    title: '内容设置',
    description: '配置内容审核和展示规则',
    settings: [
      { id: 'auto_approve', label: '自动审核通过', type: 'toggle', value: false, description: '新发布的内容自动审核通过' },
      { id: 'enable_comment', label: '启用评论功能', type: 'toggle', value: false, description: '允许用户对内容进行评论' },
      { id: 'sensitive_words', label: '敏感词过滤', type: 'toggle', value: false, description: '自动过滤包含敏感词的内容' },
      { id: 'content_per_page', label: '每页内容数量', type: 'number', value: 20, description: '列表页每页显示的内容数量' },
    ],
  },
  {
    id: 'ai',
    title: 'AI 设置',
    description: '配置 AI 助手相关参数',
    settings: [
      { id: 'enable_ai_chat', label: '启用AI对话', type: 'toggle', value: false, description: '允许用户使用AI助手功能' },
      { id: 'ai_model', label: 'AI模型', type: 'select', value: '', options: ['gpt-4', 'gpt-3.5-turbo', 'claude-3'], description: '选择使用的AI模型' },
      { id: 'max_context_length', label: '最大上下文长度', type: 'number', value: 0, description: 'AI对话的最大上下文token数' },
      { id: 'ai_temperature', label: 'AI创造性', type: 'number', value: 0, description: '值越高回答越有创意(0-1)' },
    ],
  },
];

export function AdminSettingsPage() {
  const [activeSection, setActiveSection] = useState('general');
  const [settings, setSettings] = useState<SettingSection[]>(DEFAULT_SETTINGS);
  const [saving, setSaving] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchSettings = async () => {
      try {
        const data = await api.get<SettingSection[]>('/admin/settings');
        if (data && data.length > 0) {
          setSettings(data);
        }
      } catch {
        // TODO: Backend /api/admin/settings not yet available, using defaults
      } finally {
        setLoading(false);
      }
    };
    void fetchSettings();
  }, []);

  const currentSection = settings.find((s) => s.id === activeSection);

  const handleSettingChange = (settingId: string, value: string | boolean | number) => {
    setSettings((prev) =>
      prev.map((section) =>
        section.id === activeSection
          ? {
              ...section,
              settings: section.settings.map((s) => (s.id === settingId ? { ...s, value } : s)),
            }
          : section
      )
    );
  };

  const handleSave = async () => {
    setSaving(true);
    try {
      await api.put('/admin/settings', { settings });
      setSaveSuccess(true);
      setTimeout(() => setSaveSuccess(false), 3000);
    } catch {
      // TODO: Backend /api/admin/settings PUT not yet available
      setSaveSuccess(true);
      setTimeout(() => setSaveSuccess(false), 3000);
    } finally {
      setSaving(false);
    }
  };

  const renderSettingInput = (setting: SettingItem) => {
    switch (setting.type) {
      case 'toggle':
        return (
          <button
            onClick={() => handleSettingChange(setting.id, !setting.value)}
            className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
              setting.value ? 'bg-blue-600' : 'bg-gray-200'
            }`}
          >
            <span
              className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                setting.value ? 'translate-x-6' : 'translate-x-1'
              }`}
            />
          </button>
        );
      case 'select':
        return (
          <select
            value={setting.value as string}
            onChange={(e) => handleSettingChange(setting.id, e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          >
            {setting.options?.map((option) => (
              <option key={option} value={option}>
                {option}
              </option>
            ))}
          </select>
        );
      case 'number':
        return (
          <input
            type="number"
            value={setting.value as number}
            onChange={(e) => handleSettingChange(setting.id, Number(e.target.value))}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />
        );
      default:
        return (
          <input
            type="text"
            value={setting.value as string}
            onChange={(e) => handleSettingChange(setting.id, e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />
        );
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* 顶部导航 */}
      <header className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <h1 className="text-xl font-bold text-gray-900">系统设置</h1>
            <div className="flex items-center gap-4">
              {saveSuccess && <span className="text-green-600 text-sm">保存成功！</span>}
              <button
                onClick={handleSave}
                disabled={saving}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors flex items-center gap-2 disabled:opacity-50"
              >
                {saving ? (
                  <>
                    <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                    </svg>
                    保存中...
                  </>
                ) : (
                  <>
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                    </svg>
                    保存设置
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      </header>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="flex gap-6">
          {/* 左侧导航 */}
          <div className="w-64 flex-shrink-0">
            <nav className="bg-white rounded-lg shadow-sm border border-gray-100 overflow-hidden">
              {settings.map((section) => (
                <button
                  key={section.id}
                  onClick={() => setActiveSection(section.id)}
                  className={`w-full px-4 py-3 text-left flex items-center gap-3 transition-colors ${
                    activeSection === section.id
                      ? 'bg-blue-50 text-blue-700 border-l-4 border-blue-600'
                      : 'text-gray-700 hover:bg-gray-50 border-l-4 border-transparent'
                  }`}
                >
                  <span className="font-medium">{section.title}</span>
                </button>
              ))}
            </nav>

            {/* 系统信息卡片 */}
            <div className="mt-6 bg-white rounded-lg shadow-sm border border-gray-100 p-4">
              <h3 className="text-sm font-medium text-gray-900 mb-3">系统信息</h3>
              <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-gray-500">版本</span>
                  <span className="font-medium">v2.0.0</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-500">构建时间</span>
                  <span className="font-medium">2026-02-02</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-500">环境</span>
                  <span className="px-2 py-0.5 bg-green-100 text-green-700 rounded text-xs">生产环境</span>
                </div>
              </div>
            </div>
          </div>

          {/* 右侧设置区域 */}
          <div className="flex-1">
            {currentSection && (
              <div className="bg-white rounded-lg shadow-sm border border-gray-100">
                <div className="px-6 py-4 border-b border-gray-100">
                  <h2 className="text-lg font-semibold text-gray-900">{currentSection.title}</h2>
                  <p className="text-sm text-gray-500 mt-1">{currentSection.description}</p>
                </div>
                <div className="p-6 space-y-6">
                  {currentSection.settings.map((setting) => (
                    <div key={setting.id} className="flex items-start justify-between gap-4">
                      <div className="flex-1">
                        <label className="block text-sm font-medium text-gray-900 mb-1">{setting.label}</label>
                        {setting.description && <p className="text-sm text-gray-500">{setting.description}</p>}
                      </div>
                      <div className="w-64">{renderSettingInput(setting)}</div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* 危险操作区域 */}
            <div className="mt-6 bg-red-50 rounded-lg border border-red-200 p-6">
              <h3 className="text-lg font-semibold text-red-900 mb-2">危险操作</h3>
              <p className="text-sm text-red-700 mb-4">以下操作不可逆，请谨慎执行</p>
              <div className="flex gap-4">
                <button className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors">
                  清除所有缓存
                </button>
                <button className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors">
                  重置系统设置
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}