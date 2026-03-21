import { apiClient } from '@/shared/lib/api/client';
import type {
  LawyerSchedule,
  GetLawyerScheduleResponse,
  GetAvailableSlotsResponse,
} from '../types';
import { transformSchedule, transformAvailableSlot } from './transforms';
import type { ScheduleResponseSnake, AvailableSlotResponseSnake } from '../types';

const LAWFIRM_API_BASE = '/lawfirm';

export async function getLawyerSchedule(
  lawyerId: string,
  params: { dateFrom?: string; dateTo?: string; page?: number; pageSize?: number } = {}
): Promise<GetLawyerScheduleResponse> {
  const { data } = await apiClient.get<{
    items: ScheduleResponseSnake[];
    total: number;
    page: number;
    page_size: number;
  }>(`/lawyer/schedules`, {
    params: {
      ...(params.dateFrom && { date_from: params.dateFrom }),
      ...(params.dateTo && { date_to: params.dateTo }),
      ...(params.page && { page: params.page }),
      ...(params.pageSize && { page_size: params.pageSize }),
    },
  });

  return {
    schedules: data.items.map(transformSchedule),
    total: data.total,
    page: data.page,
    pageSize: data.page_size,
  };
}

export async function getLawyerAvailableSlots(lawyerId: string, date: string): Promise<GetAvailableSlotsResponse> {
  const { data } = await apiClient.get<{
    lawyer_id: number;
    date: string;
    slots: AvailableSlotResponseSnake[];
  }>(`${LAWFIRM_API_BASE}/lawyers/${lawyerId}/available-slots`, {
    params: { date },
  });

  return {
    lawyerId: String(data.lawyer_id),
    date: data.date,
    slots: data.slots.map(transformAvailableSlot),
  };
}
