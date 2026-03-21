/**
 * WechatCallbackPage - 微信登录回调页面
 * 处理微信登录后的回调逻辑，对接后端真实API
 */
import { useEffect, useState, useCallback } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';

import { Loading } from '@/shared/components/Loading';
import { setRefreshToken, setToken } from '@/shared/lib/security/tokenStorage';

import { apiHandleWechatCallback } from '../api';

/**
 * 微信回调响应类型
 */
interface WechatCallbackResult {
  success: boolean;
  openid?: string;
  accessToken?: string;
  refreshToken?: string;
  errorMessage?: string;
}

/**
 * 微信登录回调页面
 */
export function WechatCallbackPage(): JSX.Element {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const [error, setError] = useState<string | null>(null);
  const [isProcessing, setIsProcessing] = useState(true);

  /**
   * 处理登录成功后的跳转
   */
  const handleRedirect = useCallback((redirectUrl: string): void => {
    // 保存登录成功标记，用于显示欢迎消息
    sessionStorage.setItem('wechat_login_success', 'true');
    navigate(redirectUrl, { replace: true });
  }, [navigate]);

  useEffect(() => {
    const handleCallback = async (): Promise<void> => {
      const code = searchParams.get('code');
      const state = searchParams.get('state');
      const errorCode = searchParams.get('error');
      const errorMsg = searchParams.get('error_description');

      // 用户取消授权
      if (errorCode || errorMsg) {
        setError(errorMsg || '授权被取消');
        setIsProcessing(false);
        setTimeout(() => {
          navigate('/login', { replace: true });
        }, 3000);
        return;
      }

      // 缺少必要参数
      if (!code) {
        setError('授权失败：缺少必要参数');
        setIsProcessing(false);
        setTimeout(() => {
          navigate('/login', { replace: true });
        }, 3000);
        return;
      }

      try {
        setIsProcessing(true);
        
        // 调用后端API处理微信登录回调
        const result = await apiHandleWechatCallback(code, state || '') as WechatCallbackResult;

        if (result.success) {
          // 保存登录凭证
          if (result.accessToken) {
            setToken(result.accessToken);
          }
          if (result.refreshToken) {
            setRefreshToken(result.refreshToken);
          }
          if (result.openid) {
            localStorage.setItem('wechat_openid', result.openid);
          }

          // 登录成功，跳转到首页或之前保存的页面
          const redirectUrl = sessionStorage.getItem('wechat_redirect') || '/';
          sessionStorage.removeItem('wechat_redirect');
          
          handleRedirect(redirectUrl);
        } else {
          throw new Error(result.errorMessage ?? '登录失败');
        }
      } catch (err) {
        const errorMessage = err instanceof Error ? err.message : '登录失败，请重试';
        setError(errorMessage);
        setIsProcessing(false);
        setTimeout(() => {
          navigate('/login', { replace: true });
        }, 3000);
      }
    };

    void handleCallback();
  }, [navigate, searchParams, handleRedirect]);

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center px-4">
        <div className="max-w-md w-full bg-white rounded-lg shadow-sm p-8 text-center">
          <div className="mx-auto w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mb-4">
            <svg className="w-8 h-8 text-red-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </div>
          <h2 className="text-xl font-semibold text-gray-900 mb-2">登录失败</h2>
          <p className="text-gray-600 mb-6">{error}</p>
          <p className="text-sm text-gray-500">即将跳转到登录页面...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center px-4">
      <div className="text-center">
        <Loading size="lg" text={isProcessing ? '正在处理登录...' : '即将完成...'} />
        <p className="mt-4 text-gray-600">请稍候，正在完成微信登录...</p>
        
        {/* 添加手动跳转链接，以防自动跳转失败 */}
        <button
          onClick={() => navigate('/')}
          className="mt-6 text-sm text-green-600 hover:text-green-700 underline"
        >
          如果长时间未跳转，点击这里返回首页
        </button>
      </div>
    </div>
  );
}