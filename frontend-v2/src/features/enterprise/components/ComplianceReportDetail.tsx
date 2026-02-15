
/**
 * ComplianceReportDetail - 合规报告详情组件
 *
 * 展示单份合规报告的详细信息，包括报告头部、摘要、统计数据、图表和建议列表
 * 支持PDF导出、分享功能、Skeleton加载状态和EmptyState错误状态
 */

import { useState, useMemo } from 'react';

import { StatCard } from '../../analytics/components/StatCard';
import { FunnelChart } from '../../analytics/components/FunnelChart';
import { EmptyState } from '../../../components/ui/EmptyState';
import type { FunnelChartDataItem } from '../../analytics/types';

// ==================== 类型定义 ====================

/**
 * 合规报告类型
 */
export type ComplianceReportType = 'gdpr' | 'iso27001' | 'hipaa' | 'soc2' | 'pci' | 'custom';

/**
 * 合规报告状态
 */
export type ComplianceReportStatus = 'pending' | 'generating' | 'completed' | 'failed';

/**
 * 合规报告基础信息
 */
export interface ComplianceReport {
  /** 报告ID */
  id: number;
  /** 报告名称 */
  name: string;
  /** 报告类型 */
  type: ComplianceReportType;
  /** 报告状态 */
  status: ComplianceReportStatus;
  /** 创建时间 */
  createdAt: string;
  /** 文件URL */
  fileUrl: string;
  /** 报告描述 */
  description: string;
  /** 报告周期开始 */
  periodStart: string;
  /** 报告周期结束 */
  periodEnd: string;
  /** 文件大小（字节） */
  fileSize: number;
  /** 报告摘要 */
  summary?: ReportSummary;
}

/**
 * 报告摘要数据
 */
export interface ReportSummary {
  /** 合规评分 0-100 */
  complianceScore: number;
  /** 风险等级 */
  riskLevel: 'low' | 'medium' | 'high' | 'critical';
  /** 关键发现数量 */
  findingsCount: number;
  /** 建议数量 */
  recommendationsCount: number;
  /** 分类评分 */
  categories: {
    name: string;
    score: number;
    status: 'pass' | 'fail' | 'warning';
  }[];
}

/**
 * 报告详细数据
 */
export interface ReportDetailData {
  /** 统计数据 */
  statistics: {
    contractsReviewed: number;
    ordersAudited: number;
    membersChecked: number;
    issuesFound: number;
  };
  /** 审查发现 */
  findings: {
    id: string;
    category: string;
    severity: 'low' | 'medium' | 'high' | 'critical';
    title: string;
    description: string;
    recommendation: string;
  }[];
}

/**
 * 合规报告详情组件属性
 */
export interface ComplianceReportDetailProps {
  /** 企业账户ID */
  accountId: number;
  /** 报告ID */
  reportId: number;
  /** 报告数据 */
  report?: ComplianceReport & { summary?: ReportSummary };
  /** 详细数据 */
  detailData?: ReportDetailData;
  /** 加载状态 */
  isLoading?: boolean;
  /** 错误状态 */
  error?: Error | null;
  /** 返回回调 */
  onBack?: () => void;
  /** PDF导出回调 */
  onExportPDF?: (reportId: number) => void;
  /** 分享回调 */
  onShare?: (reportId: number, method: 'link' | 'email') => void;
  /** 刷新回调 */
  onRefresh?: () => void;
}

// ==================== 常量定义 ====================

/** 报告类型标签映射 */
const REPORT_TYPE_LABELS: Record<ComplianceReportType, string> = {
  gdpr: 'GDPR合规',
  iso27001: 'ISO 27001',
  hipaa: 'HIPAA合规',
  soc2: 'SOC 2',
  pci: 'PCI DSS',
  custom: '自定义合规',
};

/** 报告状态标签映射 */
const REPORT_STATUS_LABELS: Record<ComplianceReportStatus, string> = {
  pending: '待生成',
  generating: '生成中',
  completed: '已完成',
  failed: '失败',
};

/** 报告状态颜色映射 */
const REPORT_STATUS_COLORS: Record<ComplianceReportStatus, string> = {
  pending: 'bg-yellow-100 text-yellow-800',
  generating: 'bg-blue-100 text-blue-800',
  completed: 'bg-green-100 text-green-800',
  failed: 'bg-red-100 text-red-800',
};

/** 风险等级标签映射 */
const RISK_LEVEL_LABELS: Record<string, string> = {
  low: '低风险',
  medium: '中风险',
  high: '高风险',
  critical: '严重风险',
};

/** 风险等级颜色映射 */
const RISK_LEVEL_COLORS: Record<string, string> = {
  low: '#22c55e',
  medium: '#eab308',
  high: '#f97316',
  critical: '#ef4444',
};

/** 严重程度标签映射 */
const SEVERITY_LABELS: Record<string, string> = {
  low: '低',
  medium: '中',
  high: '高',
  critical: '严重',
};

/** 严重程度颜色映射 */
const SEVERITY_COLORS: Record<string, string> = {
  low: 'bg-green-100 text-green-800',
  medium: 'bg-yellow-100 text-yellow-800',
  high: 'bg-orange-100 text-orange-800',
  critical: 'bg-red-100 text-red-800',
};

// ==================== 辅助函数 ====================

/**
 * 格式化日期
 * @param dateString - ISO日期字符串
 * @returns 格式化后的日期字符串
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
 * 格式化文件大小
 * @param bytes - 字节数
 * @returns 格式化后的文件大小字符串
 */
function formatFileSize(bytes: number): string {
  if (bytes === 0) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(2))} ${sizes[i]}`;
}

/**
 * 计算合规评分颜色
 * @param score - 合规评分
 * @returns 颜色值
 */
function getScoreColor(score: number): string {
  if (score >= 90) return 'text-green-600';
  if (score >= 70) return 'text-yellow-600';
  if (score >= 50) return 'text-orange-600';
  return 'text-red-600';
}

/**
 * 转换分类评分为漏斗图数据
 * @param categories - 分类评分数组
 * @returns 漏斗图数据
 */
function convertCategoriesToFunnelData(categories: ReportSummary['categories']): FunnelChartDataItem[] {
  return categories.map((item) => ({
    name: item.name,
    value: item.score,
    conversionRate: item.score,
    dropRate: 100 - item.score,
    color: item.status === 'pass' ? '#22c55e' : item.status === 'warning' ? '#eab308' : '#ef4444',
  }));
}

// ==================== 图标组件 ====================

/**
 * 返回图标
 */
function BackIcon({ className = 'h-5 w-5' }: { className?: string }): JSX.Element {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
    </svg>
  );
}

/**
 * 下载图标
 */
function DownloadIcon({ className = 'h-5 w-5' }: { className?: string }): JSX.Element {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth={2}
        d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
      />
    </svg>
  );
}

/**
 * 分享图标
 */
function ShareIcon({ className = 'h-5 w-5' }: { className?: string }): JSX.Element {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth={2}
        d="M8.684 13.342C8.886 12.938 9 12.482 9 12c0-.482-.114-.938-.316-1.342m0 2.684a3 3 0 110-2.684m0 2.684l6.632 3.316m-6.632-6l6.632-3.316m0 0a3 3 0 105.367-2.684 3 3 0 00-5.367 2.684zm0 9.316a3 3 0 105.368 2.684 3 3 0 00-5.368-2.684z"
      />
    </svg>
  );
}

/**
 * 链接图标
 */
function LinkIcon({ className = 'h-5 w-5' }: { className?: string }): JSX.Element {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth={2}
        d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1"
      />
    </svg>
  );
}

/**
 * 邮件图标
 */
function MailIcon({ className = 'h-5 w-5' }: { className?: string }): JSX.Element {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth={2}
        d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"
      />
    </svg>
  );
}

/**
 * 刷新图标
 */
function RefreshIcon({ className = 'h-5 w-5' }: { className?: string }): JSX.Element {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth={2}
        d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
      />
    </svg>
  );
}

/**
 * 文件图标
 */
function FileIcon({ className = 'h-5 w-5' }: { className?: string }): JSX.Element {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth={2}
        d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
      />
    </svg>
  );
}

/**
 * 勾选图标
 */
function CheckIcon({ className = 'h-5 w-5' }: { className?: string }): JSX.Element {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
    </svg>
  );
}

/**
 * 活动图标
 */
function ActivityIcon({ className = 'h-6 w-6' }: { className?: string }): JSX.Element {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth={2}
        d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"
      />
    </svg>
  );
}

// ==================== 骨架屏组件 ====================

/**
 * 头部骨架屏
 */
function HeaderSkeleton(): JSX.Element {
  return (
    <div className="animate-pulse rounded-lg bg-white p-6 shadow-sm dark:bg-gray-800">
      <div className="flex items-center gap-4">
        <div className="h-10 w-10 rounded-full bg-gray-200 dark:bg-gray-700" />
        <div className="flex-1">
          <div className="h-6 w-48 rounded bg-gray-200 dark:bg-gray-700" />
          <div className="mt-2 h-4 w-32 rounded bg-gray-200 dark:bg-gray-700" />
        </div>
      </div>
    </div>
  );
}

/**
 * 摘要骨架屏
 */
function SummarySkeleton(): JSX.Element {
  return (
    <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
      {[1, 2, 3, 4].map((i) => (
        <div
          key={i}
          className="animate-pulse rounded-lg bg-white p-6 shadow-sm dark:bg-gray-800"
        >
          <div className="flex items-center justify-between">
            <div className="h-4 w-24 rounded bg-gray-200 dark:bg-gray-700" />
            <div className="h-10 w-10 rounded-full bg-gray-200 dark:bg-gray-700" />
          </div>
          <div className="mt-4 h-8 w-32 rounded bg-gray-200 dark:bg-gray-700" />
          <div className="mt-2 h-4 w-20 rounded bg-gray-200 dark:bg-gray-700" />
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
    <div className="animate-pulse rounded-lg bg-white p-6 shadow-sm dark:bg-gray-800">
      <div className="mb-4 h-6 w-32 rounded bg-gray-200 dark:bg-gray-700" />
      <div className="rounded-lg bg-gray-200 dark:bg-gray-700" style={{ height: `${height}px` }} />
    </div>
  );
}

/**
 * 发现列表骨架屏
 */
function FindingsSkeleton(): JSX.Element {
  return (
    <div className="animate-pulse rounded-lg bg-white shadow-sm dark:bg-gray-800">
      <div className="space-y-3 p-6">
        <div className="mb-4 h-6 w-32 rounded bg-gray-200 dark:bg-gray-700" />
        {[1, 2, 3].map((i) => (
          <div key={i} className="rounded-lg border border-gray-100 p-4 dark:border-gray-700">
            <div className="h-5 w-3/4 rounded bg-gray-200 dark:bg-gray-700" />
            <div className="mt-2 h-4 w-full rounded bg-gray-200 dark:bg-gray-700" />
            <div className="mt-2 h-4 w-2/3 rounded bg-gray-200 dark:bg-gray-700" />
          </div>
        ))}
      </div>
    </div>
  );
}

// ==================== 子组件 ====================

/**
 * 分享弹窗组件
 */
interface ShareModalProps {
  isOpen: boolean;
  onClose: () => void;
  onShareLink: () => void;
  onShareEmail: () => void;
  reportName: string;
}

function ShareModal({ isOpen, onClose, onShareLink, onShareEmail, reportName }: ShareModalProps): JSX.Element | null {
  const [copied, setCopied] = useState(false);

  if (!isOpen) return null;

  const handleCopyLink = (): void => {
    onShareLink();
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
      <div className="w-full max-w-md rounded-lg bg-white p-6 shadow-xl dark:bg-gray-800">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">分享报告</h3>
        <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">{reportName}</p>

        <div className="mt-6 space-y-3">
          <button
            onClick={handleCopyLink}
            className="flex w-full items-center gap-3 rounded-lg border border-gray-200 p-4 transition-colors hover:bg-gray-50 dark:border-gray-700 dark:hover:bg-gray-700"
          >
            <div className="rounded-full bg-blue-100 p-2 text-blue-600 dark:bg-blue-900 dark:text-blue-300">
              {copied ? <CheckIcon className="h-5 w-5" /> : <LinkIcon className="h-5 w-5" />}
            </div>
            <div className="text-left">
              <p className="font-medium text-gray-900 dark:text-gray-100">
                {copied ? '链接已复制' : '复制链接'}
              </p>
              <p className="text-sm text-gray-500 dark:text-gray-400">复制报告链接分享给他人</p>
            </div>
          </button>

          <button
            onClick={onShareEmail}
            className="flex w-full items-center gap-3 rounded-lg border border-gray-200 p-4 transition-colors hover:bg-gray-50 dark:border-gray-700 dark:hover:bg-gray-700"
          >
            <div className="rounded-full bg-green-100 p-2 text-green-600 dark:bg-green-900 dark:text-green-300">
              <MailIcon className="h-5 w-5" />
            </div>
            <div className="text-left">
              <p className="font-medium text-gray-900 dark:text-gray-100">邮件分享</p>
              <p className="text-sm text-gray-500 dark:text-gray-400">通过邮件发送报告</p>
            </div>
          </button>
        </div>

        <button
          onClick={onClose}
          className="mt-6 w-full rounded-lg bg-gray-100 px-4 py-2 text-sm font-medium text-gray-700 transition-colors hover:bg-gray-200 dark:bg-gray-700 dark:text-gray-300 dark:hover:bg-gray-600"
        >
          关闭
        </button>
      </div>
    </div>
  );
}

/**
 * 报告头部组件
 */
interface ReportHeaderProps {
  report: ComplianceReport;
  onBack?: () => void;
  onExportPDF?: (reportId: number) => void;
  onShare?: () => void;
}

function ReportHeader({ report, onBack, onExportPDF, onShare }: ReportHeaderProps): JSX.Element {
  const handleExportPDF = (): void => {
    if (onExportPDF) {
      onExportPDF(report.id);
    }
  };

  return (
    <div className="rounded-lg bg-white p-6 shadow-sm dark:bg-gray-800">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
        <div className="flex items-start gap-4">
          {onBack && (
            <button
              onClick={onBack}
              className="rounded-full p-2 text-gray-500 transition-colors hover:bg-gray-100 hover:text-gray-700 dark:text-gray-400 dark:hover:bg-gray-700 dark:hover:text-gray-200"
              aria-label="返回"
            >
              <BackIcon />
            </button>
          )}
          <div>
            <div className="flex flex-wrap items-center gap-2">
              <h1 className="text-xl font-bold text-gray-900 dark:text-gray-100">{report.name}</h1>
              <span
                className={`rounded-full px-2.5 py-0.5 text-xs font-medium ${REPORT_STATUS_COLORS[report.status]}`}
              >
                {REPORT_STATUS_LABELS[report.status]}
              </span>
            </div>
            <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">{report.description}</p>
            <div className="mt-3 flex flex-wrap items-center gap-4 text-sm text-gray-500 dark:text-gray-400">
              <span className="flex items-center gap-1">
                <FileIcon className="h-4 w-4" />
                {REPORT_TYPE_LABELS[report.type]}
              </span>
              <span>创建于 {formatDate(report.createdAt)}</span>
              <span>周期: {formatDate(report.periodStart)} - {formatDate(report.periodEnd)}</span>
              <span>大小: {formatFileSize(report.fileSize)}</span>
            </div>
          </div>
        </div>

        <div className="flex flex-wrap gap-2">
          <button
            onClick={handleExportPDF}
            disabled={report.status !== 'completed'}
            className="flex items-center gap-2 rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-50 dark:bg-blue-700 dark:hover:bg-blue-800"
          >
            <DownloadIcon className="h-4 w-4" />
            导出PDF
          </button>
          <button
            onClick={onShare}
            disabled={report.status !== 'completed'}
            className="flex items-center gap-2 rounded-lg border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 transition-colors hover:bg-gray-50 disabled:cursor-not-allowed disabled:opacity-50 dark:border-gray-600 dark:bg-gray-700 dark:text-gray-200 dark:hover:bg-gray-600"
          >
            <ShareIcon className="h-4 w-4" />
            分享
          </button>
        </div>
      </div>
    </div>
  );
}

/**
 * 报告摘要组件
 */
interface ReportSummaryProps {
  summary: ReportSummary;
}

function ReportSummarySection({ summary }: ReportSummaryProps): JSX.Element {
  return (
    <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
      {/* 合规评分卡片 - 特殊样式 */}
      <div className="rounded-lg bg-white p-6 shadow-sm dark:bg-gray-800">
        <div className="flex items-center justify-between">
          <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400">合规评分</h3>
          <div className="rounded-full bg-blue-50 p-2 text-blue-600 dark:bg-blue-900 dark:text-blue-300">
            <ActivityIcon className="h-6 w-6" />
          </div>
        </div>
        <div className="mt-4">
          <p className={`text-3xl font-bold ${getScoreColor(summary.complianceScore)}`}>
            {summary.complianceScore}
            <span className="ml-1 text-lg text-gray-400">/100</span>
          </p>
          <div className="mt-2">
            <div className="h-2 w-full rounded-full bg-gray-200 dark:bg-gray-700">
              <div
                className="h-2 rounded-full bg-blue-600 transition-all duration-500"
                style={{ width: `${summary.complianceScore}%` }}
              />
            </div>
          </div>
        </div>
      </div>

      {/* 风险等级卡片 - 特殊样式 */}
      <div className="rounded-lg bg-white p-6 shadow-sm dark:bg-gray-800">
        <div className="flex items-center justify-between">
          <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400">风险等级</h3>
          <div className="rounded-full bg-red-50 p-2 text-red-600 dark:bg-red-900 dark:text-red-300">
            <ActivityIcon className="h-6 w-6" />
          </div>
        </div>
        <div className="mt-4">
          <p
            className="text-2xl font-bold"
            style={{ color: RISK_LEVEL_COLORS[summary.riskLevel] }}
          >
            {RISK_LEVEL_LABELS[summary.riskLevel]}
          </p>
          <p className="mt-2 text-sm text-gray-400 dark:text-gray-500">
            基于 {summary.findingsCount} 项发现评估
          </p>
        </div>
      </div>

      {/* 关键发现 */}
      <StatCard
        data={{
          title: '关键发现',
          value: summary.findingsCount,
          change: -2,
          changeType: 'decrease',
          icon: 'Activity',
        }}
      />

      {/* 改进建议 */}
      <StatCard
        data={{
          title: '改进建议',
          value: summary.recommendationsCount,
          icon: 'Activity',
        }}
      />
    </div>
  );
}

/**
 * 分类评分图表组件
 */
interface CategoryChartProps {
  categories: ReportSummary['categories'];
}

function CategoryChart({ categories }: CategoryChartProps): JSX.Element {
  const funnelData = useMemo(() => convertCategoriesToFunnelData(categories), [categories]);

  return (
    <FunnelChart
      data={funnelData}
      title="合规分类评分"
      showLegend={true}
      showRates={false}
    />
  );
}

/**
 * 统计数据组件
 */
interface StatisticsProps {
  statistics: ReportDetailData['statistics'];
}

function StatisticsSection({ statistics }: StatisticsProps): JSX.Element {
  return (
    <div className="rounded-lg bg-white p-6 shadow-sm dark:bg-gray-800">
      <h3 className="mb-4 text-lg font-semibold text-gray-900 dark:text-gray-100">审查统计</h3>
      <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
        <div className="rounded-lg bg-blue-50 p-4 text-center dark:bg-blue-900/20">
          <p className="text-2xl font-bold text-blue-600 dark:text-blue-400">
            {statistics.contractsReviewed}
          </p>
          <p className="mt-1 text-sm text-gray-600 dark:text-gray-400">合同审查</p>
        </div>
        <div className="rounded-lg bg-green-50 p-4 text-center dark:bg-green-900/20">
          <p className="text-2xl font-bold text-green-600 dark:text-green-400">
            {statistics.ordersAudited}
          </p>
          <p className="mt-1 text-sm text-gray-600 dark:text-gray-400">订单审计</p>
        </div>
        <div className="rounded-lg bg-purple-50 p-4 text-center dark:bg-purple-900/20">
          <p className="text-2xl font-bold text-purple-600 dark:text-purple-400">
            {statistics.membersChecked}
          </p>
          <p className="mt-1 text-sm text-gray-600 dark:text-gray-400">成员检查</p>
        </div>
        <div className="rounded-lg bg-red-50 p-4 text-center dark:bg-red-900/20">
          <p className="text-2xl font-bold text-red-600 dark:text-red-400">
            {statistics.issuesFound}
          </p>
          <p className="mt-1 text-sm text-gray-600 dark:text-gray-400">发现问题</p>
        </div>
      </div>
    </div>
  );
}

/**
 * 发现列表组件
 */
interface FindingsListProps {
  findings: ReportDetailData['findings'];
}

function FindingsList({ findings }: FindingsListProps): JSX.Element {
  if (findings.length === 0) {
    return (
      <div className="rounded-lg bg-white p-6 shadow-sm dark:bg-gray-800">
        <h3 className="mb-4 text-lg font-semibold text-gray-900 dark:text-gray-100">审查发现</h3>
        <EmptyState
          title="暂无发现"
          description="本次审查未发现合规问题"
          icon="box"
          size="sm"
        />
      </div>
    );
  }

  return (
    <div className="rounded-lg bg-white shadow-sm dark:bg-gray-800">
      <div className="border-b border-gray-200 p-6 dark:border-gray-700">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">审查发现</h3>
        <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
          共 {findings.length} 项发现，请优先处理高风险项
        </p>
      </div>
      <div className="divide-y divide-gray-200 dark:divide-gray-700">
        {findings.map((finding) => (
          <div key={finding.id} className="p-6">
            <div className="flex flex-wrap items-start justify-between gap-2">
              <div className="flex-1">
                <div className="flex flex-wrap items-center gap-2">
                  <span
                    className={`rounded-full px-2.5 py-0.5 text-xs font-medium ${SEVERITY_COLORS[finding.severity]}`}
                  >
                    {SEVERITY_LABELS[finding.severity]}
                  </span>
                  <span className="text-sm text-gray-500 dark:text-gray-400">{finding.category}</span>
                </div>
                <h4 className="mt-2 font-medium text-gray-900 dark:text-gray-100">{finding.title}</h4>
                <p className="mt-1 text-sm text-gray-600 dark:text-gray-400">{finding.description}</p>
              </div>
            </div>
            <div className="mt-3 rounded-lg bg-gray-50 p-3 dark:bg-gray-700/50">
              <p className="text-sm font-medium text-gray-700 dark:text-gray-300">建议：</p>
              <p className="mt-1 text-sm text-gray-600 dark:text-gray-400">{finding.recommendation}</p>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

// ==================== 主组件 ====================

/**
 * 合规报告详情组件
 *
 * @example
 * ```tsx
 * <ComplianceReportDetail
 *   accountId={1}
 *   reportId={123}
 *   report={reportData}
 *   detailData={detailData}
 *   onBack={() => navigate(-1)}
 *   onExportPDF={(id) => console.log('Export PDF', id)}
 *   onShare={(id, method) => console.log('Share', id, method)}
 * />
 * ```
 */
export function ComplianceReportDetail({
  accountId: _accountId,
  reportId,
  report,
  detailData,
  isLoading = false,
  error = null,
  onBack,
  onExportPDF,
  onShare,
  onRefresh,
}: ComplianceReportDetailProps): JSX.Element {
  const [isShareModalOpen, setIsShareModalOpen] = useState(false);

  // 处理分享链接
  const handleShareLink = (): void => {
    if (onShare) {
      onShare(reportId, 'link');
    }
  };

  // 处理邮件分享
  const handleShareEmail = (): void => {
    if (onShare) {
      onShare(reportId, 'email');
    }
    setIsShareModalOpen(false);
  };

  // 错误状态
  if (error) {
    return (
      <div className="space-y-6">
        <div className="flex items-center gap-4">
          {onBack && (
            <button
              onClick={onBack}
              className="rounded-full p-2 text-gray-500 transition-colors hover:bg-gray-100 hover:text-gray-700 dark:text-gray-400 dark:hover:bg-gray-700 dark:hover:text-gray-200"
              aria-label="返回"
            >
              <BackIcon />
            </button>
          )}
          <h1 className="text-xl font-bold text-gray-900 dark:text-gray-100">合规报告详情</h1>
        </div>
        <EmptyState
          title="加载失败"
          description={error.message || '无法加载报告详情，请稍后重试'}
          icon="error"
          action={
            onRefresh && (
              <button
                onClick={onRefresh}
                className="flex items-center gap-2 rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-blue-700"
              >
                <RefreshIcon className="h-4 w-4" />
                重新加载
              </button>
            )
          }
        />
      </div>
    );
  }

  // 加载状态
  if (isLoading) {
    return (
      <div className="space-y-6">
        <HeaderSkeleton />
        <SummarySkeleton />
        <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
          <ChartSkeleton height={250} />
          <ChartSkeleton height={250} />
        </div>
        <FindingsSkeleton />
      </div>
    );
  }

  // 数据为空状态
  if (!report) {
    return (
      <div className="space-y-6">
        <div className="flex items-center gap-4">
          {onBack && (
            <button
              onClick={onBack}
              className="rounded-full p-2 text-gray-500 transition-colors hover:bg-gray-100 hover:text-gray-700 dark:text-gray-400 dark:hover:bg-gray-700 dark:hover:text-gray-200"
              aria-label="返回"
            >
              <BackIcon />
            </button>
          )}
          <h1 className="text-xl font-bold text-gray-900 dark:text-gray-100">合规报告详情</h1>
        </div>
        <EmptyState
          title="报告不存在"
          description="无法找到该合规报告"
          icon="document"
          action={
            onBack && (
              <button
                onClick={onBack}
                className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-blue-700"
              >
                返回列表
              </button>
            )
          }
        />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* 分享弹窗 */}
      <ShareModal
        isOpen={isShareModalOpen}
        onClose={() => setIsShareModalOpen(false)}
        onShareLink={handleShareLink}
        onShareEmail={handleShareEmail}
        reportName={report.name}
      />

      {/* 报告头部 */}
      <ReportHeader
        report={report}
        onBack={onBack}
        onExportPDF={onExportPDF}
        onShare={() => setIsShareModalOpen(true)}
      />

      {/* 报告摘要 */}
      {report.summary && <ReportSummarySection summary={report.summary} />}

      {/* 详细数据 */}
      {detailData && (
        <>
          {/* 统计数据 */}
          <StatisticsSection statistics={detailData.statistics} />

          {/* 分类评分图表和发现列表 */}
          <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
            {report.summary && (
              <CategoryChart categories={report.summary.categories} />
            )}
          </div>

          {/* 发现列表 */}
          <FindingsList findings={detailData.findings} />
        </>
      )}
    </div>
  );
}