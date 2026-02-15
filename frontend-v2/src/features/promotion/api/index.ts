/**
 * Promotion（推广系统）API 层
 * 对接后端 /api/promotion 邀请系统端点
 */

import apiClient from "@/shared/lib/api/client";

import type {
  PromotionLink,
  PromotionStats,
  CommissionRecord,
  PromotionPoster,
  CommissionWithdrawal,
  GetPromotionStatsRequest,
  GetCommissionRecordsRequest,
  GeneratePosterRequest,
  RequestWithdrawalRequest,
  InviteHistoryItem,
  InviteRankingItem,
  // 提现管理类型
  WithdrawalItem,
  WithdrawalDetail,
  WithdrawalStats,
  GetWithdrawalsRequest,
  GetWithdrawalsAdminResponse,
  ReviewWithdrawalRequest,
  WithdrawalItemSnake,
  WithdrawalDetailSnake,
  WithdrawalStatsSnake,
} from '../types';

// API 基础路径
const API_BASE = '/promotion';

/** API 错误响应 */
interface ApiErrorResponse {
  detail?: string;
}

/**
 * 安全获取 JSON 响应
 */
async function safeJson<T>(response: Response): Promise<T> {
  const data = await response.json() as T;
  return data;
}

/**
 * 获取 API 错误信息
 */
function getErrorMessage(error: unknown, defaultMsg: string): string {
  if (typeof error === 'object' && error !== null && 'detail' in error) {
    return (error as ApiErrorResponse).detail || defaultMsg;
  }
  return defaultMsg;
}

/**
 * 获取推广链接（邀请码）
 */
export async function apiGetPromotionLink(): Promise<PromotionLink> {
  const response = await apiClient.get<{
    invite_code: string;
    invite_url: string;
    short_url: string;
    qrcode_url: string;
  }>(`${API_BASE}/invite/generate`);

  return {
    code: response.data.invite_code,
    url: response.data.invite_url,
    shortUrl: response.data.short_url,
    qrCodeUrl: response.data.qrcode_url,
    createdAt: new Date().toISOString(),
    expiresAt: null,
  };
}

/**
 * 生成推广链接（重新生成邀请码）
 */
export async function apiGeneratePromotionLink(): Promise<PromotionLink> {
  // 后端每次调用都会生成新的邀请码
  return apiGetPromotionLink();
}

/**
 * 获取推广统计
 */
export async function apiGetPromotionStats(
  _params: GetPromotionStatsRequest = {}
): Promise<PromotionStats> {
  const response = await fetch(`${API_BASE}/invite/stats`, {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json',
    },
    credentials: 'include',
  });

  if (!response.ok) {
    const error = await safeJson<ApiErrorResponse>(response).catch(() => ({ detail: '获取推广统计失败' }));
    throw new Error(getErrorMessage(error, '获取推广统计失败'));
  }

  const data = await safeJson<{
    total_invited?: number;
    total_registered?: number;
    total_rewards?: number;
    pending_rewards?: number;
    conversion_rate?: number;
  }>(response);

  return {
    totalInvited: data.total_invited ?? 0,
    totalRegistered: data.total_registered ?? 0,
    totalRewards: data.total_rewards ?? 0,
    pendingRewards: data.pending_rewards ?? 0,
    conversionRate: data.conversion_rate ?? 0,
    period: 'all',
    totalCommission: data.total_rewards ?? 0,
    pendingCommission: data.pending_rewards ?? 0,
    paidCommission: (data.total_rewards ?? 0) - (data.pending_rewards ?? 0),
  };
}

/**
 * 获取邀请历史记录（映射到佣金记录）
 */
export async function apiGetCommissionRecords(
  params: GetCommissionRecordsRequest = {}
): Promise<{
  records: CommissionRecord[];
  total: number;
  limit: number;
  offset: number;
}> {
  const searchParams = new URLSearchParams();
  if (params.limit) searchParams.set('page_size', String(params.limit));
  if (params.offset) {
    const page = Math.floor(params.offset / (params.limit ?? 20)) + 1;
    searchParams.set('page', String(page));
  }

  const url = `${API_BASE}/invite/history${searchParams.toString() ? `?${searchParams.toString()}` : ''}`;

  const response = await fetch(url, {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json',
    },
    credentials: 'include',
  });

  if (!response.ok) {
    const error = await safeJson<ApiErrorResponse>(response).catch(() => ({ detail: '获取邀请记录失败' }));
    throw new Error(getErrorMessage(error, '获取邀请记录失败'));
  }

  const data = await safeJson<{
    history?: InviteHistoryItem[];
    total?: number;
  }>(response);

  // 将邀请历史映射到佣金记录格式
  const records: CommissionRecord[] = (data.history ?? []).map(item => ({
    id: String(item.id ?? Math.random()),
    orderId: String(item.invited_user_id ?? ''),
    orderAmount: 0,
    commissionAmount: item.reward_amount ?? 0,
    commissionRate: 0,
    status: item.status === 'claimed' ? 'paid' : 'pending',
    sourceUserId: String(item.invited_user_id ?? ''),
    sourceUserName: item.invited_user_name,
    createdAt: item.invited_at,
    confirmedAt: item.claimed_at,
    paidAt: item.claimed_at,
    description: `邀请用户: ${item.invited_user_name ?? '未知用户'}`,
  }));

  return {
    records,
    total: data.total ?? records.length,
    limit: params.limit ?? 20,
    offset: params.offset ?? 0,
  };
}

/**
 * 获取邀请排行榜（映射到海报列表）
 */
export async function apiGetPosters(): Promise<PromotionPoster[]> {
  const response = await fetch(`${API_BASE}/ranking/invite?limit=10`, {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json',
    },
    credentials: 'include',
  });

  if (!response.ok) {
    const error = await safeJson<ApiErrorResponse>(response).catch(() => ({ detail: '获取排行榜失败' }));
    throw new Error(getErrorMessage(error, '获取排行榜失败'));
  }

  const data = await safeJson<{
    ranking?: InviteRankingItem[];
  }>(response);

  // 将排行榜映射到海报格式（用于展示优秀推广者）
  return (data.ranking ?? []).map((item, index) => ({
    id: String(item.user_id ?? index),
    templateId: 'ranking',
    imageUrl: item.avatar_url ?? `https://api.dicebear.com/7.x/avataaars/svg?seed=${item.user_id}`,
    title: `第${index + 1}名: ${item.user_name ?? '匿名用户'}`,
    description: `已邀请 ${item.invite_count ?? 0} 人`,
    customData: {
      rank: index + 1,
      inviteCount: item.invite_count ?? 0,
    },
    createdAt: new Date().toISOString(),
  }));
}

/**
 * 生成推广海报（使用邀请链接生成二维码）
 */
export async function apiGeneratePoster(
  request: GeneratePosterRequest = {}
): Promise<PromotionPoster> {
  // 首先获取邀请码
  const linkResponse = await fetch(`${API_BASE}/invite/generate`, {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json',
    },
    credentials: 'include',
  });

  if (!linkResponse.ok) {
    const error = await safeJson<ApiErrorResponse>(linkResponse).catch(() => ({ detail: '生成海报失败' }));
    throw new Error(getErrorMessage(error, '生成海报失败'));
  }

  const linkData = await linkResponse.json() as {
    invite_code: string;
    qrcode_url: string;
  };

  return {
    id: `poster-${Date.now()}`,
    templateId: request.templateId ?? 'default',
    imageUrl: linkData.qrcode_url,
    title: request.customTitle ?? '扫码加入百姓助手',
    description: request.customDescription ?? '专业法律服务平台',
    customData: {
      inviteCode: linkData.invite_code,
    },
    createdAt: new Date().toISOString(),
  };
}

/**
 * 领取邀请奖励（映射到申请提现）
 */
export async function apiRequestWithdrawal(
  _request: RequestWithdrawalRequest
): Promise<CommissionWithdrawal> {
  const response = await apiClient.post<{
    success?: boolean;
    claimed_amount?: number;
    claimed_count?: number;
  }>(`${API_BASE}/invite/claim`, {
    invite_code: 'all',
  });

  if (!response.data.success) {
    const error = {
      detail: '领取奖励失败',
    };
    throw new Error(getErrorMessage(error, '领取奖励失败'));
  }

  return {
    id: `withdrawal-${Date.now()}`,
    amount: response.data.claimed_amount ?? 0,
    status: 'pending',
    withdrawalMethod: 'reward',
    createdAt: new Date().toISOString(),
    accountInfo: {
      claimedCount: response.data.claimed_count ?? 0,
    },
  };
}

/**
 * 获取奖励记录
 */
export async function apiGetWithdrawals(): Promise<CommissionWithdrawal[]> {
  const response = await fetch(`${API_BASE}/invite/history`, {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json',
    },
    credentials: 'include',
  });

  if (!response.ok) {
    const error = await safeJson<ApiErrorResponse>(response).catch(() => ({ detail: '获取奖励记录失败' }));
    throw new Error(getErrorMessage(error, '获取奖励记录失败'));
  }

  const data = await safeJson<{
    history?: InviteHistoryItem[];
  }>(response);

  // 将已领取的邀请记录映射到提现记录
  return (data.history ?? [])
    .filter(item => item.status === 'claimed')
    .map(item => ({
      id: String(item.id ?? Math.random()),
      amount: item.reward_amount ?? 0,
      status: 'completed',
      withdrawalMethod: 'reward',
      createdAt: item.invited_at,
      processedAt: item.claimed_at,
      accountInfo: {
        invitedUserId: item.invited_user_id,
        invitedUserName: item.invited_user_name,
      },
    }));
}

/**
 * 获取推广规则（使用 SEO 配置作为规则说明）
 */
export async function apiGetPromotionRules(): Promise<{
  rules: {
    commissionRate: number;
    minWithdrawal: number;
    withdrawalMethods: string[];
    description: string;
  };
}> {
  const response = await fetch(`${API_BASE}/seo/config`, {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json',
    },
    credentials: 'include',
  });

  if (!response.ok) {
    const error = await safeJson<ApiErrorResponse>(response).catch(() => ({ detail: '获取推广规则失败' }));
    throw new Error(getErrorMessage(error, '获取推广规则失败'));
  }

  const data = await safeJson<{
    config?: {
      description?: string;
    };
  }>(response);

  return {
    rules: {
      commissionRate: 10, // 默认奖励比例
      minWithdrawal: 0,
      withdrawalMethods: ['reward'],
      description: data.config?.description ?? '邀请好友加入百姓助手，获得积分奖励',
    },
  };
}

/**
 * 获取邀请转化分析（扩展统计）
 */
export async function apiGetInvitationAnalytics(): Promise<{
  totalVisits: number;
  totalSignups: number;
  conversionRate: number;
  rewardsClaimed: number;
  rewardsPending: number;
}> {
  const response = await fetch(`${API_BASE}/analytics/invitation`, {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json',
    },
    credentials: 'include',
  });

  if (!response.ok) {
    const error = await safeJson<ApiErrorResponse>(response).catch(() => ({ detail: '获取转化分析失败' }));
    throw new Error(getErrorMessage(error, '获取转化分析失败'));
  }

  const data = await safeJson<{
    total_visits?: number;
    total_signups?: number;
    conversion_rate?: number;
    rewards_claimed?: number;
    rewards_pending?: number;
  }>(response);

  return {
    totalVisits: data.total_visits ?? 0,
    totalSignups: data.total_signups ?? 0,
    conversionRate: data.conversion_rate ?? 0,
    rewardsClaimed: data.rewards_claimed ?? 0,
    rewardsPending: data.rewards_pending ?? 0,
  };
}

// ==================== 提现管理API（管理员用） ====================

/**
 * 转换提现数据 snake_case → camelCase
 */
function transformWithdrawalItem(data: WithdrawalItemSnake): WithdrawalItem {
  return {
    id: String(data.id),
    requestNo: data.request_no,
    lawyerId: String(data.lawyer_id),
    lawyerName: data.lawyer_name ?? null,
    lawyerRating: data.lawyer_rating ?? null,
    lawyerCompletedCount: data.lawyer_completed_count ?? null,
    platformFeeRate: data.platform_fee_rate ?? null,
    amount: data.amount,
    fee: data.fee,
    actualAmount: data.actual_amount,
    withdrawMethod: data.withdraw_method,
    accountInfoMasked: data.account_info_masked,
    status: data.status as 'pending' | 'approved' | 'rejected' | 'completed',
    rejectReason: data.reject_reason,
    adminId: data.admin_id ? String(data.admin_id) : null,
    reviewedAt: data.reviewed_at,
    completedAt: data.completed_at,
    remark: data.remark,
    createdAt: data.created_at,
    updatedAt: data.updated_at,
  };
}

/**
 * 转换提现详情
 */
function transformWithdrawalDetail(data: WithdrawalDetailSnake): WithdrawalDetail {
  return {
    ...transformWithdrawalItem(data),
    accountInfo: data.account_info,
  };
}

/**
 * 转换提现统计
 */
function transformWithdrawalStats(data: WithdrawalStatsSnake): WithdrawalStats {
  return {
    totalCount: data.total_count,
    totalAmount: data.total_amount,
    pendingCount: data.pending_count,
    pendingAmount: data.pending_amount,
    approvedCount: data.approved_count,
    approvedAmount: data.approved_amount,
    rejectedCount: data.rejected_count,
    rejectedAmount: data.rejected_amount,
    completedCount: data.completed_count,
    completedAmount: data.completed_amount,
  };
}

/**
 * 获取提现列表（管理员用）
 */
export async function apiGetWithdrawalsAdmin(
  params: GetWithdrawalsRequest = {}
): Promise<GetWithdrawalsAdminResponse> {
  const searchParams = new URLSearchParams();
  if (params.page) searchParams.set('page', String(params.page));
  if (params.pageSize) searchParams.set('page_size', String(params.pageSize));
  if (params.status) searchParams.set('status', params.status);
  if (params.keyword) searchParams.set('keyword', params.keyword);
  if (params.fromTime) searchParams.set('from_time', params.fromTime);
  if (params.toTime) searchParams.set('to_time', params.toTime);

  const response = await fetch(`${API_BASE}/admin/withdrawals?${searchParams.toString()}`, {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json',
    },
    credentials: 'include',
  });

  if (!response.ok) {
    const error = await safeJson<ApiErrorResponse>(response).catch(() => ({ detail: '获取提现列表失败' }));
    throw new Error(getErrorMessage(error, '获取提现列表失败'));
  }

  const data = await safeJson<{
    items: WithdrawalItemSnake[];
    total: number;
    page: number;
    page_size: number;
    stats: WithdrawalStatsSnake;
  }>(response);

  return {
    items: (data.items ?? []).map(transformWithdrawalItem),
    total: data.total,
    page: data.page,
    pageSize: data.page_size,
    stats: transformWithdrawalStats(data.stats),
  };
}

/**
 * 获取提现详情（管理员用）
 */
export async function apiGetWithdrawalDetail(id: string): Promise<WithdrawalDetail> {
  const response = await fetch(`${API_BASE}/admin/withdrawals/${id}`, {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json',
    },
    credentials: 'include',
  });

  if (!response.ok) {
    const error = await safeJson<ApiErrorResponse>(response).catch(() => ({ detail: '获取提现详情失败' }));
    throw new Error(getErrorMessage(error, '获取提现详情失败'));
  }

  const data = await safeJson<WithdrawalDetailSnake>(response);
  return transformWithdrawalDetail(data);
}

/**
 * 审核提现申请（管理员用）
 */
export async function apiReviewWithdrawal(
  id: string,
  request: ReviewWithdrawalRequest
): Promise<WithdrawalItem> {
  const response = await apiClient.post<WithdrawalItemSnake>(`${API_BASE}/admin/withdrawals/${id}/review`, {
    approved: request.approved,
    reject_reason: request.rejectReason,
    remark: request.remark,
  });

  return transformWithdrawalItem(response.data);
}

/**
 * 导出提现记录（管理员用）
 */
export async function apiExportWithdrawals(
  params: Omit<GetWithdrawalsRequest, 'page' | 'pageSize'>
): Promise<Blob> {
  const searchParams = new URLSearchParams();
  if (params.status) searchParams.set('status', params.status);
  if (params.keyword) searchParams.set('keyword', params.keyword);
  if (params.fromTime) searchParams.set('from_time', params.fromTime);
  if (params.toTime) searchParams.set('to_time', params.toTime);

  const response = await fetch(`${API_BASE}/admin/withdrawals/export?${searchParams.toString()}`, {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json',
    },
    credentials: 'include',
  });

  if (!response.ok) {
    const error = await safeJson<ApiErrorResponse>(response).catch(() => ({ detail: '导出提现记录失败' }));
    throw new Error(getErrorMessage(error, '导出提现记录失败'));
  }

  return response.blob();
}