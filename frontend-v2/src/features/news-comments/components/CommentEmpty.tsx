/**
 * 评论空状态组件
 */

interface CommentEmptyProps {
  title?: string;
  description?: string;
}

/**
 * 评论空状态组件
 */
export function CommentEmpty({
  title = '暂无评论',
  description = '成为第一个发表评论的人吧',
}: CommentEmptyProps): JSX.Element {
  return (
    <div className="flex flex-col items-center justify-center py-12 text-center">
      <div className="w-16 h-16 mb-4 rounded-full bg-gray-100 flex items-center justify-center">
        <svg
          className="w-8 h-8 text-gray-400"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={1.5}
            d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"
          />
        </svg>
      </div>
      <h3 className="text-gray-900 font-medium mb-1">{title}</h3>
      <p className="text-gray-500 text-sm">{description}</p>
    </div>
  );
}

export default CommentEmpty;