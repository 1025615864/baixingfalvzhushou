/**
 * WechatLoginButton - 微信扫码登录按钮组件
 * 真实二维码生成 + 状态轮询 + 自动登录
 */
import { useState, useRef, useCallback } from 'react';

import { useAuthStore } from '@/features/auth/store/authStore';
import { authKeys } from '@/features/auth/hooks/useAuth';
import { setToken } from '@/shared/lib/security/tokenStorage';
import { api } from '@/shared/lib/api/client';
import { useQueryClient } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import type { LoginResponse } from '@/features/auth/types';

type QrCodeStatus = 'loading' | 'pending' | 'scanned' | 'confirmed' | 'expired' | 'error';

interface WechatLoginButtonProps {
  loginType: 'official' | 'mini_program';
  size?: 'small' | 'medium' | 'large';
  variant?: 'default' | 'outline';
  onLoginSuccess?: (token: string, username: string) => void;
  onLoginFailure?: (error: Error) => void;
  children?: string;
  showQrCode?: boolean;
}

function WechatIcon(): JSX.Element {
  return (
    <svg className="w-5 h-5" viewBox="0 0 24 24" fill="currentColor">
      <path d="M8.691 2.188C3.891 2.188 0 5.476 0 9.53c0 2.212 1.17 4.203 3.002 5.55a.59.59 0 0 1 .213.665l-.39 1.48c-.019.07-.048.141-.048.213 0 .163.13.295.29.295a.326.326 0 0 0 .167-.054l1.903-1.114a.864.864 0 0 1 .717-.098 10.16 10.16 0 0 0 2.837.403c.276 0 .543-.027.811-.05-.857-2.578.157-4.972 1.932-6.446 1.703-1.415 3.882-1.98 5.853-1.838-.576-3.583-4.196-6.348-8.596-6.348zM5.785 5.991c.642 0 1.162.529 1.162 1.18a1.17 1.17 0 0 1-1.162 1.178A1.17 1.17 0 0 1 4.623 7.17c0-.651.52-1.18 1.162-1.18zm5.813 0c.642 0 1.162.529 1.162 1.18a1.17 1.17 0 0 1-1.162 1.178 1.17 1.17 0 0 1-1.162-1.178c0-.651.52-1.18 1.162-1.18zm5.34 2.867c-1.797-.052-3.746.512-5.28 1.786-1.72 1.428-2.687 3.72-1.78 6.22.942 2.453 3.666 4.229 6.884 4.229.826 0 1.622-.12 2.361-.336a.722.722 0 0 1 .598.082l1.584.926a.272.272 0 0 0 .14.047c.134 0 .24-.111.24-.247 0-.06-.023-.12-.038-.177l-.327-1.233a.582.582 0 0 1-.023-.156.49.49 0 0 1 .201-.398C23.024 18.48 24 16.82 24 14.98c0-3.21-2.931-5.837-6.656-6.088V8.89c-.135-.01-.269-.03-.407-.03zm-2.53 3.274c.535 0 .969.44.969.982a.976.976 0 0 1-.969.983.976.976 0 0 1-.969-.983c0-.542.434-.982.97-.982zm4.844 0c.535 0 .969.44.969.982a.976.976 0 0 1-.969.983.976.976 0 0 1-.969-.983c0-.542.434-.982.969-.982z"/>
    </svg>
  );
}

function LoaderIcon(): JSX.Element {
  return (
    <svg className="w-4 h-4 animate-spin" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
    </svg>
  );
}

function CloseIcon(): JSX.Element {
  return (
    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
    </svg>
  );
}

export function WechatLoginButton({
  loginType: _loginType,
  size = 'medium',
  variant = 'default',
  onLoginSuccess,
  onLoginFailure,
  children,
  showQrCode: _showQrCode = false,
}: WechatLoginButtonProps): JSX.Element {
  const [isQrCodeModalOpen, setIsQrCodeModalOpen] = useState(false);
  const [qrCodeImage, setQrCodeImage] = useState<string | null>(null);
  const [qrcodeId, setQrcodeId] = useState<string | null>(null);
  const [qrStatus, setQrStatus] = useState<QrCodeStatus>('loading');
  const [expireSeconds, setExpireSeconds] = useState(300);
  const [isLoggingIn, setIsLoggingIn] = useState(false);

  const setAuth = useAuthStore((state) => state.setAuth);
  const queryClient = useQueryClient();
  const navigate = useNavigate();

  const pollTimerRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const countdownRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const sizeClasses = {
    small: 'px-3 py-1.5 text-sm',
    medium: 'px-4 py-2 text-sm',
    large: 'px-6 py-3 text-base',
  };

  const variantClasses = {
    default: 'bg-green-600 text-white hover:bg-green-700 border-transparent',
    outline: 'bg-white text-green-600 border-green-600 hover:bg-green-50',
  };

  const clearTimers = useCallback(() => {
    if (pollTimerRef.current) { clearInterval(pollTimerRef.current); pollTimerRef.current = null; }
    if (countdownRef.current) { clearInterval(countdownRef.current); countdownRef.current = null; }
  }, []);

  const fetchQrCode = useCallback(async () => {
    setQrStatus('loading');
    clearTimers();
    try {
      const response = await fetch('/api/wechat/qrcode', { credentials: 'include' });
      if (!response.ok) throw new Error('获取二维码失败');

      const data = await response.json();
      setQrcodeId(data.qrcode_id);
      setQrCodeImage(`data:image/png;base64,${data.qrcode_base64}`);
      setExpireSeconds(data.expire_seconds);
      setQrStatus('pending');

      let remaining = data.expire_seconds;
      countdownRef.current = setInterval(() => {
        remaining -= 1;
        if (remaining <= 0) {
          setQrStatus('expired');
          clearTimers();
        }
        setExpireSeconds(Math.max(0, remaining));
      }, 1000);

      pollTimerRef.current = setInterval(async () => {
        try {
          const statusResp = await fetch(`/api/wechat/qrcode/status/${data.qrcode_id}`, {
            credentials: 'include',
          });
          if (!statusResp.ok) return;
          const statusData = await statusResp.json();

          if (statusData.status === 'scanned') {
            setQrStatus('scanned');
          }
          if (statusData.status === 'confirmed' && statusData.token) {
            setQrStatus('confirmed');
            clearTimers();
            await handleWechatLogin(statusData.token);
          }
          if (statusData.status === 'expired') {
            setQrStatus('expired');
            clearTimers();
          }
        } catch {
          // 轮询失败静默处理
        }
      }, 2000);
    } catch {
      setQrStatus('error');
    }
  }, [clearTimers]);

  const handleWechatLogin = useCallback(async (wechatToken: string) => {
    setIsLoggingIn(true);
    try {
      const response = await api.post<LoginResponse>('/auth/wechat/login', {
        code: wechatToken,
        state: '',
      });

      if (response.token?.access_token) {
        setToken(response.token.access_token);
      }
      setAuth(response.user);
      void queryClient.setQueryData(authKeys.user(), response.user);

      setIsQrCodeModalOpen(false);
      clearTimers();
      onLoginSuccess?.(response.token?.access_token || '', response.user.username);
      navigate('/');
    } catch (error) {
      const err = error instanceof Error ? error : new Error('微信登录失败');
      onLoginFailure?.(err);
    } finally {
      setIsLoggingIn(false);
    }
  }, [clearTimers, onLoginSuccess, onLoginFailure, setAuth, queryClient, navigate]);

  const handleOpenQrCode = () => {
    setIsQrCodeModalOpen(true);
    fetchQrCode();
  };

  const handleClose = () => {
    setIsQrCodeModalOpen(false);
    clearTimers();
    setQrStatus('loading');
  };

  const handleLogin = () => {
    handleOpenQrCode();
  };

  const statusText: Record<QrCodeStatus, string> = {
    loading: '正在生成二维码...',
    pending: '请使用微信扫一扫登录',
    scanned: '已扫码，请在手机上确认登录',
    confirmed: '登录成功！',
    expired: '二维码已过期',
    error: '二维码生成失败',
  };

  const buttonText = children || '微信登录';

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
          <><LoaderIcon /><span>登录中...</span></>
        ) : (
          <><WechatIcon /><span>{buttonText}</span></>
        )}
      </button>

      {isQrCodeModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50">
          <div className="bg-white rounded-lg shadow-xl p-6 max-w-sm w-full mx-4">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-medium text-gray-900">微信扫码登录</h3>
              <button onClick={handleClose} className="text-gray-400 hover:text-gray-600 transition-colors">
                <CloseIcon />
              </button>
            </div>

            <div className="flex flex-col items-center py-4">
              {qrStatus === 'loading' && (
                <div className="w-48 h-48 bg-gray-100 rounded-lg flex items-center justify-center border-2 border-gray-200">
                  <LoaderIcon />
                </div>
              )}

              {qrStatus === 'error' && (
                <div className="w-48 h-48 bg-red-50 rounded-lg flex flex-col items-center justify-center border-2 border-red-200">
                  <p className="text-red-500 text-sm mb-2">二维码加载失败</p>
                  <button onClick={fetchQrCode} className="text-blue-600 text-sm underline">
                    点击重试
                  </button>
                </div>
              )}

              {qrStatus === 'expired' && (
                <div className="w-48 h-48 bg-yellow-50 rounded-lg flex flex-col items-center justify-center border-2 border-yellow-200">
                  <p className="text-yellow-600 text-sm mb-2">二维码已过期</p>
                  <button onClick={fetchQrCode} className="text-blue-600 text-sm underline">
                    刷新二维码
                  </button>
                </div>
              )}

              {(qrStatus === 'pending' || qrStatus === 'scanned' || qrStatus === 'confirmed') && qrCodeImage && (
                <div className="relative">
                  <img
                    src={qrCodeImage}
                    alt="微信扫码登录二维码"
                    className={`w-48 h-48 rounded-lg border-2 ${
                      qrStatus === 'confirmed' ? 'border-green-500 opacity-60' : 'border-gray-300'
                    } ${qrStatus === 'scanned' ? 'border-blue-500' : ''}`}
                  />
                  {qrStatus === 'scanned' && (
                    <div className="absolute inset-0 flex items-center justify-center bg-black bg-opacity-30 rounded-lg">
                      <span className="bg-blue-500 text-white px-3 py-1 rounded-full text-sm">已扫码</span>
                    </div>
                  )}
                  {qrStatus === 'confirmed' && (
                    <div className="absolute inset-0 flex items-center justify-center bg-black bg-opacity-30 rounded-lg">
                      <span className="bg-green-500 text-white px-3 py-1 rounded-full text-sm">已确认</span>
                    </div>
                  )}
                </div>
              )}

              <p className="mt-3 text-sm text-gray-600">{statusText[qrStatus]}</p>

              {(qrStatus === 'pending' || qrStatus === 'scanned') && (
                <p className="mt-1 text-xs text-gray-400">
                  有效期剩余 {expireSeconds} 秒
                </p>
              )}
            </div>

            <div className="mt-4 flex justify-center space-x-4 text-xs text-gray-500">
              <button onClick={fetchQrCode} className="hover:text-gray-700 underline">
                刷新二维码
              </button>
              <span>|</span>
              <button onClick={handleClose} className="hover:text-gray-700 underline">
                使用密码登录
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}