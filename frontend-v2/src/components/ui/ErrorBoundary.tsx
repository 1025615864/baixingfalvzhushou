/**
 * ErrorBoundary - 错误边界组件
 *
 * 捕获渲染错误，提供优雅的错误处理界面
 */

import { logger } from '@/shared/lib/logger';
/* eslint-disable react-refresh/only-export-components */

import React, { Component, type ErrorInfo, type ReactNode } from 'react';

import { ErrorFallback, type ErrorFallbackProps } from './ErrorFallback';

/**
 * 错误边界属性
 */
export interface ErrorBoundaryProps {
  /** 子组件 */
  children: ReactNode;
  /** 自定义错误回退UI */
  fallback?: ReactNode | ((error: Error, reset: () => void) => ReactNode);
  /** 错误回退组件属性（使用默认fallback时） */
  fallbackProps?: Partial<Omit<ErrorFallbackProps, 'error' | 'onReset'>>;
  /** 错误捕获回调 */
  onError?: (error: Error, errorInfo: ErrorInfo) => void;
  /** 错误重置回调 */
  onReset?: () => void;
  /** 自定义重置逻辑 */
  resetKeys?: Array<string | number>;
}

/**
 * 错误边界状态
 */
interface ErrorBoundaryState {
  hasError: boolean;
  error: Error | null;
}

/**
 * 错误边界组件
 *
 * @example
 * ```tsx
 * // 基本使用
 * <ErrorBoundary>
 *   <MyComponent />
 * </ErrorBoundary>
 *
 * // 自定义错误UI
 * <ErrorBoundary
 *   fallback={(error, reset) => (
 *     <div>
 *       <p>出错了: {error.message}</p>
 *       <button onClick={reset}>重试</button>
 *     </div>
 *   )}
 * >
 *   <MyComponent />
 * </ErrorBoundary>
 *
 * // 使用 resetKeys
 * <ErrorBoundary resetKeys={[userId]}>
 *   <UserProfile userId={userId} />
 * </ErrorBoundary>
 * ```
 */
export class ErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
  private resetTimeoutId: ReturnType<typeof setTimeout> | null = null;
  private prevResetKeys: Array<string | number> = [];

  constructor(props: ErrorBoundaryProps) {
    super(props);
    this.state = {
      hasError: false,
      error: null,
    };
  }

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return {
      hasError: true,
      error,
    };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo): void {
    // 调用错误回调
    this.props.onError?.(error, errorInfo);

    // 可以在这里添加错误上报逻辑
    this.reportError(error, errorInfo);
  }

  componentDidUpdate(_prevProps: ErrorBoundaryProps): void {
    const { resetKeys } = this.props;
    const { hasError } = this.state;

    // 检查 resetKeys 是否变化
    if (hasError && resetKeys) {
      const hasResetKeyChanged = resetKeys.some(
        (key, index) => key !== this.prevResetKeys[index]
      );

      if (hasResetKeyChanged) {
        this.handleReset();
      }
    }

    this.prevResetKeys = resetKeys || [];
  }

  componentWillUnmount(): void {
    // 清理定时器
    if (this.resetTimeoutId) {
      clearTimeout(this.resetTimeoutId);
    }
  }

  /**
   * 上报错误（可以扩展为发送到监控服务）
   */
  private reportError(error: Error, errorInfo: ErrorInfo): void {
    // 在开发环境下输出到控制台
    if (process.env.NODE_ENV === 'development') {
      logger.error('ErrorBoundary caught an error:', error);
      logger.error('Component stack:', errorInfo.componentStack);
    }

    // TODO: 可以在这里集成 Sentry、LogRocket 等监控服务
    // 示例：
    // if (typeof window !== 'undefined' && window.Sentry) {
    //   window.Sentry.captureException(error, {
    //     contexts: {
    //       react: {
    //         componentStack: errorInfo.componentStack,
    //       },
    //     },
    //   });
    // }
  }

  /**
   * 重置错误状态
   */
  private handleReset = (): void => {
    const { onReset } = this.props;

    this.setState({
      hasError: false,
      error: null,
    });

    onReset?.();
  };

  /**
   * 渲染错误回退UI
   */
  private renderFallback(): ReactNode {
    const { fallback, fallbackProps } = this.props;
    const { error } = this.state;

    if (!error) return null;

    // 使用自定义 fallback
    if (fallback) {
      if (typeof fallback === 'function') {
        return fallback(error, this.handleReset);
      }
      return fallback;
    }

    // 使用默认 ErrorFallback
    return (
      <ErrorFallback
        error={error}
        onReset={this.handleReset}
        {...fallbackProps}
      />
    );
  }

  render(): ReactNode {
    const { hasError } = this.state;
    const { children } = this.props;

    if (hasError) {
      return this.renderFallback();
    }

    return children;
  }
}

/**
 * 高阶组件 - 为组件添加错误边界
 */
export function withErrorBoundary<P extends object>(
  Component: React.ComponentType<P>,
  errorBoundaryProps?: Omit<ErrorBoundaryProps, 'children'>
): React.FC<P> {
  const WrappedComponent: React.FC<P> = (props) => (
    <ErrorBoundary {...errorBoundaryProps}>
      <Component {...props} />
    </ErrorBoundary>
  );

  WrappedComponent.displayName = `withErrorBoundary(${Component.displayName || Component.name})`;

  return WrappedComponent;
}

export default ErrorBoundary;