import { apiClient } from '@/shared/lib/api/client';
import type {
  LawyerHomepage,
  LawyerHomepagePublic,
  CreateHomepageRequest,
  UpdateHomepageRequest,
} from '../types';
import { transformHomepage, transformHomepagePublic } from './transforms';
import type { LawyerHomepageResponseSnake, LawyerHomepagePublicResponseSnake } from '../types';

const API_BASE = '/lawyers';

export async function getMyHomepage(): Promise<LawyerHomepage> {
  const { data } = await apiClient.get<LawyerHomepageResponseSnake>(`${API_BASE}/homepage`);
  return transformHomepage(data);
}

export async function createHomepage(request: CreateHomepageRequest): Promise<LawyerHomepage> {
  const response = await apiClient.post<LawyerHomepageResponseSnake>(`${API_BASE}/homepage`, {
    banner_image: request.bannerImage,
    profile_image: request.profileImage,
    slogan: request.slogan,
    bio: request.bio,
    specialties_display: request.specialtiesDisplay,
    achievements: request.achievements,
    education: request.education,
    service_areas: request.serviceAreas,
    service_hours: request.serviceHours,
    response_time: request.responseTime,
    contact_phone: request.contactPhone,
    contact_email: request.contactEmail,
    wechat_qrcode: request.wechatQrcode,
    weibo_url: request.weiboUrl,
    linkedin_url: request.linkedinUrl,
    zhihu_url: request.zhihuUrl,
    case_studies: request.caseStudies,
    video_url: request.videoUrl,
    video_cover: request.videoCover,
    seo_title: request.seoTitle,
    seo_description: request.seoDescription,
    seo_keywords: request.seoKeywords,
    theme_color: request.themeColor,
    background_color: request.backgroundColor,
  });

  return transformHomepage(response.data);
}

export async function updateHomepage(request: UpdateHomepageRequest): Promise<LawyerHomepage> {
  const response = await apiClient.put<LawyerHomepageResponseSnake>(`${API_BASE}/homepage`, {
    banner_image: request.bannerImage,
    profile_image: request.profileImage,
    slogan: request.slogan,
    bio: request.bio,
    specialties_display: request.specialtiesDisplay,
    achievements: request.achievements,
    education: request.education,
    service_areas: request.serviceAreas,
    service_hours: request.serviceHours,
    response_time: request.responseTime,
    contact_phone: request.contactPhone,
    contact_email: request.contactEmail,
    wechat_qrcode: request.wechatQrcode,
    weibo_url: request.weiboUrl,
    linkedin_url: request.linkedinUrl,
    zhihu_url: request.zhihuUrl,
    case_studies: request.caseStudies,
    video_url: request.videoUrl,
    video_cover: request.videoCover,
    seo_title: request.seoTitle,
    seo_description: request.seoDescription,
    seo_keywords: request.seoKeywords,
    theme_color: request.themeColor,
    background_color: request.backgroundColor,
  });

  return transformHomepage(response.data);
}

export async function getPublicHomepage(lawyerId: string): Promise<LawyerHomepagePublic> {
  const { data } = await apiClient.get<LawyerHomepagePublicResponseSnake>(
    `${API_BASE}/${lawyerId}/homepage/public`
  );
  return transformHomepagePublic(data);
}

export async function publishHomepage(): Promise<{ success: boolean }> {
  const response = await apiClient.post<{ success: boolean }>(`${API_BASE}/homepage/publish`);
  return response.data;
}

export async function unpublishHomepage(): Promise<{ success: boolean }> {
  const response = await apiClient.post<{ success: boolean }>(`${API_BASE}/homepage/unpublish`);
  return response.data;
}
