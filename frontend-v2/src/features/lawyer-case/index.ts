/**
 * 律师案件管理模块导出
 */

export type {
  CaseStatus,
  CaseResultType,
  CasePriority,
  ProgressNode,
  LawCase,
  LawCaseListItem,
  CaseListResponse,
  CaseStats,
  CreateCaseRequest,
  UpdateCaseRequest,
  AddProgressRequest,
  CloseCaseRequest,
  DispatchRecord,
  DispatchListResponse,
  DispatchPoolItem,
  DispatchPoolResponse,
} from './types';

export {
  useCases,
  useCaseDetail,
  useCaseStats,
  useCreateCase,
  useUpdateCase,
  useAddProgressNode,
  useCloseCase,
  useDispatchPool,
  useGrabConsultation,
  useMyDispatches,
} from './hooks/useCases';

export { CaseStatsCards } from './components/CaseStatsCards';
export { CaseTimeline } from './components/CaseTimeline';
export { CaseCreateDialog } from './components/CaseCreateDialog';
export { CaseDetail } from './components/CaseDetail';
export { DispatchPool } from './components/DispatchPool';
export { CaseManagementPage } from './pages/CaseManagementPage';