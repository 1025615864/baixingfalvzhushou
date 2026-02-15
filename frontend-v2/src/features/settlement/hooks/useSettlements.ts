/**
 * Settlement（结算管理）Hooks
 *
 * 使用真实后端API进行数据获取
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';

import {
  apiGetWalletBalance,
  apiGetIncomeRecords,
  apiGetWithdrawalRecords,
  apiGetWithdrawalDetail,
  apiRequestWithdrawal,
  apiGetBankAccounts,
  apiAddBankAccount,
  apiDeleteBankAccount,
  apiSetDefaultBankAccount,
} from '../api';
import type {
  WalletBalance,
  IncomeRecord,
  WithdrawalRequest,
  WithdrawalStatus,
  BankAccount,
  GetIncomeRecordsRequest,
  GetWithdrawalRecordsRequest,
  RequestWithdrawalRequest,
  AddBankAccountRequest,
} from '../types';

// 状态配置
const statusConfig: Record<WithdrawalStatus, { label: string; color: string }> = {
  pending: { label: '待审核', color: 'bg-yellow-100 text-yellow-800' },
  approved: { label: '已批准', color: 'bg-blue-100 text-blue-800' },
  processing: { label: '处理中', color: 'bg-purple-100 text-purple-800' },
  completed: { label: '已完成', color: 'bg-green-100 text-green-800' },
  rejected: { label: '已拒绝', color: 'bg-red-100 text-red-800' },
  failed: { label: '失败', color: 'bg-red-100 text-red-800' },
};

/**
 * 获取钱包余额 Hook
 */
export function useWalletBalance() {
  return useQuery<WalletBalance>({
    queryKey: ['wallet-balance'],
    queryFn: apiGetWalletBalance,
    staleTime: 30000, // 30秒内不重新请求
  });
}

/**
 * 获取收入记录 Hook
 */
export function useIncomeRecords(params: GetIncomeRecordsRequest = {}) {
  return useQuery<{
    items: IncomeRecord[];
    meta: { page: number; pageSize: number; total: number; totalPages: number };
  }>({
    queryKey: ['income-records', params],
    queryFn: () => apiGetIncomeRecords(params),
  });
}

/**
 * 获取提现记录 Hook
 */
export function useWithdrawals(params: GetWithdrawalRecordsRequest = {}) {
  return useQuery<{
    items: WithdrawalRequest[];
    meta: { page: number; pageSize: number; total: number; totalPages: number };
  }>({
    queryKey: ['withdrawals', params],
    queryFn: () => apiGetWithdrawalRecords(params),
  });
}

/**
 * 获取提现详情 Hook
 */
export function useWithdrawalDetail(withdrawalId: string | undefined) {
  return useQuery<WithdrawalRequest>({
    queryKey: ['withdrawal', withdrawalId],
    queryFn: () => apiGetWithdrawalDetail(withdrawalId!),
    enabled: !!withdrawalId,
  });
}

/**
 * 申请提现 Mutation Hook
 */
export function useRequestWithdrawal() {
  const queryClient = useQueryClient();

  return useMutation<WithdrawalRequest, Error, RequestWithdrawalRequest>({
    mutationFn: apiRequestWithdrawal,
    onSuccess: () => {
      // 刷新相关数据
      void queryClient.invalidateQueries({ queryKey: ['withdrawals'] });
      void queryClient.invalidateQueries({ queryKey: ['wallet-balance'] });
      void queryClient.invalidateQueries({ queryKey: ['income-records'] });
    },
  });
}

/**
 * 获取银行账户列表 Hook
 */
export function useBankAccounts() {
  return useQuery<BankAccount[]>({
    queryKey: ['bank-accounts'],
    queryFn: apiGetBankAccounts,
  });
}

/**
 * 添加银行账户 Mutation Hook
 */
export function useAddBankAccount() {
  const queryClient = useQueryClient();

  return useMutation<BankAccount, Error, AddBankAccountRequest>({
    mutationFn: apiAddBankAccount,
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['bank-accounts'] });
    },
  });
}

/**
 * 删除银行账户 Mutation Hook
 */
export function useDeleteBankAccount() {
  const queryClient = useQueryClient();

  return useMutation<{ message: string }, Error, string>({
    mutationFn: apiDeleteBankAccount,
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['bank-accounts'] });
    },
  });
}

/**
 * 设置默认银行账户 Mutation Hook
 */
export function useSetDefaultBankAccount() {
  const queryClient = useQueryClient();

  return useMutation<{ message: string }, Error, string>({
    mutationFn: apiSetDefaultBankAccount,
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['bank-accounts'] });
    },
  });
}

// 导出状态配置
export { statusConfig, statusConfig as withdrawalStatusConfig };

// 兼容旧API - 保持向后兼容
export function useSettlements() {
  // 结算记录现在通过钱包余额和收入记录来展示
  // 这个hook保留用于向后兼容，但返回钱包余额数据
  return useWalletBalance();
}