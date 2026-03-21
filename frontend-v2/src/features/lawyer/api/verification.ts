import { apiClient } from '@/shared/lib/api/client';
import type {
  SubmitVerificationRequest,
  SubmitVerificationResponse,
  VerificationStatusResponse,
  LawyerVerification,
} from '../types';
import { transformVerification, transformVerificationStatus } from './transforms';
import type { VerificationResponseSnake, VerificationStatusResponseSnake } from '../types';

const API_BASE = '/lawyers';

export async function submitVerification(request: SubmitVerificationRequest): Promise<SubmitVerificationResponse> {
  const response = await apiClient.post<VerificationResponseSnake>(`${API_BASE}/verification/submit`, {
    real_name: request.realName,
    id_card_no: request.idCardNo,
    license_no: request.licenseNo,
    firm_name: request.firmName,
    id_card_front: request.idCardFront,
    id_card_back: request.idCardBack,
    license_photo: request.licensePhoto,
    specialties: request.specialties,
    introduction: request.introduction,
    experience_years: request.experienceYears,
  });

  return {
    verification: transformVerification(response.data),
  };
}

export async function getVerificationStatus(): Promise<VerificationStatusResponse> {
  const { data } = await apiClient.get<VerificationStatusResponseSnake>(`${API_BASE}/verification/status`);
  return transformVerificationStatus(data);
}

export async function getVerificationDetail(verificationId: string): Promise<LawyerVerification> {
  const { data } = await apiClient.get<VerificationResponseSnake>(
    `${API_BASE}/verification/${verificationId}`
  );
  return transformVerification(data);
}
