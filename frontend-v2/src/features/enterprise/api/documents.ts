import { apiClient } from '@/shared/lib/api/client';
import type {
  EnterpriseDocument,
  UploadDocumentRequest,
  UpdateDocumentRequest,
  GetDocumentVersionsResponse,
} from '../types';
import type { BackendEnterpriseDocument } from './transforms';

const API_BASE = '/enterprise';

export async function apiGetDocuments(
  accountId: number,
  params: { page?: number; pageSize?: number; type?: string }
): Promise<{ documents: EnterpriseDocument[]; total: number }> {
  const response = await apiClient.get<{
    documents: BackendEnterpriseDocument[];
    total: number;
  }>(`${API_BASE}/account/${accountId}/documents`, {
    params,
  });

  return {
    documents: response.data.documents.map(doc => ({
      id: doc.id,
      accountId: doc.account_id,
      name: doc.name,
      type: doc.type,
      size: doc.size,
      url: doc.url,
      uploadedBy: doc.uploaded_by,
      uploadedAt: doc.uploaded_at,
      updatedAt: doc.updated_at,
      version: doc.version,
      status: doc.status as EnterpriseDocument['status'],
    })),
    total: response.data.total,
  };
}

export async function apiGetDocumentById(
  accountId: number,
  documentId: number
): Promise<EnterpriseDocument> {
  const response = await apiClient.get<BackendEnterpriseDocument>(
    `${API_BASE}/account/${accountId}/documents/${documentId}`
  );

  return {
    id: response.data.id,
    accountId: response.data.account_id,
    name: response.data.name,
    type: response.data.type,
    size: response.data.size,
    url: response.data.url,
    uploadedBy: response.data.uploaded_by,
    uploadedAt: response.data.uploaded_at,
    updatedAt: response.data.updated_at,
    version: response.data.version,
    status: response.data.status as EnterpriseDocument['status'],
  };
}

export async function apiUploadDocument(
  accountId: number,
  request: UploadDocumentRequest
): Promise<{ documentId: number }> {
  const formData = new FormData();
  formData.append('file', request.file);
  formData.append('name', request.name);
  formData.append('type', request.type);
  if (request.description) {
    formData.append('description', request.description);
  }

  const response = await apiClient.post<{ document_id: number }>(
    `${API_BASE}/account/${accountId}/documents`,
    formData,
    {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    }
  );

  return { documentId: response.data.document_id };
}

export async function apiUpdateDocument(
  accountId: number,
  documentId: number,
  request: UpdateDocumentRequest
): Promise<void> {
  await apiClient.put(`${API_BASE}/account/${accountId}/documents/${documentId}`, {
    name: request.name,
    description: request.description,
  });
}

export async function apiDeleteDocument(
  accountId: number,
  documentId: number
): Promise<void> {
  await apiClient.delete(`${API_BASE}/account/${accountId}/documents/${documentId}`);
}

export async function apiGetDocumentVersions(
  accountId: number,
  documentId: number
): Promise<GetDocumentVersionsResponse> {
  const response = await apiClient.get<{
    versions: Array<{
      version: number;
      uploaded_at: string;
      uploaded_by: number;
      size: number;
      url: string;
    }>;
  }>(`${API_BASE}/account/${accountId}/documents/${documentId}/versions`);

  return {
    versions: response.data.versions.map(v => ({
      version: v.version,
      uploadedAt: v.uploaded_at,
      uploadedBy: v.uploaded_by,
      size: v.size,
      url: v.url,
    })),
  };
}
