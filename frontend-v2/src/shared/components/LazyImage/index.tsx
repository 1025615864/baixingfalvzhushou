/**
 * 懒加载图片组件
 * 使用 Intersection Observer API 实现图片懒加载
 */

import { useState, useEffect, useRef, memo } from 'react';

interface LazyImageProps {
  /** 图片源地址 */
  src: string;
  /** 图片描述（alt 属性） */
  alt: string;
  /** 占位图片 */
  placeholder?: string;
  /** 图片宽度 */
  width?: number | string;
  /** 图片高度 */
  height?: number | string;
  /** 自定义类名 */
  className?: string;
  /** 图片加载时的类名 */
  loadingClassName?: string;
  /** 图片加载完成后的类名 */
  loadedClassName?: string;
  /** 图片加载错误时的类名 */
  errorClassName?: string;
  /** 加载错误时显示的图片 */
  errorPlaceholder?: string;
  /** 加载错误时的回调 */
  onError?: (e: React.SyntheticEvent<HTMLImageElement, Event>) => void;
  /** 加载完成时的回调 */
  onLoad?: (e: React.SyntheticEvent<HTMLImageElement, Event>) => void;
  /** 根元素边距，用于提前加载 */
  rootMargin?: string;
  /** 交叉阈值 */
  threshold?: number | number[];
  /** 图片适应模式 */
  objectFit?: 'contain' | 'cover' | 'fill' | 'none' | 'scale-down';
}

// 默认占位图（1x1 透明像素）
const DEFAULT_PLACEHOLDER = 'data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7';

// 默认错误占位图（灰色背景）
const DEFAULT_ERROR_PLACEHOLDER = 'data:image/svg+xml,%3Csvg xmlns="http://www.w3.org/2000/svg" width="100" height="100" viewBox="0 0 100 100"%3E%3Crect fill="%23e5e7eb" width="100" height="100"/%3E%3Ctext x="50" y="50" text-anchor="middle" dy=".3em" fill="%239ca3af" font-size="14"%3E加载失败%3C/text%3E%3C/svg%3E';

/**
 * 懒加载图片组件
 * 
 * @example
 * ```tsx
 * <LazyImage
 *   src="https://example.com/image.jpg"
 *   alt="示例图片"
 *   width={200}
 *   height={150}
 *   objectFit="cover"
 * />
 * ```
 */
export const LazyImage = memo(function LazyImage({
  src,
  alt,
  placeholder = DEFAULT_PLACEHOLDER,
  width,
  height,
  className = '',
  loadingClassName = 'opacity-0',
  loadedClassName = 'opacity-100',
  errorClassName = '',
  errorPlaceholder = DEFAULT_ERROR_PLACEHOLDER,
  onError,
  onLoad,
  rootMargin = '50px',
  threshold = 0.1,
  objectFit = 'cover',
}: LazyImageProps): JSX.Element {
  const [isLoaded, setIsLoaded] = useState(false);
  const [hasError, setHasError] = useState(false);
  const [isInView, setIsInView] = useState(false);
  const imgRef = useRef<HTMLImageElement>(null);

  useEffect(() => {
    const imgElement = imgRef.current;
    if (!imgElement) return;

    // 检查是否支持 Intersection Observer
    if (!('IntersectionObserver' in window)) {
      // 不支持则直接显示图片
      setIsInView(true);
      return;
    }

    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            setIsInView(true);
            observer.unobserve(entry.target);
          }
        });
      },
      {
        rootMargin,
        threshold,
      }
    );

    observer.observe(imgElement);

    return () => {
      observer.disconnect();
    };
  }, [rootMargin, threshold]);

  const handleLoad = (e: React.SyntheticEvent<HTMLImageElement, Event>) => {
    setIsLoaded(true);
    setHasError(false);
    onLoad?.(e);
  };

  const handleError = (e: React.SyntheticEvent<HTMLImageElement, Event>) => {
    setHasError(true);
    setIsLoaded(false);
    onError?.(e);
  };

  const currentSrc = hasError 
    ? errorPlaceholder 
    : isInView 
      ? src 
      : placeholder;

  const containerStyle: React.CSSProperties = {
    width: typeof width === 'number' ? `${width}px` : width,
    height: typeof height === 'number' ? `${height}px` : height,
    overflow: 'hidden',
  };

  const imageStyle: React.CSSProperties = {
    width: '100%',
    height: '100%',
    objectFit,
    transition: 'opacity 0.3s ease-in-out',
  };

  const combinedClassName = [
    className,
    !isLoaded && !hasError && isInView ? loadingClassName : '',
    isLoaded ? loadedClassName : '',
    hasError ? errorClassName : '',
  ].filter(Boolean).join(' ');

  return (
    <div style={containerStyle} className="lazy-image-container">
      <img
        ref={imgRef}
        src={currentSrc}
        alt={alt}
        className={combinedClassName}
        style={imageStyle}
        onLoad={handleLoad}
        onError={handleError}
        loading="lazy"
        decoding="async"
      />
    </div>
  );
});

export default LazyImage;