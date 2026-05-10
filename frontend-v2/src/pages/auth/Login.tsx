import { type FormEvent, useState } from 'react';
import { Link } from 'react-router-dom';

import { useLogin } from '@/features/auth/hooks/useAuth';
import type { LoginRequest } from '@/features/auth/types';
import { Input } from '@/shared/components/Input';
import { Button } from '@/shared/components/Button';

export function Login(): JSX.Element {
  const loginMutation = useLogin();
  const [formData, setFormData] = useState<LoginRequest>({
    username: '',
    password: '',
  });
  const [localError, setLocalError] = useState<string | null>(null);

  function handleChange(e: React.ChangeEvent<HTMLInputElement>): void {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
    if (localError) {
      setLocalError(null);
    }
  }

  async function handleSubmit(e: FormEvent<HTMLFormElement>): Promise<void> {
    e.preventDefault();
    setLocalError(null);

    if (!formData.username.trim()) {
      setLocalError('请输入用户名或邮箱');
      return;
    }

    if (!formData.password) {
      setLocalError('请输入密码');
      return;
    }

    try {
      await loginMutation.mutateAsync(formData);
    } catch (err) {
      const message = err instanceof Error ? err.message : '登录失败，请重试';
      setLocalError(message);
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-indigo-50 flex">
      {/* 左侧品牌区域 */}
      <div className="hidden lg:flex lg:w-1/2 relative overflow-hidden bg-gradient-to-br from-blue-600 to-indigo-700">
        <div className="absolute inset-0 bg-black/10"></div>
        {/* 装饰图案 */}
        <div className="absolute top-20 left-20 w-64 h-64 bg-white/10 rounded-full blur-3xl"></div>
        <div className="absolute bottom-20 right-20 w-96 h-96 bg-white/5 rounded-full blur-3xl"></div>
        
        <div className="relative z-10 flex flex-col justify-center px-16 text-white">
          {/* Logo */}
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
            专业法律服务<br />
            <span className="text-blue-200">触手可及</span>
          </h1>
          <p className="text-lg text-blue-100 mb-8 max-w-md">
            AI智能法律咨询、律师在线预约、文书代写服务
            <br />
            为您提供全方位的法律解决方案
          </p>

          {/* 功能列表 */}
          <div className="space-y-4">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-white/15 rounded-lg flex items-center justify-center flex-shrink-0">
                <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M9.813 15.904L9 18.75l-.813-2.846a4.5 4.5 0 00-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 003.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 003.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 00-3.09 3.09zM18.259 8.715L18 9.75l-.259-1.035a3.375 3.375 0 00-2.455-2.456L14.25 6l1.036-.259a3.375 3.375 0 002.455-2.456L18 2.25l.259 1.035a3.375 3.375 0 002.456 2.456L21.75 6l-1.035.259a3.375 3.375 0 00-2.456 2.456z" />
                </svg>
              </div>
              <span className="text-blue-50">AI智能法律咨询，7×24小时在线</span>
            </div>
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-white/15 rounded-lg flex items-center justify-center flex-shrink-0">
                <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M15.75 6a3.75 3.75 0 11-7.5 0 3.75 3.75 0 017.5 0zM4.501 20.118a7.5 7.5 0 0114.998 0A17.933 17.933 0 0112 21.75c-2.676 0-5.216-.584-7.499-1.632z" />
                </svg>
              </div>
              <span className="text-blue-50">万名专业律师，在线即时响应</span>
            </div>
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-white/15 rounded-lg flex items-center justify-center flex-shrink-0">
                <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m0 12.75h7.5m-7.5 3H12M10.5 2.25H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z" />
                </svg>
              </div>
              <span className="text-blue-50">法律文书代写，合同审查把关</span>
            </div>
          </div>
        </div>
      </div>

      {/* 右侧登录表单 */}
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
            <h1 className="text-3xl font-bold text-gray-900">欢迎回来</h1>
            <p className="mt-2 text-gray-600">登录您的账号继续使用</p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-6">
            {localError && (
              <div className="bg-red-50 border border-red-200 rounded-xl px-4 py-3 flex items-start gap-3">
                <svg className="w-5 h-5 text-red-400 mt-0.5 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m9-.75a9 9 0 11-18 0 9 9 0 0118 0zm-9 3.75h.008v.008H12v-.008z" />
                </svg>
                <p className="text-sm text-red-700">{localError}</p>
              </div>
            )}

            {loginMutation.error && !localError && (
              <div className="bg-red-50 border border-red-200 rounded-xl px-4 py-3 flex items-start gap-3">
                <svg className="w-5 h-5 text-red-400 mt-0.5 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m9-.75a9 9 0 11-18 0 9 9 0 0118 0zm-9 3.75h.008v.008H12v-.008z" />
                </svg>
                <p className="text-sm text-red-700">{loginMutation.error.message}</p>
              </div>
            )}

            <div className="space-y-4">
              <Input
                label="用户名或邮箱"
                type="text"
                name="username"
                value={formData.username}
                onChange={handleChange}
                placeholder="请输入用户名或邮箱"
                autoComplete="username"
                required
              />

              <Input
                label="密码"
                type="password"
                name="password"
                value={formData.password}
                onChange={handleChange}
                placeholder="请输入密码"
                autoComplete="current-password"
                required
              />
            </div>

            <div className="flex items-center justify-between">
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  className="w-4 h-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500 cursor-pointer"
                />
                <span className="text-sm text-gray-600">记住我</span>
              </label>
              <a href="#" className="text-sm text-blue-600 hover:text-blue-700 font-medium">
                忘记密码？
              </a>
            </div>

            <Button
              type="submit"
              variant="primary"
              size="lg"
              isLoading={loginMutation.isPending}
              className="w-full rounded-xl bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 shadow-lg shadow-blue-500/25"
            >
              登录
            </Button>

            <div className="text-center text-sm text-gray-600 pt-4 border-t border-gray-100">
              还没有账号？{' '}
              <Link to="/register" className="text-blue-600 hover:text-blue-700 font-semibold">
                立即注册
              </Link>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
}
