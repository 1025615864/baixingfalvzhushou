/**
 * ReadableMessage - 可读消息展示组件
 *
 * 用于展示 AI 对话中的消息，支持用户消息和 AI 消息的不同展示样式
 */

import { useCallback } from 'react';

import type { AIMessage, SuggestedAction } from '../types';

import { AIResponseFormatter } from './AIResponseFormatter';
import { ConfidenceIndicator } from './ConfidenceIndicator';

interface ReadableMessageProps {
  /** 消息数据 */
  message: AIMessage;
  /** 是否显示时间戳 */
  showTimestamp?: boolean;
  /** 是否显示置信度 */
  showConfidence?: boolean;
  /** 是否显示操作按钮 */
  showActions?: boolean;
  /** 操作点击回调 */
  onActionClick?: (action: SuggestedAction) => void;
  /** 自定义类名 */
  className?: string;
}

/**
 * 格式化时间戳
 */
function formatTimestamp(timestamp: string): string {
  const date = new Date(timestamp);
  const now = new Date();
  const diff = now.getTime() - date.getTime();
  
  // 小于1分钟
  if (diff < 60 * 1000) {
    return '刚刚';
  }
  
  // 小于1小时
  if (diff < 60 * 60 * 1000) {
    return `${Math.floor(diff / (60 * 1000))}分钟前`;
  }
  
  // 小于24小时
  if (diff < 24 * 60 * 60 * 1000) {
    return `${Math.floor(diff / (60 * 60 * 1000))}小时前`;
  }
  
  // 小于7天
  if (diff < 7 * 24 * 60 * 60 * 1000) {
    return `${Math.floor(diff / (24 * 60 * 60 * 1000))}天前`;
  }
  
  // 默认显示日期时间
  return date.toLocaleString('zh-CN', {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
}

/**
 * 获取操作类型图标
 */
function getActionIcon(type: string): string {
  const iconMap: Record<string, string> = {
    consult_lawyer: '👨‍⚖️',
    view_case: '📋',
    generate_document: '📝',
    schedule_appointment: '📅',
    read_article: '📄',
    ask_followup: '💬',
  };
  return iconMap[type] || '👉';
}

/**
 * 获取操作类型标签
 */
function getActionLabel(type: string): string {
  const labelMap: Record<string, string> = {
    consult_lawyer: '咨询律师',
    view_case: '查看案例',
    generate_document: '生成文档',
    schedule_appointment: '预约咨询',
    read_article: '阅读文章',
    ask_followup: '继续追问',
  };
  return labelMap[type] || '了解更多';
}

/**
 * 用户头像组件
 */
function UserAvatar(): JSX.Element {
  return (
    <div className="flex-shrink-0 w-8 h-8 bg-blue-500 rounded-full flex items-center justify-center">
      <svg 
        className="w-5 h-5 text-white" 
        fill="none" 
        stroke="currentColor" 
        viewBox="0 0 24 24"
      >
        <path 
          strokeLinecap="round" 
          strokeLinejoin="round" 
          strokeWidth={2} 
          d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" 
        />
      </svg>
    </div>
  );
}

/**
 * AI 头像组件
 */
function AIAvatar(): JSX.Element {
  return (
    <div className="flex-shrink-0 w-8 h-8 bg-gradient-to-br from-purple-500 to-indigo-600 rounded-full flex items-center justify-center">
      <svg 
        className="w-5 h-5 text-white" 
        fill="none" 
        stroke="currentColor" 
        viewBox="0 0 24 24"
      >
        <path 
          strokeLinecap="round" 
          strokeLinejoin="round" 
          strokeWidth={2} 
          d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" 
        />
      </svg>
    </div>
  );
}

/**
 * 消息状态指示器
 */
function MessageStatus({ status }: { status: AIMessage['status'] }): JSX.Element {
  switch (status) {
    case 'sending':
      return (
        <span className="inline-flex items-center gap-1 text-xs text-gray-400">
          <svg className="w-3 h-3 animate-spin" fill="none" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
          </svg>
          <span>发送中</span>
        </span>
      );
    case 'streaming':
      return (
        <span className="inline-flex items-center gap-1 text-xs text-blue-500">
          <span className="relative flex h-2 w-2">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-blue-400 opacity-75" />
            <span className="relative inline-flex rounded-full h-2 w-2 bg-blue-500" />
          </span>
          <span>生成中...</span>
        </span>
      );
    case 'error':
      return (
        <span className="inline-flex items-center gap-1 text-xs text-red-500">
          <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <span>发送失败</span>
        </span>
      );
    default:
      return <></>;
  }
}

/**
 * 可读消息展示组件
 */
export function ReadableMessage({
  message,
  showTimestamp = true,
  showConfidence = true,
  showActions = true,
  onActionClick,
  className = '',
}: ReadableMessageProps): JSX.Element {
  const isUser = message.role === 'user';
  const isAssistant = message.role === 'assistant';
  
  const hasConfidence = showConfidence && 
    isAssistant && 
    message.metadata?.confidence !== undefined;
  
  const hasActions = showActions && 
    isAssistant && 
    message.metadata?.suggestedActions && 
    message.metadata.suggestedActions.length > 0;

  const handleActionClick = useCallback((action: SuggestedAction) => {
    onActionClick?.(action);
  }, [onActionClick]);

  return (
    <div className={`flex gap-3 ${isUser ? 'flex-row-reverse' : ''} ${className}`}>
      {/* 头像 */}
      {isUser ? <UserAvatar /> : <AIAvatar />}

      {/* 消息内容 */}
      <div className={`flex-1 max-w-[80%] ${isUser ? 'items-end' : 'items-start'} flex flex-col`}>
        {/* 消息气泡 */}
        <div
          className={`rounded-2xl px-4 py-3 ${
            isUser
              ? 'bg-blue-500 text-white rounded-tr-none'
              : 'bg-gray-100 text-gray-800 rounded-tl-none'
          }`}
        >
          {isUser ? (
            <p className="text-sm leading-relaxed whitespace-pre-wrap">{message.content}</p>
          ) : (
            <AIResponseFormatter
              content={message.content}
              sources={message.metadata?.sources}
              legalReferences={message.metadata?.legalReferences}
              showSources={message.status === 'completed'}
              showLegalReferences={message.status === 'completed'}
            />
          )}
        </div>

        {/* 元信息 */}
        <div className={`mt-1 flex flex-col gap-2 ${isUser ? 'items-end' : 'items-start'}`}>
          {/* 时间和状态 */}
          {showTimestamp && (
            <div className="flex items-center gap-2 text-xs text-gray-400">
              <span>{formatTimestamp(message.createdAt)}</span>
              <MessageStatus status={message.status} />
            </div>
          )}

          {/* 置信度指示器 */}
          {hasConfidence && message.metadata && (
            <div className="w-full max-w-xs mt-2">
              <ConfidenceIndicator 
                score={message.metadata.confidence || 0} 
                mode="compact"
              />
            </div>
          )}

          {/* 建议操作按钮 */}
          {hasActions && message.metadata?.suggestedActions && (
            <div className="flex flex-wrap gap-2 mt-2">
              {message.metadata.suggestedActions.map((action, index) => (
                <button
                  key={`${action.type}-${index}`}
                  onClick={() => handleActionClick(action)}
                  className="inline-flex items-center gap-1.5 px-3 py-1.5 
                           bg-white border border-gray-200 rounded-full
                           text-xs text-gray-600 hover:bg-gray-50 
                           hover:border-gray-300 transition-colors"
                >
                  <span>{getActionIcon(action.type)}</span>
                  <span>{getActionLabel(action.type)}</span>
                </button>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}