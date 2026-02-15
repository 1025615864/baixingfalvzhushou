/**
 * Enterprise Feature - Components Index
 *
 * 导出企业功能相关的所有组件
 */

// 合同合规仪表盘
export { ContractComplianceDashboard } from './ContractComplianceDashboard';

// 合规报告列表
export { ComplianceReportList } from './ComplianceReportList';
export type {
  ComplianceReport,
  PaginationConfig,
  FilterConfig,
} from './ComplianceReportList';

// 合规报告生成器
export { ComplianceReportGenerator } from './ComplianceReportGenerator';
export type {
  ComplianceReportType,
  ComplianceReportStatus,
} from './ComplianceReportGenerator';

// 合规报告详情
export { ComplianceReportDetail } from './ComplianceReportDetail';
export type {
  ComplianceReport as ComplianceReportDetailType,
  ReportSummary,
  ReportDetailData,
} from './ComplianceReportDetail';

// 团队管理组件（如存在）
export { TeamManager } from './TeamManager';

// 企业信息组件（如存在）
export { EnterpriseInfo } from './EnterpriseInfo';

// 企业订单组件（如存在）
export { EnterpriseOrders } from './EnterpriseOrders';

// 权限设置组件（如存在）
export { PermissionSettings } from './PermissionSettings';