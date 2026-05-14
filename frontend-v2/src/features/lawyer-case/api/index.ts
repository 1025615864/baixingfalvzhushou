/**
 * 律师案件管理 API 层
 * 对接后端 /cases 和 /dispatch 端点
 */

import { apiClient } from '@/shared/lib/api/client';

import type {
  CaseListResponse,
  CaseStats,
  CreateCaseRequest,
  UpdateCaseRequest,
  AddProgressRequest,
  CloseCaseRequest,
  DispatchPoolResponse,
} from '../types';

const CASE_API_BASE = '/cases';
const DISPATCH_API_BASE = '/dispatch';

export async function getCases(params: {
  status?: string;
  page?: number;
  pageSize?: number;
} = {}): Promise<CaseListResponse> {
  const { data } = await apiClient.get<CaseListResponse>(`${CASE_API_BASE}/`, { params });
  return data;
}

export async function getCaseDetail(caseId: number) {
  const { data } = await apiClient.get(`${CASE_API_BASE}/${caseId}`);
  return data.data;
}

export async function createCase(request: CreateCaseRequest) {
  const { data } = await apiClient.post(`${CASE_API_BASE}/`, request);
  return data.data;
}

export async function updateCase(caseId: number, request: UpdateCaseRequest) {
  const { data } = await apiClient.patch(`${CASE_API_BASE}/${caseId}`, request);
  return data.data;
}

export async function addProgressNode(caseId: number, request: AddProgressRequest) {
  const { data } = await apiClient.post(`${CASE_API_BASE}/${caseId}/progress`, request);
  return data.data;
}

export async function closeCase(caseId: number, request: CloseCaseRequest) {
  const { data } = await apiClient.post(`${CASE_API_BASE}/${caseId}/close`, request);
  return data.data;
}

export async function getCaseStats(): Promise<CaseStats> {
  const { data } = await apiClient.get<{ data: CaseStats }>(`${CASE_API_BASE}/stats/summary`);
  return data.data;
}

export async function getDispatchPool(params: {
  page?: number;
  pageSize?: number;
  category?: string;
} = {}): Promise<DispatchPoolResponse> {
  const { data } = await apiClient.get<DispatchPoolResponse>(`${DISPATCH_API_BASE}/pool`, { params });
  return data;
}

export async function grabConsultation(consultationId: number) {
  const { data } = await apiClient.post(`${DISPATCH_API_BASE}/grab/${consultationId}`);
  return data.data;
}

export async function getMyDispatches(params: {
  page?: number;
  pageSize?: number;
} = {}) {
  const { data } = await apiClient.get(`${DISPATCH_API_BASE}/my-dispatches`, { params });
  return data;
}