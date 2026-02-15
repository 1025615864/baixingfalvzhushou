/**
 * ContractComplianceDashboard - 合同合规统计仪表盘
 *
 * 展示企业合同合规相关的统计数据、风险分布、审查记录和合规趋势
 */

import { useMemo } from 'react';

import { StatCard } from '../../analytics/components/StatCard';
import { TrendChart } from '../../analytics/components/TrendChart';
import { FunnelChart } from '../../analytics/components/FunnelChart';
import { DataTable } from '../../analytics/components/DataTable';
import { EmptyState } from '../../../components/ui/EmptyState';
import type { StatCardData, TrendDataPoint, FunnelChartDataItem, DataTableColumn } from '../../analytics/types';

// ==================== 类型定义 ====================

/**
 * 合同统计数据
 */
interface ContractStats {
  /** 总合同数 */
  total: number;
  /** 待审查数量 */
  pending: number;
  /** 已审查数量 */
  reviewed: number;
  /** 风险合同数 */
  risk: number;
  /** 合规率百分比 */
  complianceRate: number;
}

/**
 * 风险等级分布项
 */
interface RiskDistributionItem {
  /** 风险等级 */
  level: 'low' | 'medium' | 'high' | 'critical';
  /** 数量 */
  count: number;
  /** 百分比 */
  percentage: number;
}

/**
 * 审查记录
 */
interface ReviewRecord extends Record<string, unknown> {
  /** 记录ID */
  id: number;
  /** 合同名称 */
  contractName: string;
  /** 审查状态 */
  status: 'pending' | 'approved' | 'rejected' | 'needs_review';
  /** 审查时间 */
  reviewedAt: string;
  /** 风险等级 */
  riskLevel: 'low' | 'medium' | 'high' | 'critical';
  /** 审查员 */
  reviewer?: string;
}

/**
 * 合同合规仪表盘属性
 */
interface ContractComplianceDashboardProps {
  /** 企业账户ID */
  accountId: number;
  /** 统计数据 */
  stats?: ContractStats;
  /** 风险分布数据 */
  riskDistribution?: RiskDistributionItem[];
  /** 审查记录列表 */
  reviewRecords?: ReviewRecord[];
  /** 合规率趋势数据 */
  complianceTrend?: TrendDataPoint[];
  /** 加载状态 */
  isLoading?: boolean;
  /** 错误状态 */
  error?: Error | null;
}

// ==================== 常量定义 ====================

const RISK_LEVEL_LABELS: Record<string, string> = {
  low: '低风险',
  medium: '中风险',
  high: '高风险',
  critical: '严重风险',
};

const RISK_LEVEL_COLORS: Record<string, string> = {
  low: '#22c55e', // green-500
  medium: '#eab308', // yellow-500
  high: '#f97316', // orange-500
  critical: '#ef4444', // red-500
};

const REVIEW_STATUS_LABELS: Record<string, string> = {
  pending: '待审查',
  approved: '已通过',
  rejected: '已驳回',
  needs_review: '需复审',
};

const REVIEW_STATUS_COLORS: Record<string, string> = {
  pending: 'bg-yellow-100 text-yellow-800',
  approved: 'bg-green-100 text-green-800',
  rejected: 'bg-red-100 text-red-800',
  needs_review: 'bg-orange-100 text-orange-800',
};

// ==================== 辅助函数 ====================

/**
 * 格式化日期
 */
function formatDate(dateString: string): string {
  const date = new Date(dateString);
  return date.toLocaleDateString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  });
}

/**
 * 转换风险分布为漏斗图数据
 */
function convertRiskToFunnelData(riskDistribution: RiskDistributionItem[]): FunnelChartDataItem[] {
  return riskDistribution.map((item) => ({
    name: RISK_LEVEL_LABELS[item.level] || item.level,
    value: item.count,
    conversionRate: item.percentage,
    dropRate: 0,
    color: RISK_LEVEL_COLORS[item.level],
  }));
}

// ==================== 子组件 ====================

/**
 * 统计卡片骨架屏
 */
function StatsSkeleton(): JSX.Element {
  return (
    <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
      {[1, 2, 3, 4].map((i) => (
        <div key={i} className="rounded-lg bg-white p-6 shadow-sm">
          <div className="animate-pulse">
            <div className="flex items-center justify-between">
              <div className="h-4 w-24 rounded bg-gray-200"></div>
              <div className="h-10 w-10 rounded-full bg-gray-200"></div>
            </div>
            <div className="mt-4 h-8 w-32 rounded bg-gray-200"></div>
            <div className="mt-2 h-4 w-20 rounded bg-gray-200"></div>
          </div>
        </div>
      ))}
    </div>
  );
}

/**
 * 图表骨架屏
 */
function ChartSkeleton({ height = 300 }: { height?: number }): JSX.Element {
  return (
    <div className="rounded-lg bg-white p-6 shadow-sm">
      <div className="animate-pulse">
        <div className="mb-4 h-6 w-32 rounded bg-gray-200"></div>
        <div className="rounded-lg bg-gray-200" style={{ height: `${height}px` }}></div>
      </div>
    </div>
  );
}

/**
 * 表格骨架屏
 */
function TableSkeleton(): JSX.Element {
  return (
    <div className="rounded-lg bg-white shadow-sm">
      <div className="animate-pulse p-6">
        <div className="mb-4 h-6 w-32 rounded bg-gray-200"></div>
        <div className="space-y-3">
          <div className="h-10 rounded bg-gray-200"></div>
          {[1, 2, 3, 4, 5].map((i) => (
            <div key={i} className="h-12 rounded bg-gray-100"></div>
          ))}
        </div>
      </div>
    </div>
  );
}

// ==================== 主组件 ====================

/**
 * 合同合规统计仪表盘组件
 */
export function ContractComplianceDashboard({
  accountId,
  stats,
  riskDistribution,
  reviewRecords,
  complianceTrend,
  isLoading = false,
  error = null,
}: ContractComplianceDashboardProps): JSX.Element {
  // 构建统计卡片数据
  const statCardsData: StatCardData[] = useMemo(() => {
    if (!stats) return [];

    return [
      {
        title: '总合同数',
        value: stats.total,
        change: stats.total > 0 ? 12.5 : 0,
        changeType: 'increase',
        icon: 'Activity',
      },
      {
        title: '待审查',
        value: stats.pending,
        change: stats.pending > 0 ? -5.2 : 0,
        changeType: 'decrease',
        icon: 'Clock',
      },
      {
        title: '已审查',
        value: stats.reviewed,
        change: stats.reviewed > 0 ? 8.3 : 0,
        changeType: 'increase',
        icon: 'Users',
      },
      {
        title: '风险合同',
        value: stats.risk,
        change: stats.risk > 0 ? -15.0 : 0,
        changeType: 'decrease',
        icon: 'Activity',
      },
    ];
  }, [stats]);

  // 审查记录表格列定义
  const reviewColumns: DataTableColumn<ReviewRecord>[] = useMemo(
    () => [
      {
        key: 'contractName',
        title: '合同名称',
        dataIndex: 'contractName',
        render: (_record, index) => {
          const record = reviewRecords?.[index];
          return record ? (
            <span className="font-medium text-gray-900">{record.contractName}</span>
          ) : <span />;
        },
      },
      {
        key: 'status',
        title: '审查状态',
        dataIndex: 'status',
        render: (_record, index) => {
          const record = reviewRecords?.[index];
          return record ? (
            <span
              className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${REVIEW_STATUS_COLORS[record.status] || 'bg-gray-100 text-gray-800'}`}
            >
              {REVIEW_STATUS_LABELS[record.status] || record.status}
            </span>
          ) : <span />;
        },
      },
      {
        key: 'riskLevel',
        title: '风险等级',
        dataIndex: 'riskLevel',
        render: (_record, index) => {
          const record = reviewRecords?.[index];
          return record ? (
            <div className="flex items-center gap-2">
              <div
                className="h-2 w-2 rounded-full"
                style={{ backgroundColor: RISK_LEVEL_COLORS[record.riskLevel] || '#9ca3af' }}
              />
              <span className="text-sm text-gray-600">
                {RISK_LEVEL_LABELS[record.riskLevel] || record.riskLevel}
              </span>
            </div>
          ) : <span />;
        },
      },
      {
        key: 'reviewer',
        title: '审查员',
        dataIndex: 'reviewer',
        render: (_record, index) => {
          const record = reviewRecords?.[index];
          return record ? (
            <span className="text-sm text-gray-600">{record.reviewer || '-'}</span>
          ) : <span />;
        },
      },
      {
        key: 'reviewedAt',
        title: '审查时间',
        dataIndex: 'reviewedAt',
        render: (_record, index) => {
          const record = reviewRecords?.[index];
          return record ? (
            <span className="text-sm text-gray-500">{formatDate(record.reviewedAt)}</span>
          ) : <span />;
        },
        sorter: (a: ReviewRecord, b: ReviewRecord) =>
          new Date(a.reviewedAt).getTime() - new Date(b.reviewedAt).getTime(),
      },
    ],
    [reviewRecords]
  );

  // 错误状态
  if (error) {
    return (
      <div className="space-y-6">
        <div>
          <h2 className="text-xl font-semibold text-gray-900">合同合规仪表盘</h2>
          <p className="text-sm text-gray-500 mt-1">监控企业合同审查与合规状态</p>
        </div>
        <EmptyState
          icon="error"
          title="加载失败"
          description={error.message || '无法加载合同合规数据，请稍后重试'}
        />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* 标题区域 */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h2 className="text-xl font-semibold text-gray-900 dark:text-gray-100">
            合同合规仪表盘
          </h2>
          <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
            监控企业合同审查与合规状态
          </p>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-sm text-gray-500 dark:text-gray-400">
            企业ID: {accountId}
          </span>
        </div>
      </div>

      {/* 统计卡片区域 */}
      {isLoading ? (
        <StatsSkeleton />
      ) : (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {statCardsData.map((stat, index) => (
            <StatCard key={`${stat.title}-${index}`} data={stat} />
          ))}
        </div>
      )}

      {/* 合规率概览 */}
      {!isLoading && stats && (
        <div className="rounded-lg bg-white dark:bg-gray-800 p-6 shadow-sm">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
                整体合规率
              </h3>
              <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
                基于已审查合同的合规评估
              </p>
            </div>
            <div className="text-right">
              <div className="text-3xl font-bold text-blue-600 dark:text-blue-400">
                {stats.complianceRate.toFixed(1)}%
              </div>
              <div className="text-sm text-gray-500 dark:text-gray-400 mt-1">
                {stats.reviewed > 0
                  ? `${stats.reviewed} 份合同已审查`
                  : '暂无审查数据'}
              </div>
            </div>
          </div>
          <div className="mt-4">
            <div className="h-3 w-full rounded-full bg-gray-200 dark:bg-gray-700">
              <div
                className="h-3 rounded-full bg-blue-600 transition-all duration-500"
                style={{ width: `${Math.min(stats.complianceRate, 100)}%` }}
              />
            </div>
          </div>
        </div>
      )}

      {/* 图表区域 */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        {/* 风险等级分布 */}
        {isLoading ? (
          <ChartSkeleton height={320} />
        ) : riskDistribution && riskDistribution.length > 0 ? (
          <FunnelChart
            data={convertRiskToFunnelData(riskDistribution)}
            title="风险等级分布"
            showLegend={true}
            showRates={true}
          />
        ) : (
          <div className="rounded-lg bg-white dark:bg-gray-800 p-6 shadow-sm">
            <h3 className="mb-4 text-lg font-semibold text-gray-900 dark:text-gray-100">
              风险等级分布
            </h3>
            <EmptyState
              icon="document"
              title="暂无数据"
              description="暂无风险分布数据"
              compact={true}
            />
          </div>
        )}

        {/* 合规率趋势 */}
        {isLoading ? (
          <ChartSkeleton height={320} />
        ) : complianceTrend && complianceTrend.length > 0 ? (
          <TrendChart
            data={complianceTrend}
            title="合规率趋势（近30天）"
            height={300}
            showArea={true}
            color="#3b82f6"
            unit="%"
          />
        ) : (
          <div className="rounded-lg bg-white dark:bg-gray-800 p-6 shadow-sm">
            <h3 className="mb-4 text-lg font-semibold text-gray-900 dark:text-gray-100">
              合规率趋势
            </h3>
            <EmptyState
              icon="document"
              title="暂无数据"
              description="暂无合规率趋势数据"
              compact={true}
            />
          </div>
        )}
      </div>

      {/* 最近审查记录 */}
      {isLoading ? (
        <TableSkeleton />
      ) : reviewRecords && reviewRecords.length > 0 ? (
        <DataTable<ReviewRecord>
          data={reviewRecords}
          columns={reviewColumns}
          title="最近审查记录"
          rowKey="id"
          striped={true}
          size="middle"
        />
      ) : (
        <div className="rounded-lg bg-white dark:bg-gray-800 p-6 shadow-sm">
          <h3 className="mb-4 text-lg font-semibold text-gray-900 dark:text-gray-100">
            最近审查记录
          </h3>
          <EmptyState
            icon="document"
            title="暂无审查记录"
            description="还没有合同审查记录"
            compact={true}
          />
        </div>
      )}
    </div>
  );
}

export default ContractComplianceDashboard;