/**
 * VideoConsultationCard - 视频咨询卡片组件
 * 显示单个视频咨询的详情和操作按钮
 */

import React from 'react';
import {
  Video,
  Calendar,
  Clock,
  User,
  Play,
  XCircle,
  CheckCircle,
  Phone,
} from 'lucide-react';

import { Badge } from '@/components/ui/Badge';
import { Button } from '@/components/ui/Button';

import type { VideoConsultation, VideoConsultationStatus } from '../types';

interface VideoConsultationCardProps {
  consultation: VideoConsultation;
  onClick?: () => void;
  onJoin?: () => void;
  onCancel?: () => void;
  onConfirm?: () => void;
  onStart?: () => void;
  loading?: boolean;
}

// 状态配置
const statusConfig: Record<VideoConsultationStatus, { label: string; variant: 'default' | 'primary' | 'success' | 'warning' | 'danger' }> = {
  pending: { label: '待确认', variant: 'warning' },
  confirmed: { label: '已确认', variant: 'primary' },
  in_progress: { label: '进行中', variant: 'success' },
  completed: { label: '已完成', variant: 'default' },
  cancelled: { label: '已取消', variant: 'danger' },
};

// 类别配置
const categoryConfig: Record<string, string> = {
  civil: '民事咨询',
  criminal: '刑事咨询',
  contract: '合同纠纷',
  labor: '劳动争议',
  family: '婚姻家庭',
  property: '房产纠纷',
  intellectual: '知识产权',
  corporate: '公司法务',
  other: '其他咨询',
};

/**
 * 格式化日期时间
 */
function formatDateTime(dateString: string): string {
  const date = new Date(dateString);
  const now = new Date();
  const isToday = date.toDateString() === now.toDateString();
  const tomorrow = new Date(now);
  tomorrow.setDate(tomorrow.getDate() + 1);
  const isTomorrow = date.toDateString() === tomorrow.toDateString();

  const timeStr = date.toLocaleTimeString('zh-CN', {
    hour: '2-digit',
    minute: '2-digit',
  });

  if (isToday) {
    return `今天 ${timeStr}`;
  }
  if (isTomorrow) {
    return `明天 ${timeStr}`;
  }
  return date.toLocaleDateString('zh-CN', {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
}

/**
 * 格式化时长
 */
function formatDuration(minutes: number): string {
  if (minutes < 60) {
    return `${minutes}分钟`;
  }
  const hours = Math.floor(minutes / 60);
  const mins = minutes % 60;
  return mins > 0 ? `${hours}小时${mins}分钟` : `${hours}小时`;
}

/**
 * 格式化金额
 */
function formatAmount(amount: number, isFree: boolean, discountRate: number): string {
  if (isFree) {
    return '免费';
  }
  if (discountRate < 1) {
    const discountedAmount = amount * discountRate;
    return `¥${discountedAmount.toFixed(0)} (会员${Math.round(discountRate * 10)}折)`;
  }
  return `¥${amount}`;
}

/**
 * 判断是否可以加入会议
 */
function canJoinConsultation(consultation: VideoConsultation): boolean {
  if (consultation.status !== 'confirmed' && consultation.status !== 'in_progress') {
    return false;
  }
  const scheduledTime = new Date(consultation.scheduledTime);
  const now = new Date();
  // 提前10分钟可以加入
  const joinWindow = 10 * 60 * 1000;
  return now.getTime() >= scheduledTime.getTime() - joinWindow;
}

/**
 * 判断是否可以取消
 */
function canCancelConsultation(consultation: VideoConsultation): boolean {
  if (consultation.status === 'cancelled' || consultation.status === 'completed') {
    return false;
  }
  const scheduledTime = new Date(consultation.scheduledTime);
  const now = new Date();
  // 提前1小时可以取消
  const cancelDeadline = 60 * 60 * 1000;
  return scheduledTime.getTime() - now.getTime() > cancelDeadline;
}

export function VideoConsultationCard({
  consultation,
  onClick,
  onJoin,
  onCancel,
  onConfirm,
  onStart,
  loading = false,
}: VideoConsultationCardProps): JSX.Element {
  const status = statusConfig[consultation.status];
  const categoryLabel = categoryConfig[consultation.category ?? ''] || '其他咨询';
  const canJoin = canJoinConsultation(consultation);
  const canCancel = canCancelConsultation(consultation);

  const handleCardClick = (): void => {
    onClick?.();
  };

  const handleKeyDown = (e: React.KeyboardEvent): void => {
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault();
      onClick?.();
    }
  };

  return (
    <div
      className="bg-white rounded-lg shadow-sm border border-gray-200 p-4 hover:shadow-md transition-shadow cursor-pointer"
      onClick={handleCardClick}
      role="button"
      tabIndex={0}
      onKeyDown={handleKeyDown}
    >
      {/* 头部：主题和状态 */}
      <div className="flex items-start justify-between mb-3">
        <div className="flex-1 min-w-0">
          <h3 className="text-lg font-semibold text-gray-900 line-clamp-1">
            {consultation.subject}
          </h3>
          {consultation.description && (
            <p className="text-sm text-gray-500 line-clamp-1 mt-1">
              {consultation.description}
            </p>
          )}
        </div>
        <Badge variant={status.variant} size="md" className="ml-2 flex-shrink-0">
          {status.label}
        </Badge>
      </div>

      {/* 详情信息 */}
      <div className="space-y-2 mb-4">
        {/* 律师信息 */}
        <div className="flex items-center text-sm text-gray-600">
          <User className="w-4 h-4 mr-2 text-gray-400" />
          <span>{consultation.lawyerName || '待分配律师'}</span>
        </div>

        {/* 预约时间 */}
        <div className="flex items-center text-sm text-gray-600">
          <Calendar className="w-4 h-4 mr-2 text-gray-400" />
          <time dateTime={consultation.scheduledTime}>
            {formatDateTime(consultation.scheduledTime)}
          </time>
        </div>

        {/* 咨询时长 */}
        <div className="flex items-center text-sm text-gray-600">
          <Clock className="w-4 h-4 mr-2 text-gray-400" />
          <span>{formatDuration(consultation.durationMinutes)}</span>
        </div>

        {/* 费用信息 */}
        <div className="flex items-center text-sm">
          <Video className="w-4 h-4 mr-2 text-gray-400" />
          <span className="text-primary-600 font-medium">
            {formatAmount(consultation.paymentAmount, consultation.isFree, consultation.discountRate)}
          </span>
          <span className="mx-2 text-gray-300">|</span>
          <span className="text-gray-500">{categoryLabel}</span>
        </div>
      </div>

      {/* 操作按钮 */}
      <div className="flex items-center gap-2 pt-3 border-t border-gray-100">
        {consultation.status === 'pending' && onConfirm && (
          <Button
            variant="primary"
            size="sm"
            onClick={(e) => {
              e.stopPropagation();
              onConfirm();
            }}
            isLoading={loading}
            leftIcon={<CheckCircle className="w-4 h-4" />}
          >
            确认预约
          </Button>
        )}

        {canJoin && onJoin && (
          <Button
            variant="primary"
            size="sm"
            onClick={(e) => {
              e.stopPropagation();
              onJoin();
            }}
            isLoading={loading}
            leftIcon={<Play className="w-4 h-4" />}
          >
            {consultation.status === 'in_progress' ? '进入咨询' : '加入会议'}
          </Button>
        )}

        {consultation.status === 'confirmed' && onStart && (
          <Button
            variant="accent"
            size="sm"
            onClick={(e) => {
              e.stopPropagation();
              onStart();
            }}
            isLoading={loading}
            leftIcon={<Phone className="w-4 h-4" />}
          >
            开始咨询
          </Button>
        )}

        {canCancel && onCancel && (
          <Button
            variant="ghost"
            size="sm"
            onClick={(e) => {
              e.stopPropagation();
              onCancel();
            }}
            isLoading={loading}
            leftIcon={<XCircle className="w-4 h-4" />}
            className="text-red-600 hover:text-red-700 hover:bg-red-50"
          >
            取消预约
          </Button>
        )}

        {/* 已完成显示时长 */}
        {consultation.status === 'completed' && consultation.endedAt && consultation.startedAt && (
          <span className="text-sm text-gray-500">
            实际时长: {formatDuration(
              Math.round((new Date(consultation.endedAt).getTime() - new Date(consultation.startedAt).getTime()) / 60000)
            )}
          </span>
        )}
      </div>
    </div>
  );
}