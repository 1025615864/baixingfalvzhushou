/**
 * 虚拟列表组件
 * 使用虚拟滚动技术优化长列表渲染性能
 */

import { useRef, useState, useEffect, useCallback, memo, useMemo } from 'react';

interface VirtualListProps<T> {
  /** 列表数据 */
  items: T[];
  /** 每项高度（像素），可以是固定值或函数 */
  itemHeight: number | ((index: number, item: T) => number);
  /** 容器高度（像素） */
  height: number;
  /** 渲染每一项的函数 */
  renderItem: (item: T, index: number) => React.ReactNode;
  /** 预渲染的额外项数（上下各多渲染几项） */
  overscan?: number;
  /** 容器类名 */
  className?: string;
  /** 内容区域类名 */
  contentClassName?: string;
  /** 空列表时显示的内容 */
  emptyContent?: React.ReactNode;
  /** 滚动事件回调 */
  onScroll?: (scrollTop: number) => void;
  /** 列表项的唯一标识符获取函数 */
  getItemKey?: (item: T, index: number) => string | number;
}

interface VirtualListHandle {
  /** 滚动到指定索引 */
  scrollToIndex: (index: number, align?: 'start' | 'center' | 'end') => void;
  /** 滚动到顶部 */
  scrollToTop: () => void;
  /** 获取当前滚动位置 */
  getScrollTop: () => number;
}

/**
 * 虚拟列表组件
 * 
 * @example
 * ```tsx
 * <VirtualList
 *   items={data}
 *   itemHeight={50}
 *   height={400}
 *   renderItem={(item, index) => (
 *     <div key={index}>{item.name}</div>
 *   )}
 * />
 * ```
 */
export const VirtualList = memo(function VirtualList<T>({
  items,
  itemHeight,
  height,
  renderItem,
  overscan = 3,
  className = '',
  contentClassName = '',
  emptyContent,
  onScroll,
  getItemKey,
}: VirtualListProps<T>): JSX.Element {
  const containerRef = useRef<HTMLDivElement>(null);
  const [scrollTop, setScrollTop] = useState(0);

  // 计算每个项目的位置信息
  const itemPositions = useMemo(() => {
    const positions: { top: number; height: number }[] = [];
    let currentTop = 0;

    items.forEach((item, index) => {
      const h = typeof itemHeight === 'function' ? itemHeight(index, item) : itemHeight;
      positions.push({ top: currentTop, height: h });
      currentTop += h;
    });

    return positions;
  }, [items, itemHeight]);

  // 计算总高度
  const totalHeight = useMemo(() => {
    if (itemPositions.length === 0) return 0;
    const lastItem = itemPositions[itemPositions.length - 1];
    return lastItem.top + lastItem.height;
  }, [itemPositions]);

  // 计算可见范围
  const visibleRange = useMemo(() => {
    if (items.length === 0) {
      return { startIndex: 0, endIndex: 0 };
    }

    // 二分查找起始索引
    let startIndex = 0;
    let endIndex = items.length - 1;

    // 查找第一个可见项
    for (let i = 0; i < itemPositions.length; i++) {
      const pos = itemPositions[i];
      if (pos.top + pos.height > scrollTop) {
        startIndex = Math.max(0, i - overscan);
        break;
      }
    }

    // 查找最后一个可见项
    const viewportBottom = scrollTop + height;
    for (let i = startIndex; i < itemPositions.length; i++) {
      const pos = itemPositions[i];
      if (pos.top > viewportBottom) {
        endIndex = Math.min(items.length - 1, i + overscan);
        break;
      }
    }

    return { startIndex, endIndex };
  }, [scrollTop, height, items.length, itemPositions, overscan]);

  // 处理滚动事件
  const handleScroll = useCallback((e: React.UIEvent<HTMLDivElement>) => {
    const target = e.currentTarget;
    const newScrollTop = target.scrollTop;
    setScrollTop(newScrollTop);
    onScroll?.(newScrollTop);
  }, [onScroll]);

  // 渲染空内容
  if (items.length === 0 && emptyContent) {
    return (
      <div
        className={className}
        style={{ height, overflow: 'auto' }}
      >
        {emptyContent}
      </div>
    );
  }

  // 获取可见项的偏移量
  const offsetY = itemPositions[visibleRange.startIndex]?.top ?? 0;

  return (
    <div
      ref={containerRef}
      className={className}
      style={{ height, overflow: 'auto', position: 'relative' }}
      onScroll={handleScroll}
    >
      <div
        className={contentClassName}
        style={{
          height: totalHeight,
          position: 'relative',
        }}
      >
        <div
          style={{
            position: 'absolute',
            top: offsetY,
            left: 0,
            right: 0,
          }}
        >
          {items.slice(visibleRange.startIndex, visibleRange.endIndex + 1).map((item, index) => {
            const actualIndex = visibleRange.startIndex + index;
            const key = getItemKey ? getItemKey(item, actualIndex) : actualIndex;
            return (
              <div
                key={key}
                style={{
                  height: itemPositions[actualIndex]?.height,
                  overflow: 'hidden',
                }}
              >
                {renderItem(item, actualIndex)}
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}) as <T>(props: VirtualListProps<T>) => JSX.Element;

/**
 * 带有 ref 的虚拟列表组件
 * 提供命令式滚动控制 API
 */
export const VirtualListWithRef = memo(function VirtualListWithRef<T>(
  props: VirtualListProps<T> & { ref?: React.Ref<VirtualListHandle> }
): JSX.Element {
  const { ref, items, itemHeight, height, ...restProps } = props;

  // 暴露给父组件的方法
  const handleRef = useCallback(() => {
    if (ref) {
      const handle: VirtualListHandle = {
        scrollToIndex: (index: number, align: 'start' | 'center' | 'end' = 'start') => {
          if (!items[index]) return;
          
          const h = typeof itemHeight === 'function'
            ? itemHeight(index, items[index])
            : itemHeight;
          
          let scrollTop = 0;
          if (align === 'start') {
            scrollTop = index * h;
          } else if (align === 'center') {
            scrollTop = index * h - height / 2 + h / 2;
          } else {
            scrollTop = index * h - height + h;
          }
          
          return Math.max(0, scrollTop);
        },
        scrollToTop: () => 0,
        getScrollTop: () => 0,
      };
      
      if (typeof ref === 'function') {
        ref(handle);
      } else {
        (ref as React.MutableRefObject<VirtualListHandle>).current = handle;
      }
    }
  }, [ref, items, itemHeight, height]);

  // 使用 useEffect 同步 ref
  useEffect(() => {
    handleRef();
  }, [handleRef]);

  return (
    <VirtualList
      items={items}
      itemHeight={itemHeight}
      height={height}
      {...restProps}
    />
  );
}) as <T>(props: VirtualListProps<T> & { ref?: React.Ref<VirtualListHandle> }) => JSX.Element;

export default VirtualList;