/**
 * useExchangeVoucher - 兑换凭证数据 Hook
 */

import { useState, useCallback } from 'react';

import type { ExchangeOrder } from '../types';

import { useExchangeOrders } from './usePoints';

interface UseExchangeVoucherOptions {
  /** 订单状态筛选 */
  status?: ExchangeOrder['status'];
  /** 每页数量 */
  pageSize?: number;
}

interface UseExchangeVoucherReturn {
  /** 订单列表 */
  orders: ExchangeOrder[];
  /** 当前选中的订单 */
  selectedOrder: ExchangeOrder | null;
  /** 是否正在加载 */
  isLoading: boolean;
  /** 是否还有更多数据 */
  hasMore: boolean;
  /** 当前页码 */
  currentPage: number;
  /** 选择订单 */
  selectOrder: (order: ExchangeOrder | null) => void;
  /** 加载更多 */
  loadMore: () => void;
  /** 刷新数据 */
  refresh: () => void;
  /** 分享订单 */
  shareOrder: (order: ExchangeOrder) => Promise<boolean>;
  /** 下载订单凭证 */
  downloadVoucher: (order: ExchangeOrder) => void;
  /** 导出订单列表 */
  exportOrders: () => void;
}

/**
 * 兑换凭证数据 Hook
 */
export function useExchangeVoucher(
  options: UseExchangeVoucherOptions = {}
): UseExchangeVoucherReturn {
  const { status, pageSize = 10 } = options;
  const [selectedOrder, setSelectedOrder] = useState<ExchangeOrder | null>(null);
  const [currentPage, setCurrentPage] = useState(1);

  // 获取订单列表
  const { data: orders = [], isLoading, refetch } = useExchangeOrders(status);

  // 计算是否还有更多
  const hasMore = orders.length >= currentPage * pageSize;

  /**
   * 选择订单
   */
  const selectOrder = useCallback((order: ExchangeOrder | null) => {
    setSelectedOrder(order);
  }, []);

  /**
   * 加载更多
   */
  const loadMore = useCallback(() => {
    if (!isLoading && hasMore) {
      setCurrentPage((prev) => prev + 1);
    }
  }, [isLoading, hasMore]);

  /**
   * 刷新数据
   */
  const refresh = useCallback(() => {
    setCurrentPage(1);
    void refetch();
  }, [refetch]);

  /**
   * 分享订单
   */
  const shareOrder = useCallback(async (order: ExchangeOrder): Promise<boolean> => {
    const shareData = {
      title: '积分兑换成功',
      text: `我用 ${order.pointsSpent} 积分兑换了 ${order.productName}`,
      url: window.location.href,
    };

    try {
      if (navigator.share) {
        await navigator.share(shareData);
        return true;
      } else {
        // 复制到剪贴板
        await navigator.clipboard.writeText(
          `我用 ${order.pointsSpent} 积分兑换了 ${order.productName}，订单号：${order.id}`
        );
        return true;
      }
    } catch {
      return false;
    }
  }, []);

  /**
   * 下载订单凭证
   */
  const downloadVoucher = useCallback((order: ExchangeOrder): void => {
    // 创建凭证数据
    const voucherData = {
      orderId: order.id,
      productName: order.productName,
      pointsSpent: order.pointsSpent,
      createdAt: order.createdAt,
      status: order.status,
    };

    // 转换为 JSON 并下载
    const blob = new Blob([JSON.stringify(voucherData, null, 2)], {
      type: 'application/json',
    });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `voucher_${order.id}.json`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  }, []);

  /**
   * 导出订单列表
   */
  const exportOrders = useCallback((): void => {
    if (orders.length === 0) return;

    // 创建 CSV 内容
    const headers = ['订单号', '商品名称', '消耗积分', '状态', '创建时间'];
    const rows = orders.map((order) => [
      order.id,
      order.productName,
      order.pointsSpent,
      order.status,
      new Date(order.createdAt).toLocaleString('zh-CN'),
    ]);

    const csvContent = [headers.join(','), ...rows.map((row) => row.join(','))].join('\n');

    // 添加 BOM 以支持中文
    const BOM = '\uFEFF';
    const blob = new Blob([BOM + csvContent], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `exchange_orders_${new Date().toISOString().split('T')[0]}.csv`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  }, [orders]);

  // 分页后的订单
  const paginatedOrders = orders.slice(0, currentPage * pageSize);

  return {
    orders: paginatedOrders,
    selectedOrder,
    isLoading,
    hasMore,
    currentPage,
    selectOrder,
    loadMore,
    refresh,
    shareOrder,
    downloadVoucher,
    exportOrders,
  };
}

/**
 * 单个订单详情 Hook
 */
export function useExchangeOrderDetail(orderId: string | null) {
  const { data: orders = [], isLoading } = useExchangeOrders();
  
  const order = orderId 
    ? orders.find((o) => o.id === orderId) || null
    : null;

  return {
    order,
    isLoading,
  };
}