interface LoadingProps {
  size?: 'sm' | 'md' | 'lg';
  fullScreen?: boolean;
  text?: string;
  /** 自定义类名 */
  className?: string;
}

const sizeMap = {
  sm: 'w-6 h-6',
  md: 'w-10 h-10',
  lg: 'w-16 h-16',
};

export function Loading({
  size = 'md',
  fullScreen = false,
  text,
  className = '',
}: LoadingProps): JSX.Element {
  const spinner = (
    <div className="flex flex-col items-center gap-3">
      <div
        className={`${sizeMap[size]} animate-spin rounded-full border-4 border-gray-200 border-t-primary-600`}
      />
      {text && <p className="text-gray-600 text-sm">{text}</p>}
    </div>
  );

  if (fullScreen) {
    return (
      <div className="fixed inset-0 bg-white/80 backdrop-blur-sm flex items-center justify-center z-50">
        {spinner}
      </div>
    );
  }

  return (
    <div className={`flex items-center justify-center p-8 ${className}`}>{spinner}</div>
  );
}

// ============================================
// Skeleton 骨架屏组件
// ============================================

interface SkeletonProps {
  /** 宽度 */
  width?: string | number;
  /** 高度 */
  height?: string | number;
  /** 圆角 */
  radius?: string | number;
  /** 自定义类名 */
  className?: string;
}

export function Skeleton({ width, height, radius, className = '' }: SkeletonProps): JSX.Element {
  return (
    <div
      className={`animate-pulse bg-gray-200 rounded ${className}`}
      style={{
        width: typeof width === 'number' ? `${width}px` : width,
        height: typeof height === 'number' ? `${height}px` : height,
        borderRadius: typeof radius === 'number' ? `${radius}px` : radius,
      }}
    />
  );
}

// ============================================
// 列表骨架屏
// ============================================

interface SkeletonListProps {
  /** 项数 */
  count?: number;
  /** 高度 */
  height?: number;
}

export function SkeletonList({ count = 3, height = 60 }: SkeletonListProps): JSX.Element {
  return (
    <div className="space-y-3">
      {Array.from({ length: count }).map((_, i) => (
        <Skeleton key={i} width="100%" height={height} radius={8} />
      ))}
    </div>
  );
}