/**
 * ConfidenceIndicator - 置信度指示器组件
 * 
 * 用于显示 AI 响应的可信度
 */

import { useMemo } from 'react';

import type { ConfidenceLevel } from '../types';

interface ConfidenceIndicatorProps {
  /** 置信度分数 (0-1) */
  score: number;
  /** 显示模式 */
  mode?: 'compact' | 'full' | 'icon';
  /** 显示标签 */
  showLabel?: boolean;
  /** 自定义类名 */
  className?: string;
}

/**
 * 根据分数获取置信度等级
 */
function getConfidenceLevel(score: number): ConfidenceLevel {
  if (score >= 0.8) return 'high';
  if (score >= 0.5) return 'medium';
  return 'low';
}

/**
 * 获取置信度等级配置
 */
function getLevelConfig(level: ConfidenceLevel): {
  color: string;
  bgColor: string;
  label: string;
  icon: string;
} {
  const config: Record<ConfidenceLevel, { color: string; bgColor: string; label: string; icon: string }> = {
    high: {
      color: 'text-green-600',
      bgColor: 'bg-green-100',
      label: '高可信度',
      icon: '✓',
    },
    medium: {
      color: 'text-yellow-600',
      bgColor: 'bg-yellow-100',
      label: '中等可信度',
      icon: '~',
    },
    low: {
      color: 'text-red-600',
      bgColor: 'bg-red-100',
      label: '低可信度',
      icon: '!',
    },
  };
  return config[level];
}

/**
 * 置信度指示器组件
 */
export function ConfidenceIndicator({
  score,
  mode = 'full',
  showLabel = true,
  className = '',
}: ConfidenceIndicatorProps): JSX.Element {
  const level = useMemo(() => getConfidenceLevel(score), [score]);
  const config = useMemo(() => getLevelConfig(level), [level]);
  
  const percentage = useMemo(() => Math.round(score * 100), [score]);

  // 紧凑模式 - 只显示进度条
  if (mode === 'compact') {
    return (
      <div className={`flex items-center gap-2 ${className}`}>
        <div className="flex-1 h-1.5 bg-gray-200 rounded-full overflow-hidden">
          <div
            className={`h-full rounded-full transition-all duration-300 ${
              level === 'high' 
                ? 'bg-green-500' 
                : level === 'medium' 
                  ? 'bg-yellow-500' 
                  : 'bg-red-500'
            }`}
            style={{ width: `${percentage}%` }}
          />
        </div>
        <span className={`text-xs font-medium ${config.color}`}>
          {percentage}%
        </span>
      </div>
    );
  }

  // 图标模式 - 只显示图标
  if (mode === 'icon') {
    return (
      <div 
        className={`inline-flex items-center justify-center w-5 h-5 rounded-full ${config.bgColor} ${config.color} ${className}`}
        title={`可信度: ${percentage}% - ${config.label}`}
      >
        <span className="text-xs font-bold">{config.icon}</span>
      </div>
    );
  }

  // 完整模式
  return (
    <div className={`flex items-center gap-3 ${className}`}>
      {/* 图标 */}
      <div className={`flex items-center justify-center w-8 h-8 rounded-full ${config.bgColor}`}>
        <span className={`text-sm font-bold ${config.color}`}>
          {config.icon}
        </span>
      </div>

      {/* 进度条和标签 */}
      <div className="flex-1">
        <div className="flex items-center justify-between mb-1">
          {showLabel && (
            <span className={`text-sm font-medium ${config.color}`}>
              {config.label}
            </span>
          )}
          <span className={`text-sm font-bold ${config.color}`}>
            {percentage}%
          </span>
        </div>
        <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
          <div
            className={`h-full rounded-full transition-all duration-500 ease-out ${
              level === 'high' 
                ? 'bg-green-500' 
                : level === 'medium' 
                  ? 'bg-yellow-500' 
                  : 'bg-red-500'
            }`}
            style={{ width: `${percentage}%` }}
          />
        </div>
        {/* 提示信息 */}
        <p className="text-xs text-gray-500 mt-1">
          {level === 'high' 
            ? 'AI 对此回答有较高把握，信息可信度较高' 
            : level === 'medium' 
              ? 'AI 对此回答有一定把握，建议进一步核实' 
              : 'AI 对此回答把握较低，建议咨询专业律师'}
        </p>
      </div>
    </div>
  );
}