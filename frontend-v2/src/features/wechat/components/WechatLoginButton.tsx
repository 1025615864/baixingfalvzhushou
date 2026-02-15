/**
 * WechatLoginButton - 微信登录按钮组件
 * 支持公众号和小程序登录方式
 */

import { useState } from 'react';

import { useWechatLogin, useSilentLogin } from '../hooks/useWechat';

interface WechatLoginButtonProps {
  /** 登录类型：official-公众号，mini_program-小程序 */
  loginType: 'official' | 'mini_program';
  /** 按钮尺寸：small-小，medium-中（默认），large-大 */
  size?: 'small' | 'medium' | 'large';
  /** 按钮样式：default-默认（绿色），outline-描边 */
  variant?: 'default' | 'outline';
  /** 登录成功回调 */
  onLoginSuccess?: (sessionToken: string, openid: string) => void;
  /** 登录失败回调 */
  onLoginFailure?: (error: Error) => void;
  /** 自定义按钮文字 */
  children?: string;
  /** 是否显示扫码登录 */
  showQrCode?: boolean;
}

/**
 * 微信图标组件
 */
function WechatIcon(): JSX.Element {
  return (
    <svg className="w-5 h-5" viewBox="0 0 24 24" fill="currentColor">
      <path d="M8.691 2.188C3.891 2.188 0 5.476 0 9.53c0 2.212 1.17 4.203 3.002 5.55a.59.59 0 0 1 .213.665l-.39 1.48c-.019.07-.048.141-.048.213 0 .163.13.295.29.295a.326.326 0 0 0 .167-.054l1.903-1.114a.864.864 0 0 1 .717-.098 10.16 10.16 0 0 0 2.837.403c.276 0 .543-.027.811-.05-.857-2.578.157-4.972 1.932-6.446 1.703-1.415 3.882-1.98 5.853-1.838-.576-3.583-4.196-6.348-8.596-6.348zM5.785 5.991c.642 0 1.162.529 1.162 1.18a1.17 1.17 0 0 1-1.162 1.178A1.17 1.17 0 0 1 4.623 7.17c0-.651.52-1.18 1.162-1.18zm5.813 0c.642 0 1.162.529 1.162 1.18a1.17 1.17 0 0 1-1.162 1.178 1.17 1.17 0 0 1-1.162-1.178c0-.651.52-1.18 1.162-1.18zm5.34 2.867c-1.797-.052-3.746.512-5.28 1.786-1.72 1.428-2.687 3.72-1.78 6.22.942 2.453 3.666 4.229 6.884 4.229.826 0 1.622-.12 2.361-.336a.722.722 0 0 1 .598.082l1.584.926a.272.272 0 0 0 .14.047c.134 0 .24-.111.24-.247 0-.06-.023-.12-.038-.177l-.327-1.233a.582.582 0 0 1-.023-.156.49.49 0 0 1 .201-.398C23.024 18.48 24 16.82 24 14.98c0-3.21-2.931-5.837-6.656-6.088V8.89c-.135-.01-.269-.03-.407-.03zm-2.53 3.274c.535 0 .969.44.969.982a.976.976 0 0 1-.969.983.976.976 0 0 1-.969-.983c0-.542.434-.982.97-.982zm4.844 0c.535 0 .969.44.969.982a.976.976 0 0 1-.969.983.976.976 0 0 1-.969-.983c0-.542.434-.982.969-.982z"/>
    </svg>
  );
}

/**
 * 加载图标组件
 */
function LoaderIcon(): JSX.Element {
  return (
    <svg className="w-4 h-4 animate-spin" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
    </svg>
  );
}

/**
 * 关闭图标组件
 */
function CloseIcon(): JSX.Element {
  return (
    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
    </svg>
  );
}

/**
 * 二维码图标组件
 */
function QrCodeIcon(): JSX.Element {
  return (
    <svg className="w-20 h-20" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 4v1m6 11h2m-6 0h-2v4h2v-4zM6 20h2v-4H6v4zm6-6h2v-4h-2v4zm-6 0h2v-4H6v4zm12-6h2V4h-2v4zM6 10h2V4H6v6zm6-6h2V4h-2v4z" />
    </svg>
  );
}

/**
 * 微信登录按钮组件
 */
export function WechatLoginButton({
  loginType,
  size = 'medium',
  variant = 'default',
  onLoginSuccess,
  onLoginFailure,
  children,
  showQrCode = false,
}: WechatLoginButtonProps): JSX.Element {
  const [isQrCodeModalOpen, setIsQrCodeModalOpen] = useState(false);
  const { login, isLoggingIn } = useWechatLogin();
  const { silentLogin } = useSilentLogin();

  // 按钮尺寸样式
  const sizeClasses = {
    small: 'px-3 py-1.5 text-sm',
    medium: 'px-4 py-2 text-sm',
    large: 'px-6 py-3 text-base',
  };

  // 按钮样式变体
  const variantClasses = {
    default: 'bg-green-600 text-white hover:bg-green-700 border-transparent',
    outline: 'bg-white text-green-600 border-green-600 hover:bg-green-50',
  };

  /**
   * 处理登录
   */
  const handleLogin = (): void => {
    void (async (): Promise<void> => {
    try {
      // 先尝试静默登录
      const silentResult = silentLogin();
      if (silentResult?.success && silentResult.sessionToken) {
        onLoginSuccess?.(silentResult.sessionToken, silentResult.userInfo?.openid || '');
        return;
      }

      if (loginType === 'official' && showQrCode) {
        // 公众号扫码登录
        setIsQrCodeModalOpen(true);
        return;
      }

      // 小程序登录或其他方式
      const mockCode = `mock_code_${Date.now()}`;
      const result = await login({
        code: mockCode,
      });

      if (result.success && result.sessionToken) {
        // 保存会话
        localStorage.setItem('wechat_session_token', result.sessionToken);
        onLoginSuccess?.(result.sessionToken, result.userInfo?.openid || '');
      } else {
        throw new Error(result.errorMessage || '登录失败');
      }
    } catch (error) {
      const err = error instanceof Error ? error : new Error('登录失败');
      onLoginFailure?.(err);
    }
    })();
  };

  /**
   * 处理扫码登录成功
   */
  const handleQrCodeLogin = (): void => {
    void (async (): Promise<void> => {
      // 模拟扫码登录成功
      const mockCode = `mock_qrcode_${Date.now()}`;
      const result = await login({
        code: mockCode,
      });

      if (result.success && result.sessionToken) {
        localStorage.setItem('wechat_session_token', result.sessionToken);
        setIsQrCodeModalOpen(false);
        onLoginSuccess?.(result.sessionToken, result.userInfo?.openid || '');
      } else {
        throw new Error(result.errorMessage || '扫码登录失败');
      }
    })();
  };

  const buttonText = children || (loginType === 'official' ? '微信登录' : '小程序登录');

  return (
    <>
      <button
        onClick={handleLogin}
        disabled={isLoggingIn}
        className={`
          inline-flex items-center justify-center space-x-2 
          rounded-md font-medium transition-colors 
          focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500
          disabled:opacity-50 disabled:cursor-not-allowed
          border
          ${sizeClasses[size]}
          ${variantClasses[variant]}
        `}
      >
        {isLoggingIn ? (
          <>
            <LoaderIcon />
            <span>登录中...</span>
          </>
        ) : (
          <>
            <WechatIcon />
            <span>{buttonText}</span>
          </>
        )}
      </button>

      {/* 二维码登录弹窗 */}
      {isQrCodeModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50">
          <div className="bg-white rounded-lg shadow-xl p-6 max-w-sm w-full mx-4">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-medium text-gray-900">
                微信扫码登录
              </h3>
              <button
                onClick={() => setIsQrCodeModalOpen(false)}
                className="text-gray-400 hover:text-gray-600 transition-colors"
              >
                <CloseIcon />
              </button>
            </div>
            
            <div className="flex flex-col items-center py-6">
              {/* 二维码区域 */}
              <div className="w-48 h-48 bg-gray-100 rounded-lg flex items-center justify-center border-2 border-gray-200">
                <div className="text-center">
                  <div className="text-gray-400 mb-2">
                    <QrCodeIcon />
                  </div>
                  <p className="text-sm text-gray-500">
                    模拟二维码
                  </p>
                </div>
              </div>
              
              <p className="mt-4 text-sm text-gray-600 text-center">
                请使用微信扫一扫登录
              </p>
              
              {/* 模拟扫码成功按钮（仅用于演示） */}
              <button
                onClick={handleQrCodeLogin}
                disabled={isLoggingIn}
                className="mt-6 w-full px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 transition-colors disabled:opacity-50"
              >
                {isLoggingIn ? '登录中...' : '模拟扫码成功'}
              </button>
            </div>
            
            <div className="mt-4 text-xs text-gray-500 text-center">
              刷新二维码 | 使用密码登录
            </div>
          </div>
        </div>
      )}
    </>
  );
}