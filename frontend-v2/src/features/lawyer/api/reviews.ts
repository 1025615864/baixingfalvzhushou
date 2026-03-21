import { apiClient } from '@/shared/lib/api/client';
import type {
  LawyerReview,
  GetLawyerReviewsResponse,
  CreateReviewRequest,
  CreateReviewResponse,
} from '../types';
import { transformReview } from './transforms';
import type { ReviewResponseSnake } from '../types';

const API_BASE = '/lawyers';

export async function getLawyerReviews(
  lawyerId: string,
  params: { page?: number; pageSize?: number } = {}
): Promise<GetLawyerReviewsResponse> {
  const { data } = await apiClient.get<{
    items: ReviewResponseSnake[];
    total: number;
    page: number;
    page_size: number;
    average_rating: number;
  }>(`/reviews`, {
    params: {
      lawyer_id: lawyerId,
      ...(params.page && { page: params.page }),
      ...(params.pageSize && { page_size: params.pageSize }),
    },
  });

  return {
    reviews: data.items.map(transformReview),
    total: data.total,
    page: data.page,
    pageSize: data.page_size,
    averageRating: data.average_rating,
  };
}

export async function createReview(request: CreateReviewRequest): Promise<CreateReviewResponse> {
  const response = await apiClient.post<ReviewResponseSnake>(`${API_BASE}/${request.lawyerId}/reviews`, {
    lawyer_id: Number(request.lawyerId),
    consultation_id: Number(request.consultationId),
    rating: request.rating,
    content: request.content,
    is_anonymous: request.isAnonymous ?? false,
    professionalism: request.professionalism,
    responsiveness: request.responsiveness,
    attitude: request.attitude,
    tags: request.tags,
  });

  return {
    review: transformReview(response.data),
  };
}
