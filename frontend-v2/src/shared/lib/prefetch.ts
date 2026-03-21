/**
 * React Query 预加载工具
 * 提供数据预加载功能，用于优化用户体验
 */

import { queryClient } from './query-client';
import { api } from './api/client';
import { CACHE_TIMES } from './cache-utils';

// ============================================================
// 类型定义
// ============================================================

export interface PrefetchOptions {
  /** 缓存时间（毫秒） */
  staleTime?: number;
  /** 是否强制刷新 */
  force?: boolean;
}

// ============================================================
// 用户相关预加载
// ============================================================

/**
 * 预加载用户数据
 * @param userId 用户ID
 * @param options 预加载选项
 */
export const prefetchUserData = async (
  userId: number,
  options: PrefetchOptions = {}
): Promise<void> => {
  const { staleTime = CACHE_TIMES.MEDIUM, force = false } = options;

  // 如果不是强制刷新，检查是否已有缓存
  if (!force) {
    const cached = queryClient.getQueryData(['user', 'profile', userId]);
    if (cached) {
      return;
    }
  }

  await queryClient.prefetchQuery({
    queryKey: ['user', 'profile', userId],
    queryFn: () => api.get(`/user/${userId}`),
    staleTime,
  });
};

/**
 * 预加载当前用户设置
 * @param options 预加载选项
 */
export const prefetchUserSettings = async (
  options: PrefetchOptions = {}
): Promise<void> => {
  const { staleTime = CACHE_TIMES.LONG, force = false } = options;

  if (!force) {
    const cached = queryClient.getQueryData(['user', 'settings']);
    if (cached) {
      return;
    }
  }

  await queryClient.prefetchQuery({
    queryKey: ['user', 'settings'],
    queryFn: () => api.get('/user/me/settings'),
    staleTime,
  });
};

// ============================================================
// 会员相关预加载
// ============================================================

/**
 * 预加载会员数据
 * @param options 预加载选项
 */
export const prefetchMembershipData = async (
  options: PrefetchOptions = {}
): Promise<void> => {
  const { staleTime = CACHE_TIMES.MEDIUM, force = false } = options;

  if (!force) {
    const cached = queryClient.getQueryData(['membership', 'current']);
    if (cached) {
      return;
    }
  }

  await queryClient.prefetchQuery({
    queryKey: ['membership', 'current'],
    queryFn: () => api.get('/membership/me'),
    staleTime,
  });
};

/**
 * 预加载会员套餐列表
 * @param options 预加载选项
 */
export const prefetchMembershipPlans = async (
  options: PrefetchOptions = {}
): Promise<void> => {
  const { staleTime = CACHE_TIMES.VERY_LONG, force = false } = options;

  if (!force) {
    const cached = queryClient.getQueryData(['membership', 'plans']);
    if (cached) {
      return;
    }
  }

  await queryClient.prefetchQuery({
    queryKey: ['membership', 'plans'],
    queryFn: () => api.get('/membership/plans'),
    staleTime,
  });
};

// ============================================================
// 视频咨询相关预加载
// ============================================================

/**
 * 预加载视频咨询详情
 * @param consultationId 咨询ID
 * @param options 预加载选项
 */
export const prefetchVideoConsultation = async (
  consultationId: number,
  options: PrefetchOptions = {}
): Promise<void> => {
  const { staleTime = CACHE_TIMES.SHORT, force = false } = options;

  if (!force) {
    const cached = queryClient.getQueryData(['videoConsultation', 'detail', consultationId]);
    if (cached) {
      return;
    }
  }

  await queryClient.prefetchQuery({
    queryKey: ['videoConsultation', 'detail', consultationId],
    queryFn: () => api.get(`/video-consultation/${consultationId}`),
    staleTime,
  });
};

/**
 * 预加载律师日程
 * @param lawyerId 律师ID
 * @param options 预加载选项
 */
export const prefetchLawyerSchedule = async (
  lawyerId: number,
  options: PrefetchOptions = {}
): Promise<void> => {
  const { staleTime = CACHE_TIMES.SHORT, force = false } = options;

  if (!force) {
    const cached = queryClient.getQueryData(['videoConsultation', 'schedule', lawyerId]);
    if (cached) {
      return;
    }
  }

  await queryClient.prefetchQuery({
    queryKey: ['videoConsultation', 'schedule', lawyerId],
    queryFn: () => api.get(`/video-consultation/schedule/${lawyerId}`),
    staleTime,
  });
};

// ============================================================
// 法律文档相关预加载
// ============================================================

/**
 * 预加载法律文档详情
 * @param documentId 文档ID
 * @param options 预加载选项
 */
export const prefetchLegalDocument = async (
  documentId: number,
  options: PrefetchOptions = {}
): Promise<void> => {
  const { staleTime = CACHE_TIMES.LONG, force = false } = options;

  if (!force) {
    const cached = queryClient.getQueryData(['legalDocument', 'detail', documentId]);
    if (cached) {
      return;
    }
  }

  await queryClient.prefetchQuery({
    queryKey: ['legalDocument', 'detail', documentId],
    queryFn: () => api.get(`/legal-documents/${documentId}`),
    staleTime,
  });
};

/**
 * 预加载法律文档分类
 * @param options 预加载选项
 */
export const prefetchLegalDocumentCategories = async (
  options: PrefetchOptions = {}
): Promise<void> => {
  const { staleTime = CACHE_TIMES.VERY_LONG, force = false } = options;

  if (!force) {
    const cached = queryClient.getQueryData(['legalDocument', 'categories']);
    if (cached) {
      return;
    }
  }

  await queryClient.prefetchQuery({
    queryKey: ['legalDocument', 'categories'],
    queryFn: () => api.get('/legal-documents/categories'),
    staleTime,
  });
};

// ============================================================
// 知识库相关预加载
// ============================================================

/**
 * 预加载知识库详情
 * @param knowledgeId 知识ID
 * @param options 预加载选项
 */
export const prefetchKnowledge = async (
  knowledgeId: number,
  options: PrefetchOptions = {}
): Promise<void> => {
  const { staleTime = CACHE_TIMES.LONG, force = false } = options;

  if (!force) {
    const cached = queryClient.getQueryData(['knowledge', 'detail', knowledgeId]);
    if (cached) {
      return;
    }
  }

  await queryClient.prefetchQuery({
    queryKey: ['knowledge', 'detail', knowledgeId],
    queryFn: () => api.get(`/knowledge/${knowledgeId}`),
    staleTime,
  });
};

/**
 * 预加载知识库分类
 * @param options 预加载选项
 */
export const prefetchKnowledgeCategories = async (
  options: PrefetchOptions = {}
): Promise<void> => {
  const { staleTime = CACHE_TIMES.VERY_LONG, force = false } = options;

  if (!force) {
    const cached = queryClient.getQueryData(['knowledge', 'categories']);
    if (cached) {
      return;
    }
  }

  await queryClient.prefetchQuery({
    queryKey: ['knowledge', 'categories'],
    queryFn: () => api.get('/knowledge/categories'),
    staleTime,
  });
};

// ============================================================
// 律师相关预加载
// ============================================================

/**
 * 预加载律师详情
 * @param lawyerId 律师ID
 * @param options 预加载选项
 */
export const prefetchLawyer = async (
  lawyerId: number,
  options: PrefetchOptions = {}
): Promise<void> => {
  const { staleTime = CACHE_TIMES.MEDIUM, force = false } = options;

  if (!force) {
    const cached = queryClient.getQueryData(['lawyer', 'detail', lawyerId]);
    if (cached) {
      return;
    }
  }

  await queryClient.prefetchQuery({
    queryKey: ['lawyer', 'detail', lawyerId],
    queryFn: () => api.get(`/lawyer/${lawyerId}`),
    staleTime,
  });
};

/**
 * 预加载律师评价
 * @param lawyerId 律师ID
 * @param options 预加载选项
 */
export const prefetchLawyerReviews = async (
  lawyerId: number,
  options: PrefetchOptions = {}
): Promise<void> => {
  const { staleTime = CACHE_TIMES.MEDIUM, force = false } = options;

  if (!force) {
    const cached = queryClient.getQueryData(['lawyer', 'reviews', lawyerId]);
    if (cached) {
      return;
    }
  }

  await queryClient.prefetchQuery({
    queryKey: ['lawyer', 'reviews', lawyerId],
    queryFn: () => api.get(`/lawyer/${lawyerId}/reviews`),
    staleTime,
  });
};

// ============================================================
// 积分相关预加载
// ============================================================

/**
 * 预加载积分余额
 * @param options 预加载选项
 */
export const prefetchPointsBalance = async (
  options: PrefetchOptions = {}
): Promise<void> => {
  const { staleTime = CACHE_TIMES.SHORT, force = false } = options;

  if (!force) {
    const cached = queryClient.getQueryData(['points', 'balance']);
    if (cached) {
      return;
    }
  }

  await queryClient.prefetchQuery({
    queryKey: ['points', 'balance'],
    queryFn: () => api.get('/points/balance'),
    staleTime,
  });
};

/**
 * 预加载积分任务
 * @param options 预加载选项
 */
export const prefetchPointsTasks = async (
  options: PrefetchOptions = {}
): Promise<void> => {
  const { staleTime = CACHE_TIMES.MEDIUM, force = false } = options;

  if (!force) {
    const cached = queryClient.getQueryData(['points', 'tasks']);
    if (cached) {
      return;
    }
  }

  await queryClient.prefetchQuery({
    queryKey: ['points', 'tasks'],
    queryFn: () => api.get('/points/tasks'),
    staleTime,
  });
};

// ============================================================
// 通知相关预加载
// ============================================================

/**
 * 预加载未读通知数量
 * @param options 预加载选项
 */
export const prefetchUnreadNotificationCount = async (
  options: PrefetchOptions = {}
): Promise<void> => {
  const { staleTime = CACHE_TIMES.SHORT, force = false } = options;

  if (!force) {
    const cached = queryClient.getQueryData(['notification', 'unreadCount']);
    if (cached) {
      return;
    }
  }

  await queryClient.prefetchQuery({
    queryKey: ['notification', 'unreadCount'],
    queryFn: () => api.get('/notification/unread-count'),
    staleTime,
  });
};

// ============================================================
// 组合预加载
// ============================================================

/**
 * 预加载首页数据
 */
export const prefetchHomePageData = async (): Promise<void> => {
  await Promise.all([
    prefetchMembershipData(),
    prefetchPointsBalance(),
    prefetchUnreadNotificationCount(),
    prefetchKnowledgeCategories(),
  ]);
};

/**
 * 预加载用户仪表板数据
 */
export const prefetchDashboardData = async (): Promise<void> => {
  await Promise.all([
    prefetchMembershipData(),
    prefetchPointsBalance(),
    prefetchPointsTasks(),
    prefetchUnreadNotificationCount(),
    prefetchUserSettings(),
  ]);
};

/**
 * 预加载律师详情页数据
 * @param lawyerId 律师ID
 */
export const prefetchLawyerPageData = async (lawyerId: number): Promise<void> => {
  await Promise.all([
    prefetchLawyer(lawyerId),
    prefetchLawyerReviews(lawyerId),
    prefetchLawyerSchedule(lawyerId),
  ]);
};

// ============================================================
// 悬停预加载 Hook 工具
// ============================================================

/**
 * 创建悬停预加载函数
 * 用于在用户悬停在链接/元素上时预加载数据
 * @param prefetchFn 预加载函数
 * @param delay 延迟时间（毫秒），默认 100ms
 * @returns 包含开始和取消预加载的对象
 */
export const createHoverPrefetch = <T extends unknown[]>(
  prefetchFn: (...args: T) => Promise<void>,
  delay: number = 100
): {
  start: (...args: T) => void;
  cancel: () => void;
} => {
  let timeoutId: ReturnType<typeof setTimeout> | null = null;

  return {
    start: (...args: T) => {
      if (timeoutId) {
        clearTimeout(timeoutId);
      }
      timeoutId = setTimeout(() => {
        void prefetchFn(...args);
        timeoutId = null;
      }, delay);
    },
    cancel: () => {
      if (timeoutId) {
        clearTimeout(timeoutId);
        timeoutId = null;
      }
    },
  };
};