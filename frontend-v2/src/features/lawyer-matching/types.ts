export type LawyerStatus = 'online' | 'offline' | 'busy';

export type ConsultationType = 'online' | 'phone' | 'offline' | 'video' | 'in_person';

export interface LawyerMatchResult {
  lawyerId: string;
  lawyerName: string;
  specialties: string[];
  rating: number;
  completedCount: number;
  matchScore: number;
  overallScore: number;
  matchReasons: string[];
}

export interface LawyerDetail {
  id: string;
  name: string;
  avatar?: string;
  title?: string;
  firmName?: string;
  specialties: string[];
  rating: number;
  completedCount: number;
  status: 'online' | 'offline' | 'busy';
  isVerified: boolean;
  phone?: string;
  email?: string;
  introduction?: string;
  experience: number;
  education?: string[];
  certifications?: string[];
  casesHandled?: number;
  languages?: string[];
  workingHours?: string;
}

export interface Booking {
  id: string;
  lawyerId: string;
  lawyerName: string;
  userId: string;
  consultationType: string;
  scheduledTime: string;
  duration: number;
  status: 'pending' | 'confirmed' | 'cancelled' | 'completed';
  topic: string;
  description?: string;
  price: number;
  createdAt: string;
  updatedAt: string;
}

export interface LawyerReview {
  id: string;
  lawyerId: string;
  userId: string;
  userName: string;
  userAvatar?: string;
  bookingId: string;
  rating: number;
  dimensions: ReviewDimensions;
  content: string;
  tags?: string[];
  isAnonymous: boolean;
  isRecommended: boolean;
  createdAt: string;
  replyContent?: string;
  repliedAt?: string;
}

export interface Lawyer {
  id: string;
  name: string;
  avatar?: string;
  title?: string;
  firmName?: string;
  specialties: string[];
  rating: number;
  completedCount: number;
  status: 'online' | 'offline' | 'busy';
  isVerified: boolean;
}

export interface ReviewDimensions {
  professionalism: number;
  responsiveness: number;
  attitude: number;
  valueForMoney: number;
}

export interface ReviewStats {
  lawyerId: string;
  totalReviews: number;
  averageRating: number;
  averageDimensions: ReviewDimensions;
  ratingDistribution: Record<string, number>;
  tagCounts: Record<string, number>;
}

export type LegalDomain =
  | 'civil'
  | 'criminal'
  | 'administrative'
  | 'commercial'
  | 'labor'
  | 'intellectual_property'
  | 'intellectual'
  | 'real_estate'
  | 'property'
  | 'family'
  | 'contract'
  | 'tort'
  | 'corporate'
  | 'tax'
  | 'other';

export interface MatchingCriteria {
  domains?: LegalDomain[];
  minRating?: number;
  maxPrice?: number;
  onlineOnly?: boolean;
  verifiedOnly?: boolean;
}

export type GetRecommendationsRequest = {
  queryText?: string;
  keywords?: string[];
  domains?: string[];
  limit?: number;
  criteria?: MatchingCriteria;
};

export type GetRecommendationsResponse = {
  recommendations: LawyerMatchResult[];
  total: number;
};

export type GetLawyerDetailRequest = {
  lawyerId: string;
};

export type GetLawyerDetailResponse = {
  lawyer: LawyerDetail;
};

export type CreateBookingRequest = {
  lawyerId: string;
  topic: string;
  description?: string;
  scheduledTime: string;
  consultationType?: string;
  duration?: number;
};

export type CreateBookingResponse = {
  success: boolean;
  booking: Booking;
  paymentUrl?: string;
};

export type GetBookingsRequest = {
  offset?: number;
  limit?: number;
  status?: string;
};

export type GetBookingsResponse = {
  bookings: Booking[];
  total: number;
};

export type CancelBookingRequest = {
  bookingId: string;
};

export type CancelBookingResponse = {
  success: boolean;
  refundAmount?: number;
};

export type GetReviewsRequest = {
  lawyerId: string;
  offset?: number;
  limit?: number;
  sortBy?: string;
};

export type GetReviewsResponse = {
  reviews: LawyerReview[];
  total: number;
  stats: ReviewStats;
};

export type SubmitReviewRequest = {
  lawyerId: string;
  bookingId: string;
  rating: number;
  content: string;
  dimensions: ReviewDimensions;
  tags?: string[];
  isAnonymous?: boolean;
  isRecommended?: boolean;
};

export type SubmitReviewResponse = {
  success: boolean;
  review: LawyerReview;
};

export type SearchLawyersRequest = {
  query?: string;
  offset?: number;
  limit?: number;
  filters?: {
    domains?: string[];
    minRating?: number;
    maxPrice?: number;
  };
};

export type SearchLawyersResponse = {
  lawyers: Lawyer[];
  total: number;
  hasMore: boolean;
};

export type GetOnlineStatusRequest = {
  lawyerIds: string[];
};

export type GetOnlineStatusResponse = {
  statuses: LawyerOnlineInfo[];
};

export interface LawyerOnlineInfo {
  lawyerId: string;
  status: 'online' | 'offline' | 'busy';
  lastActiveAt?: string;
  currentConsultationCount?: number;
  estimatedWaitTime?: number;
}
