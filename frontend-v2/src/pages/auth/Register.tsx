import { type FormEvent, useState } from 'react';
import { Link } from 'react-router-dom';

import { useRegister } from '@/features/auth/hooks/useAuth';
import type { RegisterFormData, RegisterRequest } from '@/features/auth/types';
import { Input } from '@/shared/components/Input';
import { Button } from '@/shared/components/Button';

export function Register(): JSX.Element {
  const registerMutation = useRegister();
  const [formData, setFormData] = useState<RegisterFormData>({
    username: '',
    email: '',
    password: '',
    nickname: '',
    agree_terms: false,
    agree_privacy: false,
    agree_ai_disclaimer: false,
  });
  const [localError, setLocalError] = useState<string | null>(null);
  const [passwordVisible, setPasswordVisible] = useState(false);

  function handleChange(e: React.ChangeEvent<HTMLInputElement>): void {
    const { name, value, type, checked } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value,
    }));
    if (localError) {
      setLocalError(null);
    }
  }

  async function handleSubmit(e: FormEvent<HTMLFormElement>): Promise<void> {
    e.preventDefault();
    setLocalError(null);

    if (!formData.username.trim()) {
      setLocalError('请输入用户名');
      return;
    }

    if (!formData.email.trim()) {
      setLocalError('请输入邮箱');
      return;
    }

    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.email)) {
      setLocalError('请输入有效的邮箱地址');
      return;
    }

    if (formData.password.length < 6) {
      setLocalError('密码长度不能少于6位');
      return;
    }

    if (!formData.agree_terms || !formData.agree_privacy || !formData.agree_ai_disclaimer) {
      setLocalError('请同意用户协议、隐私政策和AI使用声明');
      return;
    }

    try {
      const payload: RegisterRequest = {
        username: formData.username,
        email: formData.email,
        password: formData.password,
        nickname: formData.nickname || undefined,
      };
      await registerMutation.mutateAsync(payload);
    } catch (err) {
      const message = err instanceof Error ? err.message : '注册失败，请重试';
      setLocalError(message);
    }
  }

  const agreements = [
    { key: 'agree_terms' as const, label: '《用户协议》', href: '/terms' },
    { key: 'agree_privacy' as const, label: '《隐私政策》', href: '/privacy' },
    { key: 'agree_ai_disclaimer' as const, label: '《AI使用声明》', href: '/ai-disclaimer' },
  ];

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-indigo-50 flex">
      {/* 左侧品牌区域 */}
      <div className="hidden lg:flex lg:w-1/2 relative overflow-hidden bg-gradient-to-br from-blue-600 to-indigo-700">
        <div className="absolute inset-0 bg-black/10"></div>
        <div className="absolute top-20 left-20 w-64 h-64 bg-white/10 rounded-full blur-3xl"></div>
        <div className="absolute bottom-20 right-20 w-96 h-96 bg-white/5 rounded-full blur-3xl"></div>

        <div className="relative z-10 flex flex-col justify-center px-16 text-white">
          <div className="flex items-center gap-3 mb-8">
            <div className="w-14 h-14 bg-white/20 backdrop-blur-sm rounded-xl flex items-center justify-center">
              <svg className="w-8 h-8 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M12 3v17.25m0 0c-1.472 0-2.882.265-4.185.75M12 20.25c1.472 0 2.882.265 4.185.75M18.75 4.97A48.416 48.416 0 0012 4.5c-2.291 0-4.545.16-6.75.47m13.5 0c.01.635.01 1.274.01 1.918m-13.52 0c-.01-.639-.01-1.282-.01-1.918m0 9.174c.01.644.01 1.287.01 1.932m13.52 0c-.01-.64-.01-1.283-.01-1.926m-13.52-9.174c2.355-.289 4.748-.437 7.176-.437 2.428 0 4.821.148 7.176.437M3.75 16.5V4.5m16.5 12V4.5M3.75 16.5c0 .415.335.75.75.75h15c.415 0 .75-.335.75-.75m-16.5 0c0 .415.335.75.75.75h15c.415 0 .75-.335.75-.75m-16.5 0v3.75c0 .415.335.75.75.75h15c.415 0 .75-.335.75-.75v-3.75M12 12.75v3.75" />
              </svg>
            </div>
            <div>
              <h2 className="text-2xl font-bold">百姓法律助手</h2>
              <p className="text-blue-100 text-sm">Baixing Legal Assistant</p>
            </div>
          </div>

          <h1 className="text-4xl font-bold mb-4">
            加入百万用户<br />
            <span className="text-blue-200">共享法律智慧</span>
          </h1>
          <p className="text-lg text-blue-100 mb-8 max-w-md">
            注册即享 AI 智能法律咨询
            <br />
            万名专业律师在线服务
          </p>

          <div className="space-y-4">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-white/15 rounded-lg flex items-center justify-center flex-shrink-0">
                <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75L11.25 15 15 9.75m-3-7.036A11.959 11.959 0 013.598 6 11.99 11.99 0 003 9.749c0 5.592 3.824 10.29 9 11.623 5.176-1.332 9-6.03 9-11.622 0-1.31-.21-2.571-.598-3.751h-.152c-3.196 0-6.1-1.248-8.25-3.285z" />
                </svg>
              </div>
              <span className="text-blue-50">隐私保护，数据安全</span>
            </div>
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-white/15 rounded-lg flex items-center justify-center flex-shrink-0">
                <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M21 11.25v8.25a1.5 1.5 0 01-1.5 1.5H5.25a1.5 1.5 0 01-1.5-1.5v-8.25M12 4.875A2.625 2.625 0 109.375 7.5H12m0-2.625V7.5m0-2.625A2.625 2.625 0 1114.625 7.5H12m0 0V21m-8.625-9.75h18c.621 0 1.125-.504 1.125-1.125v-1.5c0-.621-.504-1.125-1.125-1.125h-18c-.621 0-1.125.504-1.125 1.125v1.5c0 .621.504 1.125 1.125 1.125z" />
                </svg>
              </div>
              <span className="text-blue-50">新用户注册享专属优惠</span>
            </div>
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-white/15 rounded-lg flex items-center justify-center flex-shrink-0">
                <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M3.75 13.5l10.5-11.25L12 10.5h8.25L9.75 21.75 12 13.5H3.75z" />
                </svg>
              </div>
              <span className="text-blue-50">快速注册，即刻使用</span>
            </div>
          </div>
        </div>
      </div>

      {/* 右侧注册表单 */}
      <div className="flex-1 flex items-center justify-center px-4 py-12 lg:px-16">
        <div className="w-full max-w-md">
          {/* 移动端 Logo */}
          <div className="lg:hidden text-center mb-8">
            <div className="inline-flex items-center gap-3">
              <div className="w-12 h-12 bg-gradient-to-br from-blue-600 to-indigo-600 rounded-xl flex items-center justify-center">
                <svg className="w-7 h-7 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M12 3v17.25m0 0c-1.472 0-2.882.265-4.185.75M12 20.25c1.472 0 2.882.265 4.185.75M18.75 4.97A48.416 48.416 0 0012 4.5c-2.291 0-4.545.16-6.75.47m13.5 0c.01.635.01 1.274.01 1.918m-13.52 0c-.01-.639-.01-1.282-.01-1.918m0 9.174c.01.644.01 1.287.01 1.932m13.52 0c-.01-.64-.01-1.283-.01-1.926m-13.52-9.174c2.355-.289 4.748-.437 7.176-.437 2.428 0 4.821.148 7.176.437M3.75 16.5V4.5m16.5 12V4.5M3.75 16.5c0 .415.335.75.75.75h15c.415 0 .75-.335.75-.75m-16.5 0c0 .415.335.75.75.75h15c.415 0 .75-.335.75-.75m-16.5 0v3.75c0 .415.335.75.75.75h15c.415 0 .75-.335.75-.75v-3.75M12 12.75v3.75" />
                </svg>
              </div>
              <div className="text-left">
                <h2 className="text-xl font-bold text-gray-900">百姓法律助手</h2>
                <p className="text-sm text-gray-500">Baixing Legal Assistant</p>
              </div>
            </div>
          </div>

          <div className="mb-8">
            <h1 className="text-3xl font-bold text-gray-900">创建账号</h1>
            <p className="mt-2 text-gray-600">注册百姓法律助手，开始您的法律之旅</p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-5">
            {localError && (
              <div className="bg-red-50 border border-red-200 rounded-xl px-4 py-3 flex items-start gap-3">
                <svg className="w-5 h-5 text-red-400 mt-0.5 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m9-.75a9 9 0 11-18 0 9 9 0 0118 0zm-9 3.75h.008v.008H12v-.008z" />
                </svg>
                <p className="text-sm text-red-700">{localError}</p>
              </div>
            )}

            {registerMutation.error && !localError && (
              <div className="bg-red-50 border border-red-200 rounded-xl px-4 py-3 flex items-start gap-3">
                <svg className="w-5 h-5 text-red-400 mt-0.5 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m9-.75a9 9 0 11-18 0 9 9 0 0118 0zm-9 3.75h.008v.008H12v-.008z" />
                </svg>
                <p className="text-sm text-red-700">{registerMutation.error.message}</p>
              </div>
            )}

            <div className="space-y-4">
              <Input
                label="用户名"
                type="text"
                name="username"
                value={formData.username}
                onChange={handleChange}
                placeholder="2-50个字符"
                autoComplete="username"
                required
              />

              <Input
                label="邮箱"
                type="email"
                name="email"
                value={formData.email}
                onChange={handleChange}
                placeholder="用于账号找回和通知"
                autoComplete="email"
                required
              />

              <div className="relative">
                <Input
                  label="密码"
                  type={passwordVisible ? 'text' : 'password'}
                  name="password"
                  value={formData.password}
                  onChange={handleChange}
                  placeholder="至少6位密码"
                  autoComplete="new-password"
                  required
                />
                <button
                  type="button"
                  className="absolute right-3 top-9 text-gray-400 hover:text-gray-600"
                  onClick={() => setPasswordVisible(!passwordVisible)}
                  tabIndex={-1}
                >
                  {passwordVisible ? (
                    <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                      <path strokeLinecap="round" strokeLinejoin="round" d="M3.98 8.223A10.477 10.477 0 001.934 12C3.226 16.338 7.244 19.5 12 19.5c.993 0 1.953-.138 2.863-.395M6.228 6.228A10.45 10.45 0 0112 4.5c4.756 0 8.773 3.162 10.065 7.498a10.523 10.523 0 01-4.293 5.774M6.228 6.228L3 3m3.228 3.228l3.65 3.65m7.894 7.894L21 21m-3.228-3.228l-3.65-3.65m0 0a3 3 0 10-4.243-4.243m4.242 4.242L9.88 9.88" />
                    </svg>
                  ) : (
                    <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                      <path strokeLinecap="round" strokeLinejoin="round" d="M2.036 12.322a1.012 1.012 0 010-.639C3.423 7.51 7.36 4.5 12 4.5c4.638 0 8.573 3.007 9.963 7.178.07.207.07.431 0 .639C20.577 16.49 16.64 19.5 12 19.5c-4.638 0-8.573-3.007-9.963-7.178z" />
                      <path strokeLinecap="round" strokeLinejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                    </svg>
                  )}
                </button>
              </div>

              <Input
                label="昵称（可选）"
                type="text"
                name="nickname"
                value={formData.nickname}
                onChange={handleChange}
                placeholder="其他用户看到的名称"
                autoComplete="nickname"
              />
            </div>

            <div className="space-y-3 pt-2">
              <p className="text-sm font-medium text-gray-700">阅读并同意以下协议</p>
              {agreements.map(({ key, label, href }) => (
                <label key={key} className="flex items-start gap-2 cursor-pointer group">
                  <input
                    type="checkbox"
                    name={key}
                    checked={formData[key]}
                    onChange={handleChange}
                    className="mt-1 h-4 w-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500 cursor-pointer"
                    required
                  />
                  <span className="text-sm text-gray-600 group-hover:text-gray-800">
                    我已阅读并同意{' '}
                    <Link to={href} className="text-blue-600 hover:text-blue-700 hover:underline font-medium">
                      {label}
                    </Link>
                  </span>
                </label>
              ))}
            </div>

            <Button
              type="submit"
              variant="primary"
              size="lg"
              isLoading={registerMutation.isPending}
              className="w-full rounded-xl bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 shadow-lg shadow-blue-500/25"
            >
              注册
            </Button>

            <div className="text-center text-sm text-gray-600 pt-4 border-t border-gray-100">
              已有账号？{' '}
              <Link to="/login" className="text-blue-600 hover:text-blue-700 font-semibold">
                立即登录
              </Link>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
}
