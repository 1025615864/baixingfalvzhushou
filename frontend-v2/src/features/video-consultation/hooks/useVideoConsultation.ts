/**
 * Video Consultation Hooks
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';

import {
  getVideoConsultations,
  getVideoConsultation,
  createVideoConsultation,
  confirmVideoConsultation,
  startVideoConsultation,
  endVideoConsultation,
  cancelVideoConsultation,
  getLawyerVideoSlots,
  getLawyerVideoFee,
  getMemberDiscount,
  getMyUsage,
} from '../api';
import type { CreateVideoConsultationRequest } from '../types';


/**
 * 获取视频咨询列表
 */
export function useVideoConsultations(params?: {
  status?: string;
  page?: number;
  pageSize?: number;
}) {
  return useQuery({
    queryKey: ['video-consultations', params],
    queryFn: () => getVideoConsultations(params),
  });
}


/**
 * 获取视频咨询详情
 */
export function useVideoConsultation(id: string | number) {
  return useQuery({
    queryKey: ['video-consultation', id],
    queryFn: () => getVideoConsultation(id),
    enabled: !!id,
  });
}


/**
 * 创建视频咨询预约
 */
export function useCreateVideoConsultation() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (data: CreateVideoConsultationRequest) =>
      createVideoConsultation(data),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['video-consultations'] });
      void queryClient.invalidateQueries({ queryKey: ['video-consultation-usage'] });
    },
  });
}


/**
 * 确认视频咨询（律师端）
 */
export function useConfirmVideoConsultation() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (id: string | number) => confirmVideoConsultation(id),
    onSuccess: (_, id) => {
      void queryClient.invalidateQueries({ queryKey: ['video-consultation', id] });
      void queryClient.invalidateQueries({ queryKey: ['video-consultations'] });
      void queryClient.invalidateQueries({ queryKey: ['video-consultation-usage'] });
    },
  });
}


/**
 * 开始视频咨询
 */
export function useStartVideoConsultation() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (id: string | number) => startVideoConsultation(id),
    onSuccess: (_, id) => {
      void queryClient.invalidateQueries({ queryKey: ['video-consultation', id] });
      void queryClient.invalidateQueries({ queryKey: ['video-consultations'] });
      void queryClient.invalidateQueries({ queryKey: ['video-consultation-usage'] });
    },
  });
}


/**
 * 结束视频咨询
 */
export function useEndVideoConsultation() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (id: string | number) => endVideoConsultation(id),
    onSuccess: (_, id) => {
      void queryClient.invalidateQueries({ queryKey: ['video-consultation', id] });
      void queryClient.invalidateQueries({ queryKey: ['video-consultations'] });
      void queryClient.invalidateQueries({ queryKey: ['video-consultation-usage'] });
    },
  });
}


/**
 * 取消视频咨询
 */
export function useCancelVideoConsultation() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (id: string | number) => cancelVideoConsultation(id),
    onSuccess: (_, id) => {
      void queryClient.invalidateQueries({ queryKey: ['video-consultation', id] });
      void queryClient.invalidateQueries({ queryKey: ['video-consultations'] });
      void queryClient.invalidateQueries({ queryKey: ['video-consultation-usage'] });
    },
  });
}


/**
 * 获取律师可用视频时段
 */
export function useLawyerVideoSlots(lawyerId: number | string, date: string) {
  return useQuery({
    queryKey: ['lawyer-video-slots', lawyerId, date],
    queryFn: () => getLawyerVideoSlots(lawyerId, date),
    enabled: !!lawyerId && !!date,
  });
}


/**
 * 获取律师视频咨询费用
 */
export function useLawyerVideoFee(lawyerId: number | string) {
  return useQuery({
    queryKey: ['lawyer-video-fee', lawyerId],
    queryFn: () => getLawyerVideoFee(lawyerId),
    enabled: !!lawyerId,
  });
}


/**
 * 获取我的会员折扣
 */
export function useMemberDiscount() {
  return useQuery({
    queryKey: ['member-discount'],
    queryFn: getMemberDiscount,
  });
}


/**
 * 获取我的使用情况
 */
export function useMyUsage() {
  return useQuery({
    queryKey: ['video-consultation-usage'],
    queryFn: getMyUsage,
  });
}