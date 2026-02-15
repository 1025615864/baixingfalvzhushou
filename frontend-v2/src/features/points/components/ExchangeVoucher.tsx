/**
 * ExchangeVoucher - 兑换凭证组件
 * 功能：展示兑换订单信息（商品名称、兑换时间、积分消耗、订单号）、下载/分享功能
 * 支持打印样式的凭证卡片
 */

import { useState, useRef } from 'react';

import type { ExchangeOrder } from '../types';

interface ExchangeVoucherProps {
  order: ExchangeOrder;
  className?: string;
  onClose?: () => void;
}

/**
 * 复制订单号
 */
async function copyOrderNo(orderNo: string): Promise<boolean> {
  try {
    await navigator.clipboard.writeText(orderNo);
    return true;
  } catch {
    return false;
  }
}

/**
 * 下载凭证为图片
 */
function downloadVoucher(order: ExchangeOrder): void {
  // 创建 canvas 元素
  const canvas = document.createElement('canvas');
  const ctx = canvas.getContext('2d');
  if (!ctx) return;

  // 设置画布尺寸
  canvas.width = 600;
  canvas.height = 400;

  // 绘制背景
  const gradient = ctx.createLinearGradient(0, 0, 600, 400);
  gradient.addColorStop(0, '#FFF8E1');
  gradient.addColorStop(1, '#FFECB3');
  ctx.fillStyle = gradient;
  ctx.fillRect(0, 0, 600, 400);

  // 绘制边框
  ctx.strokeStyle = '#FFB300';
  ctx.lineWidth = 4;
  ctx.strokeRect(10, 10, 580, 380);

  // 绘制装饰线条
  ctx.beginPath();
  ctx.moveTo(0, 80);
  ctx.lineTo(600, 80);
  ctx.strokeStyle = '#FFB300';
  ctx.lineWidth = 2;
  ctx.stroke();

  // 绘制标题
  ctx.font = 'bold 32px "Microsoft YaHei", sans-serif';
  ctx.fillStyle = '#E65100';
  ctx.textAlign = 'center';
  ctx.fillText('兑换凭证', 300, 60);

  // 绘制内容
  ctx.font = '20px "Microsoft YaHei", sans-serif';
  ctx.fillStyle = '#333333';
  ctx.textAlign = 'left';

  const startY = 130;
  const lineHeight = 50;

  // 商品名称
  ctx.fillText(`商品名称：${order.productName}`, 50, startY);
  
  // 订单号
  ctx.fillText(`订单编号：${order.id}`, 50, startY + lineHeight);
  
  // 兑换时间
  ctx.fillText(`兑换时间：${formatDateTime(order.createdAt)}`, 50, startY + lineHeight * 2);
  
  // 积分消耗
  ctx.font = 'bold 24px "Microsoft YaHei", sans-serif';
  ctx.fillStyle = '#D32F2F';
  ctx.fillText(`消耗积分：${order.pointsSpent}`, 50, startY + lineHeight * 3);

  // 绘制底部提示
  ctx.font = '16px "Microsoft YaHei", sans-serif';
  ctx.fillStyle = '#666666';
  ctx.textAlign = 'center';
  ctx.fillText('请妥善保管此凭证，凭此领取您的商品', 300, 360);

  // 下载图片
  const link = document.createElement('a');
  link.download = `兑换凭证_${order.id}.png`;
  link.href = canvas.toDataURL('image/png');
  link.click();
}

/**
 * 格式化日期时间
 */
function formatDateTime(isoString: string): string {
  const date = new Date(isoString);
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  });
}

/**
 * 获取状态标签
 */
function getStatusLabel(status: ExchangeOrder['status']): string {
  const labels: Record<ExchangeOrder['status'], string> = {
    pending: '待处理',
    completed: '已完成',
    cancelled: '已取消',
  };
  return labels[status];
}

/**
 * 获取状态颜色
 */
function getStatusColor(status: ExchangeOrder['status']): string {
  const colors: Record<ExchangeOrder['status'], string> = {
    pending: 'bg-yellow-100 text-yellow-800',
    completed: 'bg-green-100 text-green-800',
    cancelled: 'bg-red-100 text-red-800',
  };
  return colors[status];
}

/**
 * 兑换凭证组件
 */
export function ExchangeVoucher({
  order,
  className = '',
  onClose,
}: ExchangeVoucherProps): JSX.Element {
  const [copied, setCopied] = useState(false);
  const voucherRef = useRef<HTMLDivElement>(null);

  /**
   * 处理复制订单号
   */
  const handleCopyOrderNo = async () => {
    const success = await copyOrderNo(order.id);
    if (success) {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  /**
   * 处理下载凭证
   */
  const handleDownload = () => {
    downloadVoucher(order);
  };

  /**
   * 处理分享
   */
  const handleShare = async () => {
    const shareData = {
      title: '积分兑换凭证',
      text: `我刚刚用 ${order.pointsSpent} 积分兑换了 ${order.productName}！`,
      url: window.location.href,
    };

    if (navigator.share) {
      try {
        await navigator.share(shareData);
      } catch {
        // 用户取消分享
      }
    } else {
      // 复制到剪贴板
      await copyOrderNo(`我用 ${order.pointsSpent} 积分兑换了 ${order.productName}！`);
      alert('分享内容已复制到剪贴板');
    }
  };

  /**
   * 处理打印
   */
  const handlePrint = () => {
    const printWindow = window.open('', '_blank');
    if (!printWindow) return;

    const voucherHtml = voucherRef.current?.outerHTML || '';
    printWindow.document.write(`
      <!DOCTYPE html>
      <html>
      <head>
        <title>兑换凭证 - ${order.productName}</title>
        <style>
          body { margin: 0; padding: 20px; font-family: 'Microsoft YaHei', sans-serif; }
          .print-voucher { max-width: 600px; margin: 0 auto; }
          @media print {
            body { padding: 0; }
            .no-print { display: none !important; }
          }
        </style>
      </head>
      <body>
        <div class="print-voucher">
          ${voucherHtml}
        </div>
        <div class="no-print" style="text-align: center; margin-top: 20px;">
          <button onclick="window.print()" style="padding: 10px 20px; font-size: 16px; cursor: pointer;">
            打印凭证
          </button>
        </div>
      </body>
      </html>
    `);
    printWindow.document.close();
  };

  return (
    <div className={`bg-white rounded-xl shadow-lg overflow-hidden ${className}`}>
      {/* 头部 */}
      <div className="bg-gradient-to-r from-amber-500 to-orange-500 px-6 py-4 flex items-center justify-between">
        <h3 className="text-white font-bold text-lg flex items-center gap-2">
          <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          兑换凭证
        </h3>
        <span className={`px-3 py-1 rounded-full text-xs font-medium ${getStatusColor(order.status)}`}>
          {getStatusLabel(order.status)}
        </span>
      </div>

      {/* 凭证内容 */}
      <div ref={voucherRef} className="p-6 bg-gradient-to-br from-amber-50 to-orange-50">
        {/* 商品信息 */}
        <div className="text-center mb-6">
          <div className="w-20 h-20 mx-auto mb-3 bg-gradient-to-br from-amber-400 to-orange-500 rounded-2xl flex items-center justify-center text-white text-3xl shadow-lg">
            🎁
          </div>
          <h4 className="text-xl font-bold text-gray-900 mb-1">{order.productName}</h4>
          <p className="text-amber-600 font-medium">-{order.pointsSpent} 积分</p>
        </div>

        {/* 订单详情 */}
        <div className="space-y-3 bg-white/70 rounded-lg p-4">
          <div className="flex justify-between items-center">
            <span className="text-gray-500 text-sm">订单编号</span>
            <div className="flex items-center gap-2">
              <span className="text-gray-900 font-mono text-sm">{order.id}</span>
              <button
                onClick={() => void handleCopyOrderNo()}
                className="p-1 hover:bg-gray-100 rounded transition-colors"
                title="复制订单号"
              >
                {copied ? (
                  <svg className="w-4 h-4 text-green-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  </svg>
                ) : (
                  <svg className="w-4 h-4 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
                  </svg>
                )}
              </button>
            </div>
          </div>
          
          <div className="flex justify-between items-center">
            <span className="text-gray-500 text-sm">兑换时间</span>
            <span className="text-gray-900 text-sm">{formatDateTime(order.createdAt)}</span>
          </div>

          {order.completedAt && (
            <div className="flex justify-between items-center">
              <span className="text-gray-500 text-sm">完成时间</span>
              <span className="text-gray-900 text-sm">{formatDateTime(order.completedAt)}</span>
            </div>
          )}

          <div className="flex justify-between items-center">
            <span className="text-gray-500 text-sm">消耗积分</span>
            <span className="text-red-500 font-bold">-{order.pointsSpent}</span>
          </div>
        </div>

        {/* 装饰性虚线 */}
        <div className="my-6 border-t-2 border-dashed border-amber-300" />

        {/* 提示信息 */}
        <div className="text-center text-sm text-gray-500">
          <p>请妥善保管此凭证，凭此领取您的商品</p>
          <p className="mt-1">如有问题请联系客服</p>
        </div>
      </div>

      {/* 操作按钮 */}
      <div className="px-6 py-4 bg-gray-50 border-t flex flex-wrap gap-3 justify-center">
        <button
          onClick={handleDownload}
          className="flex items-center gap-2 px-4 py-2 bg-amber-500 text-white rounded-lg hover:bg-amber-600 transition-colors"
        >
          <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
          </svg>
          下载凭证
        </button>
        
        <button
          onClick={() => void handleShare()}
          className="flex items-center gap-2 px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors"
        >
          <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8.684 13.342C8.886 12.938 9 12.482 9 12c0-.482-.114-.938-.316-1.342m0 2.684a3 3 0 110-2.684m0 2.684l6.632 3.316m-6.632-6l6.632-3.316m0 0a3 3 0 105.367-2.684 3 3 0 00-5.367 2.684zm0 9.316a3 3 0 105.368 2.684 3 3 0 00-5.368-2.684z" />
          </svg>
          分享
        </button>
        
        <button
          onClick={handlePrint}
          className="flex items-center gap-2 px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700 transition-colors"
        >
          <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 17h2a2 2 0 002-2v-4a2 2 0 00-2-2H5a2 2 0 00-2 2v4a2 2 0 002 2h2m2 4h6a2 2 0 002-2v-4a2 2 0 00-2-2H9a2 2 0 00-2 2v4a2 2 0 002 2zm8-12V5a2 2 0 00-2-2H9a2 2 0 00-2 2v4h10z" />
          </svg>
          打印
        </button>

        {onClose && (
          <button
            onClick={onClose}
            className="flex items-center gap-2 px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-100 transition-colors"
          >
            关闭
          </button>
        )}
      </div>
    </div>
  );
}

/**
 * 兑换凭证列表组件
 */
interface ExchangeVoucherListProps {
  orders: ExchangeOrder[];
  className?: string;
  onSelectOrder?: (order: ExchangeOrder) => void;
}

export function ExchangeVoucherList({
  orders,
  className = '',
  onSelectOrder,
}: ExchangeVoucherListProps): JSX.Element {
  if (orders.length === 0) {
    return (
      <div className={`text-center py-12 bg-gray-50 rounded-xl ${className}`}>
        <div className="w-16 h-16 mx-auto mb-4 bg-gray-200 rounded-full flex items-center justify-center text-3xl">
          📝
        </div>
        <p className="text-gray-500">暂无兑换记录</p>
      </div>
    );
  }

  return (
    <div className={`space-y-4 ${className}`}>
      {orders.map((order) => (
        <div
          key={order.id}
          onClick={() => onSelectOrder?.(order)}
          className="bg-white rounded-lg shadow-sm border border-gray-100 p-4 hover:shadow-md transition-shadow cursor-pointer"
        >
          <div className="flex items-start justify-between">
            <div className="flex items-center gap-3">
              <div className="w-12 h-12 bg-amber-100 rounded-lg flex items-center justify-center text-amber-600 text-xl">
                🎁
              </div>
              <div>
                <h4 className="font-medium text-gray-900">{order.productName}</h4>
                <p className="text-sm text-gray-500">{formatDateTime(order.createdAt)}</p>
              </div>
            </div>
            <div className="text-right">
              <span className={`inline-block px-2 py-1 rounded text-xs font-medium ${getStatusColor(order.status)}`}>
                {getStatusLabel(order.status)}
              </span>
              <p className="text-red-500 font-medium mt-1">-{order.pointsSpent}</p>
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}