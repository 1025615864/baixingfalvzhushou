/**
 * SessionReview - 会话审核组件
 */

import { useState } from 'react';

import type { SessionDetail, ReviewResult } from '../types';

interface SessionReviewProps {
  session: SessionDetail | undefined;
  loading?: boolean;
  onReview?: (result: ReviewResult, score: number, comment: string, issues: string[], suggestions: string[]) => void;
}

/**
 * 质量等级标签
 */
function QualityBadge({ level, score }: { level: string | null; score: number | null }): JSX.Element {
  const getColorClass = (): string => {
    if (!level || !score) return 'bg-gray-100 text-gray-600';
    if (score >= 90) return 'bg-green-100 text-green-700';
    if (score >= 70) return 'bg-blue-100 text-blue-700';
    if (score >= 50) return 'bg-yellow-100 text-yellow-700';
    return 'bg-red-100 text-red-700';
  };

  const getLabel = (): string => {
    if (!level) return '未评分';
    const labels: Record<string, string> = {
      excellent: '优秀',
      good: '良好',
      average: '一般',
      poor: '较差',
      unknown: '未知',
    };
    return labels[level] || level;
  };

  return (
    <span className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${getColorClass()}`}>
      {getLabel()}
      {score !== null && ` (${score.toFixed(1)})`}
    </span>
  );
}

/**
 * 消息气泡
 */
function MessageBubble({
  role,
  content,
  timestamp,
  responseTime,
}: {
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: string;
  responseTime?: number | null;
}): JSX.Element {
  const isUser = role === 'user';

  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'}`}>
      <div className={`max-w-3/4 rounded-lg px-4 py-2 ${isUser ? 'bg-blue-500 text-white' : 'bg-gray-100 text-gray-900'}`}>
        <div className="mb-1 text-xs opacity-70">
          {role === 'user' ? '用户' : role === 'assistant' ? 'AI助手' : '系统'} · {new Date(timestamp).toLocaleString()}
          {responseTime !== null && responseTime !== undefined && (
            <span className="ml-2">({responseTime}ms)</span>
          )}
        </div>
        <div className="whitespace-pre-wrap text-sm">{content}</div>
      </div>
    </div>
  );
}

/**
 * 评分星级
 */
function StarRating({
  value,
  onChange,
  readonly = false,
}: {
  value: number;
  onChange?: (value: number) => void;
  readonly?: boolean;
}): JSX.Element {
  const [hoverValue, setHoverValue] = useState<number | null>(null);

  return (
    <div className="flex gap-1">
      {[1, 2, 3, 4, 5].map((star) => (
        <button
          key={star}
          type="button"
          disabled={readonly}
          className={`${readonly ? 'cursor-default' : 'cursor-pointer'} transition-colors`}
          onMouseEnter={() => !readonly && setHoverValue(star)}
          onMouseLeave={() => !readonly && setHoverValue(null)}
          onClick={() => onChange && onChange(star * 20)}
        >
          <svg
            className={`h-6 w-6 ${
              (hoverValue !== null ? star <= hoverValue : star <= Math.ceil(value / 20))
                ? 'text-yellow-400'
                : 'text-gray-300'
            }`}
            fill="currentColor"
            viewBox="0 0 20 20"
          >
            <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
          </svg>
        </button>
      ))}
    </div>
  );
}

/**
 * 会话审核组件
 */
export function SessionReview({ session, loading = false, onReview }: SessionReviewProps): JSX.Element {
  const [reviewResult, setReviewResult] = useState<ReviewResult>('approved');
  const [qualityScore, setQualityScore] = useState<number>(80);
  const [comment, setComment] = useState('');
  const [issues, setIssues] = useState<string[]>([]);
  const [suggestions, setSuggestions] = useState<string[]>([]);
  const [newIssue, setNewIssue] = useState('');
  const [newSuggestion, setNewSuggestion] = useState('');

  const handleAddIssue = (): void => {
    if (newIssue.trim()) {
      setIssues([...issues, newIssue.trim()]);
      setNewIssue('');
    }
  };

  const handleRemoveIssue = (index: number): void => {
    setIssues(issues.filter((_, i) => i !== index));
  };

  const handleAddSuggestion = (): void => {
    if (newSuggestion.trim()) {
      setSuggestions([...suggestions, newSuggestion.trim()]);
      setNewSuggestion('');
    }
  };

  const handleRemoveSuggestion = (index: number): void => {
    setSuggestions(suggestions.filter((_, i) => i !== index));
  };

  const handleSubmit = (): void => {
    onReview?.(reviewResult, qualityScore, comment, issues, suggestions);
  };

  if (loading || !session) {
    return (
      <div className="space-y-4">
        <div className="h-32 animate-pulse rounded-lg bg-gray-200"></div>
        <div className="h-64 animate-pulse rounded-lg bg-gray-200"></div>
        <div className="h-48 animate-pulse rounded-lg bg-gray-200"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* 会话信息头部 */}
      <div className="rounded-lg border border-gray-200 bg-white p-4">
        <div className="mb-4 flex items-center justify-between">
          <div>
            <h3 className="text-lg font-medium text-gray-900">会话详情</h3>
            <p className="text-sm text-gray-500">会话ID: {session.session_id}</p>
          </div>
          <QualityBadge level={session.quality_level} score={session.quality_score} />
        </div>

        <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
          <div>
            <p className="text-xs text-gray-500">用户</p>
            <p className="font-medium">{session.user_name || `用户${session.user_id}`}</p>
          </div>
          <div>
            <p className="text-xs text-gray-500">消息数</p>
            <p className="font-medium">{session.message_count}</p>
          </div>
          <div>
            <p className="text-xs text-gray-500">平均响应时间</p>
            <p className="font-medium">{session.avg_response_time_ms.toFixed(0)}ms</p>
          </div>
          <div>
            <p className="text-xs text-gray-500">错误数</p>
            <p className={`font-medium ${session.error_count > 0 ? 'text-red-600' : ''}`}>{session.error_count}</p>
          </div>
        </div>

        {session.topics.length > 0 && (
          <div className="mt-4">
            <p className="text-xs text-gray-500">相关话题</p>
            <div className="mt-1 flex flex-wrap gap-2">
              {session.topics.map((topic) => (
                <span key={topic} className="rounded-full bg-gray-100 px-2 py-1 text-xs text-gray-600">
                  {topic}
                </span>
              ))}
            </div>
          </div>
        )}

        {session.tools_used.length > 0 && (
          <div className="mt-4">
            <p className="text-xs text-gray-500">使用工具</p>
            <div className="mt-1 flex flex-wrap gap-2">
              {session.tools_used.map((tool) => (
                <span key={tool} className="rounded-full bg-blue-50 px-2 py-1 text-xs text-blue-600">
                  {tool}
                </span>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* 对话记录 */}
      <div className="rounded-lg border border-gray-200 bg-white p-4">
        <h4 className="mb-4 text-sm font-medium text-gray-900">对话记录</h4>
        <div className="max-h-96 space-y-4 overflow-y-auto pr-2">
          {session.messages.map((message) => (
            <MessageBubble
              key={message.id}
              role={message.role}
              content={message.content}
              timestamp={message.timestamp}
              responseTime={message.response_time_ms}
            />
          ))}
        </div>
      </div>

      {/* 用户反馈 */}
      {session.feedback && (
        <div className="rounded-lg border border-gray-200 bg-white p-4">
          <h4 className="mb-2 text-sm font-medium text-gray-900">用户反馈</h4>
          <div className="flex items-center gap-4">
            <span
              className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${
                session.feedback.is_helpful ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'
              }`}
            >
              {session.feedback.is_helpful ? '有帮助' : '无帮助'}
            </span>
            {session.feedback.rating && <StarRating value={session.feedback.rating} readonly />}
          </div>
          {session.feedback.comment && (
            <p className="mt-2 text-sm text-gray-600">{session.feedback.comment}</p>
          )}
        </div>
      )}

      {/* 审核表单 */}
      <div className="rounded-lg border border-gray-200 bg-white p-4">
        <h4 className="mb-4 text-sm font-medium text-gray-900">人工审核</h4>

        {/* 审核结果选择 */}
        <div className="mb-4">
          <label className="mb-2 block text-sm font-medium text-gray-700">审核结果</label>
          <div className="flex gap-4">
            <label className="flex items-center">
              <input
                type="radio"
                value="approved"
                checked={reviewResult === 'approved'}
                onChange={(e) => setReviewResult(e.target.value as ReviewResult)}
                className="h-4 w-4 border-gray-300 text-blue-600"
              />
              <span className="ml-2 text-sm text-gray-700">通过</span>
            </label>
            <label className="flex items-center">
              <input
                type="radio"
                value="needs_improvement"
                checked={reviewResult === 'needs_improvement'}
                onChange={(e) => setReviewResult(e.target.value as ReviewResult)}
                className="h-4 w-4 border-gray-300 text-yellow-600"
              />
              <span className="ml-2 text-sm text-gray-700">需改进</span>
            </label>
            <label className="flex items-center">
              <input
                type="radio"
                value="rejected"
                checked={reviewResult === 'rejected'}
                onChange={(e) => setReviewResult(e.target.value as ReviewResult)}
                className="h-4 w-4 border-gray-300 text-red-600"
              />
              <span className="ml-2 text-sm text-gray-700">不通过</span>
            </label>
          </div>
        </div>

        {/* 质量评分 */}
        <div className="mb-4">
          <label className="mb-2 block text-sm font-medium text-gray-700">质量评分</label>
          <div className="flex items-center gap-4">
            <StarRating value={qualityScore} onChange={setQualityScore} />
            <span className="text-lg font-medium text-gray-900">{qualityScore}</span>
          </div>
        </div>

        {/* 审核意见 */}
        <div className="mb-4">
          <label className="mb-2 block text-sm font-medium text-gray-700">审核意见</label>
          <textarea
            value={comment}
            onChange={(e) => setComment(e.target.value)}
            rows={3}
            className="w-full rounded-lg border border-gray-300 p-2 text-sm focus:border-blue-500 focus:outline-none"
            placeholder="请输入审核意见..."
          />
        </div>

        {/* 问题列表 */}
        <div className="mb-4">
          <label className="mb-2 block text-sm font-medium text-gray-700">发现的问题</label>
          <div className="flex gap-2">
            <input
              type="text"
              value={newIssue}
              onChange={(e) => setNewIssue(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && handleAddIssue()}
              className="flex-1 rounded-lg border border-gray-300 p-2 text-sm focus:border-blue-500 focus:outline-none"
              placeholder="添加问题..."
            />
            <button
              type="button"
              onClick={handleAddIssue}
              className="rounded-lg bg-gray-100 px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-200"
            >
              添加
            </button>
          </div>
          {issues.length > 0 && (
            <ul className="mt-2 space-y-1">
              {issues.map((issue, index) => (
                <li key={index} className="flex items-center justify-between rounded bg-red-50 px-3 py-1 text-sm text-red-700">
                  <span>{issue}</span>
                  <button
                    type="button"
                    onClick={() => handleRemoveIssue(index)}
                    className="text-red-500 hover:text-red-700"
                  >
                    ×
                  </button>
                </li>
              ))}
            </ul>
          )}
        </div>

        {/* 改进建议 */}
        <div className="mb-4">
          <label className="mb-2 block text-sm font-medium text-gray-700">改进建议</label>
          <div className="flex gap-2">
            <input
              type="text"
              value={newSuggestion}
              onChange={(e) => setNewSuggestion(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && handleAddSuggestion()}
              className="flex-1 rounded-lg border border-gray-300 p-2 text-sm focus:border-blue-500 focus:outline-none"
              placeholder="添加建议..."
            />
            <button
              type="button"
              onClick={handleAddSuggestion}
              className="rounded-lg bg-gray-100 px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-200"
            >
              添加
            </button>
          </div>
          {suggestions.length > 0 && (
            <ul className="mt-2 space-y-1">
              {suggestions.map((suggestion, index) => (
                <li key={index} className="flex items-center justify-between rounded bg-blue-50 px-3 py-1 text-sm text-blue-700">
                  <span>{suggestion}</span>
                  <button
                    type="button"
                    onClick={() => handleRemoveSuggestion(index)}
                    className="text-blue-500 hover:text-blue-700"
                  >
                    ×
                  </button>
                </li>
              ))}
            </ul>
          )}
        </div>

        {/* 提交按钮 */}
        <button
          type="button"
          onClick={handleSubmit}
          disabled={!comment.trim()}
          className="w-full rounded-lg bg-blue-600 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:cursor-not-allowed disabled:bg-gray-400"
        >
          提交审核
        </button>
      </div>
    </div>
  );
}