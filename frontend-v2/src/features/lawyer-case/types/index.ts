/**
 * 律师案件管理类型定义
 */

export type CaseStatus = 'active' | 'closed' | 'archived';

export type CaseResultType = 'win' | 'lose' | 'mediation' | 'withdrawal';

export type CasePriority = 0 | 1;

export interface ProgressNode {
  date: string;
  title: string;
  description: string;
}

export interface LawCase {
  id: string;
  caseNo: string;
  consultationId: number | null;
  lawyerId: number | null;
  userId: number | null;
  title: string;
  clientName: string | null;
  category: string;
  status: CaseStatus;
  priority: CasePriority;
  progressNodes: ProgressNode[];
  resultType: CaseResultType | null;
  resultReport: string | null;
  source: string;
  createdAt: string;
  updatedAt: string;
  archivedAt: string | null;
}

export interface LawCaseListItem {
  id: number;
  caseNo: string;
  consultationId: number | null;
  title: string;
  clientName: string | null;
  category: string;
  status: string;
  priority: number;
  source: string;
  resultType: string | null;
  createdAt: string;
  updatedAt: string;
}

export interface CaseListResponse {
  items: LawCaseListItem[];
  total: number;
  page: number;
  pageSize: number;
}

export interface CaseStats {
  activeCount: number;
  closedCount: number;
  winRate: number;
  winCount: number;
  channelDistribution: Array<{ channel: string; count: number }>;
}

export interface CreateCaseRequest {
  consultationId?: number;
  title: string;
  clientName?: string;
  category: string;
  priority?: number;
  source?: string;
}

export interface UpdateCaseRequest {
  title?: string;
  clientName?: string;
  status?: string;
  priority?: number;
}

export interface AddProgressRequest {
  title: string;
  description: string;
}

export interface CloseCaseRequest {
  resultType: string;
  resultReport?: string;
}

export interface DispatchRecord {
  id: number;
  consultationId: number;
  status: string;
  matchScore: number | null;
  dispatchedAt: string;
  respondedAt: string | null;
}

export interface DispatchListResponse {
  items: DispatchRecord[];
  total: number;
  page: number;
  pageSize: number;
}

export interface DispatchPoolItem {
  id: number;
  userId: number;
  category: string;
  title: string;
  description: string;
  createdAt: string;
}

export interface DispatchPoolResponse {
  items: DispatchPoolItem[];
  total: number;
  page: number;
  pageSize: number;
}