/**
 * WechatShareDialog - 微信分享弹窗组件
 * 支持分享到朋友圈、好友等
 */

import { useState, useCallback, useMemo } from 'react';

import type { WechatShareType, WechatShareConfig } from '../types';
import { useShareConfig, useWechatShare } from '../hooks/useWechat';

interface WechatShareDialogProps {
  /** 分享链接 */
  url: string;
  /** 自定义分享配置 */
  shareConfig?: Partial<WechatShareConfig>;
  /** 是否显示弹窗 */
  isOpen: boolean;
  /** 关闭弹窗回调 */
  onClose: () => void;
  /** 分享成功回调 */
  onShareSuccess?: (shareType: WechatShareType) => void;
}

interface ShareOption {
  type: WechatShareType;
  label: string;
  icon: JSX.Element;
  color: string;
}

/**
 * 关闭图标组件
 */
function CloseIcon(): JSX.Element {
  return (
    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
    </svg>
  );
}

/**
 * 链接图标组件
 */
function LinkIcon(): JSX.Element {
  return (
    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" />
    </svg>
  );
}

/**
 * 成功图标组件
 */
function SuccessIcon(): JSX.Element {
  return (
    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
    </svg>
  );
}

/**
 * 微信分享弹窗组件
 */
export function WechatShareDialog({
  url,
  shareConfig,
  isOpen,
  onClose,
  onShareSuccess,
}: WechatShareDialogProps): JSX.Element | null {
  const [copied, setCopied] = useState(false);
  const [sharingType, setSharingType] = useState<WechatShareType | null>(null);
  
  const { data: configData, isLoading } = useShareConfig(url);
  const { share, isSharing } = useWechatShare();

  // 合并配置
  const config: WechatShareConfig = useMemo(() => ({
    title: shareConfig?.title || configData?.title || '分享到微信',
    description: shareConfig?.description || configData?.description || '',
    link: shareConfig?.link || configData?.link || url,
    imgUrl: shareConfig?.imgUrl || configData?.imgUrl,
    type: shareConfig?.type || configData?.type,
  }), [shareConfig, configData, url]);

  const shareOptions: ShareOption[] = [
    {
      type: 'timeline',
      label: '朋友圈',
      icon: (
        <svg className="w-8 h-8" viewBox="0 0 24 24" fill="currentColor">
          <circle cx="12" cy="12" r="3" />
          <circle cx="6" cy="12" r="2" />
          <circle cx="18" cy="12" r="2" />
          <circle cx="12" cy="6" r="2" />
          <circle cx="12" cy="18" r="2" />
        </svg>
      ),
      color: 'bg-green-500 hover:bg-green-600',
    },
    {
      type: 'session',
      label: '微信好友',
      icon: (
        <svg className="w-8 h-8" viewBox="0 0 24 24" fill="currentColor">
          <path d="M8.691 2.188C3.891 2.188 0 5.476 0 9.53c0 2.212 1.17 4.203 3.002 5.55a.59.59 0 0 1 .213.665l-.39 1.48c-.019.07-.048.141-.048.213 0 .163.13.295.29.295a.326.326 0 0 0 .167-.054l1.903-1.114a.864.864 0 0 1 .717-.098 10.16 10.16 0 0 0 2.837.403c.276 0 .543-.027.811-.05-.857-2.578.157-4.972 1.932-6.446 1.703-1.415 3.882-1.98 5.853-1.838-.576-3.583-4.196-6.348-8.596-6.348zM5.785 5.991c.642 0 1.162.529 1.162 1.18a1.17 1.17 0 0 1-1.162 1.178A1.17 1.17 0 0 1 4.623 7.17c0-.651.52-1.18 1.162-1.18zm5.813 0c.642 0 1.162.529 1.162 1.18a1.17 1.17 0 0 1-1.162 1.178 1.17 1.17 0 0 1-1.162-1.178c0-.651.52-1.18 1.162-1.18zm5.34 2.867c-1.797-.052-3.746.512-5.28 1.786-1.72 1.428-2.687 3.72-1.78 6.22.942 2.453 3.666 4.229 6.884 4.229.826 0 1.622-.12 2.361-.336a.722.722 0 0 1 .598.082l1.584.926a.272.272 0 0 0 .14.047c.134 0 .24-.111.24-.247 0-.06-.023-.12-.038-.177l-.327-1.233a.582.582 0 0 1-.023-.156.49.49 0 0 1 .201-.398C23.024 18.48 24 16.82 24 14.98c0-3.21-2.931-5.837-6.656-6.088V8.89c-.135-.01-.269-.03-.407-.03zm-2.53 3.274c.535 0 .969.44.969.982a.976.976 0 0 1-.969.983.976.976 0 0 1-.969-.983c0-.542.434-.982.97-.982zm4.844 0c.535 0 .969.44.969.982a.976.976 0 0 1-.969.983.976.976 0 0 1-.969-.983c0-.542.434-.982.969-.982z"/>
        </svg>
      ),
      color: 'bg-green-600 hover:bg-green-700',
    },
    {
      type: 'qq',
      label: 'QQ好友',
      icon: (
        <svg className="w-8 h-8" viewBox="0 0 24 24" fill="currentColor">
          <path d="M12.003 2c-2.265 0-6.29 1.364-6.29 7.325v1.195S3.55 14.96 3.55 17.474c0 .665.17 1.025.281 1.025.114 0 .902-.484 1.748-2.072 0 0-.18 2.197 1.904 3.967 0 0-1.77.495-1.77 1.182 0 .686 4.078.43 6.29.43 2.21 0 6.29.256 6.29-.43 0-.687-1.77-1.182-1.77-1.182 2.085-1.77 1.904-3.967 1.904-3.967.846 1.588 1.634 2.072 1.748 2.072.111 0 .281-.36.281-1.025 0-2.514-2.163-6.954-2.163-6.954V9.325C18.293 3.364 14.268 2 12.003 2z"/>
        </svg>
      ),
      color: 'bg-blue-500 hover:bg-blue-600',
    },
    {
      type: 'weibo',
      label: '新浪微博',
      icon: (
        <svg className="w-8 h-8" viewBox="0 0 24 24" fill="currentColor">
          <path d="M10.098 20.323c-3.977.391-7.414-1.406-7.672-4.02-.259-2.609 2.759-5.047 6.74-5.441 3.979-.394 7.413 1.404 7.671 4.018.259 2.6-2.759 5.049-6.739 5.443zM9.05 17.219c-.384.616-1.208.884-1.829.602-.612-.279-.793-.991-.406-1.593.379-.595 1.176-.861 1.793-.601.622.263.82.972.442 1.592zm1.27-1.627c-.141.237-.449.353-.689.253-.236-.09-.313-.361-.177-.586.138-.227.436-.346.672-.24.239.09.315.36.194.573zm.176-2.719c-1.893-.493-4.033.45-4.857 2.118-.836 1.704-.026 3.591 1.886 4.21 1.983.64 4.318-.341 5.132-2.179.8-1.793-.201-3.642-2.161-4.149zm7.563-1.224c-.346-.105-.579-.18-.401-.649.386-1.031.425-1.922.009-2.557-.781-1.19-2.924-1.126-5.354-.034 0 0-.767.334-.571-.271.376-1.217.32-2.234-.267-2.822-1.331-1.335-4.869.045-7.896 3.08C1.873 10.323.152 12.402.152 14.178c0 3.394 4.353 5.46 8.607 5.46 5.582 0 9.294-3.246 9.294-5.82 0-1.557-1.313-2.438-1.894-2.549zM21.542 5.866c-1.473-1.615-3.648-2.378-5.834-2.156-.584.062-.998.589-.936 1.172.062.585.59.999 1.173.937 1.502-.158 2.978.39 4.002 1.514 1.026 1.122 1.428 2.614 1.137 4.12-.13.667.264 1.267.866 1.398.663.136 1.27-.224 1.4-.886.428-2.24-.15-4.5-1.808-6.099zm-2.751 2.753c-.549-.602-1.367-.884-2.185-.798-.323.035-.558.317-.523.64.035.323.317.559.64.523.44-.046.872.103 1.166.426.294.322.408.752.323 1.152-.069.32.132.637.453.706.32.068.638-.133.706-.453.162-.76-.072-1.532-.58-2.096z"/>
        </svg>
      ),
      color: 'bg-red-500 hover:bg-red-600',
    },
  ];

  /**
   * 处理复制链接
   */
  const handleCopyLink = useCallback((): void => {
    void navigator.clipboard.writeText(config.link).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    });
  }, [config.link]);

  /**
   * 处理分享
   */
  const handleShare = useCallback((type: WechatShareType): void => {
    setSharingType(type);
    const success = share(config, type);
    
    if (success) {
      onShareSuccess?.(type);
    }
  }, [config, share, onShareSuccess]);

  if (!isOpen) {
    return null;
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50 p-4">
      <div className="bg-white rounded-lg shadow-xl max-w-md w-full">
        {/* 头部 */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-200">
          <h3 className="text-lg font-medium text-gray-900">
            分享到
          </h3>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 transition-colors"
          >
            <CloseIcon />
          </button>
        </div>

        {/* 分享选项 */}
        <div className="px-6 py-6">
          {isLoading ? (
            <div className="flex justify-center py-8">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900"></div>
            </div>
          ) : (
            <>
              {/* 分享按钮网格 */}
              <div className="grid grid-cols-4 gap-4">
                {shareOptions.map((option) => (
                  <button
                    key={option.type}
                    onClick={() => handleShare(option.type)}
                    disabled={isSharing && sharingType === option.type}
                    className="flex flex-col items-center space-y-2 group"
                  >
                    <div className={`
                      w-14 h-14 rounded-full flex items-center justify-center text-white
                      transition-transform transform group-hover:scale-110
                      ${option.color}
                      ${isSharing && sharingType === option.type ? 'opacity-50' : ''}
                    `}>
                      {isSharing && sharingType === option.type ? (
                        <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                      ) : (
                        option.icon
                      )}
                    </div>
                    <span className="text-xs text-gray-600">{option.label}</span>
                  </button>
                ))}
              </div>

              {/* 复制链接区域 */}
              <div className="mt-6 pt-6 border-t border-gray-200">
                <div className="flex items-center space-x-3">
                  <div className="flex-1 bg-gray-50 rounded-lg px-3 py-2">
                    <p className="text-sm text-gray-600 truncate">
                      {config.link}
                    </p>
                  </div>
                  <button
                    onClick={handleCopyLink}
                    className={`
                      flex items-center space-x-1 px-4 py-2 rounded-lg text-sm font-medium
                      transition-colors
                      ${copied 
                        ? 'bg-green-100 text-green-700' 
                        : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                      }
                    `}
                  >
                    {copied ? (
                      <>
                        <SuccessIcon />
                        <span>已复制</span>
                      </>
                    ) : (
                      <>
                        <LinkIcon />
                        <span>复制链接</span>
                      </>
                    )}
                  </button>
                </div>
              </div>

              {/* 分享预览 */}
              <div className="mt-6 p-4 bg-gray-50 rounded-lg">
                <div className="flex items-start space-x-3">
                  {config.imgUrl ? (
                    <img 
                      src={config.imgUrl} 
                      alt="" 
                      className="w-16 h-16 rounded-lg object-cover flex-shrink-0"
                    />
                  ) : (
                    <div className="w-16 h-16 rounded-lg bg-gray-200 flex items-center justify-center flex-shrink-0">
                      <span className="text-gray-400 text-xs">无图片</span>
                    </div>
                  )}
                  <div className="flex-1 min-w-0">
                    <h4 className="text-sm font-medium text-gray-900 line-clamp-2">
                      {config.title}
                    </h4>
                    {config.description && (
                      <p className="mt-1 text-xs text-gray-500 line-clamp-2">
                        {config.description}
                      </p>
                    )}
                  </div>
                </div>
              </div>
            </>
          )}
        </div>

        {/* 底部提示 */}
        <div className="px-6 py-3 bg-gray-50 rounded-b-lg">
          <p className="text-xs text-gray-500 text-center">
            分享内容给朋友，让更多人看到
          </p>
        </div>
      </div>
    </div>
  );
}