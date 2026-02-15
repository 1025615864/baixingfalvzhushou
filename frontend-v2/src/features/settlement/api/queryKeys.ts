/**
 * Settlement（结算管理）模块 Query Keys
 * 用于 React Query 的缓存管理
 */

export const settlementKeys = {
  // 所有结算相关查询的根key
  all: ['settlement'] as const,

  // 钱包相关
  wallet: () => [...settlementKeys.all, 'wallet'] as const,
  walletBalance: () => [...settlementKeys.wallet(), 'balance'] as const,

  // 收入记录相关
  income: () => [...settlementKeys.all, 'income'] as const,
  incomeList: (filters: { status?: string; startDate?: string; endDate?: string }) =>
    [...settlementKeys.income(), 'list', filters] as const,
  incomeExport: (status?: string) => [...settlementKeys.income(), 'export', status] as const,

  // 银行账户相关
  bankAccounts: () => [...settlementKeys.all, 'bank-accounts'] as const,
  bankAccountList: () => [...settlementKeys.bankAccounts(), 'list'] as const,

  // 提现相关
  withdrawals: () => [...settlementKeys.all, 'withdrawals'] as const,
  withdrawalList: (filters: { status?: string; startDate?: string; endDate?: string }) =>
    [...settlementKeys.withdrawals(), 'list', filters] as const,
  withdrawalDetail: (withdrawalId: string) =>
    [...settlementKeys.withdrawals(), 'detail', withdrawalId] as const,

  // 统计相关（管理员）
  stats: () => [...settlementKeys.all, 'stats'] as const,
  settlementStats: () => [...settlementKeys.stats(), 'overview'] as const,
} as const;

// 导出默认对象便于使用
export default settlementKeys;