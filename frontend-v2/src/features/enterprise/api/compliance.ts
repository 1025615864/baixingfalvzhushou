import { apiClient } from '@/shared/lib/api/client';
import type {
  ComplianceTemplate,
  ComplianceReport,
  GetContractReviewsResponse,
  SubmitContractReviewRequest,
  GenerateReportRequest,
  ComplianceReportStatus,
} from '../types';
import type { BackendComplianceReport, BackendComplianceTemplate } from './transforms';

const API_BASE = '/enterprise';

export async function apiGetComplianceTemplates(category?: string): Promise<ComplianceTemplate[]> {
  const response = await apiClient.get<BackendComplianceTemplate[]>(`${API_BASE}/templates`, {
    params: category ? { category } : undefined,
  });
  
  return response.data.map(template => ({
    id: template.id,
    name: template.name,
    category: template.category,
    description: template.description,
    content: template.content,
    tags: template.tags,
    createdAt: template.created_at,
    updatedAt: template.updated_at,
  }));
}

export async function apiGetComplianceReports(
  accountId: number,
  params: { page?: number; pageSize?: number; type?: string }
): Promise<{ reports: ComplianceReport[]; total: number }> {
  const response = await apiClient.get<{
    reports: BackendComplianceReport[];
    total: number;
  }>(`${API_BASE}/account/${accountId}/compliance-reports`, {
    params,
  });

  return {
    reports: response.data.reports.map(report => ({
      id: report.id,
      accountId: report.account_id,
      name: report.name,
      type: report.type as ComplianceReport['type'],
      status: report.status as ComplianceReportStatus,
      content: report.content,
      generatedAt: report.generated_at,
      completedAt: report.completed_at,
      downloadUrl: report.download_url,
      fileSize: report.size,
      createdAt: report.generated_at,
    })),
    total: response.data.total,
  };
}

export async function apiGetComplianceReportById(
  accountId: number,
  reportId: number
): Promise<ComplianceReport> {
  const response = await apiClient.get<BackendComplianceReport>(
    `${API_BASE}/account/${accountId}/compliance-reports/${reportId}`
  );

  return {
    id: response.data.id,
    accountId: response.data.account_id,
    name: response.data.name,
    type: response.data.type as ComplianceReport['type'],
    status: response.data.status as ComplianceReportStatus,
    content: response.data.content,
    generatedAt: response.data.generated_at,
    completedAt: response.data.completed_at,
    downloadUrl: response.data.download_url,
    fileSize: response.data.size,
    createdAt: response.data.generated_at,
  };
}

export async function apiGenerateComplianceReport(
  request: GenerateReportRequest
): Promise<{ reportId: number }> {
  const response = await apiClient.post<{ report_id: number }>(
    `${API_BASE}/account/${request.accountId}/compliance-reports`,
    {
      name: request.name,
      type: request.type,
      parameters: request.parameters,
    }
  );

  return { reportId: response.data.report_id };
}

export async function apiDeleteComplianceReport(
  accountId: number,
  reportId: number
): Promise<void> {
  await apiClient.delete(
    `${API_BASE}/account/${accountId}/compliance-reports/${reportId}`
  );
}

export async function apiExportComplianceReport(
  accountId: number,
  reportId: number,
  format: 'pdf' | 'word' | 'excel'
): Promise<Blob> {
  const response = await apiClient.get(
    `${API_BASE}/account/${accountId}/compliance-reports/${reportId}/export`,
    {
      params: { format },
      responseType: 'blob',
    }
  );

  return response.data as Blob;
}

export function apiGetContractReviews(_accountId: number): Promise<GetContractReviewsResponse> {
  return Promise.resolve({
    contracts: [],
    total: 0,
  });
}

export async function apiSubmitContractReview(
  request: SubmitContractReviewRequest
): Promise<void> {
  await apiClient.post(`${API_BASE}/contract/submit`, {
    account_id: request.accountId,
    user_id: request.userId || 0,
    title: request.title,
    contract_type: request.contractType,
    content: request.content,
  });
}
