/**
 * LawyerOnlineStatus 组件 - 律师在线状态
 */

import { useLawyerOnlineStatus, useLawyersOnlineStatus } from '../hooks/useLawyerMatching';
import type { LawyerStatus } from '../types';

interface OnlineStatusIndicatorProps {
  status: LawyerStatus;
  size?: 'sm' | 'md' | 'lg';
  showLabel?: boolean;
}

const STATUS_CONFIG: Record<
  LawyerStatus,
  { color: string; bgColor: string; label: string; pulse: boolean }
> = {
  online: {
    color: 'bg-green-500',
    bgColor: 'bg-green-100',
    label: '在线',
    pulse: true,
  },
  offline: {
    color: 'bg-gray-400',
    bgColor: 'bg-gray-100',
    label: '离线',
    pulse: false,
  },
  busy: {
    color: 'bg-yellow-500',
    bgColor: 'bg-yellow-100',
    label: '忙碌',
    pulse: false,
  },
};

function OnlineStatusIndicator({
  status,
  size = 'md',
  showLabel = false,
}: OnlineStatusIndicatorProps): JSX.Element {
  const config = STATUS_CONFIG[status];
  
  const sizeClasses = {
    sm: 'h-2 w-2',
    md: 'h-3 w-3',
    lg: 'h-4 w-4',
  };

  const dotSize = sizeClasses[size];

  return (
    <div className="flex items-center gap-1.5">
      <span className="relative flex">
        <span
          className={`relative inline-flex rounded-full ${config.color} ${dotSize} ${
            config.pulse ? 'animate-pulse' : ''
          }`}
        />
        {config.pulse && (
          <span
            className={`absolute inline-flex h-full w-full animate-ping rounded-full ${config.color} opacity-75`}
          />
        )}
      </span>
      {showLabel && (
        <span className={`text-sm font-medium ${config.color.replace('bg-', 'text-')}`}>
          {config.label}
        </span>
      )}
    </div>
  );
}

interface LawyerOnlineStatusProps {
  lawyerId: string;
  size?: 'sm' | 'md' | 'lg';
  showLabel?: boolean;
  showWaitTime?: boolean;
}

export function LawyerOnlineStatus({
  lawyerId,
  size = 'md',
  showLabel = false,
  showWaitTime = false,
}: LawyerOnlineStatusProps): JSX.Element {
  const { data: onlineInfo, isLoading } = useLawyerOnlineStatus(lawyerId);

  if (isLoading || !onlineInfo) {
    return (
      <div className="flex items-center gap-1.5">
        <span className={`inline-flex rounded-full bg-gray-200 ${size === 'sm' ? 'h-2 w-2' : size === 'lg' ? 'h-4 w-4' : 'h-3 w-3'}`} />
        {showLabel && <span className="text-sm text-gray-400">加载中...</span>}
      </div>
    );
  }

  const status = onlineInfo.status;

  return (
    <div className="flex items-center gap-2">
      <OnlineStatusIndicator status={status} size={size} showLabel={showLabel} />
      {showWaitTime && onlineInfo.estimatedWaitTime && onlineInfo.estimatedWaitTime > 0 && (
        <span className="text-xs text-gray-500">
          预计等待 {onlineInfo.estimatedWaitTime} 分钟
        </span>
      )}
    </div>
  );
}

interface LawyerOnlineStatusListProps {
  lawyerIds: string[];
  showWaitTime?: boolean;
}

export function LawyerOnlineStatusList({
  lawyerIds,
  showWaitTime: _showWaitTime = false,
}: LawyerOnlineStatusListProps): JSX.Element {
  const { data: onlineInfos, isLoading } = useLawyersOnlineStatus(lawyerIds);

  if (isLoading || !onlineInfos) {
    return <div className="text-sm text-gray-400">加载中...</div>;
  }

  const onlineCount = onlineInfos.filter((info) => info.status === 'online').length;
  const busyCount = onlineInfos.filter((info) => info.status === 'busy').length;

  return (
    <div className="flex items-center gap-4 text-sm">
      <div className="flex items-center gap-1.5">
        <span className="relative flex h-2 w-2">
          <span className="relative inline-flex h-2 w-2 rounded-full bg-green-500 animate-pulse" />
          <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-green-500 opacity-75" />
        </span>
        <span className="text-green-600">{onlineCount} 在线</span>
      </div>
      {busyCount > 0 && (
        <div className="flex items-center gap-1.5">
          <span className="inline-flex h-2 w-2 rounded-full bg-yellow-500" />
          <span className="text-yellow-600">{busyCount} 忙碌</span>
        </div>
      )}
      <div className="flex items-center gap-1.5">
        <span className="inline-flex h-2 w-2 rounded-full bg-gray-400" />
        <span className="text-gray-500">
          {lawyerIds.length - onlineCount - busyCount} 离线
        </span>
      </div>
    </div>
  );
}

interface LawyerOnlineBadgeProps {
  lawyerId: string;
  size?: 'sm' | 'md' | 'lg';
}

export function LawyerOnlineBadge({ lawyerId, size = 'md' }: LawyerOnlineBadgeProps): JSX.Element {
  const { data: onlineInfo } = useLawyerOnlineStatus(lawyerId);

  const config = onlineInfo ? STATUS_CONFIG[onlineInfo.status] : STATUS_CONFIG.offline;

  const sizeClasses = {
    sm: 'h-2.5 w-2.5',
    md: 'h-3 w-3',
    lg: 'h-4 w-4',
  };

  return (
    <span
      className={`inline-flex rounded-full border-2 border-white ${config.color} ${sizeClasses[size]}`}
      title={config.label}
    />
  );
}

interface LawyerOnlineStatusCardProps {
  lawyerId: string;
  lawyerName: string;
}

export function LawyerOnlineStatusCard({
  lawyerId,
  lawyerName,
}: LawyerOnlineStatusCardProps): JSX.Element {
  const { data: onlineInfo, isLoading } = useLawyerOnlineStatus(lawyerId);

  if (isLoading || !onlineInfo) {
    return (
      <div className="flex items-center gap-3 rounded-lg border border-gray-200 bg-white p-3">
        <div className="flex h-10 w-10 items-center justify-center rounded-full bg-gray-100">
          <span className="text-lg font-semibold text-gray-400">
            {lawyerName.charAt(0)}
          </span>
        </div>
        <div className="flex-1">
          <p className="font-medium text-gray-900">{lawyerName}</p>
          <p className="text-sm text-gray-400">加载中...</p>
        </div>
      </div>
    );
  }

  const config = STATUS_CONFIG[onlineInfo.status];

  return (
    <div className="flex items-center gap-3 rounded-lg border border-gray-200 bg-white p-3">
      <div className="relative">
        <div className="flex h-10 w-10 items-center justify-center rounded-full bg-blue-100">
          <span className="text-lg font-semibold text-blue-600">
            {lawyerName.charAt(0)}
          </span>
        </div>
        <span
          className={`absolute -bottom-0.5 -right-0.5 h-3 w-3 rounded-full border-2 border-white ${config.color}`}
        />
      </div>
      <div className="flex-1">
        <p className="font-medium text-gray-900">{lawyerName}</p>
        <div className="flex items-center gap-2">
          <span className={`text-sm ${config.color.replace('bg-', 'text-')}`}>
            {config.label}
          </span>
          {onlineInfo.currentConsultationCount && onlineInfo.currentConsultationCount > 0 && (
            <span className="text-xs text-gray-500">
              ({onlineInfo.currentConsultationCount} 个进行中)
            </span>
          )}
        </div>
      </div>
      {onlineInfo.estimatedWaitTime && onlineInfo.estimatedWaitTime > 0 && (
        <div className="text-right">
          <p className="text-xs text-gray-500">预计等待</p>
          <p className="font-semibold text-orange-500">{onlineInfo.estimatedWaitTime} 分</p>
        </div>
      )}
    </div>
  );
}