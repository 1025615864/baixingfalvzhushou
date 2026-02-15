/**
 * 评论错误状态组件
 */

interface CommentErrorProps {
  error: string;
  onRetry?: () => void;
}

/**
 * 评论错误状态组件
 */
export function CommentError({
  error,
  onRetry,
}: CommentErrorProps): JSX.Element {
  return (
    <div className="flex flex-col items-center justify-center py-12 text-center">
      <div className="w-16 h-16 mb-4 rounded-full bg-red-50 flex items-center justify-center">
        <svg
          className="w-8 h-8 text-red-400"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={1.5}
            d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
          />
        </svg>
      </div>
      <h3 className="text-gray-900 font-medium mb-1">加载失败</h3>
      <p className="text-gray-500 text-sm mb-4">{error}</p>
      {onRetry && (
        <button
          onClick={onRetry}
          className="px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-lg
                     hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 transition-colors"
          type="button"
        >
          重新加载
        </button>
      )}
    </div>
  );
}

export default CommentError;