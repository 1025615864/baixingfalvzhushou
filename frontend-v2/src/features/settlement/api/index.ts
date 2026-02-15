/**
 * Settlement（结算管理）API 层
 *
 * 使用统一的 apiClient 进行 HTTP 请求
 * 后端路由: /api/v1/settlement/*
 */

import { apiClient } from "@/shared/lib/api/client";

import type {
  WithdrawalRequest,
  BankAccount,
  IncomeRecord,
  WalletBalance,
  PaginationMeta,
  GetIncomeRecordsRequest,
  RequestWithdrawalRequest,
  GetWithdrawalRecordsRequest,
  WithdrawalStatus,
  IncomeStatus,
  WithdrawMethod,
  AccountType,
} from '../types';


/** 添加银行账户请求 */
interface AddBankAccountRequest {
  accountType: AccountType;
  bankName: string;
  accountNo: string;
  accountHolder: string;
  isDefault?: boolean;
}

/** 更新银行账户请求 */
interface UpdateBankAccountRequest {
  bankName?: string;
  accountNo?: string;
  accountHolder?: string;
  isDefault?: boolean;
  isActive?: boolean;
}

// API 基础路径
const SETTLEMENT_BASE = '/settlement';

// ==================== 后端响应类型定义 ====================

/** 后端钱包余额数据 */
interface BackendWalletBalance {
  lawyer_id: number;
  total_income: number;
  withdrawn_amount: number;
  pending_amount: number;
  frozen_amount: number;
  available_amount: number;
  created_at: string;
  updated_at: string;
}

/** 后端收入记录数据 */
interface BackendIncomeRecord {
  id: number;
  lawyer_id: number;
  consultation_id: number | null;
  consultation_subject: string | null;
  order_no: string | null;
  user_paid_amount: number;
  platform_fee: number;
  lawyer_income: number;
  withdrawn_amount: number;
  status: string;
  settle_time: string | null;
  created_at: string;
  updated_at: string;
}

/** 后端收入记录列表响应 */
interface BackendIncomeRecordListResponse {
  items: BackendIncomeRecord[];
  total: number;
  page: number;
  page_size: number;
}

/** 后端银行账户数据 */
interface BackendBankAccount {
  id: number;
  lawyer_id: number;
  account_type: string;
  bank_name: string | null;
  account_no_masked: string;
  account_holder: string;
  is_default: boolean;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

/** 后端银行账户列表响应 */
interface BackendBankAccountListResponse {
  items: BackendBankAccount[];
  total: number;
}

/** 后端提现申请数据 */
interface BackendWithdrawalItem {
  id: number;
  request_no: string;
  lawyer_id: number;
  lawyer_name: string | null;
  lawyer_rating: number | null;
  lawyer_completed_count: number | null;
  platform_fee_rate: number | null;
  amount: number;
  fee: number;
  actual_amount: number;
  withdraw_method: string;
  account_info_masked: string;
  status: string;
  reject_reason: string | null;
  admin_id: number | null;
  reviewed_at: string | null;
  completed_at: string | null;
  remark: string | null;
  created_at: string;
  updated_at: string;
}

/** 后端提现申请列表响应 */
interface BackendWithdrawalListResponse {
  items: BackendWithdrawalItem[];
  total: number;
  page: number;
  page_size: number;
}

/** 后端结算统计数据 */
interface BackendSettlementStats {
  month_start: string;
  month_end: string;
  wallet_summary: {
    total_income: number;
    withdrawn_amount: number;
    pending_amount: number;
    frozen_amount: number;
    available_amount: number;
  };
  withdrawal_summary: {
    pending_count: number;
    pending_amount: number;
    approved_count: number;
    approved_amount: number;
    completed_month_count: number;
    completed_month_amount: number;
  };
  platform_fee_month_total: number;
  lawyer_income_month_total: number;
  top_lawyers: Array<{
    lawyer_id: number;
    lawyer_name: string | null;
    income_records: number;
    lawyer_income: number;
    platform_fee: number;
  }>;
}

// ==================== 数据转换函数 ====================

/**
 * 转换后端钱包余额为前端格式
 */
function transformWalletBalance(backend: BackendWalletBalance): WalletBalance {
  return {
    userId: String(backend.lawyer_id),
    lawyerId: String(backend.lawyer_id),
    balance: backend.available_amount,
    frozenBalance: backend.frozen_amount,
    currency: 'CNY',
    totalIncome: backend.total_income,
    withdrawnAmount: backend.withdrawn_amount,
    pendingAmount: backend.pending_amount,
    availableAmount: backend.available_amount,
    updatedAt: backend.updated_at,
  };
}

/**
 * 转换后端收入记录为前端格式
 */
function transformIncomeRecord(backend: BackendIncomeRecord): IncomeRecord {
  return {
    id: String(backend.id),
    userId: String(backend.lawyer_id),
    lawyerId: String(backend.lawyer_id),
    sourceId: String(backend.consultation_id || backend.id),
    sourceType: 'consultation',
    consultationId: backend.consultation_id ? String(backend.consultation_id) : undefined,
    orderNo: backend.order_no || undefined,
    amount: backend.lawyer_income,
    userPaidAmount: backend.user_paid_amount,
    platformFee: backend.platform_fee,
    lawyerIncome: backend.lawyer_income,
    description: backend.consultation_subject || '法律咨询收入',
    status: backend.status as IncomeStatus,
    settled: backend.status === 'settled',
    settleTime: backend.settle_time || undefined,
    createdAt: backend.created_at,
    updatedAt: backend.updated_at,
  };
}

/**
 * 转换后端银行账户为前端格式
 */
function transformBankAccount(backend: BackendBankAccount): BankAccount {
  return {
    id: String(backend.id),
    lawyerId: String(backend.lawyer_id),
    accountType: backend.account_type === 'alipay' ? 'personal' : (backend.account_type as AccountType),
    bankName: backend.bank_name || '',
    accountNo: backend.account_no_masked,
    accountHolder: backend.account_holder,
    isDefault: backend.is_default,
    isActive: backend.is_active,
    createdAt: backend.created_at,
    updatedAt: backend.updated_at,
  };
}

/**
 * 转换后端提现申请为前端格式
 */
function transformWithdrawalRequest(backend: BackendWithdrawalItem): WithdrawalRequest {
  return {
    id: String(backend.id),
    requestNo: backend.request_no,
    lawyerId: String(backend.lawyer_id),
    amount: backend.amount,
    fee: backend.fee,
    actualAmount: backend.actual_amount,
    withdrawMethod: backend.withdraw_method as WithdrawMethod,
    accountInfoMasked: backend.account_info_masked,
    status: backend.status as WithdrawalStatus,
    rejectReason: backend.reject_reason || undefined,
    reviewedAt: backend.reviewed_at || undefined,
    completedAt: backend.completed_at || undefined,
    createdAt: backend.created_at,
    updatedAt: backend.updated_at,
  };
}

/**
 * 构建分页元数据
 */
function buildPaginationMeta(page: number, pageSize: number, total: number): PaginationMeta {
  return {
    page,
    pageSize,
    total,
    totalPages: Math.ceil(total / pageSize),
  };
}

// ==================== API 函数 ====================

/**
 * 获取钱包余额
 * GET /settlement/lawyer/wallet
 */
export async function apiGetWalletBalance(): Promise<WalletBalance> {
  const { data } = await apiClient.get<BackendWalletBalance>(`${SETTLEMENT_BASE}/lawyer/wallet`);
  return transformWalletBalance(data);
}

/**
 * 获取收入记录
 * GET /settlement/lawyer/income-records
 */
export async function apiGetIncomeRecords(
  params: GetIncomeRecordsRequest
): Promise<{
  items: IncomeRecord[];
  meta: PaginationMeta;
}> {
  const { data } = await apiClient.get<BackendIncomeRecordListResponse>(
    `${SETTLEMENT_BASE}/lawyer/income-records`,
    {
      params: {
        page: params.page || 1,
        page_size: params.pageSize || 20,
        ...(params.status && { status: params.status }),
      },
    }
  );

  return {
    items: data.items.map(transformIncomeRecord),
    meta: buildPaginationMeta(data.page, data.page_size, data.total),
  };
}

/**
 * 导出收入记录
 * GET /settlement/lawyer/income-records/export
 */
export async function apiExportIncomeRecords(status?: IncomeStatus): Promise<Blob> {
  const response = await apiClient.get<Blob>(
    `${SETTLEMENT_BASE}/lawyer/income-records/export`,
    {
      params: {
        ...(status && { status }),
      },
      responseType: 'blob',
    }
  );
  return response.data;
}

/**
 * 获取银行账户列表
 * GET /settlement/lawyer/bank-accounts
 */
export async function apiGetBankAccounts(): Promise<BankAccount[]> {
  const { data } = await apiClient.get<BackendBankAccountListResponse>(
    `${SETTLEMENT_BASE}/lawyer/bank-accounts`
  );
  return data.items.map(transformBankAccount);
}

/**
 * 添加银行账户
 * POST /settlement/lawyer/bank-accounts
 */
export async function apiAddBankAccount(request: AddBankAccountRequest): Promise<BankAccount> {
  const { data } = await apiClient.post<BackendBankAccount>(
    `${SETTLEMENT_BASE}/lawyer/bank-accounts`,
    {
      account_type: request.accountType === 'personal' ? 'bank_card' : request.accountType,
      bank_name: request.bankName,
      account_no: request.accountNo,
      account_holder: request.accountHolder,
      is_default: request.isDefault,
    }
  );
  return transformBankAccount(data);
}

/**
 * 更新银行账户
 * PUT /settlement/lawyer/bank-accounts/:id
 */
export async function apiUpdateBankAccount(
  accountId: string,
  request: UpdateBankAccountRequest
): Promise<BankAccount> {
  const { data } = await apiClient.put<BackendBankAccount>(
    `${SETTLEMENT_BASE}/lawyer/bank-accounts/${accountId}`,
    {
      ...(request.bankName !== undefined && { bank_name: request.bankName }),
      ...(request.accountNo !== undefined && { account_no: request.accountNo }),
      ...(request.accountHolder !== undefined && { account_holder: request.accountHolder }),
      ...(request.isDefault !== undefined && { is_default: request.isDefault }),
      ...(request.isActive !== undefined && { is_active: request.isActive }),
    }
  );
  return transformBankAccount(data);
}

/**
 * 删除银行账户
 * DELETE /settlement/lawyer/bank-accounts/:id
 */
export async function apiDeleteBankAccount(accountId: string): Promise<{ message: string }> {
  const { data } = await apiClient.delete<{ message: string }>(
    `${SETTLEMENT_BASE}/lawyer/bank-accounts/${accountId}`
  );
  return data;
}

/**
 * 设置默认银行账户
 * PUT /settlement/lawyer/bank-accounts/:id/default
 */
export async function apiSetDefaultBankAccount(accountId: string): Promise<{ message: string }> {
  const { data } = await apiClient.put<{ message: string }>(
    `${SETTLEMENT_BASE}/lawyer/bank-accounts/${accountId}/default`
  );
  return data;
}

/**
 * 获取提现记录
 * GET /settlement/lawyer/withdrawals
 */
export async function apiGetWithdrawalRecords(
  params: GetWithdrawalRecordsRequest
): Promise<{
  items: WithdrawalRequest[];
  meta: PaginationMeta;
}> {
  const { data } = await apiClient.get<BackendWithdrawalListResponse>(
    `${SETTLEMENT_BASE}/lawyer/withdrawals`,
    {
      params: {
        page: params.page || 1,
        page_size: params.pageSize || 20,
        ...(params.status && { status: params.status }),
      },
    }
  );

  return {
    items: data.items.map(transformWithdrawalRequest),
    meta: buildPaginationMeta(data.page, data.page_size, data.total),
  };
}

/**
 * 获取提现详情
 * GET /settlement/lawyer/withdrawals/:id
 */
export async function apiGetWithdrawalDetail(withdrawalId: string): Promise<WithdrawalRequest> {
  const { data } = await apiClient.get<BackendWithdrawalItem>(
    `${SETTLEMENT_BASE}/lawyer/withdrawals/${withdrawalId}`
  );
  return transformWithdrawalRequest(data);
}

/**
 * 申请提现
 * POST /settlement/lawyer/withdrawals
 */
export async function apiRequestWithdrawal(
  request: RequestWithdrawalRequest
): Promise<WithdrawalRequest> {
  const { data } = await apiClient.post<BackendWithdrawalItem>(
    `${SETTLEMENT_BASE}/lawyer/withdrawals`,
    {
      amount: request.amount,
      withdraw_method: request.withdrawMethod,
      bank_account_id: parseInt(request.bankAccountId || '0', 10),
    }
  );
  return transformWithdrawalRequest(data);
}

// ==================== 管理员接口（预留）====================

/**
 * 获取结算统计数据（管理员）
 * GET /settlement/admin/stats
 */
export async function apiGetSettlementStats(): Promise<BackendSettlementStats> {
  const { data } = await apiClient.get<BackendSettlementStats>(
    `${SETTLEMENT_BASE}/admin/stats`
  );
  return data;
}

// ==================== 导出 API 对象 ====================

export const settlementApi = {
  // 钱包相关
  getWalletBalance: apiGetWalletBalance,

  // 收入相关
  getIncomeRecords: apiGetIncomeRecords,
  exportIncomeRecords: apiExportIncomeRecords,

  // 银行账户相关
  getBankAccounts: apiGetBankAccounts,
  addBankAccount: apiAddBankAccount,
  updateBankAccount: apiUpdateBankAccount,
  deleteBankAccount: apiDeleteBankAccount,
  setDefaultBankAccount: apiSetDefaultBankAccount,

  // 提现相关
  getWithdrawalRecords: apiGetWithdrawalRecords,
  getWithdrawalDetail: apiGetWithdrawalDetail,
  requestWithdrawal: apiRequestWithdrawal,

  // 管理员接口
  getSettlementStats: apiGetSettlementStats,
};

export default settlementApi;