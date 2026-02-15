/**
 * Settlement（结算管理）类型定义
 */

// ==================== 枚举类型 ====================

/** 结算状态 */
export type SettlementStatus =
  | 'pending'
  | 'processing'
  | 'completed'
  | 'failed';

/** 提现状态 */
export type WithdrawalStatus =
  | 'pending'
  | 'approved'
  | 'rejected'
  | 'processing'
  | 'completed'
  | 'failed';

/** 提现方式 */
export type WithdrawMethod =
  | 'bank_transfer'
  | 'alipay'
  | 'wechat_pay';

/** 银行账户类型 */
export type AccountType = 'personal' | 'corporate';

/** 收入记录状态 */
export type IncomeStatus =
  | 'pending'
  | 'settled'
  | 'cancelled';

/** 收入类型 */
export type IncomeType =
  | 'consultation'
  | 'reward'
  | 'bonus'
  | 'other';

// ==================== 核心类型 ====================

/** 结算记录 */
export interface SettlementRecord {
  id: string;
  userId: string;
  lawyerId?: string;
  period: string;
  startDate: string;
  endDate: string;
  totalIncome: number;
  platformFee: number;
  taxAmount: number;
  netAmount: number;
  amount?: number;
  status: SettlementStatus;
  description?: string;
  createdAt: string;
  updatedAt?: string;
  completedAt?: string;
}

/** 提现申请 */
export interface WithdrawalRequest {
  id: string;
  requestNo: string;
  lawyerId: string;
  amount: number;
  fee: number;
  actualAmount: number;
  withdrawMethod: WithdrawMethod;
  accountInfoMasked: string;
  status: WithdrawalStatus;
  rejectReason?: string;
  reviewedAt?: string;
  completedAt?: string;
  createdAt: string;
  updatedAt: string;
}

/** 银行账户 */
export interface BankAccount {
  id: string;
  lawyerId: string;
  accountType: AccountType;
  bankName: string;
  accountNo: string;
  accountHolder: string;
  isDefault: boolean;
  isActive: boolean;
  createdAt: string;
  updatedAt: string;
}

/** 收入记录 */
export interface IncomeRecord {
  id: string;
  userId: string;
  lawyerId?: string;
  sourceId: string;
  sourceType: string;
  consultationId?: string;
  orderNo?: string;
  amount: number;
  userPaidAmount?: number;
  platformFee?: number;
  lawyerIncome?: number;
  description: string;
  status: IncomeStatus;
  settled?: boolean;
  settleTime?: string;
  createdAt: string;
  updatedAt?: string;
}

/** 钱包余额 */
export interface WalletBalance {
  userId: string;
  lawyerId?: string;
  balance: number;
  frozenBalance: number;
  currency: string;
  totalIncome?: number;
  withdrawnAmount?: number;
  pendingAmount?: number;
  availableAmount?: number;
  updatedAt: string;
}

// ==================== 分页类型 ====================

/** 分页参数 */
export interface PaginationParams {
  page?: number;
  pageSize?: number;
}

/** 分页响应元数据 */
export interface PaginationMeta {
  page: number;
  pageSize: number;
  total: number;
  totalPages: number;
}

// ==================== API 请求/响应类型 ====================

/** 获取结算记录请求 */
export interface GetSettlementRecordsRequest extends PaginationParams {
  status?: SettlementStatus;
  startDate?: string;
  endDate?: string;
  period?: string;
}

/** 获取结算记录响应 */
export interface GetSettlementRecordsResponse {
  items: SettlementRecord[];
  meta: PaginationMeta;
}

/** 获取收入记录请求 */
export interface GetIncomeRecordsRequest extends PaginationParams {
  status?: IncomeStatus;
  incomeType?: IncomeType;
  startDate?: string;
  endDate?: string;
}

/** 获取收入记录响应 */
export interface GetIncomeRecordsResponse {
  items: IncomeRecord[];
  meta: PaginationMeta;
}

/** 获取钱包余额响应 */
export interface GetWalletBalanceResponse {
  balance: WalletBalance;
}

/** 申请提现请求 */
export interface RequestWithdrawalRequest {
  amount: number;
  withdrawMethod: WithdrawMethod;
  bankAccountId?: string;
  verificationCode?: string;
}

/** 申请提现响应 */
export interface RequestWithdrawalResponse {
  withdrawal: WithdrawalRequest;
}

/** 获取银行账户列表响应 */
export interface GetBankAccountsResponse {
  accounts: BankAccount[];
}

/** 添加银行账户请求 */
export interface AddBankAccountRequest {
  accountType: AccountType;
  bankName: string;
  accountNo: string;
  accountHolder: string;
  isDefault?: boolean;
  branchName?: string;
  phone?: string;
  idCard?: string;
  verifyCode?: string;
}

/** 添加银行账户响应 */
export interface AddBankAccountResponse {
  account: BankAccount;
}

/** 删除银行账户请求 */
export interface DeleteBankAccountRequest {
  accountId: string;
}

/** 删除银行账户响应 */
export interface DeleteBankAccountResponse {
  success: boolean;
}

/** 设置默认银行账户请求 */
export interface SetDefaultBankAccountRequest {
  accountId: string;
}

/** 设置默认银行账户响应 */
export interface SetDefaultBankAccountResponse {
  account: BankAccount;
}

/** 获取提现记录请求 */
export interface GetWithdrawalRecordsRequest extends PaginationParams {
  status?: WithdrawalStatus;
  startDate?: string;
  endDate?: string;
}

/** 获取提现记录响应 */
export interface GetWithdrawalRecordsResponse {
  items: WithdrawalRequest[];
  meta: PaginationMeta;
}