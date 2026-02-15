/**
 * TwoFactorVerify - 2FA验证码输入组件
 */

import { useState, useRef, useEffect } from 'react';
import { LockOutlined, ReloadOutlined } from '@ant-design/icons';

interface TwoFactorVerifyProps {
  onVerify: (code: string) => void;
  onCancel?: () => void;
  isLoading?: boolean;
  error?: string | null;
  method?: 'totp' | 'sms' | 'email';
}

/**
 * 2FA验证码输入组件
 */
export function TwoFactorVerify({ 
  onVerify, 
  onCancel, 
  isLoading = false, 
  error = null,
  method = 'totp'
}: TwoFactorVerifyProps): JSX.Element {
  const [code, setCode] = useState<string[]>(['', '', '', '', '', '']);
  const inputRefs = useRef<(HTMLInputElement | null)[]>([]);

  const methodLabels: Record<string, string> = {
    totp: '身份验证器应用',
    sms: '短信',
    email: '邮箱',
  };

  useEffect(() => {
    // 自动聚焦第一个输入框
    inputRefs.current[0]?.focus();
  }, []);

  const handleChange = (index: number, value: string): void => {
    // 只允许数字
    if (!/^\d*$/.test(value)) return;

    const newCode = [...code];
    newCode[index] = value.slice(0, 1);
    setCode(newCode);

    // 如果输入了数字，自动跳到下一个输入框
    if (value && index < 5) {
      inputRefs.current[index + 1]?.focus();
    }

    // 如果所有输入框都填满了，自动提交
    const fullCode = [...newCode];
    fullCode[index] = value.slice(0, 1);
    if (fullCode.every(digit => digit !== '') && index === 5) {
      onVerify(fullCode.join(''));
    }
  };

  const handleKeyDown = (index: number, e: React.KeyboardEvent<HTMLInputElement>): void => {
    // 处理退格键
    if (e.key === 'Backspace') {
      if (!code[index] && index > 0) {
        // 如果当前输入框为空，跳到上一个输入框
        const newCode = [...code];
        newCode[index - 1] = '';
        setCode(newCode);
        inputRefs.current[index - 1]?.focus();
      } else {
        // 清空当前输入框
        const newCode = [...code];
        newCode[index] = '';
        setCode(newCode);
      }
    }

    // 处理左右箭头键
    if (e.key === 'ArrowLeft' && index > 0) {
      inputRefs.current[index - 1]?.focus();
    }
    if (e.key === 'ArrowRight' && index < 5) {
      inputRefs.current[index + 1]?.focus();
    }
  };

  const handlePaste = (e: React.ClipboardEvent<HTMLInputElement>): void => {
    e.preventDefault();
    const pastedData = e.clipboardData.getData('text').replace(/\D/g, '').slice(0, 6);
    
    if (pastedData.length === 6) {
      const newCode = pastedData.split('');
      setCode(newCode);
      onVerify(pastedData);
    }
  };

  const handleSubmit = (): void => {
    const fullCode = code.join('');
    if (fullCode.length === 6) {
      onVerify(fullCode);
    }
  };

  const handleReset = (): void => {
    setCode(['', '', '', '', '', '']);
    inputRefs.current[0]?.focus();
  };

  return (
    <div className="p-6 bg-white rounded-lg shadow-sm">
      <div className="flex items-center justify-center mb-6">
        <div className="w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center">
          <LockOutlined className="text-3xl text-blue-600" />
        </div>
      </div>

      <h3 className="text-xl font-semibold text-center mb-2">
        输入验证码
      </h3>
      <p className="text-gray-600 text-center mb-6">
        请输入来自{methodLabels[method]}的6位验证码
      </p>

      <div className="flex justify-center gap-2 mb-6">
        {code.map((digit, index) => (
          <input
            key={index}
            ref={(el) => { inputRefs.current[index] = el; }}
            type="text"
            value={digit}
            onChange={(e) => handleChange(index, e.target.value)}
            onKeyDown={(e) => handleKeyDown(index, e)}
            onPaste={handlePaste}
            className="w-12 h-14 text-center text-2xl font-bold border-2 border-gray-200 rounded-lg focus:border-blue-500 focus:outline-none transition-colors"
            maxLength={1}
            disabled={isLoading}
          />
        ))}
      </div>

      {error && (
        <div className="mb-4 p-3 bg-red-50 text-red-600 rounded-lg text-center text-sm">
          {error}
        </div>
      )}

      <div className="flex flex-col gap-3">
        <button
          onClick={handleSubmit}
          disabled={code.join('').length !== 6 || isLoading}
          className="w-full py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50 font-medium"
        >
          {isLoading ? '验证中...' : '验证'}
        </button>

        <div className="flex justify-between">
          <button
            onClick={handleReset}
            disabled={isLoading}
            className="flex items-center px-4 py-2 text-gray-600 hover:text-gray-800 transition-colors disabled:opacity-50"
          >
            <ReloadOutlined className="mr-2" />
            重置
          </button>
          
          {onCancel && (
            <button
              onClick={onCancel}
              disabled={isLoading}
              className="px-4 py-2 text-gray-600 hover:text-gray-800 transition-colors disabled:opacity-50"
            >
              取消
            </button>
          )}
        </div>
      </div>
    </div>
  );
}