/**
 * TwoFactorSetup - 2FA设置向导组件
 */

import { useState } from 'react';
import {
  SafetyCertificateOutlined,
  MobileOutlined,
  MailOutlined,
  QrcodeOutlined,
  CheckOutlined,
  CopyOutlined,
  DownloadOutlined,
  ArrowRightOutlined,
  ArrowLeftOutlined,
  ReloadOutlined,
  WarningOutlined,
} from '@ant-design/icons';

import type { TwoFactorMethod, TwoFactorSetupStep } from '../types';
import { 
  useTwoFactorSetup, 
  useTwoFactorVerify, 
  useRegenerateBackupCodes,
  useTwoFactorStatus 
} from '../hooks/useSecurity';

interface TwoFactorSetupProps {
  onComplete?: () => void;
  onCancel?: () => void;
}

const methodConfig: Record<TwoFactorMethod, { label: string; description: string }> = {
  totp: {
    label: '身份验证器应用',
    description: '使用 Google Authenticator、Authy 等应用生成验证码',
  },
  sms: {
    label: '短信验证',
    description: '通过短信接收验证码',
  },
  email: {
    label: '邮箱验证',
    description: '通过邮件接收验证码',
  },
};

const methodIcons: Record<TwoFactorMethod, React.ReactNode> = {
  totp: <QrcodeOutlined />,
  sms: <MobileOutlined />,
  email: <MailOutlined />,
};

/**
 * 2FA设置向导组件
 */
export function TwoFactorSetup({ onComplete, onCancel }: TwoFactorSetupProps): JSX.Element {
  const [step, setStep] = useState<TwoFactorSetupStep>('select-method');
  const [selectedMethod, setSelectedMethod] = useState<TwoFactorMethod>('totp');
  const [verificationCode, setVerificationCode] = useState<string>('');
  const [backupCodes, setBackupCodes] = useState<string[]>([]);
  const [setupData, setSetupData] = useState<{ secret: string; qrCodeUrl: string } | null>(null);
  const [copiedCode, setCopiedCode] = useState<boolean>(false);
  
  const { data: twoFactorStatus } = useTwoFactorStatus();
  const setupMutation = useTwoFactorSetup();
  const verifyMutation = useTwoFactorVerify();
  const regenerateMutation = useRegenerateBackupCodes();

  const handleSelectMethod = (method: TwoFactorMethod): void => {
    setSelectedMethod(method);
  };

  const handleStartSetup = (): void => {
    void (async (): Promise<void> => {
      try {
        const result = await setupMutation.mutateAsync();
        setSetupData({
          secret: result.secret,
          qrCodeUrl: result.qrCodeUrl,
        });
        setBackupCodes(result.backupCodes);
        setStep('show-qr');
      } catch {
        // 错误已在 mutation 中处理
      }
    })();
  };

  const handleVerifyCode = (): void => {
    if (verificationCode.length !== 6) return;
    
    void (async (): Promise<void> => {
      try {
        await verifyMutation.mutateAsync({
          code: verificationCode,
        });
        setStep('backup-codes');
      } catch {
        // 错误已在 mutation 中处理
      }
    })();
  };

  const handleCopySecret = (): void => {
    if (setupData?.secret) {
      void navigator.clipboard.writeText(setupData.secret);
      setCopiedCode(true);
      setTimeout(() => setCopiedCode(false), 2000);
    }
  };

  const handleDownloadBackupCodes = (): void => {
    const content = backupCodes.join('\n');
    const blob = new Blob([content], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'backup-codes.txt';
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const handleComplete = (): void => {
    onComplete?.();
  };

  const handleRegenerateBackupCodes = (): void => {
    void (async (): Promise<void> => {
      try {
        const result = await regenerateMutation.mutateAsync({ code: verificationCode });
        setBackupCodes(result.backupCodes);
      } catch {
        // 错误已在 mutation 中处理
      }
    })();
  };

  // 如果2FA已启用，显示禁用选项
  if (twoFactorStatus?.enabled) {
    return (
      <div className="p-6 bg-white rounded-lg shadow-sm">
        <div className="flex items-center justify-center mb-6">
          <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center">
            <SafetyCertificateOutlined className="text-3xl text-green-600" />
          </div>
        </div>
        
        <h3 className="text-xl font-semibold text-center mb-2">
          双重验证已启用
        </h3>
        <p className="text-gray-600 text-center mb-6">
          您的账户已启用{methodConfig[twoFactorStatus.method || 'totp'].label}验证
        </p>
        
        <div className="bg-blue-50 p-4 rounded-lg mb-6">
          <p className="text-sm text-blue-800">
            双重验证已成功配置。每次登录时，除了密码外，您还需要输入来自验证应用的动态验证码。
          </p>
        </div>

        <button
          onClick={handleComplete}
          className="w-full py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors font-medium"
        >
          完成
        </button>
      </div>
    );
  }

  // 步骤1：选择验证方法
  if (step === 'select-method') {
    return (
      <div className="p-6 bg-white rounded-lg shadow-sm">
        <h3 className="text-xl font-semibold mb-4">启用双重验证</h3>
        <p className="text-gray-600 mb-6">
          请选择您偏好的验证方式
        </p>

        <div className="space-y-3 mb-6">
          {(Object.keys(methodConfig) as TwoFactorMethod[]).map((method) => (
            <button
              key={method}
              onClick={() => handleSelectMethod(method)}
              className={`w-full p-4 border-2 rounded-lg text-left transition-all ${
                selectedMethod === method
                  ? 'border-blue-500 bg-blue-50'
                  : 'border-gray-200 hover:border-gray-300'
              }`}
            >
              <div className="flex items-center">
                <div className={`w-10 h-10 rounded-full flex items-center justify-center mr-3 ${
                  selectedMethod === method ? 'bg-blue-100' : 'bg-gray-100'
                }`}>
                  <span className={selectedMethod === method ? 'text-blue-600' : 'text-gray-600'}>
                    {methodIcons[method]}
                  </span>
                </div>
                <div>
                  <div className="font-medium text-gray-900">
                    {methodConfig[method].label}
                  </div>
                  <div className="text-sm text-gray-500">
                    {methodConfig[method].description}
                  </div>
                </div>
                {selectedMethod === method && (
                  <CheckOutlined className="ml-auto text-blue-600" />
                )}
              </div>
            </button>
          ))}
        </div>

        <div className="flex gap-3">
          {onCancel && (
            <button
              onClick={onCancel}
              className="flex-1 py-3 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors font-medium"
            >
              取消
            </button>
          )}
          <button
            onClick={handleStartSetup}
            disabled={setupMutation.isPending}
            className="flex-1 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors font-medium flex items-center justify-center disabled:opacity-50"
          >
            {setupMutation.isPending ? '设置中...' : '下一步'}
            <ArrowRightOutlined className="ml-2" />
          </button>
        </div>
      </div>
    );
  }

  // 步骤2：显示二维码
  if (step === 'show-qr' && setupData) {
    return (
      <div className="p-6 bg-white rounded-lg shadow-sm">
        <h3 className="text-xl font-semibold mb-4">扫描二维码</h3>
        <p className="text-gray-600 mb-6">
          使用身份验证器应用扫描下方的二维码
        </p>

        <div className="flex flex-col items-center mb-6">
          {setupData.qrCodeUrl ? (
            <img
              src={setupData.qrCodeUrl}
              alt="QR Code"
              className="w-48 h-48 border border-gray-200 rounded-lg"
            />
          ) : (
            <div className="w-48 h-48 bg-gray-100 rounded-lg flex items-center justify-center">
              <QrcodeOutlined className="text-6xl text-gray-400" />
            </div>
          )}
          
          <div className="mt-4 p-3 bg-gray-50 rounded-lg w-full">
            <div className="text-sm text-gray-600 mb-1">无法扫描？手动输入密钥：</div>
            <div className="flex items-center justify-between">
              <code className="text-sm font-mono break-all flex-1 mr-2">
                {setupData.secret}
              </code>
              <button
                onClick={handleCopySecret}
                className="flex items-center px-3 py-1 text-sm text-blue-600 hover:bg-blue-50 rounded transition-colors"
              >
                {copiedCode ? <CheckOutlined className="mr-1" /> : <CopyOutlined className="mr-1" />}
                {copiedCode ? '已复制' : '复制'}
              </button>
            </div>
          </div>
        </div>

        <div className="flex gap-3">
          <button
            onClick={() => setStep('select-method')}
            className="flex-1 py-3 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors font-medium flex items-center justify-center"
          >
            <ArrowLeftOutlined className="mr-2" />
            返回
          </button>
          <button
            onClick={() => setStep('verify-code')}
            className="flex-1 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors font-medium flex items-center justify-center"
          >
            下一步
            <ArrowRightOutlined className="ml-2" />
          </button>
        </div>
      </div>
    );
  }

  // 步骤3：验证验证码
  if (step === 'verify-code') {
    return (
      <div className="p-6 bg-white rounded-lg shadow-sm">
        <h3 className="text-xl font-semibold mb-4">验证设置</h3>
        <p className="text-gray-600 mb-6">
          请输入身份验证器应用中的6位验证码以确认设置
        </p>

        <div className="mb-6">
          <input
            type="text"
            value={verificationCode}
            onChange={(e) => setVerificationCode(e.target.value.replace(/\D/g, '').slice(0, 6))}
            placeholder="000000"
            className="w-full px-4 py-3 border border-gray-300 rounded-lg text-center text-2xl font-mono tracking-widest focus:border-blue-500 focus:outline-none"
            maxLength={6}
          />
        </div>

        {verifyMutation.error && (
          <div className="mb-4 p-3 bg-red-50 text-red-600 rounded-lg text-center text-sm">
            验证码错误，请重试
          </div>
        )}

        <div className="flex gap-3">
          <button
            onClick={() => setStep('show-qr')}
            className="flex-1 py-3 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors font-medium flex items-center justify-center"
          >
            <ArrowLeftOutlined className="mr-2" />
            返回
          </button>
          <button
            onClick={handleVerifyCode}
            disabled={verificationCode.length !== 6 || verifyMutation.isPending}
            className="flex-1 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors font-medium disabled:opacity-50 flex items-center justify-center"
          >
            {verifyMutation.isPending ? '验证中...' : '验证'}
            <CheckOutlined className="ml-2" />
          </button>
        </div>
      </div>
    );
  }

  // 步骤4：显示备用码
  if (step === 'backup-codes') {
    return (
      <div className="p-6 bg-white rounded-lg shadow-sm">
        <h3 className="text-xl font-semibold mb-4">保存备用码</h3>
        <p className="text-gray-600 mb-4">
          请将以下备用码保存在安全的地方。如果您无法访问验证器，可以使用备用码登录。
        </p>

        <div className="bg-amber-50 border border-amber-200 rounded-lg p-4 mb-4">
          <div className="flex items-start">
            <WarningOutlined className="text-amber-500 mt-0.5 mr-2" />
            <p className="text-sm text-amber-800">
              每个备用码只能使用一次。建议您将其下载或打印保存。
            </p>
          </div>
        </div>

        <div className="grid grid-cols-2 gap-2 mb-6">
          {backupCodes.map((code) => (
            <div
              key={code}
              className="px-3 py-2 bg-gray-100 rounded font-mono text-sm text-center"
            >
              {code}
            </div>
          ))}
        </div>

        <div className="flex gap-3 mb-4">
          <button
            onClick={handleDownloadBackupCodes}
            className="flex-1 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors font-medium flex items-center justify-center"
          >
            <DownloadOutlined className="mr-2" />
            下载备用码
          </button>
          <button
            onClick={handleRegenerateBackupCodes}
            disabled={regenerateMutation.isPending}
            className="flex-1 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors font-medium flex items-center justify-center disabled:opacity-50"
          >
            <ReloadOutlined className={`mr-2 ${regenerateMutation.isPending ? 'animate-spin' : ''}`} />
            重新生成
          </button>
        </div>

        <button
          onClick={handleComplete}
          className="w-full py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors font-medium"
        >
          完成设置
          <CheckOutlined className="ml-2" />
        </button>
      </div>
    );
  }

  return <></>;
}