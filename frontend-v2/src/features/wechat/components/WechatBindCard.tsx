/**
 * WechatBindCard - 微信绑定卡片组件
 * 用于展示和管理微信账号绑定状态
 */

import { useState } from 'react';

import type { WechatBindInfo, WechatAccountType } from '../types';
import { useBindWechat, useUnbindWechat } from '../hooks/useWechat';

interface WechatBindCardProps {
  userId: number;
  bindInfo: WechatBindInfo | null;
  accountType: WechatAccountType;
  isLoading?: boolean;
}

interface AccountTypeConfig {
  icon: JSX.Element;
  title: string;
  description: string;
  color: string;
  bgColor: string;
}

/**
 * 检查图标组件
 */
function CheckCircleIcon(): JSX.Element {
  return (
    <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
    </svg>
  );
}

/**
 * 关闭图标组件
 */
function XCircleIcon(): JSX.Element {
  return (
    <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z" />
    </svg>
  );
}

/**
 * 加载图标组件
 */
function LoaderIcon(): JSX.Element {
  return (
    <svg className="w-3 h-3 animate-spin" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
    </svg>
  );
}

/**
 * 消息图标组件
 */
function MessageCircleIcon(): JSX.Element {
  return (
    <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
    </svg>
  );
}

/**
 * 手机图标组件
 */
function SmartphoneIcon(): JSX.Element {
  return (
    <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 18h.01M8 21h8a2 2 0 002-2V5a2 2 0 00-2-2H8a2 2 0 00-2 2v14a2 2 0 002 2z" />
    </svg>
  );
}

const accountTypeConfig: Record<WechatAccountType, AccountTypeConfig> = {
  official: {
    icon: <MessageCircleIcon />,
    title: '微信公众号',
    description: '绑定公众号，接收消息通知和服务提醒',
    color: 'text-green-600',
    bgColor: 'bg-green-50',
  },
  mini_program: {
    icon: <SmartphoneIcon />,
    title: '微信小程序',
    description: '绑定小程序，快速登录和便捷使用',
    color: 'text-blue-600',
    bgColor: 'bg-blue-50',
  },
};

/**
 * 微信绑定卡片组件
 */
export function WechatBindCard({
  userId,
  bindInfo,
  accountType,
  isLoading = false,
}: WechatBindCardProps): JSX.Element {
  const [isConfirmingUnbind, setIsConfirmingUnbind] = useState(false);
  const bindMutation = useBindWechat();
  const unbindMutation = useUnbindWechat();

  const config = accountTypeConfig[accountType];

  const isBound = bindInfo?.bindStatus === 'bound';
  const isPending = bindInfo?.bindStatus === 'pending';

  /**
   * 处理绑定操作
   */
  const handleBind = (): void => {
    // 实际实现中应该调用微信OAuth授权
    // 这里模拟授权码流程
    const mockAuthCode = `mock_auth_code_${Date.now()}`;
    
    void bindMutation.mutateAsync({
      userId,
      accountType,
      authCode: mockAuthCode,
    });
  };

  /**
   * 处理解绑操作
   */
  const handleUnbind = (): void => {
    if (!bindInfo) return;
    
    void unbindMutation.mutateAsync({
      userId,
      accountType,
      bindId: bindInfo.id,
    }).then(() => {
      setIsConfirmingUnbind(false);
    });
  };

  if (isLoading) {
    return (
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <div className="animate-pulse flex items-center space-x-4">
          <div className="w-12 h-12 bg-gray-200 rounded-lg"></div>
          <div className="flex-1 space-y-2">
            <div className="h-4 bg-gray-200 rounded w-1/3"></div>
            <div className="h-3 bg-gray-200 rounded w-1/2"></div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 hover:shadow-md transition-shadow">
      <div className="flex items-start space-x-4">
        {/* 图标区域 */}
        <div className={`flex-shrink-0 w-12 h-12 ${config.bgColor} rounded-lg flex items-center justify-center ${config.color}`}>
          {config.icon}
        </div>

        {/* 内容区域 */}
        <div className="flex-1 min-w-0">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-lg font-medium text-gray-900">
                {config.title}
              </h3>
              <p className="mt-1 text-sm text-gray-500">
                {config.description}
              </p>
            </div>

            {/* 状态标签 */}
            <div className="flex items-center space-x-2">
              {isBound && (
                <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
                  <CheckCircleIcon />
                  <span className="ml-1">已绑定</span>
                </span>
              )}
              {isPending && (
                <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800">
                  <LoaderIcon />
                  <span className="ml-1">绑定中</span>
                </span>
              )}
              {!isBound && !isPending && (
                <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-800">
                  <XCircleIcon />
                  <span className="ml-1">未绑定</span>
                </span>
              )}
            </div>
          </div>

          {/* 绑定信息展示 */}
          {isBound && bindInfo?.wechatInfo && (
            <div className="mt-4 flex items-center space-x-3 p-3 bg-gray-50 rounded-lg">
              {bindInfo.wechatInfo.avatarUrl ? (
                <img
                  src={bindInfo.wechatInfo.avatarUrl}
                  alt={bindInfo.wechatInfo.nickname || '微信用户'}
                  className="w-10 h-10 rounded-full object-cover"
                />
              ) : (
                <div className="w-10 h-10 rounded-full bg-gray-200 flex items-center justify-center">
                  <span className={config.color}>{config.icon}</span>
                </div>
              )}
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-gray-900 truncate">
                  {bindInfo.wechatInfo.nickname || '微信用户'}
                </p>
                <p className="text-xs text-gray-500">
                  绑定时间：{bindInfo.boundAt ? new Date(bindInfo.boundAt).toLocaleString('zh-CN') : '-'}
                </p>
              </div>
            </div>
          )}

          {/* 操作按钮 */}
          <div className="mt-4 flex items-center justify-end space-x-3">
            {isConfirmingUnbind ? (
              <>
                <span className="text-sm text-gray-500">
                  确认解绑？
                </span>
                <button
                  onClick={() => setIsConfirmingUnbind(false)}
                  className="px-3 py-1.5 text-sm text-gray-600 hover:text-gray-800 transition-colors"
                >
                  取消
                </button>
                <button
                  onClick={handleUnbind}
                  disabled={unbindMutation.isPending}
                  className="px-4 py-1.5 text-sm font-medium text-white bg-red-600 rounded-md hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {unbindMutation.isPending ? (
                    <span className="flex items-center">
                      <LoaderIcon />
                      <span className="ml-1">解绑中...</span>
                    </span>
                  ) : (
                    '确认解绑'
                  )}
                </button>
              </>
            ) : (
              <>
                {isBound ? (
                  <button
                    onClick={() => setIsConfirmingUnbind(true)}
                    className="px-4 py-2 text-sm font-medium text-red-600 border border-red-300 rounded-md hover:bg-red-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500 transition-colors"
                  >
                    解绑
                  </button>
                ) : (
                  <button
                    onClick={handleBind}
                    disabled={bindMutation.isPending || isPending}
                    className="px-4 py-2 text-sm font-medium text-white bg-green-600 rounded-md hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                  >
                    {bindMutation.isPending ? (
                      <span className="flex items-center">
                        <LoaderIcon />
                        <span className="ml-1">绑定中...</span>
                      </span>
                    ) : (
                      '立即绑定'
                    )}
                  </button>
                )}
              </>
            )}
          </div>

          {/* 错误提示 */}
          {(bindMutation.error || unbindMutation.error) && (
            <div className="mt-3 p-3 bg-red-50 border border-red-200 rounded-md">
              <p className="text-sm text-red-600">
                {bindMutation.error?.message || unbindMutation.error?.message}
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}