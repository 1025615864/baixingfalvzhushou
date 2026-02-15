/**
 * SmartReply - 智能回复组件
 */

import { useState } from 'react';

import type { SmartReplySuggestion } from '../types';
import { useSmartReplySuggestions, useAdoptSmartReply } from '../hooks/useForumAssistant';

interface SmartReplyProps {
  postId: string;
  postTitle?: string;
  className?: string;
  onReplyAdopted?: (content: string) => void;
}

/**
 * 智能回复组件
 */
export function SmartReply({ postId, postTitle, className = '', onReplyAdopted }: SmartReplyProps): JSX.Element {
  const [selectedSuggestion, setSelectedSuggestion] = useState<SmartReplySuggestion | null>(null);
  const [modifiedContent, setModifiedContent] = useState<string>('');
  const [showSuccess, setShowSuccess] = useState<boolean>(false);

  const { data: suggestions, isLoading, error } = useSmartReplySuggestions(postId);
  const adoptMutation = useAdoptSmartReply();

  /**
   * 选择建议
   */
  const handleSelectSuggestion = (suggestion: SmartReplySuggestion): void => {
    setSelectedSuggestion(suggestion);
    setModifiedContent(suggestion.content);
    setShowSuccess(false);
  };

  /**
   * 采纳回复
   */
  const handleAdoptReply = async (): Promise<void> => {
    if (!selectedSuggestion) return;

    try {
      await adoptMutation.mutateAsync({
        suggestionId: selectedSuggestion.id,
        postId,
        modifiedContent: modifiedContent !== selectedSuggestion.content ? modifiedContent : undefined,
      });

      setShowSuccess(true);
      onReplyAdopted?.(modifiedContent);

      // 3秒后重置状态
      setTimeout(() => {
        setShowSuccess(false);
        setSelectedSuggestion(null);
        setModifiedContent('');
      }, 3000);
    } catch {
      // 错误已在 hook 中处理
    }
  };

  /**
   * 取消选择
   */
  const handleCancel = (): void => {
    setSelectedSuggestion(null);
    setModifiedContent('');
    setShowSuccess(false);
  };

  /**
   * 获取置信度颜色
   */
  const getConfidenceColor = (confidence: number): string => {
    if (confidence >= 0.8) return 'text-green-600 bg-green-50';
    if (confidence >= 0.6) return 'text-yellow-600 bg-yellow-50';
    return 'text-gray-600 bg-gray-50';
  };

  if (isLoading) {
    return (
      <div className={`bg-white rounded-xl shadow-sm p-6 ${className}`}>
        <div className="animate-pulse space-y-4">
          <div className="h-5 bg-gray-200 rounded w-1/3" />
          <div className="space-y-3">
            <div className="h-20 bg-gray-200 rounded" />
            <div className="h-20 bg-gray-200 rounded" />
            <div className="h-20 bg-gray-200 rounded" />
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className={`bg-white rounded-xl shadow-sm p-6 ${className}`}>
        <div className="text-center text-red-500">
          <svg className="w-12 h-12 mx-auto mb-3 text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
          </svg>
          <p className="text-sm">获取智能回复建议失败</p>
          <p className="text-xs text-gray-400 mt-1">请稍后重试</p>
        </div>
      </div>
    );
  }

  if (!suggestions || suggestions.length === 0) {
    return (
      <div className={`bg-white rounded-xl shadow-sm p-6 ${className}`}>
        <div className="text-center text-gray-500">
          <svg className="w-12 h-12 mx-auto mb-3 text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
          </svg>
          <p className="text-sm">暂无智能回复建议</p>
          <p className="text-xs text-gray-400 mt-1">系统会根据帖子内容生成建议</p>
        </div>
      </div>
    );
  }

  return (
    <div className={`bg-white rounded-xl shadow-sm p-6 ${className}`}>
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
          <svg className="w-5 h-5 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
          </svg>
          智能回复建议
        </h3>
        <span className="text-xs text-gray-500 bg-gray-100 px-2 py-1 rounded-full">
          {suggestions.length} 条建议
        </span>
      </div>

      {postTitle && (
        <div className="mb-4 p-3 bg-gray-50 rounded-lg">
          <p className="text-xs text-gray-500 mb-1">回复帖子</p>
          <p className="text-sm text-gray-900 font-medium line-clamp-2">{postTitle}</p>
        </div>
      )}

      {showSuccess ? (
        <div className="text-center py-8">
          <div className="w-16 h-16 mx-auto mb-4 bg-green-100 rounded-full flex items-center justify-center">
            <svg className="w-8 h-8 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
            </svg>
          </div>
          <p className="text-green-600 font-medium">回复已采纳</p>
          <p className="text-sm text-gray-500 mt-1">感谢您的参与！</p>
        </div>
      ) : selectedSuggestion ? (
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">编辑回复内容</label>
            <textarea
              value={modifiedContent}
              onChange={(e) => setModifiedContent(e.target.value)}
              rows={5}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm resize-none"
              placeholder="编辑您的回复..."
            />
          </div>

          <div className="flex items-center justify-between">
            <button
              onClick={handleCancel}
              className="px-4 py-2 text-sm text-gray-600 hover:text-gray-800"
            >
              返回
            </button>
            <div className="flex gap-2">
              <button
                onClick={() => void handleAdoptReply()}
                disabled={adoptMutation.isPending || modifiedContent.trim().length === 0}
                className="px-4 py-2 bg-blue-600 text-white text-sm rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {adoptMutation.isPending ? '提交中...' : '采纳回复'}
              </button>
            </div>
          </div>

          {adoptMutation.isError && (
            <p className="text-sm text-red-500 text-center">
              采纳失败，请重试
            </p>
          )}
        </div>
      ) : (
        <div className="space-y-3">
          {suggestions.map((suggestion) => (
            <button
              key={suggestion.id}
              onClick={() => handleSelectSuggestion(suggestion)}
              className="w-full text-left p-4 rounded-lg border border-gray-200 hover:border-blue-300 hover:bg-blue-50 transition-colors group"
            >
              <div className="flex items-start justify-between gap-2">
                <p className="text-sm text-gray-700 line-clamp-3 flex-1">
                  {suggestion.content}
                </p>
                <span className={`text-xs px-2 py-0.5 rounded-full whitespace-nowrap ${getConfidenceColor(suggestion.confidence)}`}>
                  {(suggestion.confidence * 100).toFixed(0)}% 匹配
                </span>
              </div>
              <div className="flex items-center gap-2 mt-2">
                {suggestion.tags.map((tag) => (
                  <span
                    key={tag}
                    className="text-xs text-gray-400 bg-gray-100 px-1.5 py-0.5 rounded"
                  >
                    {tag}
                  </span>
                ))}
              </div>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}