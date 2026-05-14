/**
 * 律师案件管理 Hooks
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';

import type {
  CreateCaseRequest,
  UpdateCaseRequest,
  AddProgressRequest,
  CloseCaseRequest,
} from '../types';
import {
  getCases,
  getCaseDetail,
  createCase,
  updateCase,
  addProgressNode,
  closeCase,
  getCaseStats,
  getDispatchPool,
  grabConsultation,
  getMyDispatches,
} from '../api';

const CASE_KEYS = {
  all: ['lawyer', 'cases'] as const,
  lists: () => [...CASE_KEYS.all, 'list'] as const,
  list: (filters: Record<string, unknown>) => [...CASE_KEYS.lists(), filters] as const,
  details: () => [...CASE_KEYS.all, 'detail'] as const,
  detail: (id: number) => [...CASE_KEYS.details(), id] as const,
  stats: () => [...CASE_KEYS.all, 'stats'] as const,
  dispatchPool: (filters?: Record<string, unknown>) => ['dispatch', 'pool', filters ?? {}] as const,
  dispatches: () => ['dispatch', 'list'] as const,
};

export function useCases(params: {
  status?: string;
  page?: number;
  pageSize?: number;
} = {}) {
  return useQuery({
    queryKey: CASE_KEYS.list(params),
    queryFn: () => getCases(params),
    staleTime: 30 * 1000,
  });
}

export function useCaseDetail(caseId: number | null) {
  return useQuery({
    queryKey: CASE_KEYS.detail(caseId!),
    queryFn: () => getCaseDetail(caseId!),
    enabled: caseId !== null && caseId > 0,
  });
}

export function useCaseStats() {
  return useQuery({
    queryKey: CASE_KEYS.stats(),
    queryFn: getCaseStats,
    staleTime: 60 * 1000,
  });
}

export function useCreateCase() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: CreateCaseRequest) => createCase(data),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: CASE_KEYS.lists() });
      void queryClient.invalidateQueries({ queryKey: CASE_KEYS.stats() });
    },
  });
}

export function useUpdateCase() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ caseId, data }: { caseId: number; data: UpdateCaseRequest }) =>
      updateCase(caseId, data),
    onSuccess: (_, variables) => {
      void queryClient.invalidateQueries({ queryKey: CASE_KEYS.lists() });
      void queryClient.invalidateQueries({ queryKey: CASE_KEYS.detail(variables.caseId) });
    },
  });
}

export function useAddProgressNode() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ caseId, data }: { caseId: number; data: AddProgressRequest }) =>
      addProgressNode(caseId, data),
    onSuccess: (_, variables) => {
      void queryClient.invalidateQueries({ queryKey: CASE_KEYS.detail(variables.caseId) });
    },
  });
}

export function useCloseCase() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ caseId, data }: { caseId: number; data: CloseCaseRequest }) =>
      closeCase(caseId, data),
    onSuccess: (_, variables) => {
      void queryClient.invalidateQueries({ queryKey: CASE_KEYS.lists() });
      void queryClient.invalidateQueries({ queryKey: CASE_KEYS.detail(variables.caseId) });
      void queryClient.invalidateQueries({ queryKey: CASE_KEYS.stats() });
    },
  });
}

export function useDispatchPool(params: {
  page?: number;
  pageSize?: number;
  category?: string;
} = {}) {
  return useQuery({
    queryKey: CASE_KEYS.dispatchPool(params),
    queryFn: () => getDispatchPool(params),
    staleTime: 15 * 1000,
  });
}

export function useGrabConsultation() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (consultationId: number) => grabConsultation(consultationId),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['dispatch', 'pool'] });
      void queryClient.invalidateQueries({ queryKey: ['dispatch', 'list'] });
    },
  });
}

export function useMyDispatches(params: {
  page?: number;
  pageSize?: number;
} = {}) {
  return useQuery({
    queryKey: CASE_KEYS.dispatches(),
    queryFn: () => getMyDispatches(params),
    staleTime: 30 * 1000,
  });
}