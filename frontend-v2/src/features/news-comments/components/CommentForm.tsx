/**
 * 评论表单组件
 */

import { useState, useCallback } from 'react';

interface CommentFormProps {
  onSubmit?: (content: string) => Promise<void> | void;
  isSubmitting?: boolean;
  placeholder?: string;
  maxLength?: number;
}

/**
 * 评论表单组件
 */
export function CommentForm({
  onSubmit,
  isSubmitting = false,
  placeholder = '写下你的评论...',
  maxLength = 500,
}: CommentFormProps): JSX.Element {
  const [content, setContent] = useState('');
  const [error, setError] = useState<string | null>(null);

  const handleChange = useCallback((e: React.ChangeEvent<HTMLTextAreaElement>) => {
    const value = e.target.value;
    if (value.length <= maxLength) {
      setContent(value);
      setError(null);
    }
  }, [maxLength]);

  const handleSubmit = useCallback(async () => {
    const trimmedContent = content.trim();
    
    if (!trimmedContent) {
      setError('请输入评论内容');
      return;
    }

    if (trimmedContent.length < 2) {
      setError('评论内容至少需要2个字符');
      return;
    }

    try {
      await onSubmit?.(trimmedContent);
      setContent('');
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : '发送失败，请重试');
    }
  }, [content, onSubmit]);

  const handleKeyDown = useCallback((e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    // Ctrl/Cmd + Enter 提交
    if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
      e.preventDefault();
      void handleSubmit();
    }
  }, [handleSubmit]);

  const remainingChars = maxLength - content.length;
  const isNearLimit = remainingChars < 50;

  return (
    <div className="bg-white rounded-lg border border-gray-200 p-4">
      <div className="relative">
        <textarea
          value={content}
          onChange={handleChange}
          onKeyDown={handleKeyDown}
          placeholder={placeholder}
          disabled={isSubmitting}
          className="w-full min-h-[100px] p-3 text-sm text-gray-700 placeholder-gray-400 
                     border border-gray-200 rounded-lg resize-none focus:outline-none 
                     focus:ring-2 focus:ring-blue-500 focus:border-transparent
                     disabled:bg-gray-50 disabled:cursor-not-allowed"
        />
        
        {/* 字符计数 */}
        <div className={`absolute bottom-2 right-2 text-xs ${isNearLimit ? 'text-orange-500' : 'text-gray-400'}`}>
          {remainingChars}
        </div>
      </div>

      {/* 错误提示 */}
      {error && (
        <div className="mt-2 text-sm text-red-500">
          {error}
        </div>
      )}

      {/* 操作按钮 */}
      <div className="flex justify-between items-center mt-3">
        <span className="text-xs text-gray-400">
          按 Ctrl + Enter 快速发送
        </span>
        
        <button
          onClick={() => { void handleSubmit(); }}
          disabled={isSubmitting || !content.trim()}
          className="px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-lg
                     hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500
                     disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors"
          type="button"
        >
          {isSubmitting ? '发送中...' : '发表评论'}
        </button>
      </div>
    </div>
  );
}

export default CommentForm;