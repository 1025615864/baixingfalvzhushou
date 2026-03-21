import { useState, useMemo, useCallback } from 'react';
import { Link } from 'react-router-dom';

import { useRegister } from '@/features/auth/hooks/useAuth';
import type { ApiError } from '@/shared/lib/api/client';

// 密码验证规则
const KEYBOARD_PATTERNS = ['qwerty', 'asdfgh', 'zxcvbn', '123456', '987654', 'abcdef'];

interface PasswordValidation {
  isValid: boolean;
  minLength: boolean;
  hasUpper: boolean;
  hasLower: boolean;
  hasDigit: boolean;
  noRepeating: boolean;
  noKeyboardPattern: boolean;
  strength: 'weak' | 'medium' | 'strong';
}

function validatePassword(password: string): PasswordValidation {
  const minLength = password.length >= 8;
  const hasUpper = /[A-Z]/.test(password);
  const hasLower = /[a-z]/.test(password);
  const hasDigit = /[0-9]/.test(password);
  const noRepeating = !/(.)\1\1/.test(password);
  const noKeyboardPattern = !KEYBOARD_PATTERNS.some(pattern =>
    password.toLowerCase().includes(pattern)
  );

  const validCount = [minLength, hasUpper, hasLower, hasDigit, noRepeating, noKeyboardPattern]
    .filter(Boolean).length;

  let strength: 'weak' | 'medium' | 'strong' = 'weak';
  if (validCount >= 5) strength = 'medium';
  if (validCount === 6) strength = 'strong';

  const isValid = minLength && hasUpper && hasLower && hasDigit && noRepeating && noKeyboardPattern;

  return { isValid, minLength, hasUpper, hasLower, hasDigit, noRepeating, noKeyboardPattern, strength };
}

// 用户名验证
interface UsernameValidation {
  isValid: boolean;
  minLength: boolean;
  maxLength: boolean;
  validChars: boolean;
  noInvalidStartEnd: boolean;
  noDoubleUnderscore: boolean;
}

function validateUsername(username: string): UsernameValidation {
  const minLength = username.length >= 2;
  const maxLength = username.length <= 20;
  const validChars = /^[\u4e00-\u9fa5a-zA-Z0-9_]*$/.test(username);
  const noInvalidStartEnd = username.length === 0 || (
    !/^[0-9_]/.test(username) && !/_$/.test(username)
  );
  const noDoubleUnderscore = !username.includes('__');

  const isValid = minLength && maxLength && validChars && noInvalidStartEnd && noDoubleUnderscore;

  return { isValid, minLength, maxLength, validChars, noInvalidStartEnd, noDoubleUnderscore };
}

// 验证项组件
function ValidationItem({ valid, text }: { valid: boolean; text: string }) {
  return (
    <li className={`flex items-center text-xs ${valid ? 'text-green-600' : 'text-gray-400'}`}>
      <span className={`mr-1.5 ${valid ? 'text-green-500' : 'text-gray-300'}`}>
        {valid ? '✓' : '○'}
      </span>
      {text}
    </li>
  );
}

export function Register(): JSX.Element {
  const [formData, setFormData] = useState({
    username: '',
    email: '',
    password: '',
    confirmPassword: '',
    agree_terms: false,
    agree_privacy: false,
    agree_ai_disclaimer: false,
  });
  const [errorMsg, setErrorMsg] = useState('');
  const [successMsg, setSuccessMsg] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [touched, setTouched] = useState<Record<string, boolean>>({});

  const { mutate: register, isPending, error, isSuccess } = useRegister();

  // 实时验证
  const passwordValidation = useMemo(
    () => validatePassword(formData.password),
    [formData.password]
  );

  const usernameValidation = useMemo(
    () => validateUsername(formData.username),
    [formData.username]
  );

  const passwordsMatch = formData.password === formData.confirmPassword;
  const allAgreed = formData.agree_terms && formData.agree_privacy && formData.agree_ai_disclaimer;

  // 表单是否可以提交
  const canSubmit = useMemo(() => {
    return (
      usernameValidation.isValid &&
      formData.email.length > 0 &&
      passwordValidation.isValid &&
      formData.confirmPassword.length > 0 &&
      passwordsMatch &&
      allAgreed &&
      !isPending
    );
  }, [usernameValidation.isValid, formData.email, formData.confirmPassword, passwordValidation.isValid, passwordsMatch, allAgreed, isPending]);

  // 格式化错误消息
  const getErrorMessage = useCallback((err: unknown): string => {
    if (!err) return '';

    const apiErr = err as ApiError;
    if (apiErr.message) {
      return apiErr.message;
    }

    if (err instanceof Error) {
      return err.message;
    }

    return '注册失败，请稍后重试';
  }, []);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMsg('');
    setSuccessMsg('');

    // 前端验证
    if (!usernameValidation.isValid) {
      setErrorMsg('请输入有效的用户名');
      return;
    }

    if (!passwordValidation.isValid) {
      setErrorMsg('密码不符合安全要求');
      return;
    }

    if (!passwordsMatch) {
      setErrorMsg('两次输入的密码不一致');
      return;
    }

    if (!allAgreed) {
      setErrorMsg('请阅读并同意所有协议');
      return;
    }

    const submitData = {
      username: formData.username,
      email: formData.email,
      password: formData.password,
      agree_terms: formData.agree_terms,
      agree_privacy: formData.agree_privacy,
      agree_ai_disclaimer: formData.agree_ai_disclaimer,
    };

    register(submitData, {
      onSuccess: (response) => {
        if (response.message) {
          setSuccessMsg(response.message);
        }
      },
    });
  };

  // 标记字段为已触碰
  const handleBlur = (field: string) => {
    setTouched(prev => ({ ...prev, [field]: true }));
  };

  return (
    <div className="auth-page relative">
      {/* 背景装饰 */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute -top-40 -right-40 w-80 h-80 bg-primary-200/30 rounded-full blur-3xl" />
        <div className="absolute -bottom-40 -left-40 w-80 h-80 bg-secondary-200/30 rounded-full blur-3xl" />
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] bg-dots opacity-50" />
      </div>

      <div className="max-w-md w-full px-4 relative z-10">
        {/* 头部 */}
        <div className="text-center mb-8">
          {/* Logo 和品牌 */}
          <div className="flex items-center justify-center gap-2 mb-4">
            <div className="w-12 h-12 bg-gradient-hero rounded-2xl flex items-center justify-center shadow-lg shadow-primary-500/30">
              <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 6l3 1m0 0l-3 9a5.002 5.002 0 006.001 0M6 7l3 9M6 7l6-2m6 2l3-1m-3 1l-3 9a5.002 5.002 0 006.001 0M18 7l3 9m-3-9l-6-2m0-2v2m0 16V5m0 16H9m3 0h3" />
              </svg>
            </div>
          </div>
          <h2 className="text-2xl font-bold text-slate-900">
            创建<span className="text-primary-600">百姓助手</span>账户
          </h2>
          <p className="mt-2 text-sm text-slate-500">
            开启您的专业法律服务之旅
          </p>
        </div>

        {/* 表单卡片 */}
        <div className="auth-card">
          <form className="space-y-5" onSubmit={handleSubmit}>
            {/* 错误提示 */}
            {(errorMsg || error) && (
              <div className="rounded-lg bg-red-50 p-4 border border-red-200">
                <div className="flex">
                  <div className="flex-shrink-0">
                    <svg className="h-5 w-5 text-red-400" viewBox="0 0 20 20" fill="currentColor">
                      <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                    </svg>
                  </div>
                  <div className="ml-3">
                    <p className="text-sm text-red-700 font-medium">
                      {errorMsg || getErrorMessage(error)}
                    </p>
                  </div>
                </div>
              </div>
            )}

            {/* 成功提示 */}
            {(isSuccess || successMsg) && (
              <div className="rounded-lg bg-green-50 p-4 border border-green-200">
                <div className="flex">
                  <div className="flex-shrink-0">
                    <svg className="h-5 w-5 text-green-400" viewBox="0 0 20 20" fill="currentColor">
                      <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                    </svg>
                  </div>
                  <div className="ml-3">
                    <p className="text-sm text-green-700 font-medium">
                      {successMsg || '注册成功！'}
                    </p>
                  </div>
                </div>
              </div>
            )}

            {/* 用户名 */}
            <div>
              <label htmlFor="username" className="block text-sm font-medium text-gray-700 mb-1">
                用户名 <span className="text-red-500">*</span>
              </label>
              <input
                id="username"
                name="username"
                type="text"
                required
                minLength={2}
                maxLength={20}
                className={`appearance-none block w-full px-3 py-2.5 border rounded-lg shadow-sm placeholder-gray-400
                  focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500 sm:text-sm
                  ${touched.username && !usernameValidation.isValid && formData.username
                    ? 'border-red-300 bg-red-50'
                    : touched.username && usernameValidation.isValid
                    ? 'border-green-300 bg-green-50'
                    : 'border-gray-300'}`}
                placeholder="2-20位，支持中英文、数字、下划线"
                value={formData.username}
                onChange={(e) => setFormData({ ...formData, username: e.target.value })}
                onBlur={() => handleBlur('username')}
              />
              {touched.username && formData.username && (
                <ul className="mt-2 space-y-1">
                  <ValidationItem valid={usernameValidation.minLength} text="至少2个字符" />
                  <ValidationItem valid={usernameValidation.maxLength} text="不超过20个字符" />
                  <ValidationItem valid={usernameValidation.validChars} text="仅包含中英文、数字、下划线" />
                  <ValidationItem valid={usernameValidation.noInvalidStartEnd} text="不以数字或下划线开头/结尾" />
                </ul>
              )}
            </div>

            {/* 邮箱 */}
            <div>
              <label htmlFor="email" className="block text-sm font-medium text-gray-700 mb-1">
                邮箱 <span className="text-red-500">*</span>
              </label>
              <input
                id="email"
                name="email"
                type="email"
                required
                className="appearance-none block w-full px-3 py-2.5 border border-gray-300 rounded-lg shadow-sm placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500 sm:text-sm"
                placeholder="your@email.com"
                value={formData.email}
                onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                onBlur={() => handleBlur('email')}
              />
            </div>

            {/* 密码 */}
            <div>
              <label htmlFor="password" className="block text-sm font-medium text-gray-700 mb-1">
                密码 <span className="text-red-500">*</span>
              </label>
              <div className="relative">
                <input
                  id="password"
                  name="password"
                  type={showPassword ? 'text' : 'password'}
                  required
                  minLength={8}
                  maxLength={50}
                  className={`appearance-none block w-full px-3 py-2.5 pr-10 border rounded-lg shadow-sm placeholder-gray-400
                    focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500 sm:text-sm
                    ${touched.password && !passwordValidation.isValid && formData.password
                      ? 'border-red-300 bg-red-50'
                      : touched.password && passwordValidation.isValid
                      ? 'border-green-300 bg-green-50'
                      : 'border-gray-300'}`}
                  placeholder="8-50位安全密码"
                  value={formData.password}
                  onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                  onBlur={() => handleBlur('password')}
                />
                <button
                  type="button"
                  className="absolute inset-y-0 right-0 pr-3 flex items-center text-gray-400 hover:text-gray-600"
                  onClick={() => setShowPassword(!showPassword)}
                >
                  {showPassword ? (
                    <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.88 9.88l-3.29-3.29m7.532 7.532l3.29 3.29M3 3l3.59 3.59m0 0A9.953 9.953 0 0112 5c4.478 0 8.268 2.943 9.543 7a10.025 10.025 0 01-4.132 5.411m0 0L21 21" />
                    </svg>
                  ) : (
                    <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                    </svg>
                  )}
                </button>
              </div>

              {/* 密码强度指示器 */}
              {formData.password && (
                <div className="mt-2">
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-xs text-gray-500">密码强度</span>
                    <span className={`text-xs font-medium ${
                      passwordValidation.strength === 'weak' ? 'text-red-500' :
                          passwordValidation.strength === 'medium' ? 'text-yellow-500' : 'text-green-500'
                        }`}>
                      {passwordValidation.strength === 'weak' ? '弱' :
                        passwordValidation.strength === 'medium' ? '中' : '强'}
                    </span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-1.5">
                    <div
                      className={`h-1.5 rounded-full transition-all duration-300 ${
                        passwordValidation.strength === 'weak' ? 'bg-red-500 w-1/3' :
                          passwordValidation.strength === 'medium' ? 'bg-yellow-500 w-2/3' : 'bg-green-500 w-full'
                      }`}
                    />
                  </div>
                </div>
              )}

              {/* 密码验证列表 */}
              {touched.password && formData.password && (
                <ul className="mt-2 space-y-1 grid grid-cols-2 gap-x-4">
                  <ValidationItem valid={passwordValidation.minLength} text="至少8位字符" />
                  <ValidationItem valid={passwordValidation.hasUpper} text="包含大写字母" />
                  <ValidationItem valid={passwordValidation.hasLower} text="包含小写字母" />
                  <ValidationItem valid={passwordValidation.hasDigit} text="包含数字" />
                  <ValidationItem valid={passwordValidation.noRepeating} text="无连续相同字符" />
                  <ValidationItem valid={passwordValidation.noKeyboardPattern} text="无键盘序列" />
                </ul>
              )}
            </div>

            {/* 确认密码 */}
            <div>
              <label htmlFor="confirm-password" className="block text-sm font-medium text-gray-700 mb-1">
                确认密码 <span className="text-red-500">*</span>
              </label>
              <div className="relative">
                <input
                  id="confirm-password"
                  name="confirm-password"
                  type={showConfirmPassword ? 'text' : 'password'}
                  required
                  className={`appearance-none block w-full px-3 py-2.5 pr-10 border rounded-lg shadow-sm placeholder-gray-400
                    focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500 sm:text-sm
                    ${touched.confirmPassword && formData.confirmPassword && !passwordsMatch
                      ? 'border-red-300 bg-red-50'
                      : touched.confirmPassword && formData.confirmPassword && passwordsMatch
                      ? 'border-green-300 bg-green-50'
                      : 'border-gray-300'}`}
                  placeholder="再次输入密码"
                  value={formData.confirmPassword}
                  onChange={(e) => setFormData({ ...formData, confirmPassword: e.target.value })}
                  onBlur={() => handleBlur('confirmPassword')}
                />
                <button
                  type="button"
                  className="absolute inset-y-0 right-0 pr-3 flex items-center text-gray-400 hover:text-gray-600"
                  onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                >
                  {showConfirmPassword ? (
                    <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.88 9.88l-3.29-3.29m7.532 7.532l3.29 3.29M3 3l3.59 3.59m0 0A9.953 9.953 0 0112 5c4.478 0 8.268 2.943 9.543 7a10.025 10.025 0 01-4.132 5.411m0 0L21 21" />
                    </svg>
                  ) : (
                    <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                    </svg>
                  )}
                </button>
              </div>
              {touched.confirmPassword && formData.confirmPassword && (
                <p className={`mt-1 text-xs ${passwordsMatch ? 'text-green-600' : 'text-red-500'}`}>
                  {passwordsMatch ? '✓ 密码一致' : '✗ 密码不一致'}
                </p>
              )}
            </div>

            {/* 协议同意 */}
            <div className="space-y-3 pt-2">
              <p className="text-sm font-medium text-gray-700">服务协议</p>

              <label className="flex items-start group cursor-pointer">
                <input
                  id="agree_terms"
                  name="agree_terms"
                  type="checkbox"
                  className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded mt-0.5 cursor-pointer"
                  checked={formData.agree_terms}
                  onChange={(e) => setFormData(prev => ({ ...prev, agree_terms: e.target.checked }))}
                />
                <span className="ml-3 text-sm text-gray-600 group-hover:text-gray-900">
                  我已阅读并同意
                  <Link to="/terms" className="text-primary-600 hover:text-primary-500 underline ml-1" target="_blank">
                    《用户服务协议》
                  </Link>
                </span>
              </label>

              <label className="flex items-start group cursor-pointer">
                <input
                  id="agree_privacy"
                  name="agree_privacy"
                  type="checkbox"
                  className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded mt-0.5 cursor-pointer"
                  checked={formData.agree_privacy}
                  onChange={(e) => setFormData(prev => ({ ...prev, agree_privacy: e.target.checked }))}
                />
                <span className="ml-3 text-sm text-gray-600 group-hover:text-gray-900">
                  我已阅读并同意
                  <Link to="/privacy" className="text-primary-600 hover:text-primary-500 underline ml-1" target="_blank">
                    《隐私政策》
                  </Link>
                </span>
              </label>

              <label className="flex items-start group cursor-pointer">
                <input
                  id="agree_ai_disclaimer"
                  name="agree_ai_disclaimer"
                  type="checkbox"
                  className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded mt-0.5 cursor-pointer"
                  checked={formData.agree_ai_disclaimer}
                  onChange={(e) => setFormData(prev => ({ ...prev, agree_ai_disclaimer: e.target.checked }))}
                />
                <span className="ml-3 text-sm text-gray-600 group-hover:text-gray-900">
                  我已阅读并同意
                  <Link to="/ai-disclaimer" className="text-primary-600 hover:text-primary-500 underline ml-1" target="_blank">
                    《AI咨询服务免责声明》
                  </Link>
                </span>
              </label>
            </div>

            {/* 提交按钮 */}
            <div className="pt-2">
              <button
                type="submit"
                disabled={!canSubmit}
                className={`w-full flex justify-center py-3 px-4 border border-transparent text-sm font-medium rounded-lg text-white
                  transition-all duration-200
                  ${canSubmit
                    ? 'bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 shadow-lg hover:shadow-xl'
                    : 'bg-gray-300 cursor-not-allowed'}`}
              >
                {isPending ? (
                  <span className="flex items-center">
                    <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                    </svg>
                    注册中...
                  </span>
                ) : '立即注册'}
              </button>
            </div>
          </form>

          {/* 帮助提示 */}
          <div className="mt-6 text-center space-y-3">
            <p className="text-sm text-slate-500">
              已有账户？{' '}
              <Link
                to="/login"
                className="font-medium text-primary-600 hover:text-primary-500"
              >
                立即登录
              </Link>
            </p>
            <p className="text-xs text-slate-400">
              注册即表示您同意我们的服务条款和隐私政策
            </p>
          </div>
        </div>

        {/* 底部信任标识 */}
        <div className="mt-8 flex items-center justify-center gap-6 text-xs text-slate-400">
          <span className="flex items-center gap-1.5">
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
            </svg>
            数据安全加密
          </span>
          <span className="flex items-center gap-1.5">
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 6l3 1m0 0l-3 9a5.002 5.002 0 006.001 0M6 7l3 9M6 7l6-2m6 2l3-1m-3 1l-3 9a5.002 5.002 0 006.001 0M18 7l3 9m-3-9l-6-2m0-2v2m0 16V5m0 16H9m3 0h3" />
            </svg>
            专业法律服务
          </span>
          <span className="flex items-center gap-1.5">
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            7×24小时服务
          </span>
        </div>
      </div>
    </div>
  );
}
