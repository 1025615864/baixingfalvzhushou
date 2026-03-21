/**
 * LazyImage - 图片懒加载组件
 * 
 * 使用 Intersection Observer API 实现图片懒加载
 * 支持占位图、加载状态、加载失败处理
 * 优化页面加载性能，减少首屏请求数
 */

import React, { useState, useRef, useEffect, useCallback } from 'react';

/**
 * LazyImage 组件属性
 */
export interface LazyImageProps {
  /** 图片源地址 */
  src: string;
  /** 图片描述文本（alt 属性） */
  alt?: string;
  /** 占位图（可以是颜色值、渐变或图片 URL） */
  placeholder?: string | React.ReactNode;
  /** 加载失败时显示的图片 */
  fallbackSrc?: string;
  /** 自定义类名 */
  className?: string;
  /** 图片容器类名 */
  containerClassName?: string;
  /** 图片宽度 */
  width?: number | string;
  /** 图片高度 */
  height?: number | string;
  /** 是否显示加载动画 */
  animate?: boolean;
  /** 加载优先级：'low' | 'eager' */
  loading?: 'lazy' | 'eager' | 'auto';
  /** 交叉观察器的根边距 */
  rootMargin?: string;
  /** 交叉观察器的阈值（0-1） */
  threshold?: number;
  /** 图片加载完成的回调 */
  onLoad?: () => void;
  /** 图片加载失败的回调 */
  onError?: () => void;
  /** 图片进入视口的回调 */
  onVisible?: () => void;
  /** 点击事件处理 */
  onClick?: () => void;
  /** 是否使用 object-fit: cover */
  cover?: boolean;
  /** object-fit 模式 */
  objectFit?: 'cover' | 'contain' | 'fill' | 'none' | 'scale-down';
  /** 自定义渲染器（用于高级用法） */
  children?: (props: { 
    isLoading: boolean; 
    isLoaded: boolean; 
    isError: boolean;
    ref: React.RefObject<HTMLDivElement>;
  }) => React.ReactNode;
}

/**
 * LazyImage 图片懒加载组件
 * 
 * @example
 * ```tsx
 * // 基本使用
 * <LazyImage 
 *   src="/images/photo.jpg" 
 *   alt="示例图片"
 *   width={300}
 *   height={200}
 * />
 * 
 * // 带占位图
 * <LazyImage 
 *   src="/images/photo.jpg" 
 *   alt="示例图片"
 *   placeholder="#f0f0f0"
 *   fallbackSrc="/images/fallback.png"
 * />
 * 
 * // 带自定义占位符
 * <LazyImage 
 *   src="/images/photo.jpg" 
 *   alt="示例图片"
 *   placeholder={<Skeleton width={300} height={200} />}
 * />
 * 
 * // 带回调
 * <LazyImage 
 *   src="/images/photo.jpg" 
 *   alt="示例图片"
 *   onLoad={() => console.log('图片加载完成')}
 *   onError={() => console.log('图片加载失败')}
 * />
 * 
 * // 自定义渲染
 * <LazyImage src="/images/photo.jpg" alt="示例">
 *   {({ isLoading, isLoaded, isError }) => (
 *     <div>
 *       {isLoading && <div>加载中...</div>}
 *       {isError && <div>加载失败</div>}
 *     </div>
 *   )}
 * </LazyImage>
 * ```
 */
export function LazyImage({
  src,
  alt = '',
  placeholder,
  fallbackSrc,
  className = '',
  containerClassName = '',
  width,
  height,
  animate = true,
  loading = 'lazy',
  rootMargin = '50px',
  threshold = 0,
  onLoad,
  onError,
  onVisible,
  onClick,
  cover = true,
  objectFit,
  children,
}: LazyImageProps): JSX.Element {
  // 图片加载状态
  const [isLoaded, setIsLoaded] = useState(false);
  const [isError, setIsError] = useState(false);
  const [isVisible, setIsVisible] = useState(false);
  
  // 容器引用
  const containerRef = useRef<HTMLDivElement>(null);
  // 图片引用
  const imgRef = useRef<HTMLImageElement>(null);

  // 处理图片加载完成
  const handleLoad = useCallback(() => {
    setIsLoaded(true);
    setIsError(false);
    onLoad?.();
  }, [onLoad]);

  // 处理图片加载失败
  const handleError = useCallback(() => {
    setIsError(true);
    setIsLoaded(false);
    onError?.();
  }, [onError]);

  // 使用 Intersection Observer 监听元素是否进入视口
  useEffect(() => {
    // 如果 loading 为 'eager'，直接显示
    if (loading === 'eager') {
      setIsVisible(true);
      return;
    }

    const observer = new IntersectionObserver(
      (entries) => {
        for (const entry of entries) {
          if (entry.isIntersecting) {
            setIsVisible(true);
            onVisible?.();
            // 开始观察后取消观察
            if (containerRef.current) {
              observer.unobserve(containerRef.current);
            }
          }
        }
      },
      {
        rootMargin,
        threshold,
      }
    );

    const currentContainer = containerRef.current;
    if (currentContainer) {
      observer.observe(currentContainer);
    }

    return () => {
      if (currentContainer) {
        observer.unobserve(currentContainer);
      }
    };
  }, [loading, rootMargin, threshold, onVisible]);

  // 渲染占位符
  const renderPlaceholder = () => {
    if (React.isValidElement(placeholder)) {
      return placeholder;
    }

    if (typeof placeholder === 'string') {
      // 检查是否是颜色值或渐变
      if (placeholder.startsWith('#') || placeholder.startsWith('rgb') || placeholder.startsWith('linear-gradient')) {
        return (
          <div
            className="absolute inset-0"
            style={{ backgroundColor: placeholder.startsWith('linear-gradient') ? undefined : placeholder, background: placeholder }}
          />
        );
      }
      // 如果是图片 URL，作为占位图
      return (
        <img
          src={placeholder}
          alt=""
          className="absolute inset-0 w-full h-full"
          style={{ objectFit: 'cover' }}
          aria-hidden="true"
        />
      );
    }

    // 默认占位符 - 浅灰色背景
    return (
      <div
        className="absolute inset-0 bg-gray-100 dark:bg-gray-800"
        style={{
          backgroundImage: 'linear-gradient(90deg, rgba(0,0,0,0.02) 25%, transparent 25%, transparent 50%, rgba(0,0,0,0.02) 50%, rgba(0,0,0,0.02) 75%, transparent 75%, transparent)',
          backgroundSize: '20px 100%',
        }}
      />
    );
  };

  // 计算图片样式
  const imageStyle: React.CSSProperties = {
    width: width ? (typeof width === 'number' ? `${width}px` : width) : '100%',
    height: height ? (typeof height === 'number' ? `${height}px` : height) : '100%',
    objectFit: objectFit || (cover ? 'cover' : 'contain'),
    transition: animate ? 'opacity 0.3s ease-in-out' : undefined,
    opacity: animate && !isLoaded ? 0 : 1,
  };

  // 容器样式
  const containerStyle: React.CSSProperties = {
    width: width ? (typeof width === 'number' ? `${width}px` : width) : undefined,
    height: height ? (typeof height === 'number' ? `${height}px` : height) : undefined,
    position: 'relative',
    overflow: 'hidden',
  };

  // 如果有自定义 children，使用自定义渲染
  if (children) {
    return (
      <div
        ref={containerRef}
        className={containerClassName}
        style={containerStyle}
        onClick={onClick}
      >
        {children({
          isLoading: !isLoaded && !isError,
          isLoaded,
          isError,
          ref: containerRef,
        })}
        {isVisible && (
          <img
            ref={imgRef}
            src={src}
            alt={alt}
            className={className}
            style={imageStyle}
            onLoad={handleLoad}
            onError={handleError}
          />
        )}
      </div>
    );
  }

  return (
    <div
      ref={containerRef}
      className={`relative overflow-hidden ${containerClassName}`}
      style={containerStyle}
      onClick={onClick}
      role="img"
      aria-label={alt}
    >
      {/* 占位符 */}
      {(!isLoaded || !isVisible) && renderPlaceholder()}

      {/* 实际图片 */}
      {isVisible && (
        <>
          <img
            ref={imgRef}
            src={isError && fallbackSrc ? fallbackSrc : src}
            alt={alt}
            className={`absolute inset-0 w-full h-full ${className} ${
              animate && !isLoaded ? 'opacity-0' : 'opacity-100'
            }`}
            style={imageStyle}
            onLoad={handleLoad}
            onError={handleError}
            loading={loading === 'auto' ? undefined : loading}
          />
          
          {/* 加载失败时的提示 */}
          {isError && !fallbackSrc && (
            <div className="absolute inset-0 flex items-center justify-center bg-gray-100 dark:bg-gray-800 text-gray-400 dark:text-gray-500">
              <div className="text-center">
                <svg className="w-10 h-10 mx-auto mb-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
                </svg>
                <span className="text-xs">图片加载失败</span>
              </div>
            </div>
          )}
        </>
      )}

      {/* 加载动画 */}
      {animate && !isLoaded && isVisible && (
        <div className="absolute inset-0 flex items-center justify-center">
          <div className="w-8 h-8 border-2 border-primary-200 border-t-primary-500 rounded-full animate-spin" />
        </div>
      )}
    </div>
  );
}

/**
 * LazyImageGrid - 懒加载图片网格组件
 * 用于图片墙、相册等场景
 */
export interface LazyImageGridProps {
  /** 图片数组 */
  images: Array<{
    src: string;
    alt?: string;
    fallbackSrc?: string;
  }>;
  /** 每列最小宽度 */
  columnWidth?: number;
  /** 列间距 */
  gap?: number;
  /** 图片高度（固定） */
  imageHeight?: number;
  /** 容器类名 */
  className?: string;
  /** 图片类名 */
  imageClassName?: string;
  /** 点击回调 */
  onImageClick?: (index: number) => void;
}

export function LazyImageGrid({
  images,
  columnWidth = 200,
  gap = 8,
  imageHeight = 200,
  className = '',
  imageClassName = '',
  onImageClick,
}: LazyImageGridProps): JSX.Element {
  const containerRef = useRef<HTMLDivElement>(null);
  const [columns, setColumns] = useState(4);

  // 监听容器宽度变化，动态调整列数
  useEffect(() => {
    if (!containerRef.current) return;

    const observer = new ResizeObserver((entries) => {
      for (const entry of entries) {
        const containerWidth = entry.contentRect.width;
        const newColumns = Math.max(1, Math.floor(containerWidth / columnWidth));
        setColumns(newColumns);
      }
    });

    observer.observe(containerRef.current);
    return () => observer.disconnect();
  }, [columnWidth]);

  return (
    <div
      ref={containerRef}
      className={`grid gap-2 ${className}`}
      style={{
        gridTemplateColumns: `repeat(${columns}, 1fr)`,
        gap: `${gap}px`,
      }}
    >
      {images.map((image, index) => (
        <LazyImage
          key={index}
          src={image.src}
          alt={image.alt || `图片 ${index + 1}`}
          fallbackSrc={image.fallbackSrc}
          className={imageClassName}
          height={imageHeight}
          cover
          onClick={() => onImageClick?.(index)}
        />
      ))}
    </div>
  );
}

/**
 * BlurHashPlaceholder - 使用纯色模糊作为占位符
 * 适合用于照片类应用
 */
export interface BlurHashPlaceholderProps {
  /** 主色调 */
  color?: string;
  /** 是否显示动画 */
  animate?: boolean;
}

export function BlurHashPlaceholder({
  color = '#e0e0e0',
  animate = true,
}: BlurHashPlaceholderProps): JSX.Element {
  return (
    <div
      className="absolute inset-0"
      style={{
        backgroundColor: color,
        backgroundImage: animate ? `
          linear-gradient(
            90deg,
            ${color} 0%,
            ${color}dd 50%,
            ${color} 100%
          )
        ` : undefined,
        backgroundSize: animate ? '200% 100%' : undefined,
        animation: animate ? 'shimmer 1.5s infinite' : undefined,
      }}
    >
      <style>{`
        @keyframes shimmer {
          0% { background-position: -200% 0; }
          100% { background-position: 200% 0; }
        }
      `}</style>
    </div>
  );
}

export default LazyImage;