/**
 * PasswordChange - 修改密码表单组件
 */

import { useState } from 'react';
import {
  LockOutlined,
  EyeOutlined,
  EyeInvisibleOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined,
  SafetyOutlined,
  ExclamationCircleOutlined,
} from '@ant-design/icons';

import type { PasswordStrength } from '../types';
import { useChangePassword, checkPasswordStrength } from '../hooks/useSecurity';

interface PasswordChangeProps {
  onSuccess?: () => void;
  onCancel?: () => void;
}

const strengthLabels: Record<PasswordStrength, { label: string; color: string; bgColor: string }> = {
  weak: { label: '弱', color: 'text-red-600', bgColor: 'bg-red-500' },
  fair: { label: '一般', color: 'text-yellow-600', bgColor: 'bg-yellow-500' },
  good: { label: '良好', color: 'text-blue-600', bgColor: 'bg-blue-500' },
  strong: { label: '强', color: 'text-green-600', bgColor: 'bg-green-500' },
};

/**
 * 修改密码表单组件
 */
export function PasswordChange({ onSuccess, onCancel }: PasswordChangeProps): JSX.Element {
  const [formData, setFormData] = useState({
    currentPassword: '',
    newPassword: '',
    confirmPassword: '',
  });
  const [showPassword, setShowPassword] = useState({
    current: false,
    new: false,
    confirm: false,
  });
  const [validationError, setValidationError] = useState<string | null>(null);
  
  const changePasswordMutation = useChangePassword();
  
  const strength = checkPasswordStrength(formData.newPassword);
  const passwordsMatch = formData.newPassword === formData.confirmPassword && formData.confirmPassword !== '';
  
  const handleSubmit = (): void => {
    setValidationError(null);
    
    // 验证
    if (!formData.currentPassword) {
      setValidationError('请输入当前密码');
      return;
    }
    
    if (formData.newPassword.length < 8) {
      setValidationError('新密码长度至少为8个字符');
      return;
    }
    
    if (formData.newPassword !== formData.confirmPassword) {
      setValidationError('两次输入的密码不一致');
      return;
    }
    
    if (strength.strength === 'weak') {
      setValidationError('密码强度太弱，请增加复杂度');
      return;
    }
    
    void (async (): Promise<void> => {
      try {
        await changePasswordMutation.mutateAsync({
          currentPassword: formData.currentPassword,
          newPassword: formData.newPassword,
        });
        onSuccess?.();
      } catch {
        // 错误已在 mutation 中处理
      }
    })();
  };

  const togglePasswordVisibility = (field: 'current' | 'new' | 'confirm'): void => {
    setShowPassword(prev => ({
      ...prev,
      [field]: !prev[field],
    }));
  };

  return (
    <div className="bg-white rounded-lg shadow-sm p-6 max-w-lg mx-auto">
      <div className="flex items-center mb-6">
        <div className="p-3 bg-blue-100 rounded-full mr-4">
          <LockOutlined className="text-2xl text-blue-600" />
        </div>
        <div>
          <h3 className="text-lg font-semibold text-gray-900">修改密码</h3>
          <p className="text-sm text-gray-500">建议定期更换密码以保护账号安全</p>
        </div>
      </div>

      <div className="space-y-4">
        {/* 当前密码 */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            当前密码 <span className="text-red-500">*</span>
          </label>
          <div className="relative">
            <input
              type={showPassword.current ? 'text' : 'password'}
              value={formData.currentPassword}
              onChange={(e) => setFormData(prev => ({ ...prev, currentPassword: e.target.value }))}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 pr-10"
              placeholder="请输入当前密码"
            />
            <button
              type="button"
              onClick={() => togglePasswordVisibility('current')}
              className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
            >
              {showPassword.current ? <EyeInvisibleOutlined /> : <EyeOutlined />}
            </button>
          </div>
        </div>

        {/* 新密码 */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            新密码 <span className="text-red-500">*</span>
          </label>
          <div className="relative">
            <input
              type={showPassword.new ? 'text' : 'password'}
              value={formData.newPassword}
              onChange={(e) => setFormData(prev => ({ ...prev, newPassword: e.target.value }))}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 pr-10"
              placeholder="请输入新密码（至少8个字符）"
            />
            <button
              type="button"
              onClick={() => togglePasswordVisibility('new')}
              className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
            >
              {showPassword.new ? <EyeInvisibleOutlined /> : <EyeOutlined />}
            </button>
          </div>
          
          {/* 密码强度指示器 */}
          {formData.newPassword && (
            <div className="mt-2">
              <div className="flex items-center justify-between mb-1">
                <span className="text-xs text-gray-500">密码强度</span>
                <span className={`text-xs font-medium ${strengthLabels[strength.strength].color}`}>
                  {strengthLabels[strength.strength].label}
                </span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-1.5">
                <div
                  className={`h-1.5 rounded-full transition-all duration-300 ${strengthLabels[strength.strength].bgColor}`}
                  style={{ width: `${strength.score}%` }}
                />
              </div>
              
              {/* 密码要求检查 */}
              <div className="mt-2 grid grid-cols-2 gap-1">
                <div className={`flex items-center text-xs ${strength.requirements.minLength ? 'text-green-600' : 'text-gray-400'}`}>
                  {strength.requirements.minLength ? <CheckCircleOutlined className="mr-1" /> : <CloseCircleOutlined className="mr-1" />}
                  至少8个字符
                </div>
                <div className={`flex items-center text-xs ${strength.requirements.hasUppercase ? 'text-green-600' : 'text-gray-400'}`}>
                  {strength.requirements.hasUppercase ? <CheckCircleOutlined className="mr-1" /> : <CloseCircleOutlined className="mr-1" />}
                  大写字母
                </div>
                <div className={`flex items-center text-xs ${strength.requirements.hasLowercase ? 'text-green-600' : 'text-gray-400'}`}>
                  {strength.requirements.hasLowercase ? <CheckCircleOutlined className="mr-1" /> : <CloseCircleOutlined className="mr-1" />}
                  小写字母
                </div>
                <div className={`flex items-center text-xs ${strength.requirements.hasNumbers ? 'text-green-600' : 'text-gray-400'}`}>
                  {strength.requirements.hasNumbers ? <CheckCircleOutlined className="mr-1" /> : <CloseCircleOutlined className="mr-1" />}
                  数字
                </div>
                <div className={`flex items-center text-xs ${strength.requirements.hasSpecialChars ? 'text-green-600' : 'text-gray-400'}`}>
                  {strength.requirements.hasSpecialChars ? <CheckCircleOutlined className="mr-1" /> : <CloseCircleOutlined className="mr-1" />}
                  特殊字符
                </div>
              </div>
            </div>
          )}
        </div>

        {/* 确认新密码 */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            确认新密码 <span className="text-red-500">*</span>
          </label>
          <div className="relative">
            <input
              type={showPassword.confirm ? 'text' : 'password'}
              value={formData.confirmPassword}
              onChange={(e) => setFormData(prev => ({ ...prev, confirmPassword: e.target.value }))}
              className={`w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 pr-10 ${
                formData.confirmPassword && !passwordsMatch 
                  ? 'border-red-300 focus:ring-red-500' 
                  : 'border-gray-300 focus:ring-blue-500'
              }`}
              placeholder="请再次输入新密码"
            />
            <button
              type="button"
              onClick={() => togglePasswordVisibility('confirm')}
              className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
            >
              {showPassword.confirm ? <EyeInvisibleOutlined /> : <EyeOutlined />}
            </button>
          </div>
          {formData.confirmPassword && !passwordsMatch && (
            <div className="mt-1 text-xs text-red-600 flex items-center">
              <ExclamationCircleOutlined className="mr-1" />
              两次输入的密码不一致
            </div>
          )}
          {formData.confirmPassword && passwordsMatch && (
            <div className="mt-1 text-xs text-green-600 flex items-center">
              <CheckCircleOutlined className="mr-1" />
              密码一致
            </div>
          )}
        </div>

        {/* 错误提示 */}
        {validationError && (
          <div className="p-3 bg-red-50 border border-red-200 rounded-lg flex items-center text-red-600 text-sm">
            <ExclamationCircleOutlined className="mr-2" />
            {validationError}
          </div>
        )}

        {/* 成功提示 */}
        {changePasswordMutation.isSuccess && (
          <div className="p-3 bg-green-50 border border-green-200 rounded-lg flex items-center text-green-600 text-sm">
            <SafetyOutlined className="mr-2" />
            密码修改成功！
          </div>
        )}

        {/* 操作按钮 */}
        <div className="flex gap-3 pt-4">
          {onCancel && (
            <button
              onClick={onCancel}
              disabled={changePasswordMutation.isPending}
              className="flex-1 px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200 transition-colors disabled:opacity-50"
            >
              取消
            </button>
          )}
          <button
            onClick={handleSubmit}
            disabled={
              changePasswordMutation.isPending ||
              !formData.currentPassword ||
              !formData.newPassword ||
              !formData.confirmPassword ||
              !passwordsMatch
            }
            className="flex-1 px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {changePasswordMutation.isPending ? '修改中...' : '确认修改'}
          </button>
        </div>
      </div>
    </div>
  );
}