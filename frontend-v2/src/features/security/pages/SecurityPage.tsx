/**
 * SecurityPage - 安全中心主页面
 */

import { useState } from 'react';
import {
  SafetyCertificateOutlined,
  QrcodeOutlined,
  AuditOutlined,
  DesktopOutlined,
  LockOutlined,
  SettingOutlined,
} from '@ant-design/icons';

import { TwoFactorSetup } from '../components/TwoFactorSetup';
import { LoginAuditTable } from '../components/LoginAuditTable';
import { DeviceList } from '../components/DeviceList';
import { SecurityLevel } from '../components/SecurityLevel';
import { PasswordChange } from '../components/PasswordChange';
import type { SecurityCheckItem } from '../types';

type TabId = 'overview' | '2fa' | 'audit' | 'devices' | 'password';

interface Tab {
  id: TabId;
  label: string;
  icon: React.ReactNode;
}

const tabs: Tab[] = [
  { id: 'overview', label: '安全概览', icon: <SafetyCertificateOutlined /> },
  { id: '2fa', label: '双重验证', icon: <QrcodeOutlined /> },
  { id: 'audit', label: '登录审计', icon: <AuditOutlined /> },
  { id: 'devices', label: '设备管理', icon: <DesktopOutlined /> },
  { id: 'password', label: '密码修改', icon: <LockOutlined /> },
];

/**
 * 安全中心主页面
 */
export function SecurityPage(): JSX.Element {
  const [activeTab, setActiveTab] = useState<TabId>('overview');

  const handleCheckItemClick = (item: SecurityCheckItem): void => {
    // 根据检查项跳转到对应的标签页
    if (item.id.includes('2fa') || item.id.includes('mfa')) {
      setActiveTab('2fa');
    } else if (item.id.includes('password')) {
      setActiveTab('password');
    } else if (item.id.includes('device')) {
      setActiveTab('devices');
    }
  };

  const handleTwoFASetupComplete = (): void => {
    setActiveTab('overview');
  };

  const renderContent = (): React.ReactNode => {
    switch (activeTab) {
      case 'overview':
        return (
          <div className="space-y-6">
            <SecurityLevel onCheckItemClick={handleCheckItemClick} />
            
            {/* 快捷操作 */}
            <div className="bg-white rounded-lg shadow-sm p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">快捷操作</h3>
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
                <button
                  onClick={() => setActiveTab('2fa')}
                  className="p-4 border border-gray-200 rounded-lg hover:border-blue-500 hover:bg-blue-50 transition-colors text-left"
                >
                  <QrcodeOutlined className="text-2xl text-blue-600 mb-2" />
                  <div className="text-sm font-medium text-gray-900">设置双重验证</div>
                  <div className="text-xs text-gray-500 mt-1">增强账号安全性</div>
                </button>
                <button
                  onClick={() => setActiveTab('password')}
                  className="p-4 border border-gray-200 rounded-lg hover:border-blue-500 hover:bg-blue-50 transition-colors text-left"
                >
                  <LockOutlined className="text-2xl text-blue-600 mb-2" />
                  <div className="text-sm font-medium text-gray-900">修改密码</div>
                  <div className="text-xs text-gray-500 mt-1">定期更换更安全</div>
                </button>
                <button
                  onClick={() => setActiveTab('devices')}
                  className="p-4 border border-gray-200 rounded-lg hover:border-blue-500 hover:bg-blue-50 transition-colors text-left"
                >
                  <DesktopOutlined className="text-2xl text-blue-600 mb-2" />
                  <div className="text-sm font-medium text-gray-900">管理设备</div>
                  <div className="text-xs text-gray-500 mt-1">查看登录设备</div>
                </button>
                <button
                  onClick={() => setActiveTab('audit')}
                  className="p-4 border border-gray-200 rounded-lg hover:border-blue-500 hover:bg-blue-50 transition-colors text-left"
                >
                  <AuditOutlined className="text-2xl text-blue-600 mb-2" />
                  <div className="text-sm font-medium text-gray-900">登录记录</div>
                  <div className="text-xs text-gray-500 mt-1">查看登录历史</div>
                </button>
              </div>
            </div>
          </div>
        );

      case '2fa':
        return (
          <div className="space-y-6">
            <div className="bg-white rounded-lg shadow-sm p-6">
              <div className="flex items-center mb-6">
                <div className="p-3 bg-blue-100 rounded-full mr-4">
                  <QrcodeOutlined className="text-2xl text-blue-600" />
                </div>
                <div>
                  <h3 className="text-lg font-semibold text-gray-900">双重验证 (2FA)</h3>
                  <p className="text-sm text-gray-500">
                    启用双重验证后，登录时需要额外输入验证码，大幅提升账号安全性
                  </p>
                </div>
              </div>
              
              <TwoFactorSetup 
                onComplete={handleTwoFASetupComplete}
                onCancel={() => setActiveTab('overview')}
              />
            </div>

            {/* 2FA说明 */}
            <div className="bg-blue-50 rounded-lg p-6">
              <h4 className="text-sm font-semibold text-blue-900 mb-2">什么是双重验证？</h4>
              <p className="text-sm text-blue-700 mb-4">
                双重验证是一种安全机制，在输入密码之外，还需要输入动态验证码才能登录。
                即使密码泄露，攻击者也无法登录您的账号。
              </p>
              <h4 className="text-sm font-semibold text-blue-900 mb-2">支持的方式</h4>
              <ul className="text-sm text-blue-700 space-y-1">
                <li>• 身份验证器应用（推荐）：使用 Google Authenticator、Authy 等应用</li>
                <li>• 短信验证：通过短信接收验证码</li>
                <li>• 邮箱验证：通过邮件接收验证码</li>
              </ul>
            </div>
          </div>
        );

      case 'audit':
        return (
          <div className="space-y-6">
            <div className="bg-white rounded-lg shadow-sm p-6">
              <div className="flex items-center mb-6">
                <div className="p-3 bg-blue-100 rounded-full mr-4">
                  <AuditOutlined className="text-2xl text-blue-600" />
                </div>
                <div>
                  <h3 className="text-lg font-semibold text-gray-900">登录审计日志</h3>
                  <p className="text-sm text-gray-500">
                    查看账号的登录历史记录，发现异常登录行为
                  </p>
                </div>
              </div>
            </div>
            <LoginAuditTable pageSize={10} />
          </div>
        );

      case 'devices':
        return (
          <div className="space-y-6">
            <div className="bg-white rounded-lg shadow-sm p-6">
              <div className="flex items-center mb-6">
                <div className="p-3 bg-blue-100 rounded-full mr-4">
                  <DesktopOutlined className="text-2xl text-blue-600" />
                </div>
                <div>
                  <h3 className="text-lg font-semibold text-gray-900">设备管理</h3>
                  <p className="text-sm text-gray-500">
                    管理已登录的设备，随时退出可疑设备
                  </p>
                </div>
              </div>
            </div>
            <DeviceList />
          </div>
        );

      case 'password':
        return (
          <div className="space-y-6">
            <PasswordChange 
              onSuccess={() => setActiveTab('overview')}
              onCancel={() => setActiveTab('overview')}
            />
            
            {/* 密码安全提示 */}
            <div className="bg-amber-50 rounded-lg p-6">
              <h4 className="text-sm font-semibold text-amber-900 mb-2">密码安全建议</h4>
              <ul className="text-sm text-amber-700 space-y-2">
                <li className="flex items-start">
                  <SettingOutlined className="mr-2 mt-0.5" />
                  使用至少8个字符的密码，包含大小写字母、数字和特殊字符
                </li>
                <li className="flex items-start">
                  <SettingOutlined className="mr-2 mt-0.5" />
                  不要使用与其他网站相同的密码
                </li>
                <li className="flex items-start">
                  <SettingOutlined className="mr-2 mt-0.5" />
                  定期更换密码（建议每3个月）
                </li>
                <li className="flex items-start">
                  <SettingOutlined className="mr-2 mt-0.5" />
                  启用双重验证，即使密码泄露也能保护账号安全
                </li>
              </ul>
            </div>
          </div>
        );

      default:
        return null;
    }
  };

  return (
    <div className="min-h-screen bg-gray-100">
      {/* 页面头部 */}
      <div className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex items-center">
            <SafetyCertificateOutlined className="text-3xl text-blue-600 mr-4" />
            <div>
              <h1 className="text-2xl font-bold text-gray-900">安全中心</h1>
              <p className="text-sm text-gray-500 mt-1">
                管理您的账号安全设置，保护个人信息
              </p>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="flex flex-col lg:flex-row gap-8">
          {/* 侧边导航 */}
          <div className="lg:w-64 flex-shrink-0">
            <nav className="bg-white rounded-lg shadow-sm overflow-hidden">
              {tabs.map((tab) => (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`
                    w-full flex items-center px-4 py-3 text-sm font-medium transition-colors
                    ${activeTab === tab.id 
                      ? 'bg-blue-50 text-blue-700 border-r-2 border-blue-600' 
                      : 'text-gray-700 hover:bg-gray-50'}
                  `}
                >
                  <span className={`mr-3 ${activeTab === tab.id ? 'text-blue-600' : 'text-gray-400'}`}>
                    {tab.icon}
                  </span>
                  {tab.label}
                </button>
              ))}
            </nav>

            {/* 安全提示 */}
            <div className="mt-6 bg-blue-50 rounded-lg p-4">
              <h4 className="text-sm font-semibold text-blue-900 mb-2">安全提示</h4>
              <p className="text-xs text-blue-700">
                建议您启用双重验证并定期更换密码，以保护账号安全。
              </p>
            </div>
          </div>

          {/* 主内容区 */}
          <div className="flex-1">
            {renderContent()}
          </div>
        </div>
      </div>
    </div>
  );
}