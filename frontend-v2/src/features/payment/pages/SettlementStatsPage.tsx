/**
 * Settlement Stats Page
 * 结算统计页面（管理员用）
 */

import { useState, useMemo } from 'react';
import { Download, Calendar, TrendingUp, DollarSign, ShoppingCart, Percent } from 'lucide-react';

import { Card, Button, Badge } from '@/components/ui';

import {
  useSettlementStats,
  useExportSettlementReport,
} from '../hooks/useSettlementStats';

/**
 * 格式化金额
 */
function formatMoney(amount: number): string {
  return `¥${amount.toFixed(2)}`;
}

/**
 * 格式化百分比
 */
function formatPercent(value: number): string {
  return `${(value * 100).toFixed(1)}%`;
}

/**
 * 获取支付方式标签
 */
function getPaymentMethodLabel(method: string): string {
  const labels: Record<string, string> = {
    alipay: '支付宝',
    wechat: '微信支付',
    balance: '余额支付',
    ikunpay: '爱坤支付',
  };
  return labels[method] ?? method;
}

/**
 * 结算统计页面
 */
export function SettlementStatsPage(): JSX.Element {
  const [startDate, setStartDate] = useState(() => {
    const date = new Date();
    date.setDate(date.getDate() - 30);
    return date.toISOString().split('T')[0];
  });
  const [endDate, setEndDate] = useState(() => {
    return new Date().toISOString().split('T')[0];
  });
  const [groupBy, setGroupBy] = useState<'day' | 'week' | 'month'>('day');

  // 数据查询
  const { data: statsData, isLoading } = useSettlementStats({
    startDate,
    endDate,
    groupBy,
  });

  // Mutations
  const exportMutation = useExportSettlementReport();

  const summary = statsData?.summary;
  const items = statsData?.items ?? [];
  const methodStats = statsData?.methodStats ?? [];

  // 处理导出
  const handleExport = (format: 'csv' | 'excel'): void => {
    exportMutation.mutate({ startDate, endDate, format });
  };

  // 趋势数据（预留用于图表展示）
   
  const _trendData = useMemo(() => {
    if (!statsData?.trend) return null;
    return {
      labels: statsData.trend.dates,
      amounts: statsData.trend.amounts,
      counts: statsData.trend.counts,
    };
  }, [statsData]);

  return (
    <div className="container mx-auto py-6">
      {/* 页面头部 */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">结算统计</h1>
          <p className="text-slate-600 mt-1">查看和分析平台结算数据</p>
        </div>
        <div className="flex gap-2">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => handleExport('csv')}
            disabled={exportMutation.isPending}
          >
            <Download className="h-4 w-4 mr-1" />
            导出CSV
          </Button>
          <Button
            variant="ghost"
            size="sm"
            onClick={() => handleExport('excel')}
            disabled={exportMutation.isPending}
          >
            <Download className="h-4 w-4 mr-1" />
            导出Excel
          </Button>
        </div>
      </div>

      {/* 日期筛选 */}
      <Card className="mb-6">
        <div className="p-4 flex flex-wrap items-center gap-4">
          <div className="flex items-center gap-2">
            <Calendar className="h-4 w-4 text-slate-500" />
            <span className="text-sm text-slate-700">时间范围：</span>
          </div>
          <div className="flex items-center gap-2">
            <input
              type="date"
              value={startDate}
              onChange={(e: React.ChangeEvent<HTMLInputElement>) => setStartDate(e.target.value)}
              className="px-3 py-1.5 border border-slate-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            />
            <span className="text-slate-500">至</span>
            <input
              type="date"
              value={endDate}
              onChange={(e: React.ChangeEvent<HTMLInputElement>) => setEndDate(e.target.value)}
              className="px-3 py-1.5 border border-slate-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            />
          </div>
          <div className="flex items-center gap-2 ml-auto">
            <span className="text-sm text-slate-700">分组：</span>
            <select
              value={groupBy}
              onChange={(e) => setGroupBy(e.target.value as 'day' | 'week' | 'month')}
              className="px-3 py-1.5 border border-slate-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            >
              <option value="day">按天</option>
              <option value="week">按周</option>
              <option value="month">按月</option>
            </select>
          </div>
        </div>
      </Card>

      {/* 汇总卡片 */}
      {summary && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
          <Card className="p-4">
            <div className="flex items-center gap-2 mb-2">
              <DollarSign className="h-5 w-5 text-blue-500" />
              <span className="text-sm text-slate-500">总交易额</span>
            </div>
            <p className="text-2xl font-bold text-slate-900">{formatMoney(summary.totalAmount)}</p>
            <p className="text-sm text-slate-600 mt-1">{summary.totalCount} 笔订单</p>
          </Card>
          <Card className="p-4">
            <div className="flex items-center gap-2 mb-2">
              <ShoppingCart className="h-5 w-5 text-green-500" />
              <span className="text-sm text-slate-500">成功交易</span>
            </div>
            <p className="text-2xl font-bold text-green-600">{formatMoney(summary.successAmount)}</p>
            <p className="text-sm text-slate-600 mt-1">{summary.successCount} 笔成功</p>
          </Card>
          <Card className="p-4">
            <div className="flex items-center gap-2 mb-2">
              <TrendingUp className="h-5 w-5 text-orange-500" />
              <span className="text-sm text-slate-500">退款金额</span>
            </div>
            <p className="text-2xl font-bold text-orange-600">{formatMoney(summary.refundAmount)}</p>
            <p className="text-sm text-slate-600 mt-1">{summary.refundCount} 笔退款</p>
          </Card>
          <Card className="p-4">
            <div className="flex items-center gap-2 mb-2">
              <Percent className="h-5 w-5 text-purple-500" />
              <span className="text-sm text-slate-500">成功率</span>
            </div>
            <p className="text-2xl font-bold text-purple-600">{formatPercent(summary.successRate)}</p>
            <p className="text-sm text-slate-600 mt-1">客单价 {formatMoney(summary.averageOrderValue)}</p>
          </Card>
        </div>
      )}

      {/* 详细数据 */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* 支付方式统计 */}
        <Card className="lg:col-span-1">
          <div className="p-4 border-b border-slate-200">
            <h3 className="font-semibold text-slate-900">支付方式分布</h3>
          </div>
          <div className="p-4">
            {isLoading ? (
              <div className="space-y-3">
                {Array.from({ length: 4 }).map((_, i) => (
                  <div key={i} className="h-12 bg-slate-100 rounded animate-pulse" />
                ))}
              </div>
            ) : (
              <div className="space-y-4">
                {methodStats.map((stat) => (
                  <div key={stat.method} className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <Badge variant="default" size="sm">
                        {getPaymentMethodLabel(stat.method)}
                      </Badge>
                      <span className="text-sm text-slate-500">{stat.count} 笔</span>
                    </div>
                    <div className="text-right">
                      <p className="font-medium text-slate-900">{formatMoney(stat.amount)}</p>
                      <p className="text-xs text-slate-500">{stat.percentage.toFixed(1)}%</p>
                    </div>
                  </div>
                ))}
                {!methodStats.length && (
                  <p className="text-center text-slate-500 py-4">暂无数据</p>
                )}
              </div>
            )}
          </div>
        </Card>

        {/* 每日统计 */}
        <Card className="lg:col-span-2">
          <div className="p-4 border-b border-slate-200">
            <h3 className="font-semibold text-slate-900">每日统计</h3>
          </div>
          <div className="p-4">
            {isLoading ? (
              <div className="space-y-3">
                {Array.from({ length: 5 }).map((_, i) => (
                  <div key={i} className="h-16 bg-slate-100 rounded animate-pulse" />
                ))}
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr className="text-left text-sm text-slate-500 border-b border-slate-200">
                      <th className="pb-2 font-medium">日期</th>
                      <th className="pb-2 font-medium text-right">订单数</th>
                      <th className="pb-2 font-medium text-right">成功金额</th>
                      <th className="pb-2 font-medium text-right">退款金额</th>
                      <th className="pb-2 font-medium text-right">手续费</th>
                      <th className="pb-2 font-medium text-right">净收入</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {items.map((item) => (
                      <tr key={item.date} className="text-sm">
                        <td className="py-3 text-slate-900">{item.date}</td>
                        <td className="py-3 text-right text-slate-600">{item.totalCount}</td>
                        <td className="py-3 text-right text-green-600">{formatMoney(item.successAmount)}</td>
                        <td className="py-3 text-right text-orange-600">{formatMoney(item.refundAmount)}</td>
                        <td className="py-3 text-right text-slate-600">{formatMoney(item.feeAmount)}</td>
                        <td className="py-3 text-right font-medium text-slate-900">{formatMoney(item.netAmount)}</td>
                      </tr>
                    ))}
                    {!items.length && (
                      <tr>
                        <td colSpan={6} className="py-8 text-center text-slate-500">
                          暂无数据
                        </td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </Card>
      </div>
    </div>
  );
}
