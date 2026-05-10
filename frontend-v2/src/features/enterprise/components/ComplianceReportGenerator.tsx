/**
 * ComplianceReportGenerator - 合规报告生成器组件
 *
 * 提供多步骤向导式报告生成功能，支持 GDPR、ISO 27001、HIPAA、SOC 2、PCI DSS 等合规报告类型
 * 步骤流程：配置 -> 预览 -> 生成中 -> 完成/失败
 */

import { logger } from '@/shared/lib/logger';
import { useState, useMemo, useCallback } from 'react';

import { EmptyState } from '../../../components/ui/EmptyState';

// ==================== 类型定义 ====================

/** 合规报告类型 */
export type ComplianceReportType = 'gdpr' | 'iso27001' | 'hipaa' | 'soc2' | 'pci' | 'custom';

/** 合规报告生成状态 */
export type ComplianceReportStatus = 'pending' | 'generating' | 'completed' | 'failed';

/** 报告配置 */
interface ReportConfig {
  /** 报告名称 */
  name: string;
  /** 报告描述 */
  description: string;
  /** 报告类型 */
  type: ComplianceReportType;
  /** 开始日期 */
  startDate: string;
  /** 结束日期 */
  endDate: string;
  /** 包含合同数据 */
  includeContracts: boolean;
  /** 包含订单数据 */
  includeOrders: boolean;
  /** 包含成员数据 */
  includeMembers: boolean;
  /** 包含活动日志 */
  includeActivityLogs: boolean;
}

/** 报告预览数据 */
interface PreviewData {
  /** 合同数量 */
  contractCount: number;
  /** 订单数量 */
  orderCount: number;
  /** 成员数量 */
  memberCount: number;
  /** 活动日志数量 */
  activityCount: number;
  /** 预计报告大小 */
  estimatedSize: string;
}

/** 向导步骤 */
type WizardStep = 'config' | 'preview' | 'generating' | 'result';

/** 合规报告生成器属性 */
export interface ComplianceReportGeneratorProps {
  /** 企业账户ID */
  accountId: number;
  /** 是否加载中 */
  isLoading?: boolean;
  /** 错误信息 */
  error?: Error | null;
  /** 生成状态 */
  generationStatus?: ComplianceReportStatus;
  /** 生成的报告ID */
  generatedReportId?: number;
  /** 生成进度（0-100） */
  progress?: number;
  /** 预览数据 */
  previewData?: PreviewData;
  /** 取消回调 */
  onCancel?: () => void;
  /** 提交配置回调 */
  onSubmit?: (config: ReportConfig) => void;
  /** 查看报告回调 */
  onViewReport?: (reportId: number) => void;
  /** 重试回调 */
  onRetry?: () => void;
  /** 关闭回调 */
  onClose?: () => void;
}

// ==================== 常量定义 ====================

/** 报告类型标签映射 */
const REPORT_TYPE_LABELS: Record<ComplianceReportType, string> = {
  gdpr: 'GDPR 通用数据保护条例',
  iso27001: 'ISO 27001 信息安全管理',
  hipaa: 'HIPAA 医疗健康隐私',
  soc2: 'SOC 2 服务组织控制',
  pci: 'PCI DSS 支付卡行业',
  custom: '定制报告',
};

/** 报告类型描述映射 */
const REPORT_TYPE_DESCRIPTIONS: Record<ComplianceReportType, string> = {
  gdpr: '欧盟数据保护合规报告，涵盖数据处理活动记录',
  iso27001: '信息安全管理体系合规报告',
  hipaa: '医疗信息隐私与安全合规报告',
  soc2: '服务组织控制信任服务标准报告',
  pci: '支付卡行业数据安全标准报告',
  custom: '根据自定义需求生成的合规报告',
};

/** 报告类型颜色映射 */
const REPORT_TYPE_COLORS: Record<ComplianceReportType, string> = {
  gdpr: 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200',
  iso27001: 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200',
  hipaa: 'bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-200',
  soc2: 'bg-orange-100 text-orange-800 dark:bg-orange-900 dark:text-orange-200',
  pci: 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200',
  custom: 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-200',
};

/** 数据范围选项 */
const DATA_SCOPE_OPTIONS = [
  { key: 'includeContracts' as const, label: '合同数据', description: '包含企业合同审查记录' },
  { key: 'includeOrders' as const, label: '订单数据', description: '包含企业服务订单记录' },
  { key: 'includeMembers' as const, label: '成员数据', description: '包含团队成员信息' },
  { key: 'includeActivityLogs' as const, label: '活动日志', description: '包含用户操作审计日志' },
];

/** 步骤标签映射 */
const STEP_LABELS: Record<WizardStep, string> = {
  config: '配置',
  preview: '预览',
  generating: '生成中',
  result: '完成',
};

// ==================== 辅助函数 ====================

/**
 * 获取当前步骤的索引
 */
function getStepIndex(step: WizardStep): number {
  const steps: WizardStep[] = ['config', 'preview', 'generating', 'result'];
  return steps.indexOf(step);
}

/**
 * 获取步骤状态样式
 */
function getStepStatusClass(step: WizardStep, currentStep: WizardStep): string {
  const stepIndex = getStepIndex(step);
  const currentIndex = getStepIndex(currentStep);

  if (stepIndex < currentIndex) {
    return 'text-green-600 dark:text-green-400';
  }
  if (stepIndex === currentIndex) {
    return 'text-blue-600 dark:text-blue-400';
  }
  return 'text-gray-400 dark:text-gray-600';
}

/**
 * 获取步骤圆圈样式
 */
function getStepCircleClass(step: WizardStep, currentStep: WizardStep): string {
  const stepIndex = getStepIndex(step);
  const currentIndex = getStepIndex(currentStep);

  if (stepIndex < currentIndex) {
    return 'bg-green-100 border-green-500 text-green-600 dark:bg-green-900 dark:border-green-500 dark:text-green-400';
  }
  if (stepIndex === currentIndex) {
    return 'bg-blue-100 border-blue-500 text-blue-600 ring-2 ring-blue-500 ring-offset-2 dark:bg-blue-900 dark:border-blue-500 dark:text-blue-400 dark:ring-offset-gray-800';
  }
  return 'bg-white border-gray-300 text-gray-400 dark:bg-gray-800 dark:border-gray-600 dark:text-gray-500';
}

// ==================== 子组件 ====================

/**
 * 步骤指示器组件
 */
interface StepIndicatorProps {
  currentStep: WizardStep;
}

function StepIndicator({ currentStep }: StepIndicatorProps): JSX.Element {
  const steps: WizardStep[] = ['config', 'preview', 'generating', 'result'];

  return (
    <div className="w-full py-6">
      <div className="flex items-center justify-between relative">
        {/* 进度线 */}
        <div className="absolute left-0 top-1/2 transform -translate-y-1/2 w-full h-0.5 bg-gray-200 dark:bg-gray-700 -z-10" />
        <div
          className="absolute left-0 top-1/2 transform -translate-y-1/2 h-0.5 bg-blue-500 transition-all duration-500 -z-10"
          style={{
            width: `${(getStepIndex(currentStep) / (steps.length - 1)) * 100}%`,
          }}
        />

        {/* 步骤节点 */}
        {steps.map((step, index) => (
          <div key={step} className="flex flex-col items-center bg-white dark:bg-gray-800 px-2">
            <div
              className={`
                w-10 h-10 rounded-full border-2 flex items-center justify-center
                font-semibold text-sm transition-all duration-300
                ${getStepCircleClass(step, currentStep)}
              `}
            >
              {getStepIndex(currentStep) > index ? (
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                </svg>
              ) : (
                index + 1
              )}
            </div>
            <span
              className={`
                mt-2 text-sm font-medium transition-colors duration-300
                ${getStepStatusClass(step, currentStep)}
              `}
            >
              {STEP_LABELS[step]}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}

/**
 * 配置步骤组件
 */
interface ConfigStepProps {
  config: ReportConfig;
  onConfigChange: (config: ReportConfig) => void;
  onNext: () => void;
  onCancel?: () => void;
}

function ConfigStep({ config, onConfigChange, onNext, onCancel }: ConfigStepProps): JSX.Element {
  const handleTypeChange = useCallback(
    (type: ComplianceReportType) => {
      onConfigChange({ ...config, type });
    },
    [config, onConfigChange]
  );

  const handleDataScopeChange = useCallback(
    (key: keyof ReportConfig, value: boolean) => {
      onConfigChange({ ...config, [key]: value });
    },
    [config, onConfigChange]
  );

  const isValid = config.name.trim() && config.startDate && config.endDate;

  return (
    <div className="space-y-6">
      {/* 报告类型选择 */}
      <div>
        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
          选择报告类型 <span className="text-red-500">*</span>
        </label>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {(Object.keys(REPORT_TYPE_LABELS) as ComplianceReportType[]).map((type) => (
            <button
              key={type}
              onClick={() => handleTypeChange(type)}
              className={`
                relative p-4 rounded-lg border-2 text-left transition-all duration-200
                ${config.type === type
                  ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20'
                  : 'border-gray-200 dark:border-gray-700 hover:border-blue-300 dark:hover:border-blue-700'
                }
              `}
            >
              <div className="flex items-start gap-3">
                <div
                  className={`
                    px-2 py-1 rounded text-xs font-semibold
                    ${REPORT_TYPE_COLORS[type]}
                  `}
                >
                  {type.toUpperCase()}
                </div>
              </div>
              <h4 className="mt-2 font-medium text-gray-900 dark:text-gray-100">
                {REPORT_TYPE_LABELS[type]}
              </h4>
              <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">
                {REPORT_TYPE_DESCRIPTIONS[type]}
              </p>
              {config.type === type && (
                <div className="absolute top-2 right-2 text-blue-500">
                  <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                    <path
                      fillRule="evenodd"
                      d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
                      clipRule="evenodd"
                    />
                  </svg>
                </div>
              )}
            </button>
          ))}
        </div>
      </div>

      {/* 基本信息 */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            报告名称 <span className="text-red-500">*</span>
          </label>
          <input
            type="text"
            value={config.name}
            onChange={(e) => onConfigChange({ ...config, name: e.target.value })}
            placeholder="请输入报告名称"
            className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md
              focus:outline-none focus:ring-2 focus:ring-blue-500
              bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
          />
        </div>
        <div className="md:col-span-2">
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            报告描述
          </label>
          <textarea
            value={config.description}
            onChange={(e) => onConfigChange({ ...config, description: e.target.value })}
            placeholder="请输入报告描述（可选）"
            rows={3}
            className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md
              focus:outline-none focus:ring-2 focus:ring-blue-500
              bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 resize-none"
          />
        </div>
      </div>

      {/* 时间范围 */}
      <div>
        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
          时间范围 <span className="text-red-500">*</span>
        </label>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-xs text-gray-500 dark:text-gray-400 mb-1">开始日期</label>
            <input
              type="date"
              value={config.startDate}
              onChange={(e) => onConfigChange({ ...config, startDate: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md
                focus:outline-none focus:ring-2 focus:ring-blue-500
                bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
            />
          </div>
          <div>
            <label className="block text-xs text-gray-500 dark:text-gray-400 mb-1">结束日期</label>
            <input
              type="date"
              value={config.endDate}
              onChange={(e) => onConfigChange({ ...config, endDate: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md
                focus:outline-none focus:ring-2 focus:ring-blue-500
                bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
            />
          </div>
        </div>
      </div>

      {/* 数据范围选择 */}
      <div>
        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
          数据范围 <span className="text-red-500">*</span>
        </label>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {DATA_SCOPE_OPTIONS.map((option) => (
            <label
              key={option.key}
              className={`
                flex items-start gap-3 p-4 rounded-lg border-2 cursor-pointer transition-all duration-200
                ${config[option.key]
                  ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20'
                  : 'border-gray-200 dark:border-gray-700 hover:border-gray-300 dark:hover:border-gray-600'
                }
              `}
            >
              <input
                type="checkbox"
                checked={config[option.key]}
                onChange={(e) => handleDataScopeChange(option.key, e.target.checked)}
                className="mt-1 w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
              />
              <div>
                <span className="font-medium text-gray-900 dark:text-gray-100">{option.label}</span>
                <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">{option.description}</p>
              </div>
            </label>
          ))}
        </div>
      </div>

      {/* 操作按钮 */}
      <div className="flex justify-end gap-3 pt-4 border-t border-gray-200 dark:border-gray-700">
        {onCancel && (
          <button
            onClick={onCancel}
            className="px-4 py-2 text-sm font-medium text-gray-600 dark:text-gray-400
              bg-gray-100 dark:bg-gray-700 rounded-md hover:bg-gray-200 dark:hover:bg-gray-600
              transition-colors"
          >
            取消
          </button>
        )}
        <button
          onClick={onNext}
          disabled={!isValid}
          className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md
            hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
        >
          下一步
        </button>
      </div>
    </div>
  );
}

/**
 * 预览步骤组件
 */
interface PreviewStepProps {
  config: ReportConfig;
  previewData?: PreviewData;
  onBack: () => void;
  onSubmit: () => void;
}

function PreviewStep({ config, previewData, onBack, onSubmit }: PreviewStepProps): JSX.Element {
  return (
    <div className="space-y-6">
      {/* 配置摘要 */}
      <div className="bg-gray-50 dark:bg-gray-800 rounded-lg p-6">
        <h3 className="text-lg font-medium text-gray-900 dark:text-gray-100 mb-4">配置摘要</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
          <div>
            <span className="text-gray-500 dark:text-gray-400">报告类型：</span>
            <span className="ml-2 font-medium text-gray-900 dark:text-gray-100">
              {REPORT_TYPE_LABELS[config.type]}
            </span>
          </div>
          <div>
            <span className="text-gray-500 dark:text-gray-400">报告名称：</span>
            <span className="ml-2 font-medium text-gray-900 dark:text-gray-100">{config.name}</span>
          </div>
          <div>
            <span className="text-gray-500 dark:text-gray-400">时间范围：</span>
            <span className="ml-2 font-medium text-gray-900 dark:text-gray-100">
              {config.startDate} 至 {config.endDate}
            </span>
          </div>
          {config.description && (
            <div className="md:col-span-2">
              <span className="text-gray-500 dark:text-gray-400">描述：</span>
              <span className="ml-2 font-medium text-gray-900 dark:text-gray-100">
                {config.description}
              </span>
            </div>
          )}
        </div>

        {/* 数据范围 */}
        <div className="mt-4">
          <span className="text-gray-500 dark:text-gray-400 text-sm">包含数据：</span>
          <div className="mt-2 flex flex-wrap gap-2">
            {DATA_SCOPE_OPTIONS.filter((option) => config[option.key]).map((option) => (
              <span
                key={option.key}
                className="px-2 py-1 bg-blue-100 dark:bg-blue-900 text-blue-700 dark:text-blue-200
                  text-xs rounded-full"
              >
                {option.label}
              </span>
            ))}
          </div>
        </div>
      </div>

      {/* 数据预览 */}
      {previewData ? (
        <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-6">
          <h3 className="text-lg font-medium text-gray-900 dark:text-gray-100 mb-4">数据预览</h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="text-center p-4 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
              <div className="text-2xl font-bold text-blue-600 dark:text-blue-400">
                {previewData.contractCount}
              </div>
              <div className="text-sm text-gray-500 dark:text-gray-400 mt-1">合同</div>
            </div>
            <div className="text-center p-4 bg-green-50 dark:bg-green-900/20 rounded-lg">
              <div className="text-2xl font-bold text-green-600 dark:text-green-400">
                {previewData.orderCount}
              </div>
              <div className="text-sm text-gray-500 dark:text-gray-400 mt-1">订单</div>
            </div>
            <div className="text-center p-4 bg-purple-50 dark:bg-purple-900/20 rounded-lg">
              <div className="text-2xl font-bold text-purple-600 dark:text-purple-400">
                {previewData.memberCount}
              </div>
              <div className="text-sm text-gray-500 dark:text-gray-400 mt-1">成员</div>
            </div>
            <div className="text-center p-4 bg-orange-50 dark:bg-orange-900/20 rounded-lg">
              <div className="text-2xl font-bold text-orange-600 dark:text-orange-400">
                {previewData.activityCount}
              </div>
              <div className="text-sm text-gray-500 dark:text-gray-400 mt-1">活动日志</div>
            </div>
          </div>
          <div className="mt-4 text-sm text-gray-500 dark:text-gray-400 text-center">
            预计报告大小：<span className="font-medium">{previewData.estimatedSize}</span>
          </div>
        </div>
      ) : (
        <EmptyState
          title="暂无预览数据"
          description="点击生成按钮开始生成报告预览"
          icon="document"
          size="sm"
        />
      )}

      {/* 操作按钮 */}
      <div className="flex justify-end gap-3 pt-4 border-t border-gray-200 dark:border-gray-700">
        <button
          onClick={onBack}
          className="px-4 py-2 text-sm font-medium text-gray-600 dark:text-gray-400
            bg-gray-100 dark:bg-gray-700 rounded-md hover:bg-gray-200 dark:hover:bg-gray-600
            transition-colors"
        >
          上一步
        </button>
        <button
          onClick={onSubmit}
          className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md
            hover:bg-blue-700 transition-colors"
        >
          生成报告
        </button>
      </div>
    </div>
  );
}

/**
 * 生成中步骤组件
 */
interface GeneratingStepProps {
  progress: number;
  onCancel?: () => void;
}

function GeneratingStep({ progress, onCancel }: GeneratingStepProps): JSX.Element {
  return (
    <div className="flex flex-col items-center justify-center py-12">
      {/* 加载动画 */}
      <div className="relative w-24 h-24 mb-6">
        <div className="absolute inset-0 border-4 border-gray-200 dark:border-gray-700 rounded-full" />
        <div
          className="absolute inset-0 border-4 border-blue-500 rounded-full border-t-transparent animate-spin"
          style={{ animationDuration: '1s' }}
        />
        <div className="absolute inset-0 flex items-center justify-center">
          <span className="text-xl font-bold text-blue-600 dark:text-blue-400">{Math.round(progress)}%</span>
        </div>
      </div>

      <h3 className="text-lg font-medium text-gray-900 dark:text-gray-100 mb-2">正在生成报告...</h3>
      <p className="text-sm text-gray-500 dark:text-gray-400 mb-6">请稍候，正在处理您的数据</p>

      {/* 进度条 */}
      <div className="w-full max-w-md mb-6">
        <div className="w-full h-2 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
          <div
            className="h-full bg-blue-500 transition-all duration-300 ease-out"
            style={{ width: `${progress}%` }}
          />
        </div>
      </div>

      {onCancel && (
        <button
          onClick={onCancel}
          className="px-4 py-2 text-sm font-medium text-gray-600 dark:text-gray-400
            bg-gray-100 dark:bg-gray-700 rounded-md hover:bg-gray-200 dark:hover:bg-gray-600
            transition-colors"
        >
          取消
        </button>
      )}
    </div>
  );
}

/**
 * 结果步骤组件
 */
interface ResultStepProps {
  status: ComplianceReportStatus;
  reportId?: number;
  error?: Error | null;
  onViewReport?: (reportId: number) => void;
  onRetry?: () => void;
  onClose?: () => void;
}

function ResultStep({
  status,
  reportId,
  error,
  onViewReport,
  onRetry,
  onClose,
}: ResultStepProps): JSX.Element {
  if (status === 'completed') {
    return (
      <div className="flex flex-col items-center justify-center py-12">
        <div className="w-20 h-20 bg-green-100 dark:bg-green-900 rounded-full flex items-center justify-center mb-6">
          <svg
            className="w-10 h-10 text-green-600 dark:text-green-400"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
          </svg>
        </div>
        <h3 className="text-xl font-medium text-gray-900 dark:text-gray-100 mb-2">报告生成成功！</h3>
        <p className="text-sm text-gray-500 dark:text-gray-400 mb-6 text-center max-w-md">
          您的合规报告已成功生成。您可以立即查看或下载报告。
        </p>
        <div className="flex gap-3">
          {onClose && (
            <button
              onClick={onClose}
              className="px-4 py-2 text-sm font-medium text-gray-600 dark:text-gray-400
                bg-gray-100 dark:bg-gray-700 rounded-md hover:bg-gray-200 dark:hover:bg-gray-600
                transition-colors"
            >
              关闭
            </button>
          )}
          {reportId && onViewReport && (
            <button
              onClick={() => onViewReport(reportId)}
              className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md
                hover:bg-blue-700 transition-colors"
            >
              查看报告
            </button>
          )}
        </div>
      </div>
    );
  }

  // 失败状态
  return (
    <div className="flex flex-col items-center justify-center py-12">
      <div className="w-20 h-20 bg-red-100 dark:bg-red-900 rounded-full flex items-center justify-center mb-6">
        <svg
          className="w-10 h-10 text-red-600 dark:text-red-400"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M6 18L18 6M6 6l12 12"
          />
        </svg>
      </div>
      <h3 className="text-xl font-medium text-gray-900 dark:text-gray-100 mb-2">报告生成失败</h3>
      <p className="text-sm text-gray-500 dark:text-gray-400 mb-2 text-center max-w-md">
        生成报告时发生错误，请稍后重试。
      </p>
      {error && (
        <p className="text-xs text-red-500 dark:text-red-400 mb-6 text-center max-w-md">
          {error.message}
        </p>
      )}
      <div className="flex gap-3">
        {onClose && (
          <button
            onClick={onClose}
            className="px-4 py-2 text-sm font-medium text-gray-600 dark:text-gray-400
              bg-gray-100 dark:bg-gray-700 rounded-md hover:bg-gray-200 dark:hover:bg-gray-600
              transition-colors"
          >
            关闭
          </button>
        )}
        {onRetry && (
          <button
            onClick={onRetry}
            className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md
              hover:bg-blue-700 transition-colors"
          >
            重试
          </button>
        )}
      </div>
    </div>
  );
}

/**
 * 加载骨架屏组件
 */
function LoadingSkeleton(): JSX.Element {
  return (
    <div className="p-6 bg-white dark:bg-gray-800 rounded-lg shadow-sm">
      <div className="animate-pulse space-y-4">
        {/* 步骤指示器骨架 */}
        <div className="flex justify-between mb-8">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="flex flex-col items-center">
              <div className="w-10 h-10 rounded-full bg-gray-200 dark:bg-gray-700" />
              <div className="mt-2 h-4 w-12 rounded bg-gray-200 dark:bg-gray-700" />
            </div>
          ))}
        </div>
        {/* 内容骨架 */}
        <div className="space-y-4">
          <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-1/4" />
          <div className="grid grid-cols-2 gap-4">
            <div className="h-24 bg-gray-200 dark:bg-gray-700 rounded" />
            <div className="h-24 bg-gray-200 dark:bg-gray-700 rounded" />
          </div>
          <div className="h-32 bg-gray-200 dark:bg-gray-700 rounded" />
        </div>
      </div>
    </div>
  );
}

// ==================== 主组件 ====================

/**
 * 获取默认报告配置
 */
function getDefaultConfig(): ReportConfig {
  const today = new Date();
  const thirtyDaysAgo = new Date(today.getTime() - 30 * 24 * 60 * 60 * 1000);

  return {
    name: '',
    description: '',
    type: 'gdpr',
    startDate: thirtyDaysAgo.toISOString().split('T')[0],
    endDate: today.toISOString().split('T')[0],
    includeContracts: true,
    includeOrders: true,
    includeMembers: false,
    includeActivityLogs: true,
  };
}

/**
 * 合规报告生成器组件
 *
 * @example
 * ```tsx
 * // 基本使用
 * <ComplianceReportGenerator
 *   accountId={123}
 *   onSubmit={(config) => logger.info(config)}
 * />
 *
 * // 带状态控制
 * <ComplianceReportGenerator
 *   accountId={123}
 *   generationStatus="generating"
 *   progress={45}
 *   onSubmit={handleSubmit}
 *   onViewReport={handleViewReport}
 * />
 * ```
 */
export function ComplianceReportGenerator({
  accountId: _accountId,
  isLoading = false,
  error = null,
  generationStatus = 'pending',
  generatedReportId,
  progress = 0,
  previewData,
  onCancel,
  onSubmit,
  onViewReport,
  onRetry,
  onClose,
}: ComplianceReportGeneratorProps): JSX.Element {
  // 当前步骤状态
  const [currentStep, setCurrentStep] = useState<WizardStep>('config');
  // 报告配置状态
  const [config, setConfig] = useState<ReportConfig>(getDefaultConfig);

  // 根据外部状态计算当前步骤
  const effectiveStep = useMemo<WizardStep>(() => {
    switch (generationStatus) {
      case 'generating':
        return 'generating';
      case 'completed':
      case 'failed':
        return 'result';
      default:
        return currentStep;
    }
  }, [generationStatus, currentStep]);

  // 处理下一步
  const handleNext = useCallback(() => {
    if (currentStep === 'config') {
      setCurrentStep('preview');
    }
  }, [currentStep]);

  // 处理返回
  const handleBack = useCallback(() => {
    if (currentStep === 'preview') {
      setCurrentStep('config');
    }
  }, [currentStep]);

  // 处理提交
  const handleSubmit = useCallback(() => {
    if (onSubmit) {
      onSubmit(config);
    }
    setCurrentStep('generating');
  }, [config, onSubmit]);

  // 处理重试
  const handleRetry = useCallback(() => {
    if (onRetry) {
      onRetry();
    }
    setCurrentStep('config');
  }, [onRetry]);

  // 加载状态
  if (isLoading) {
    return <LoadingSkeleton />;
  }

  // 错误状态（非生成失败的其他错误）
  if (error && generationStatus !== 'failed') {
    return (
      <div className="p-6 bg-white dark:bg-gray-800 rounded-lg shadow-sm">
        <EmptyState
          title="加载失败"
          description={error.message}
          icon="error"
          size="md"
          action={
            onClose ? (
              <button
                onClick={onClose}
                className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md
                  hover:bg-blue-700 transition-colors"
              >
                关闭
              </button>
            ) : undefined
          }
        />
      </div>
    );
  }

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm">
      {/* 头部 */}
      <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-700">
        <h2 className="text-xl font-semibold text-gray-900 dark:text-gray-100">合规报告生成器</h2>
        <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
          生成符合 GDPR、ISO 27001 等标准的合规报告
        </p>
      </div>

      {/* 步骤指示器 */}
      <div className="px-6">
        <StepIndicator currentStep={effectiveStep} />
      </div>

      {/* 内容区域 */}
      <div className="px-6 pb-6">
        {effectiveStep === 'config' && (
          <ConfigStep
            config={config}
            onConfigChange={setConfig}
            onNext={handleNext}
            onCancel={onCancel}
          />
        )}

        {effectiveStep === 'preview' && (
          <PreviewStep
            config={config}
            previewData={previewData}
            onBack={handleBack}
            onSubmit={handleSubmit}
          />
        )}

        {effectiveStep === 'generating' && (
          <GeneratingStep progress={progress} onCancel={onCancel} />
        )}

        {effectiveStep === 'result' && (
          <ResultStep
            status={generationStatus}
            reportId={generatedReportId}
            error={error}
            onViewReport={onViewReport}
            onRetry={handleRetry}
            onClose={onClose}
          />
        )}
      </div>
    </div>
  );
}
