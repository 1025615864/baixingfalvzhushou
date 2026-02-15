// ============================================
// 连接状态指示器组件
// ============================================

import { WebSocketConnectionState } from '../types/websocket';

export interface ConnectionStatusProps {
  /** 连接状态 */
  state: WebSocketConnectionState;
  /** 延迟（毫秒） */
  latency?: number;
  /** 重连次数 */
  reconnectAttempts?: number;
  /** 是否显示标签 */
  showLabel?: boolean;
  /** 是否显示延迟 */
  showLatency?: boolean;
  /** 自定义类名 */
  className?: string;
  /** 尺寸 */
  size?: 'sm' | 'md' | 'lg';
  /** 点击重连 */
  onReconnect?: () => void;
}

/**
 * 状态配置
 */
const stateConfig: Record<string, {
  label: string;
  color: string;
  bgColor: string;
  animate: boolean;
  icon: JSX.Element;
}> = {
  connecting: {
    label: '连接中',
    color: 'text-yellow-600',
    bgColor: 'bg-yellow-500',
    animate: true,
    icon: (
      <svg className="h-4 w-4 animate-spin" fill="none" viewBox="0 0 24 24">
        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
      </svg>
    ),
  },
  connected: {
    label: '已连接',
    color: 'text-green-600',
    bgColor: 'bg-green-500',
    animate: false,
    icon: (
      <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
      </svg>
    ),
  },
  disconnected: {
    label: '已断开',
    color: 'text-gray-500',
    bgColor: 'bg-gray-400',
    animate: false,
    icon: (
      <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
      </svg>
    ),
  },
  reconnecting: {
    label: '重连中',
    color: 'text-orange-600',
    bgColor: 'bg-orange-500',
    animate: true,
    icon: (
      <svg className="h-4 w-4 animate-spin" fill="none" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
      </svg>
    ),
  },
  error: {
    label: '连接错误',
    color: 'text-red-600',
    bgColor: 'bg-red-500',
    animate: false,
    icon: (
      <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
      </svg>
    ),
  },
};

/**
 * 格式化延迟
 */
function formatLatency(latency: number): string {
  if (latency < 100) return `${latency}ms`;
  if (latency < 1000) return `${latency}ms`;
  return `${(latency / 1000).toFixed(1)}s`;
}

/**
 * 连接状态指示器组件
 */
export function ConnectionStatus({
  state,
  latency,
  reconnectAttempts,
  showLabel = true,
  showLatency = true,
  className = '',
  size = 'md',
  onReconnect,
}: ConnectionStatusProps): JSX.Element {
  const config = stateConfig[state as string];
  
  const sizeConfig = {
    sm: {
      dot: 'w-2 h-2',
      text: 'text-xs',
      gap: 'gap-1',
    },
    md: {
      dot: 'w-2.5 h-2.5',
      text: 'text-sm',
      gap: 'gap-1.5',
    },
    lg: {
      dot: 'w-3 h-3',
      text: 'text-base',
      gap: 'gap-2',
    },
  };

  const s = sizeConfig[size];

  const handleClick = (): void => {
    if ((state === WebSocketConnectionState.DISCONNECTED || state === WebSocketConnectionState.ERROR) && onReconnect) {
      onReconnect();
    }
  };

  const isClickable = (state === WebSocketConnectionState.DISCONNECTED || state === WebSocketConnectionState.ERROR) && onReconnect;

  return (
    <div
      className={`
        inline-flex items-center ${s.gap}
        ${isClickable ? 'cursor-pointer hover:opacity-80' : ''}
        ${className}
      `}
      onClick={handleClick}
      role="status"
      aria-live="polite"
      aria-label={`连接状态: ${config.label}${latency ? `，延迟 ${formatLatency(latency)}` : ''}`}
    >
      {/* 状态指示灯 */}
      <span className="relative flex">
        {/* 基础圆点 */}
        <span
          className={`
            relative inline-flex rounded-full
            ${config.bgColor}
            ${s.dot}
            ${config.animate ? 'animate-pulse' : ''}
          `}
        />
        
        {/* 脉冲动画（仅连接时） */}
        {state === WebSocketConnectionState.CONNECTED && (
          <span
            className={`
              absolute inline-flex h-full w-full animate-ping rounded-full
              ${config.bgColor} opacity-75
            `}
          />
        )}
      </span>

      {/* 状态标签 */}
      {showLabel && (
        <span className={`${s.text} font-medium ${config.color}`}>
          {config.label}
          {state === WebSocketConnectionState.RECONNECTING && reconnectAttempts !== undefined && (
            <span className="ml-1 text-xs opacity-70">
              ({reconnectAttempts})
            </span>
          )}
        </span>
      )}

      {/* 延迟显示 */}
      {showLatency && latency !== undefined && state === WebSocketConnectionState.CONNECTED && (
        <span
          className={`
            ${s.text} rounded px-1.5 py-0.5 font-mono
            ${latency < 100 ? 'bg-green-100 text-green-700' :
              latency < 300 ? 'bg-yellow-100 text-yellow-700' :
              'bg-red-100 text-red-700'}
          `}
          title="网络延迟"
        >
          {formatLatency(latency)}
        </span>
      )}

      {/* 重连提示 */}
      {isClickable && (
        <span className={`${s.text} text-blue-600 hover:underline`}>
          点击重连
        </span>
      )}
    </div>
  );
}

/**
 * 简化版连接状态指示器（仅显示圆点）
 */
export function ConnectionStatusDot({
  state,
  className = '',
  size = 'md',
}: {
  state: WebSocketConnectionState;
  className?: string;
  size?: 'sm' | 'md' | 'lg';
}): JSX.Element {
  const config = stateConfig[state as string];
  
  const sizeClasses = {
    sm: 'w-2 h-2',
    md: 'w-2.5 h-2.5',
    lg: 'w-3 h-3',
  };

  return (
    <span
      className={`
        relative inline-flex rounded-full
        ${config.bgColor}
        ${sizeClasses[size]}
        ${config.animate ? 'animate-pulse' : ''}
        ${className}
      `}
      title={config.label}
      role="status"
      aria-label={config.label}
    >
      {state === WebSocketConnectionState.CONNECTED && (
        <span
          className={`
            absolute inline-flex h-full w-full animate-ping rounded-full
            ${config.bgColor} opacity-75
          `}
        />
      )}
    </span>
  );
}

/**
 * 连接状态卡片（详细信息）
 */
export function ConnectionStatusCard({
  state,
  latency,
  reconnectAttempts,
  queueLength,
  lastConnectedAt,
  lastDisconnectedAt,
  onReconnect,
}: {
  state: WebSocketConnectionState;
  latency?: number;
  reconnectAttempts: number;
  queueLength: number;
  lastConnectedAt?: Date;
  lastDisconnectedAt?: Date;
  onReconnect?: () => void;
}): JSX.Element {
  const config = stateConfig[state as string];

  return (
    <div className="rounded-lg border border-gray-200 bg-white p-4 shadow-sm">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <span className={`rounded-full p-2 ${config.bgColor} bg-opacity-20`}>
            <span className={config.color}>{config.icon}</span>
          </span>
          <div>
            <h3 className="font-medium text-gray-900">{config.label}</h3>
            {state === WebSocketConnectionState.CONNECTED && latency !== undefined && (
              <p className="text-sm text-gray-500">
                延迟: {formatLatency(latency)}
              </p>
            )}
            {state === WebSocketConnectionState.RECONNECTING && (
              <p className="text-sm text-gray-500">
                第 {reconnectAttempts} 次重连
              </p>
            )}
          </div>
        </div>
        
        {(state === WebSocketConnectionState.DISCONNECTED || state === WebSocketConnectionState.ERROR) && onReconnect && (
          <button
            type="button"
            onClick={onReconnect}
            className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
          >
            重新连接
          </button>
        )}
      </div>

      {/* 详细信息 */}
      <div className="mt-4 space-y-2 text-sm text-gray-600">
        {lastConnectedAt && (
          <div className="flex justify-between">
            <span>最后连接:</span>
            <span>{lastConnectedAt.toLocaleString('zh-CN')}</span>
          </div>
        )}
        {lastDisconnectedAt && (
          <div className="flex justify-between">
            <span>最后断开:</span>
            <span>{lastDisconnectedAt.toLocaleString('zh-CN')}</span>
          </div>
        )}
        {queueLength > 0 && (
          <div className="flex justify-between">
            <span>待发送消息:</span>
            <span className="font-medium text-orange-600">{queueLength}</span>
          </div>
        )}
      </div>
    </div>
  );
}

export default ConnectionStatus;