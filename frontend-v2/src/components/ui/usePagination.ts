/**
 * usePagination - 分页逻辑 Hook
 *
 * 提供完整的分页状态管理和计算逻辑
 */

import { useState, useCallback, useMemo } from 'react';

/**
 * 分页选项配置
 */
export interface PaginationOptions {
  /** 初始页码 */
  initialPage?: number;
  /** 初始每页条数 */
  initialPageSize?: number;
  /** 可选的每页条数 */
  pageSizeOptions?: number[];
  /** 总条目数 */
  total?: number;
}

/**
 * 分页状态
 */
export interface PaginationState {
  /** 当前页码 */
  page: number;
  /** 每页条数 */
  pageSize: number;
  /** 总条目数 */
  total: number;
}

/**
 * 分页计算结果
 */
export interface PaginationResult {
  /** 当前页码 */
  page: number;
  /** 每页条数 */
  pageSize: number;
  /** 总条目数 */
  total: number;
  /** 总页数 */
  totalPages: number;
  /** 当前页起始索引 */
  startIndex: number;
  /** 当前页结束索引 */
  endIndex: number;
  /** 是否有上一页 */
  hasPreviousPage: boolean;
  /** 是否有下一页 */
  hasNextPage: boolean;
  /** 每页条数选项 */
  pageSizeOptions: number[];
  /** 跳转到指定页 */
  goToPage: (page: number) => void;
  /** 跳转到第一页 */
  goToFirstPage: () => void;
  /** 跳转到最后一页 */
  goToLastPage: () => void;
  /** 跳转到上一页 */
  goToPreviousPage: () => void;
  /** 跳转到下一页 */
  goToNextPage: () => void;
  /** 设置每页条数 */
  setPageSize: (size: number) => void;
  /** 设置总条目数 */
  setTotal: (total: number) => void;
  /** 获取分页参数（用于 API 请求） */
  getPaginationParams: () => { limit: number; offset: number };
  /** 获取分页范围（显示用） */
  getPageRange: (maxVisiblePages?: number) => number[];
}

/**
 * 分页逻辑 Hook
 *
 * @example
 * ```tsx
 * // 基本使用
 * const pagination = usePagination({ total: 100 });
 *
 * // 带初始值
 * const pagination = usePagination({
 *   initialPage: 1,
 *   initialPageSize: 20,
 *   pageSizeOptions: [10, 20, 50],
 *   total: 100
 * });
 *
 * // 用于 API 请求
 * const { page, pageSize, getPaginationParams } = pagination;
 * const { limit, offset } = getPaginationParams();
 * ```
 */
export function usePagination(options: PaginationOptions = {}): PaginationResult {
  const {
    initialPage = 1,
    initialPageSize = 20,
    pageSizeOptions = [10, 20, 50],
    total: initialTotal = 0,
  } = options;

  const [page, setPage] = useState(initialPage);
  const [pageSize, setPageSizeState] = useState(initialPageSize);
  const [total, setTotalState] = useState(initialTotal);

  // 计算总页数
  const totalPages = useMemo(() => {
    if (total <= 0) return 1;
    return Math.max(1, Math.ceil(total / pageSize));
  }, [total, pageSize]);

  // 计算当前页起始和结束索引
  const startIndex = useMemo(() => {
    return (page - 1) * pageSize;
  }, [page, pageSize]);

  const endIndex = useMemo(() => {
    return Math.min(startIndex + pageSize - 1, total - 1);
  }, [startIndex, pageSize, total]);

  // 检查是否有上一页和下一页
  const hasPreviousPage = page > 1;
  const hasNextPage = page < totalPages;

  // 跳转到指定页
  const goToPage = useCallback((newPage: number) => {
    const validPage = Math.max(1, Math.min(newPage, totalPages));
    setPage(validPage);
  }, [totalPages]);

  // 跳转到第一页
  const goToFirstPage = useCallback(() => {
    setPage(1);
  }, []);

  // 跳转到最后一页
  const goToLastPage = useCallback(() => {
    setPage(totalPages);
  }, [totalPages]);

  // 跳转到上一页
  const goToPreviousPage = useCallback(() => {
    if (hasPreviousPage) {
      setPage((prev) => prev - 1);
    }
  }, [hasPreviousPage]);

  // 跳转到下一页
  const goToNextPage = useCallback(() => {
    if (hasNextPage) {
      setPage((prev) => prev + 1);
    }
  }, [hasNextPage]);

  // 设置每页条数（同时重置到第一页）
  const setPageSize = useCallback((size: number) => {
    setPageSizeState(size);
    setPage(1);
  }, []);

  // 设置总条目数
  const setTotal = useCallback((newTotal: number) => {
    setTotalState(newTotal);
    // 如果当前页超出范围，调整到最后有效页
    setPage((prevPage) => {
      const newTotalPages = Math.max(1, Math.ceil(newTotal / pageSize));
      return Math.min(prevPage, newTotalPages);
    });
  }, [pageSize]);

  // 获取分页参数（用于 API 请求）
  const getPaginationParams = useCallback(() => {
    return {
      limit: pageSize,
      offset: (page - 1) * pageSize,
    };
  }, [page, pageSize]);

  // 获取可显示的页码范围
  const getPageRange = useCallback((maxVisiblePages: number = 5): number[] => {
    if (totalPages <= maxVisiblePages) {
      return Array.from({ length: totalPages }, (_, i) => i + 1);
    }

    const halfVisible = Math.floor(maxVisiblePages / 2);
    let startPage = Math.max(1, page - halfVisible);
    const endPage = Math.min(totalPages, startPage + maxVisiblePages - 1);

    // 调整范围确保显示足够的页数
    if (endPage - startPage + 1 < maxVisiblePages) {
      startPage = Math.max(1, endPage - maxVisiblePages + 1);
    }

    return Array.from({ length: endPage - startPage + 1 }, (_, i) => startPage + i);
  }, [page, totalPages]);

  return {
    page,
    pageSize,
    total,
    totalPages,
    startIndex,
    endIndex,
    hasPreviousPage,
    hasNextPage,
    pageSizeOptions,
    goToPage,
    goToFirstPage,
    goToLastPage,
    goToPreviousPage,
    goToNextPage,
    setPageSize,
    setTotal,
    getPaginationParams,
    getPageRange,
  };
}

export default usePagination;