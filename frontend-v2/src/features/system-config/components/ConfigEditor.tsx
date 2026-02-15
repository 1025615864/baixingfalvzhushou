/**
 * ConfigEditor - 配置编辑器组件
 */

import { useState, useEffect } from 'react';
import { X, RotateCcw, Save, AlertCircle, Eye, EyeOff } from 'lucide-react';

import type { ConfigItem, ConfigValue } from '../types';

interface ConfigEditorProps {
  config: ConfigItem | null;
  isOpen: boolean;
  onClose: () => void;
  onSave: (configId: string, value: ConfigValue, reason?: string) => void;
  onReset: (configId: string, reason?: string) => void;
  isSaving?: boolean;
}

export function ConfigEditor({
  config,
  isOpen,
  onClose,
  onSave,
  onReset,
  isSaving = false,
}: ConfigEditorProps): JSX.Element {
  const [value, setValue] = useState<ConfigValue>(null);
  const [changeReason, setChangeReason] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [showSensitive, setShowSensitive] = useState(false);

  // 当配置变化时重置表单
  useEffect(() => {
    if (config) {
      setValue(config.value);
      setChangeReason('');
      setError(null);
      setShowSensitive(false);
    }
  }, [config]);

  if (!isOpen || !config) {
    return <></>;
  }

  // 验证配置值
  const validateValue = (val: ConfigValue, type: string): string | null => {
    switch (type) {
      case 'string':
        if (val === null || val === undefined || val === '') {
          return '字符串值不能为空';
        }
        break;
      case 'number':
        if (typeof val !== 'number' || isNaN(val)) {
          return '请输入有效的数字';
        }
        break;
      case 'boolean':
        if (typeof val !== 'boolean') {
          return '布尔值无效';
        }
        break;
      case 'json':
        if (typeof val === 'string') {
          try {
            JSON.parse(val);
          } catch {
            return '无效的 JSON 格式';
          }
        }
        break;
      case 'array':
        if (!Array.isArray(val)) {
          return '值必须是数组';
        }
        break;
      case 'select':
        if (val === null || val === undefined || val === '') {
          return '请选择一项';
        }
        break;
    }
    return null;
  };

  // 处理保存
  const handleSave = (): void => {
    const validationError = validateValue(value, config.type);
    if (validationError) {
      setError(validationError);
      return;
    }

    onSave(config.id, value, changeReason || undefined);
  };

  // 处理重置
  const handleReset = (): void => {
    if (window.confirm('确定要将此配置重置为默认值吗？')) {
      onReset(config.id, changeReason || undefined);
    }
  };

  // 渲染输入控件
  const renderInput = (): JSX.Element => {
    switch (config.type) {
      case 'string':
        return (
          <input
            type={config.isSensitive && !showSensitive ? 'password' : 'text'}
            value={(value as string) || ''}
            onChange={(e) => setValue(e.target.value)}
            disabled={isSaving}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />
        );

      case 'number':
        return (
          <input
            type="number"
            value={(value as number) || 0}
            onChange={(e) => setValue(Number(e.target.value))}
            disabled={isSaving}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />
        );

      case 'boolean':
        return (
          <div className="flex items-center gap-4">
            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="radio"
                checked={value === true}
                onChange={() => setValue(true)}
                disabled={isSaving}
                className="h-4 w-4 text-blue-600"
              />
              <span>是</span>
            </label>
            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="radio"
                checked={value === false}
                onChange={() => setValue(false)}
                disabled={isSaving}
                className="h-4 w-4 text-blue-600"
              />
              <span>否</span>
            </label>
          </div>
        );

      case 'select':
        return (
          <select
            value={(value as string) || ''}
            onChange={(e) => setValue(e.target.value)}
            disabled={isSaving}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          >
            <option value="">请选择...</option>
            {config.options?.map((option) => (
              <option key={option} value={option}>
                {option}
              </option>
            ))}
          </select>
        );

      case 'json':
        return (
          <textarea
            value={typeof value === 'object' ? JSON.stringify(value, null, 2) : (value as string) || ''}
            onChange={(e) => setValue(e.target.value)}
            disabled={isSaving}
            rows={6}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent font-mono text-sm"
          />
        );

      case 'array':
        return (
          <textarea
            value={Array.isArray(value) ? JSON.stringify(value, null, 2) : '[]'}
            onChange={(e) => {
              try {
                const parsed: unknown = JSON.parse(e.target.value);
                if (Array.isArray(parsed)) {
                  setValue(parsed as ConfigValue);
                  setError(null);
                } else {
                  setError('值必须是数组');
                }
              } catch {
                setError('无效的 JSON 数组格式');
              }
            }}
            disabled={isSaving}
            rows={6}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent font-mono text-sm"
          />
        );

      default:
        return (
          <input
            type="text"
            value={String(value || '')}
            onChange={(e) => setValue(e.target.value)}
            disabled={isSaving}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />
        );
    }
  };

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      <div className="flex items-center justify-center min-h-screen px-4 pt-4 pb-20 text-center sm:block sm:p-0">
        {/* 背景遮罩 */}
        <div
          className="fixed inset-0 transition-opacity bg-gray-500 bg-opacity-75"
          onClick={!isSaving ? onClose : undefined}
        />

        {/* 对话框 */}
        <div className="inline-block align-bottom bg-white rounded-lg text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-lg w-full">
          <div className="bg-white px-4 pt-5 pb-4 sm:p-6 sm:pb-4">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-medium text-gray-900">编辑配置</h3>
              <button
                onClick={onClose}
                disabled={isSaving}
                className="text-gray-400 hover:text-gray-500 disabled:opacity-50"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            {/* 配置信息 */}
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  配置键
                </label>
                <div className="px-3 py-2 bg-gray-100 rounded-md text-gray-600 font-mono text-sm">
                  {config.key}
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  描述
                </label>
                <p className="text-sm text-gray-600">{config.description}</p>
              </div>

              <div>
                <div className="flex items-center justify-between mb-1">
                  <label className="block text-sm font-medium text-gray-700">
                    当前值
                  </label>
                  {config.isSensitive && (
                    <button
                      type="button"
                      onClick={() => setShowSensitive(!showSensitive)}
                      className="text-gray-400 hover:text-gray-600"
                    >
                      {showSensitive ? (
                        <EyeOff className="h-4 w-4" />
                      ) : (
                        <Eye className="h-4 w-4" />
                      )}
                    </button>
                  )}
                </div>
                {renderInput()}
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  默认值
                </label>
                <div className="px-3 py-2 bg-gray-50 rounded-md text-gray-500 font-mono text-sm">
                  {config.isSensitive
                    ? '••••••••'
                    : typeof config.defaultValue === 'object'
                    ? JSON.stringify(config.defaultValue)
                    : String(config.defaultValue)}
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  变更原因（可选）
                </label>
                <input
                  type="text"
                  value={changeReason}
                  onChange={(e) => setChangeReason(e.target.value)}
                  placeholder="请输入变更原因..."
                  disabled={isSaving}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>

              {/* 错误提示 */}
              {error && (
                <div className="flex items-center gap-2 text-red-600 text-sm">
                  <AlertCircle className="h-4 w-4" />
                  <span>{error}</span>
                </div>
              )}
            </div>
          </div>

          <div className="bg-gray-50 px-4 py-3 sm:px-6 sm:flex sm:flex-row-reverse gap-2">
            <button
              type="button"
              onClick={handleSave}
              disabled={isSaving}
              className="w-full inline-flex justify-center rounded-md border border-transparent shadow-sm px-4 py-2 bg-blue-600 text-base font-medium text-white hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 sm:w-auto sm:text-sm disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isSaving ? (
                <>
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2" />
                  保存中...
                </>
              ) : (
                <>
                  <Save className="h-4 w-4 mr-2" />
                  保存
                </>
              )}
            </button>
            <button
              type="button"
              onClick={handleReset}
              disabled={isSaving}
              className="mt-3 w-full inline-flex justify-center rounded-md border border-gray-300 shadow-sm px-4 py-2 bg-white text-base font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 sm:mt-0 sm:w-auto sm:text-sm disabled:opacity-50"
            >
              <RotateCcw className="h-4 w-4 mr-2" />
              重置为默认
            </button>
            <button
              type="button"
              onClick={onClose}
              disabled={isSaving}
              className="mt-3 w-full inline-flex justify-center rounded-md border border-gray-300 shadow-sm px-4 py-2 bg-white text-base font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 sm:mt-0 sm:w-auto sm:text-sm disabled:opacity-50"
            >
              取消
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}