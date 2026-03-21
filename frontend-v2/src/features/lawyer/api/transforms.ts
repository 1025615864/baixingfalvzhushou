import type {
  LawyerResponseSnake,
  ReviewResponseSnake,
  ScheduleResponseSnake,
  ConsultationResponseSnake,
  ReviewSummaryResponseSnake,
  AvailableSlotResponseSnake,
  VerificationResponseSnake,
  VerificationStatusResponseSnake,
  LawyerHomepageResponseSnake,
  LawyerHomepagePublicResponseSnake,
  PromotionLinkResponseSnake,
  PromotionLinkStatsResponseSnake,
  ReplyTemplateResponseSnake,
  Lawyer,
  LawyerReview,
  LawyerSchedule,
  Consultation,
  ReviewSummary,
  AvailableSlot,
  LawyerVerification,
  VerificationStatusResponse,
  LawyerHomepage,
  LawyerHomepagePublic,
  LawyerPromotionLink,
  PromotionLinkStats,
  LawyerReplyTemplate,
} from '../types';

export function transformLawyer(data: LawyerResponseSnake): Lawyer {
  return {
    id: String(data.id),
    userId: data.user_id ? String(data.user_id) : null,
    firmId: data.firm_id ? String(data.firm_id) : null,
    name: data.name,
    avatar: data.avatar,
    title: data.title,
    licenseNo: data.license_no,
    phone: data.phone,
    email: data.email,
    introduction: data.introduction,
    specialties: data.specialties,
    experienceYears: data.experience_years,
    caseCount: data.case_count,
    rating: data.rating,
    reviewCount: data.review_count,
    consultationFee: data.consultation_fee,
    isVerified: data.is_verified,
    isActive: data.is_active,
    createdAt: data.created_at,
    firmName: data.firm_name,
  };
}

export function transformReview(data: ReviewResponseSnake): LawyerReview {
  return {
    id: String(data.id),
    lawyerId: String(data.lawyer_id),
    userId: String(data.user_id),
    consultationId: data.consultation_id ? String(data.consultation_id) : null,
    rating: data.rating,
    content: data.content,
    isAnonymous: data.is_anonymous,
    professionalism: data.professionalism,
    responsiveness: data.responsiveness,
    attitude: data.attitude,
    tags: data.tags ?? [],
    createdAt: data.created_at,
    username: data.username,
  };
}

export function transformSchedule(data: ScheduleResponseSnake): LawyerSchedule {
  return {
    id: String(data.id),
    lawyerId: String(data.lawyer_id),
    date: data.date,
    startTime: data.start_time,
    endTime: data.end_time,
    isAvailable: data.is_available,
    consultationId: data.consultation_id ? String(data.consultation_id) : null,
    note: data.note,
    createdAt: data.created_at,
    updatedAt: data.updated_at,
  };
}

export function transformConsultation(data: ConsultationResponseSnake): Consultation {
  return {
    id: String(data.id),
    userId: String(data.user_id),
    lawyerId: String(data.lawyer_id),
    subject: data.subject,
    description: data.description,
    category: data.category,
    contactPhone: data.contact_phone,
    preferredTime: data.preferred_time,
    status: data.status as 'pending' | 'confirmed' | 'completed' | 'cancelled',
    adminNote: data.admin_note,
    createdAt: data.created_at,
    updatedAt: data.updated_at,
    lawyerName: data.lawyer_name,
    paymentOrderNo: data.payment_order_no,
    paymentStatus: data.payment_status,
    paymentAmount: data.payment_amount,
    reviewId: data.review_id ? String(data.review_id) : null,
    canReview: data.can_review,
  };
}

export function transformReviewSummary(data: ReviewSummaryResponseSnake): ReviewSummary {
  return {
    lawyerId: String(data.lawyer_id),
    lawyerName: data.lawyer_name,
    totalReviews: data.total_reviews,
    averageRating: data.average_rating,
    dimensionStats: {
      professionalismAvg: data.dimension_stats.professionalism_avg,
      responsivenessAvg: data.dimension_stats.responsiveness_avg,
      attitudeAvg: data.dimension_stats.attitude_avg,
    },
    ratingDistribution: {
      rating5Count: data.rating_distribution.rating_5_count,
      rating4Count: data.rating_distribution.rating_4_count,
      rating3Count: data.rating_distribution.rating_3_count,
      rating2Count: data.rating_distribution.rating_2_count,
      rating1Count: data.rating_distribution.rating_1_count,
    },
    tagStats: data.tag_stats,
    popularTags: data.popular_tags,
  };
}

export function transformAvailableSlot(data: AvailableSlotResponseSnake): AvailableSlot {
  return {
    date: data.date,
    startTime: data.start_time,
    endTime: data.end_time,
  };
}

export function transformVerification(data: VerificationResponseSnake): LawyerVerification {
  return {
    id: String(data.id),
    userId: String(data.user_id),
    realName: data.real_name,
    idCardNo: data.id_card_no,
    licenseNo: data.license_no,
    firmName: data.firm_name,
    idCardFront: data.id_card_front,
    idCardBack: data.id_card_back,
    licensePhoto: data.license_photo,
    specialties: data.specialties,
    introduction: data.introduction,
    experienceYears: data.experience_years,
    status: data.status as 'pending' | 'approved' | 'rejected',
    rejectReason: data.reject_reason,
    createdAt: data.created_at,
    reviewedAt: data.reviewed_at,
  };
}

export function transformVerificationStatus(data: VerificationStatusResponseSnake): VerificationStatusResponse {
  return {
    hasVerification: data.has_verification,
    verificationStatus: data.verification_status as 'pending' | 'approved' | 'rejected' | null,
    verificationId: data.verification_id,
    submittedAt: data.submitted_at,
    reviewedAt: data.reviewed_at,
    rejectReason: data.reject_reason,
    isVerifiedLawyer: data.is_verified_lawyer,
  };
}

export function transformHomepage(data: LawyerHomepageResponseSnake): LawyerHomepage {
  return {
    id: String(data.id),
    lawyerId: String(data.lawyer_id),
    bannerImage: data.banner_image,
    profileImage: data.profile_image,
    slogan: data.slogan,
    bio: data.bio,
    specialtiesDisplay: data.specialties_display,
    achievements: data.achievements,
    education: data.education,
    serviceAreas: data.service_areas,
    serviceHours: data.service_hours,
    responseTime: data.response_time,
    contactPhone: data.contact_phone,
    contactEmail: data.contact_email,
    wechatQrcode: data.wechat_qrcode,
    weiboUrl: data.weibo_url,
    linkedinUrl: data.linkedin_url,
    zhihuUrl: data.zhihu_url,
    caseStudies: data.case_studies,
    videoUrl: data.video_url,
    videoCover: data.video_cover,
    seoTitle: data.seo_title,
    seoDescription: data.seo_description,
    seoKeywords: data.seo_keywords,
    themeColor: data.theme_color,
    backgroundColor: data.background_color,
    isPublished: data.is_published,
    viewCount: data.view_count,
    createdAt: data.created_at,
    updatedAt: data.updated_at,
  };
}

export function transformHomepagePublic(data: LawyerHomepagePublicResponseSnake): LawyerHomepagePublic {
  return {
    name: data.lawyer_name || '',
    avatarUrl: data.lawyer_avatar,
    title: data.lawyer_title,
    firmName: null,
    location: data.service_areas,
    isVerified: true,
    phone: data.contact_phone,
    email: data.contact_email,
    weixin: data.wechat_qrcode,
    bio: data.bio,
    specialties: data.lawyer_specialties ? data.lawyer_specialties.split(',').map(s => s.trim()).filter(Boolean) : [],
    cases: [],
    reviews: [],
    consultationCount: 0,
    reviewCount: data.lawyer_review_count || 0,
    responseRate: 0,
  };
}

export function transformPromotionLink(data: PromotionLinkResponseSnake): LawyerPromotionLink {
  return {
    id: String(data.id),
    lawyerId: String(data.lawyer_id),
    linkCode: data.link_code,
    linkName: data.link_name,
    description: data.description,
    isActive: data.is_active,
    clickCount: data.click_count,
    consultationCount: data.consultation_count,
    conversionCount: data.conversion_count,
    createdAt: data.created_at,
    updatedAt: data.updated_at,
  };
}

export function transformPromotionLinkStats(data: PromotionLinkStatsResponseSnake): PromotionLinkStats {
  return {
    linkId: String(data.link_id),
    linkCode: data.link_code,
    linkName: data.link_name,
    clickCount: data.click_count,
    consultationCount: data.consultation_count,
    conversionCount: data.conversion_count,
    conversionRate: data.conversion_rate,
  };
}

export function transformReplyTemplate(data: ReplyTemplateResponseSnake): LawyerReplyTemplate {
  return {
    id: String(data.id),
    lawyerId: String(data.lawyer_id),
    title: data.title,
    content: data.content,
    category: data.category,
    isActive: data.is_active,
    useCount: data.use_count,
    createdAt: data.created_at,
    updatedAt: data.updated_at,
  };
}
