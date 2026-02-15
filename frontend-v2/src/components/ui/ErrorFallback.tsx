/**
 * ErrorFallback - 错误回退UI组件
 *
 * 在错误边界捕获错误时显示的UI界面
 */

import React from 'react';

/**
 * 错误回退组件属性
 */
export interface ErrorFallbackProps {
  /** 错误对象 */
  error: Error;
  /** 重置错误回调 */
  onReset?: () => void;
  /** 自定义类名 */
  className?: string;
  /** 是否支持上报 */
  showReport?: boolean;
  /** 上报回调 */
  onReport?: (error: Error) => void;
  /** 标题 */
  title?: string;
  /** 描述 */
  description?: string;
}

/**
 * 错误回退UI组件
 *
 * @example
 * ```tsx
 * // 基本使用
 * <ErrorFallback error={error} onReset={() => window.location.reload()} />
 *
 * // 支持错误上报
 * <ErrorFallback
 *   error={error}
 *   onReset={handleReset}
 *   showReport
 *   onReport={(err) => reportError(err)}
 * />
 * ```
 */
export function ErrorFallback({
  error,
  onReset,
  className = '',
  showReport = true,
  onReport,
  title = '页面出错了',
  description = '抱歉，页面加载过程中发生了错误。请尝试刷新页面或返回首页。',
}: ErrorFallbackProps): JSX.Element {
  const [isReporting, setIsReporting] = React.useState(false);
  const [reported, setReported] = React.useState(false);

  /**
   * 处理错误上报
   */
  const handleReport = (): void => {
    if (!onReport || reported) return;
  
    setIsReporting(true);
    void Promise.resolve(onReport(error)).finally(() => {
      setIsReporting(false);
      setReported(true);
    });
  };

  /**
   * 获取友好的错误信息
   */
  const getFriendlyErrorMessage = (err: Error): string => {
    // 可以根据错误类型返回不同的提示
    if (err.message?.includes('network') || err.message?.includes('fetch')) {
      return '网络连接失败，请检查您的网络设置';
    }
    if (err.message?.includes('timeout')) {
      return '请求超时，请稍后重试';
    }
    if (err.message?.includes('permission') || err.message?.includes('unauthorized')) {
      return '权限不足，请确认您有权限访问此页面';
    }
    return err.message || '未知错误';
  };

  return (
    <div
      className={`
        flex flex-col items-center justify-center
        min-h-[300px] p-8
        text-center
        ${className}
      `}
    >
      {/* 错误图标 */}
      <div className="w-20 h-20 mb-6 text-red-500">
        <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={1.5}
            d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
          />
        </svg>
      </div>

      {/* 标题 */}
      <h2 className="text-xl font-bold text-gray-900 dark:text-gray-100 mb-2">{title}</h2>

      {/* 描述 */}
      <p className="text-gray-500 dark:text-gray-400 max-w-md mb-4">{description}</p>

      {/* 错误详情（可展开） */}
      <div className="w-full max-w-lg mb-6">
        <details className="group">
          <summary className="flex items-center justify-center gap-2 text-sm text-gray-500 hover:text-gray-700 cursor-pointer dark:text-gray-400 dark:hover:text-gray-300">
            <span>查看错误详情</span>
            <svg
              className="w-4 h-4 transition-transform group-open:rotate-180"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
            </svg>
          </summary>
          <div className="mt-3 p-4 bg-gray-50 dark:bg-gray-800 rounded-lg text-left">
            <p className="text-sm text-red-600 dark:text-red-400 mb-2">
              {getFriendlyErrorMessage(error)}
            </p>
            {error.stack && (
              <pre className="text-xs text-gray-600 dark:text-gray-400 overflow-x-auto whitespace-pre-wrap break-all">
                {error.stack}
              </pre>
            )}
          </div>
        </details>
      </div>

      {/* 操作按钮 */}
      <div className="flex flex-wrap items-center justify-center gap-3">
        {onReset && (
          <button
            onClick={onReset}
            className={`
              flex items-center gap-2
              px-6 py-2.5
              text-sm font-medium text-white
              bg-blue-600 rounded-lg
              hover:bg-blue-700
              focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2
              transition-colors
              dark:focus:ring-offset-gray-900
            `}
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
              />
            </svg>
            重试
          </button>
        )}

        <button
          onClick={() => window.location.reload()}
          className={`
            flex items-center gap-2
            px-6 py-2.5
            text-sm font-medium text-gray-700
            bg-white border border-gray-300 rounded-lg
            hover:bg-gray-50
            focus:outline-none focus:ring-2 focus:ring-gray-500 focus:ring-offset-2
            transition-colors
            dark:bg-gray-800 dark:text-gray-300 dark:border-gray-600 dark:hover:bg-gray-700
            dark:focus:ring-offset-gray-900
          `}
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
            />
          </svg>
          刷新页面
        </button>

        <a
          href="/"
          className={`
            flex items-center gap-2
            px-6 py-2.5
            text-sm font-medium text-gray-700
            bg-white border border-gray-300 rounded-lg
            hover:bg-gray-50
            focus:outline-none focus:ring-2 focus:ring-gray-500 focus:ring-offset-2
            transition-colors
            dark:bg-gray-800 dark:text-gray-300 dark:border-gray-600 dark:hover:bg-gray-700
            dark:focus:ring-offset-gray-900
          `}
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6"
            />
          </svg>
          返回首页
        </a>

        {/* 上报按钮 */}
        {showReport && onReport && (
          <button
            onClick={handleReport}
            disabled={isReporting || reported}
            className={`
              flex items-center gap-2
              px-6 py-2.5
              text-sm font-medium
              rounded-lg
              transition-colors
              ${
                reported
                  ? 'text-green-700 bg-green-50 dark:text-green-300 dark:bg-green-900/30'
                  : 'text-gray-700 bg-white border border-gray-300 hover:bg-gray-50 dark:bg-gray-800 dark:text-gray-300 dark:border-gray-600 dark:hover:bg-gray-700'
              }
              disabled:opacity-50 disabled:cursor-not-allowed
            `}
          >
            {isReporting ? (
              <>
                <svg className="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                  <path
                    className="opacity-75"
                    fill="currentColor"
                    d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                  />
                </svg>
                上报中...
              </>
            ) : reported ? (
              <>
                <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                  <path
                    fillRule="evenodd"
                    d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
                    clipRule="evenodd"
                  />
                </svg>
                已上报
              </>
            ) : (
              <>
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
                  />
                </svg>
                上报错误
              </>
            )}
          </button>
        )}
      </div>
    </div>
  );
}

export default ErrorFallback;