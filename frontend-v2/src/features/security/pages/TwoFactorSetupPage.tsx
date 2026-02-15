/**
 * TwoFactorSetupPage - 双重验证设置页面
 */

import { useNavigate } from 'react-router-dom';
import { QrcodeOutlined, ArrowLeftOutlined } from '@ant-design/icons';

import { TwoFactorSetup } from '../components/TwoFactorSetup';

/**
 * 双重验证设置页面
 */
export function TwoFactorSetupPage(): JSX.Element {
  const navigate = useNavigate();

  const handleComplete = (): void => {
    navigate('/security');
  };

  const handleCancel = (): void => {
    navigate('/security');
  };

  return (
    <div className="min-h-screen bg-gray-100">
      {/* 页面头部 */}
      <div className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex items-center">
            <button
              onClick={() => navigate('/security')}
              className="mr-4 p-2 text-gray-500 hover:text-gray-700 transition-colors"
              aria-label="返回安全中心"
            >
              <ArrowLeftOutlined className="text-xl" />
            </button>
            <div className="p-3 bg-blue-100 rounded-full mr-4">
              <QrcodeOutlined className="text-2xl text-blue-600" />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-gray-900">设置双重验证</h1>
              <p className="text-sm text-gray-500 mt-1">
                启用双重验证，增强账号安全性
              </p>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="space-y-6">
          <div className="bg-white rounded-lg shadow-sm p-6">
            <TwoFactorSetup
              onComplete={handleComplete}
              onCancel={handleCancel}
            />
          </div>

          {/* 安全提示 */}
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
      </div>
    </div>
  );
}