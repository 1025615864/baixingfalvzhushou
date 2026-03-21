import { apiClient } from '@/shared/lib/api/client';
import type {
  Consultation,
  BookingRequest,
  BookingResponse,
  GetMyConsultationsResponse,
  GetMyConsultationsRequest,
  CancelConsultationResponse,
} from '../types';
import { transformConsultation } from './transforms';
import type { ConsultationResponseSnake } from '../types';

const LAWFIRM_API_BASE = '/lawfirm';

export async function createBooking(request: BookingRequest): Promise<BookingResponse> {
  const response = await apiClient.post<ConsultationResponseSnake & {
    payment_order_no: string | null;
    payment_status: string | null;
    payment_amount: number | null;
  }>(`${LAWFIRM_API_BASE}/consultations`, {
    lawyer_id: Number(request.lawyerId),
    subject: request.subject,
    description: request.description,
    category: request.category,
    contact_phone: request.contactPhone,
    preferred_time: request.preferredTime,
  });

  const data = response.data;

  return {
    consultation: transformConsultation(data),
    paymentOrderNo: data.payment_order_no,
    paymentStatus: data.payment_status,
    paymentAmount: data.payment_amount,
  };
}

export async function getMyConsultations(params: GetMyConsultationsRequest = {}): Promise<GetMyConsultationsResponse> {
  const { data } = await apiClient.get<{
    items: ConsultationResponseSnake[];
    total: number;
    page: number;
    page_size: number;
  }>(`${LAWFIRM_API_BASE}/consultations`, {
    params: {
      ...(params.statusFilter && { status_filter: params.statusFilter }),
      ...(params.page && { page: params.page }),
      ...(params.pageSize && { page_size: params.pageSize }),
    },
  });

  return {
    consultations: data.items.map(transformConsultation),
    total: data.total,
    page: data.page,
    pageSize: data.page_size,
  };
}

export async function cancelConsultation(consultationId: string): Promise<CancelConsultationResponse> {
  const response = await apiClient.post<ConsultationResponseSnake>(
    `${LAWFIRM_API_BASE}/consultations/${consultationId}/cancel`
  );
  return {
    consultation: transformConsultation(response.data),
  };
}

export async function getConsultationById(consultationId: string): Promise<Consultation> {
  const { data } = await apiClient.get<ConsultationResponseSnake>(
    `${LAWFIRM_API_BASE}/consultations/${consultationId}`
  );
  return transformConsultation(data);
}
