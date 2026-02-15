/**
 * 分享对话框组件
 * 
 * 允许用户分享AI咨询会话
 */

import { useCallback, useState } from 'react';

import { useCreateShare, copyShareLink, generateShareUrl, formatExpireTime } from '../hooks/useShare';

/** 分享对话框Props */
interface ShareDialogProps {
  /** 会话ID */
  sessionId: string;
  /** 是否打开 */
  isOpen: boolean;
  /** 关闭回调 */
  onClose: () => void;
}

/**
 * 分享对话框组件
 */
export function ShareDialog({ sessionId, isOpen, onClose }: ShareDialogProps): JSX.Element | null {
  const { data, isLoading, error, createShare } = useCreateShare();
  const [copied, setCopied] = useState(false);

  // 创建分享
  const handleCreateShare = useCallback(async () => {
    try {
      await createShare({ sessionId, expiresDays: 7 });
    } catch {
      // 错误已通过hook处理
    }
  }, [sessionId, createShare]);

  // 复制链接
  const handleCopyLink = useCallback(async () => {
    if (!data) return;
    
    const success = await copyShareLink(data.sharePath);
    if (success) {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  }, [data]);

  // 关闭时重置状态
  const handleClose = useCallback(() => {
    setCopied(false);
    onClose();
  }, [onClose]);

  if (!isOpen) return null;

  const shareUrl = data ? generateShareUrl(data.sharePath) : '';
  const expireText = data ? formatExpireTime(data.expiresAt) : '';

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm">
      <div className="w-full max-w-md bg-white rounded-2xl shadow-xl overflow-hidden">
        {/* 头部 */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-100">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-blue-100 rounded-xl flex items-center justify-center">
              <svg 
                className="w-5 h-5 text-blue-600" 
                fill="none" 
                stroke="currentColor" 
                viewBox="0 0 24 24"
              >
                <path 
                  strokeLinecap="round" 
                  strokeLinejoin="round" 
                  strokeWidth={2} 
                  d="M8.684 13.342C8.886 12.938 9 12.482 9 12c0-.482-.114-.938-.316-1.342m0 2.684a3 3 0 110-2.684m0 2.684l6.632 3.316m-6.632-6l6.632-3.316m0 0a3 3 0 105.367-2.684 3 3 0 00-5.367 2.684zm0 9.316a3 3 0 105.368 2.684 3 3 0 00-5.368-2.684z" 
                />
              </svg>
            </div>
            <div>
              <h3 className="text-lg font-semibold text-gray-900">分享会话</h3>
              <p className="text-sm text-gray-500">生成链接分享给他人查看</p>
            </div>
          </div>
          <button
            onClick={handleClose}
            className="p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-lg transition-colors"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* 内容区 */}
        <div className="p-6">
          {!data ? (
            // 初始状态 - 创建分享
            <div className="text-center py-8">
              <div className="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <svg 
                  className="w-8 h-8 text-gray-400" 
                  fill="none" 
                  stroke="currentColor" 
                  viewBox="0 0 24 24"
                >
                  <path 
                    strokeLinecap="round" 
                    strokeLinejoin="round" 
                    strokeWidth={2} 
                    d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" 
                  />
                </svg>
              </div>
              <p className="text-gray-600 mb-6">
                创建分享链接后，其他人可以通过链接查看此会话内容
                <br />
                <span className="text-sm text-gray-400">链接有效期为7天</span>
              </p>
              <button
                onClick={() => { void handleCreateShare(); }}
                disabled={isLoading}
                className="w-full px-6 py-3 bg-blue-600 text-white rounded-xl font-medium
                         hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed
                         transition-colors flex items-center justify-center gap-2"
              >
                {isLoading ? (
                  <>
                    <svg className="w-5 h-5 animate-spin" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                    </svg>
                    <span>创建中...</span>
                  </>
                ) : (
                  <>
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                    </svg>
                    <span>创建分享链接</span>
                  </>
                )}
              </button>
              {error && (
                <p className="mt-4 text-sm text-red-500 flex items-center justify-center gap-1">
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  {error.message}
                </p>
              )}
            </div>
          ) : (
            // 已创建 - 显示链接
            <div className="space-y-4">
              <div className="p-4 bg-blue-50 border border-blue-100 rounded-xl">
                <div className="flex items-center gap-2 mb-2">
                  <svg className="w-5 h-5 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  <span className="font-medium text-blue-900">分享链接已创建</span>
                </div>
                <p className="text-sm text-blue-700">{expireText}</p>
              </div>

              {/* 链接显示 */}
              <div className="relative">
                <input
                  type="text"
                  value={shareUrl}
                  readOnly
                  className="w-full px-4 py-3 pr-24 bg-gray-50 border border-gray-200 rounded-xl
                           text-sm text-gray-700 focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
                <button
                  onClick={() => { void handleCopyLink(); }}
                  className="absolute right-2 top-1/2 -translate-y-1/2 px-3 py-1.5
                           bg-white border border-gray-200 text-gray-700 rounded-lg
                           text-sm font-medium hover:bg-gray-50 hover:border-gray-300
                           transition-colors flex items-center gap-1"
                >
                  {copied ? (
                    <>
                      <svg className="w-4 h-4 text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                      </svg>
                      <span>已复制</span>
                    </>
                  ) : (
                    <>
                      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
                      </svg>
                      <span>复制</span>
                    </>
                  )}
                </button>
              </div>

              {/* 分享选项 */}
              <div className="grid grid-cols-3 gap-3 pt-2">
                <button
                  onClick={() => {
                    void navigator.share?.({
                      title: 'AI法律咨询会话分享',
                      text: '查看我的AI法律咨询会话',
                      url: shareUrl,
                    }).catch(() => {
                      // 用户取消或不支持
                    });
                  }}
                  className="flex flex-col items-center gap-2 p-3 rounded-xl border border-gray-200
                           hover:border-blue-300 hover:bg-blue-50 transition-colors"
                >
                  <div className="w-10 h-10 bg-green-100 rounded-full flex items-center justify-center">
                    <svg className="w-5 h-5 text-green-600" fill="currentColor" viewBox="0 0 24 24">
                      <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-1 17.93c-3.95-.49-7-3.85-7-7.93 0-.62.08-1.21.21-1.79L9 15v1c0 1.1.9 2 2 2v1.93zm6.9-2.54c-.26-.81-1-1.39-1.9-1.39h-1v-3c0-.55-.45-1-1-1H8v-2h2c.55 0 1-.45 1-1V7h2c1.1 0 2-.9 2-2v-.41c2.93 1.19 5 4.06 5 7.41 0 2.08-.8 3.97-2.1 5.39z" />
                    </svg>
                  </div>
                  <span className="text-xs text-gray-600">更多</span>
                </button>
                <button
                  onClick={() => {
                    const text = `查看我的AI法律咨询会话：${shareUrl}`;
                    window.open(`https://service.weibo.com/share/share.php?url=${encodeURIComponent(shareUrl)}&title=${encodeURIComponent(text)}`, '_blank');
                  }}
                  className="flex flex-col items-center gap-2 p-3 rounded-xl border border-gray-200
                           hover:border-red-300 hover:bg-red-50 transition-colors"
                >
                  <div className="w-10 h-10 bg-red-100 rounded-full flex items-center justify-center">
                    <svg className="w-5 h-5 text-red-600" fill="currentColor" viewBox="0 0 24 24">
                      <path d="M10.098 20c-4.612 0-8.598-2.244-8.598-5.7 0-1.92 1.09-4.128 2.94-6.228 2.47-2.808 5.352-4.072 6.432-2.822.48.55.428 1.456-.11 2.538-.264.514.144.59.144.59 1.452-.374 2.738-.322 3.896.154 0 0-.066-.638-.352-.724-.396-.122-.67-.528-.586-.932.086-.41.484-.646.884-.57.922.182 2.024.72 2.024 2.338 0 .182-.01.358-.034.528.692.396 1.16 1.144 1.16 2.002 0 3.138-3.586 5.826-7.804 5.826zM6.658 16.464c.22.44.704.726 1.232.726.528 0 1.012-.286 1.232-.726.11-.22.066-.484-.11-.66-.176-.176-.44-.22-.66-.11-.132.066-.286.066-.418 0-.22-.11-.484-.066-.66.11-.176.176-.22.44-.11.66zm3.036-2.2c.22.44.704.726 1.232.726.528 0 1.012-.286 1.232-.726.11-.22.066-.484-.11-.66-.176-.176-.44-.22-.66-.11-.132.066-.286.066-.418 0-.22-.11-.484-.066-.66.11-.176.176-.22.44-.11.66zm3.74 1.32c.22.44.704.726 1.232.726.528 0 1.012-.286 1.232-.726.11-.22.066-.484-.11-.66-.176-.176-.44-.22-.66-.11-.132.066-.286.066-.418 0-.22-.11-.484-.066-.66.11-.176.176-.22.44-.11.66z" />
                    </svg>
                  </div>
                  <span className="text-xs text-gray-600">微博</span>
                </button>
                <button
                  onClick={() => {
                    const text = `查看我的AI法律咨询会话：${shareUrl}`;
                    window.open(`https://connect.qq.com/widget/shareqq/index.html?url=${encodeURIComponent(shareUrl)}&title=${encodeURIComponent(text)}`, '_blank');
                  }}
                  className="flex flex-col items-center gap-2 p-3 rounded-xl border border-gray-200
                           hover:border-blue-300 hover:bg-blue-50 transition-colors"
                >
                  <div className="w-10 h-10 bg-blue-100 rounded-full flex items-center justify-center">
                    <svg className="w-5 h-5 text-blue-600" fill="currentColor" viewBox="0 0 24 24">
                      <path d="M12.003 2c-2.265 0-6.29 1.364-6.29 7.325v1.195S3.55 14.96 3.55 17.474c0 .665.17 1.025.281 1.025.114 0 .902-.484 1.748-2.072 0 0-.18 2.197 1.904 3.967 0 0-1.77.495-1.77 1.182 0 .686 4.078.43 6.29.43 2.21 0 6.288.256 6.288-.43 0-.687-1.768-1.182-1.768-1.182 2.085-1.77 1.905-3.967 1.905-3.967.845 1.588 1.634 2.072 1.746 2.072.111 0 .283-.36.283-1.025 0-2.514-2.166-6.954-2.166-6.954V9.325C18.29 3.364 14.268 2 12.003 2z" />
                    </svg>
                  </div>
                  <span className="text-xs text-gray-600">QQ</span>
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}