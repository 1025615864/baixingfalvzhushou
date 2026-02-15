import { useMutation, useQueryClient } from '@tanstack/react-query';

import type { Consultation, CreateConsultationRequest } from '../types';

/**
 * 创建咨询 Hook
 */
export function useCreateConsultation() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (data: CreateConsultationRequest): Promise<Consultation> => {
      // 模拟 API 调用
      await new Promise((resolve) => setTimeout(resolve, 800));
      
      const newConsultation: Consultation = {
        id: Date.now().toString(),
        subject: data.subject,
        description: data.description,
        category: data.category,
        status: 'pending',
        userId: 'user1',
        lawyerId: data.lawyerId,
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString(),
        canReview: false,
      };
      
      return newConsultation;
    },
    onSuccess: () => {
      // 创建成功后刷新咨询列表
      void queryClient.invalidateQueries({ queryKey: ['consultations'] });
    },
  });
}