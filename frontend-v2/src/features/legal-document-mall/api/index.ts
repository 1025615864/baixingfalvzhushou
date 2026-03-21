/**
 * 法律文书商城 API 层
 * 对接后端 /api/legal-documents 端点
 */

import { apiClient } from "@/shared/lib/api/client";

import type {
  LegalDocument,
  LegalDocumentCategory,
  LegalDocumentQueryParams,
  LegalDocumentListResponse,
  LegalDocumentDetail,
  LegalDocumentOrderListResponse,
  PriceCalculation,
  PurchaseRequest,
  PurchaseResponse,
} from '../types';

// API 基础路径
const API_BASE = '/legal-documents';

// ==================== 分类 API ====================

/**
 * 获取文书分类列表
 */
export async function apiGetCategories(): Promise<LegalDocumentCategory[]> {
  const response = await apiClient.get<LegalDocumentCategory[]>(`${API_BASE}/categories`);
  return response.data;
}

// ==================== 文书列表 API ====================

/**
 * 获取法律文书列表
 */
export async function apiGetDocuments(
  params: LegalDocumentQueryParams = {}
): Promise<LegalDocumentListResponse> {
  const searchParams = new URLSearchParams();
  if (params.category) searchParams.set('category', params.category);
  if (params.keyword) searchParams.set('keyword', params.keyword);
  if (params.page) searchParams.set('page', String(params.page));
  if (params.page_size) searchParams.set('page_size', String(params.page_size));
  if (params.is_featured !== undefined) searchParams.set('is_featured', String(params.is_featured));
  if (params.is_free !== undefined) searchParams.set('is_free', String(params.is_free));

  const response = await apiClient.get<LegalDocumentListResponse>(
    `${API_BASE}?${searchParams.toString()}`
  );
  return response.data;
}

/**
 * 获取推荐文书
 */
export async function apiGetFeaturedDocuments(limit: number = 6): Promise<{ items: LegalDocument[] }> {
  const response = await apiClient.get<{ items: LegalDocument[] }>(
    `${API_BASE}/featured?limit=${limit}`
  );
  return response.data;
}

/**
 * 获取免费文书
 */
export async function apiGetFreeDocuments(limit: number = 10): Promise<{ items: LegalDocument[] }> {
  const response = await apiClient.get<{ items: LegalDocument[] }>(
    `${API_BASE}/free?limit=${limit}`
  );
  return response.data;
}

// ==================== 文书详情 API ====================

/**
 * 获取法律文书详情
 */
export async function apiGetDocument(documentId: number): Promise<LegalDocumentDetail> {
  const response = await apiClient.get<LegalDocumentDetail>(`${API_BASE}/${documentId}`);
  return response.data;
}

/**
 * 获取文书内容（需要已购买）
 */
export async function apiGetDocumentContent(documentId: number): Promise<{
  id: number;
  name: string;
  content: string;
  order_no: string;
  purchased_at: string | null;
}> {
  const response = await apiClient.get<{
    id: number;
    name: string;
    content: string;
    order_no: string;
    purchased_at: string | null;
  }>(`${API_BASE}/${documentId}/content`);
  return response.data;
}

// ==================== 价格计算 API ====================

/**
 * 计算文书价格（考虑会员权益）
 */
export async function apiCalculatePrice(documentId: number): Promise<PriceCalculation> {
  const response = await apiClient.get<PriceCalculation>(`${API_BASE}/${documentId}/price`);
  return response.data;
}

// ==================== 购买 API ====================

/**
 * 购买法律文书
 */
export async function apiPurchaseDocument(
  documentId: number,
  request: PurchaseRequest
): Promise<PurchaseResponse> {
  const response = await apiClient.post<PurchaseResponse>(
    `${API_BASE}/${documentId}/purchase`,
    request
  );
  return response.data;
}

// ==================== 收藏 API ====================

/**
 * 添加收藏
 */
export async function apiAddFavorite(documentId: number): Promise<{ success: boolean }> {
  const response = await apiClient.post<{ success: boolean }>(
    `${API_BASE}/${documentId}/favorite`
  );
  return response.data;
}

/**
 * 取消收藏
 */
export async function apiRemoveFavorite(documentId: number): Promise<{ success: boolean }> {
  const response = await apiClient.delete<{ success: boolean }>(
    `${API_BASE}/${documentId}/favorite`
  );
  return response.data;
}

/**
 * 获取收藏列表
 */
export async function apiGetFavorites(): Promise<{ items: LegalDocument[] }> {
  const response = await apiClient.get<{ items: LegalDocument[] }>(
    `${API_BASE}/user/favorites`
  );
  return response.data;
}

// ==================== 订单 API ====================

/**
 * 获取购买记录
 */
export async function apiGetDocumentOrders(
  page: number = 1,
  pageSize: number = 20
): Promise<LegalDocumentOrderListResponse> {
  const response = await apiClient.get<LegalDocumentOrderListResponse>(
    `${API_BASE}/user/orders?page=${page}&page_size=${pageSize}`
  );
  return response.data;
}