/**
 * VirtualList - 虚拟滚动列表组件
 * 
 * 高性能列表渲染组件，只渲染可见区域的项目
 * 支持大数据量列表，优化渲染性能
 */

import React, { useRef, useCallback, useEffect, useState } from 'react';

/**
 * VirtualList 组件属性
 */
export interface VirtualListProps<T> {
  /** 数据数组 */
  data: T[];
  /** 渲染单个项目的函数 */
  renderItem: (item: T, index: number) => React.ReactNode;
  /** 每个项目的高度（像素），支持动态高度 */
  itemHeight: number | ((item: T, index: number) => number);
  /** 容器高度（像素），默认为 400 */
  containerHeight?: number;
  /** 额外渲染的项目数量（上下各渲染多少），默认为 5 */
  overscan?: number;
  /** 自定义类名 */
  className?: string;
  /** 加载中状态 */
  loading?: boolean;
  /** 加载中的占位组件 */
  loadingComponent?: React.ReactNode;
  /** 空数据时的占位组件 */
  emptyComponent?: React.ReactNode;
  /** 是否启用虚拟滚动，设为 false 则退化为普通列表 */
  enableVirtual?: boolean;
  /** 到达底部时的回调（用于无限滚动） */
  onReachEnd?: () => void;
  /** 滚动回调 */
  onScroll?: (scrollTop: number) => void;
}

/**
 * VirtualList 虚拟滚动列表组件
 * 
 * @example
 * ```tsx
 * // 基本使用 - 固定高度
 * <VirtualList
 *   data={items}
 *   itemHeight={60}
 *   renderItem={(item, index) => (
 *     <div key={item.id} className="item">
 *       {item.name}
 *     </div>
 *   )}
 * />
 * 
 * // 动态高度
 * <VirtualList
 *   data={items}
 *   itemHeight={(item) => item.expanded ? 120 : 60}
 *   renderItem={(item, index) => <ListItem key={item.id} data={item} />}
 *   overscan={10}
 * />
 * 
 * // 无限滚动
 * <VirtualList
 *   data={items}
 *   itemHeight={80}
 *   renderItem={(item) => <ItemCard key={item.id} data={item} />}
 *   onReachEnd={loadMore}
 * />
 * ```
 */
export function VirtualList<T>({
  data,
  renderItem,
  itemHeight,
  containerHeight = 400,
  overscan = 5,
  className = '',
  loading = false,
  loadingComponent,
  emptyComponent,
  enableVirtual = true,
  onReachEnd,
  onScroll,
}: VirtualListProps<T>): JSX.Element {
  // 容器引用
  const containerRef = useRef<HTMLDivElement>(null);
  
  // 滚动位置状态
  const [scrollTop, setScrollTop] = useState(0);
  // 可见区域高度
  const [viewportHeight, setViewportHeight] = useState(containerHeight);
  // 是否正在接近底部
  const [isNearEnd, setIsNearEnd] = useState(false);

  // 获取单个项目的高度
  const getItemHeight = useCallback((item: T, index: number): number => {
    return typeof itemHeight === 'function' ? itemHeight(item, index) : itemHeight;
  }, [itemHeight]);

  // 计算总高度
  const totalHeight = data.reduce((acc, item, index) => {
    return acc + getItemHeight(item, index);
  }, 0);

  // 计算每个项目的起始位置（用于动态高度）
  const itemPositions = React.useMemo(() => {
    if (!enableVirtual || typeof itemHeight !== 'function') {
      return null;
    }
    
    const positions: { top: number; height: number }[] = [];
    let currentTop = 0;
    
    for (let i = 0; i < data.length; i++) {
      const height = getItemHeight(data[i], i);
      positions.push({ top: currentTop, height });
      currentTop += height;
    }
    
    return positions;
  }, [data, getItemHeight, itemHeight, enableVirtual]);

  // 计算可见区域的项目
  const { startIndex, endIndex, offsetY } = React.useMemo(() => {
    if (!enableVirtual || data.length === 0) {
      return { startIndex: 0, endIndex: data.length, offsetY: 0 };
    }

    // 固定高度情况
    if (typeof itemHeight === 'number') {
      const startIndex = Math.max(0, Math.floor(scrollTop / itemHeight) - overscan);
      const endIndex = Math.min(
        data.length,
        Math.ceil((scrollTop + viewportHeight) / itemHeight) + overscan
      );
      const offsetY = startIndex * itemHeight;
      
      return { startIndex, endIndex, offsetY };
    }

    // 动态高度情况
    if (itemPositions) {
      let start = 0;
      let end = data.length;
      let offset = 0;

      // 找到第一个可见的项目
      for (let i = 0; i < itemPositions.length; i++) {
        const pos = itemPositions[i];
        if (pos.top + pos.height >= scrollTop - overscan * 50) {
          start = Math.max(0, i - overscan);
          offset = itemPositions[start]?.top || 0;
          break;
        }
      }

      // 找到最后一个可见的项目
      for (let i = itemPositions.length - 1; i >= 0; i--) {
        const pos = itemPositions[i];
        if (pos.top <= scrollTop + viewportHeight + overscan * 50) {
          end = Math.min(data.length, i + 1 + overscan);
          break;
        }
      }

      return { startIndex: start, endIndex: end, offsetY: offset };
    }

    return { startIndex: 0, endIndex: data.length, offsetY: 0 };
  }, [
    enableVirtual,
    data.length,
    itemHeight,
    viewportHeight,
    scrollTop,
    overscan,
    itemPositions,
  ]);

  // 处理滚动事件
  const handleScroll = useCallback((e: React.UIEvent<HTMLDivElement>) => {
    const newScrollTop = e.currentTarget.scrollTop;
    setScrollTop(newScrollTop);

    if (onScroll) {
      onScroll(newScrollTop);
    }

    // 检查是否接近底部
    if (onReachEnd && !isNearEnd) {
      const { scrollHeight, clientHeight, scrollTop: currentScrollTop } = e.currentTarget;
      const threshold = 100; // 距离底部 100px 时触发
      const distanceToEnd = scrollHeight - clientHeight - currentScrollTop;
      
      if (distanceToEnd < threshold) {
        setIsNearEnd(true);
        onReachEnd();
      }
    }
  }, [onScroll, onReachEnd, isNearEnd]);

  // 监听容器大小变化
  useEffect(() => {
    if (!containerRef.current) return;

    const observer = new ResizeObserver((entries) => {
      for (const entry of entries) {
        setViewportHeight(entry.contentRect.height);
      }
    });

    observer.observe(containerRef.current);
    return () => observer.disconnect();
  }, []);

  // 重置接近底部状态
  useEffect(() => {
    if (isNearEnd && scrollTop === 0) {
      setIsNearEnd(false);
    }
  }, [scrollTop, isNearEnd]);

  // 渲染加载中状态
  if (loading) {
    return (
      <div
        ref={containerRef}
        className={`w-full overflow-y-auto ${className}`}
        style={{ height: containerHeight }}
      >
        {loadingComponent || (
          <div className="flex items-center justify-center h-full">
            <div className="animate-spin h-8 w-8 border-4 border-primary-500 border-t-transparent rounded-full" />
          </div>
        )}
      </div>
    );
  }

  // 渲染空状态
  if (data.length === 0) {
    return (
      <div
        ref={containerRef}
        className={`w-full overflow-y-auto ${className}`}
        style={{ height: containerHeight }}
      >
        {emptyComponent || (
          <div className="flex items-center justify-center h-full">
            <div className="text-slate-400 text-center">
              <div className="text-4xl mb-2">📭</div>
              <div className="text-sm">暂无数据</div>
            </div>
          </div>
        )}
      </div>
    );
  }

  // 非虚拟滚动模式
  if (!enableVirtual) {
    return (
      <div
        ref={containerRef}
        className={`w-full overflow-y-auto ${className}`}
        style={{ height: containerHeight }}
        onScroll={handleScroll}
      >
        {data.map((item, index) => (
          <React.Fragment key={index}>
            {renderItem(item, index)}
          </React.Fragment>
        ))}
      </div>
    );
  }

  // 可见区域的项目
  const visibleItems = data.slice(startIndex, endIndex);

  return (
    <div
      ref={containerRef}
      className={`w-full overflow-y-auto ${className}`}
      style={{ height: containerHeight }}
      onScroll={handleScroll}
      role="list"
    >
      {/* 占位容器，保持正确的滚动高度 */}
      <div style={{ height: totalHeight, position: 'relative' }}>
        {/* 可见区域的项目 */}
        <div
          style={{
            position: 'absolute',
            top: offsetY,
            left: 0,
            right: 0,
          }}
        >
          {visibleItems.map((item, index) => {
            const actualIndex = startIndex + index;
            return (
              <React.Fragment key={actualIndex}>
                {renderItem(item, actualIndex)}
              </React.Fragment>
            );
          })}
        </div>
      </div>
    </div>
  );
}

/**
 * VirtualListGrid - 虚拟滚动网格组件
 * 支持多列布局的虚拟滚动
 */
export interface VirtualListGridProps<T> extends Omit<VirtualListProps<T>, 'itemHeight'> {
  /** 每列的最小宽度 */
  columnWidth?: number;
  /** 列间距 */
  gap?: number;
  /** 单个项目的渲染高度 */
  itemHeight: number;
}

export function VirtualListGrid<T>({
  data,
  renderItem,
  itemHeight,
  columnWidth = 280,
  gap = 16,
  containerHeight = 400,
  overscan = 3,
  className = '',
  loading = false,
  loadingComponent,
  emptyComponent,
  onReachEnd,
}: VirtualListGridProps<T>): JSX.Element {
  const containerRef = useRef<HTMLDivElement>(null);
  const [scrollTop, setScrollTop] = useState(0);
  const [containerWidth, setContainerWidth] = useState(0);

  // 计算列数
  const columns = Math.max(1, Math.floor(containerWidth / columnWidth));
  
  // 计算行数
  const rows = Math.ceil(data.length / columns);
  
  // 计算总高度
  const totalHeight = rows * itemHeight + (rows - 1) * gap;

  // 计算可见区域
  const startRow = Math.max(0, Math.floor(scrollTop / (itemHeight + gap)) - overscan);
  const endRow = Math.min(
    rows,
    Math.ceil((scrollTop + containerHeight) / (itemHeight + gap)) + overscan
  );

  // 可见区域的项目
  const startIndex = startRow * columns;
  const endIndex = Math.min(data.length, endRow * columns);
  const visibleItems = data.slice(startIndex, endIndex);

  // 处理滚动事件
  const handleScroll = useCallback((e: React.UIEvent<HTMLDivElement>) => {
    const newScrollTop = e.currentTarget.scrollTop;
    setScrollTop(newScrollTop);

    // 检查是否接近底部
    if (onReachEnd) {
      const { scrollHeight, clientHeight, scrollTop: currentScrollTop } = e.currentTarget;
      const threshold = 100;
      const distanceToEnd = scrollHeight - clientHeight - currentScrollTop;
      
      if (distanceToEnd < threshold) {
        onReachEnd();
      }
    }
  }, [onReachEnd]);

  // 监听容器宽度变化
  useEffect(() => {
    if (!containerRef.current) return;

    const observer = new ResizeObserver((entries) => {
      for (const entry of entries) {
        setContainerWidth(entry.contentRect.width);
      }
    });

    observer.observe(containerRef.current);
    return () => observer.disconnect();
  }, []);

  // 渲染加载中状态
  if (loading) {
    return (
      <div
        ref={containerRef}
        className={`w-full overflow-y-auto ${className}`}
        style={{ height: containerHeight }}
      >
        {loadingComponent || (
          <div className="flex items-center justify-center h-full">
            <div className="animate-spin h-8 w-8 border-4 border-primary-500 border-t-transparent rounded-full" />
          </div>
        )}
      </div>
    );
  }

  // 渲染空状态
  if (data.length === 0) {
    return (
      <div
        ref={containerRef}
        className={`w-full overflow-y-auto ${className}`}
        style={{ height: containerHeight }}
      >
        {emptyComponent || (
          <div className="flex items-center justify-center h-full">
            <div className="text-slate-400 text-center">
              <div className="text-4xl mb-2">📭</div>
              <div className="text-sm">暂无数据</div>
            </div>
          </div>
        )}
      </div>
    );
  }

  // 计算偏移量
  const offsetY = startRow * (itemHeight + gap);

  return (
    <div
      ref={containerRef}
      className={`w-full overflow-y-auto ${className}`}
      style={{ height: containerHeight }}
      onScroll={handleScroll}
      role="list"
    >
      <div style={{ height: totalHeight, position: 'relative' }}>
        <div
          style={{
            position: 'absolute',
            top: offsetY,
            left: 0,
            right: 0,
            display: 'grid',
            gridTemplateColumns: `repeat(${columns}, 1fr)`,
            gap: `${gap}px`,
            padding: `0 ${gap}px`,
          }}
        >
          {visibleItems.map((item, index) => {
            const actualIndex = startIndex + index;
            return (
              <React.Fragment key={actualIndex}>
                {renderItem(item, actualIndex)}
              </React.Fragment>
            );
          })}
        </div>
      </div>
    </div>
  );
}

export default VirtualList;