/**
 * 评论加载状态组件
 */

interface CommentLoadingProps {
  count?: number;
}

/**
 * 单个骨架屏项
 */
function SkeletonItem(): JSX.Element {
  return (
    <div className="flex gap-3 py-4 border-b border-gray-100 animate-pulse">
      {/* 头像骨架 */}
      <div className="flex-shrink-0">
        <div className="w-10 h-10 rounded-full bg-gray-200" />
      </div>
      
      {/* 内容骨架 */}
      <div className="flex-1 space-y-2">
        <div className="flex items-center gap-2">
          <div className="h-4 w-20 bg-gray-200 rounded" />
          <div className="h-3 w-16 bg-gray-200 rounded" />
        </div>
        <div className="space-y-1">
          <div className="h-3 bg-gray-200 rounded w-full" />
          <div className="h-3 bg-gray-200 rounded w-4/5" />
        </div>
      </div>
    </div>
  );
}

/**
 * 评论加载状态组件
 */
export function CommentLoading({ count = 3 }: CommentLoadingProps): JSX.Element {
  return (
    <div className="divide-y divide-gray-100">
      {Array.from({ length: count }).map((_, index) => (
        <SkeletonItem key={index} />
      ))}
    </div>
  );
}

export default CommentLoading;