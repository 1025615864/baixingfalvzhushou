/**
 * 全局状态管理 Store 统一导出
 * 
 * 本文件整合所有 Zustand Store，提供统一的导出入口
 * 包含：App Store、Auth Store、Membership Store、Video Consultation Store
 */

// ==================== App Store ====================
export {
  // Store
  useAppStore,
  default as appStore,
  // Types
  type AppState,
  type Theme,
  type SidebarState,
  type UserPreferences,
  type MembershipInfo,
  // Selectors
  selectUser,
  selectIsAuthenticated,
  selectTheme,
  selectMembership,
  selectIsVip as selectAppIsVip,
  selectUnreadCount,
  selectPreferences,
  selectSidebarCollapsed,
  selectGlobalLoading,
  selectGlobalError,
  // Hooks
  useUser,
  useIsAuthenticated,
  useTheme,
  useMembershipInfo,
  useIsVip as useAppIsVip,
  useUnreadCount,
  usePreferences,
  useSidebarCollapsed,
  useGlobalLoading,
  useGlobalError,
} from './appStore';

// ==================== Auth Store ====================
export {
  // Store
  useAuthStore,
  default as authStore,
  // Types
  type AuthState,
  type AuthPreferences,
  type LoginMethod,
  type LoginStatus,
  // Selectors
  selectUser as selectAuthUser,
  selectIsAuthenticated as selectAuthIsAuthenticated,
  selectTokenExpiresAt,
  selectLoginStatus,
  selectIsLoggingIn,
  selectLoginError,
  selectIsLocked,
  selectPreferences as selectAuthPreferences,
  selectLastLoginMethod,
  selectIsLoading as selectAuthIsLoading,
  selectError as selectAuthError,
  // Hooks
  useUser as useAuthUser,
  useIsAuthenticated as useAuthIsAuthenticated,
  useLoginStatus,
  useIsLoggingIn,
  useLoginError,
  useIsLocked,
  useAuthPreferences,
  useLastLoginMethod,
  useAuthLoading,
  useAuthError,
} from '@/features/auth/store/authStore';

// ==================== Membership Store ====================
export {
  // Store
  useMembershipStore,
  default as membershipStore,
  // Types
  type MembershipState,
  type MembershipLevel,
  type MembershipQuota,
  // Selectors
  selectCurrentLevel,
  selectMembershipInfo,
  selectBenefits,
  selectIsVip as selectMembershipIsVip,
  selectFreeVideoConsultations,
  selectFreeDocumentReviews,
  selectQuota,
  selectAiChatQuota,
  selectDocumentQuota,
  selectVideoConsultationQuota,
  selectContractReviewQuota,
  selectIsLoading as selectMembershipIsLoading,
  selectError as selectMembershipError,
  // Hooks
  useMembershipLevel,
  useMembershipInfoState,
  useMembershipBenefits,
  useMembershipVipStatus,
  useFreeVideoConsultations,
  useFreeDocumentReviews,
  useMembershipQuota,
  useAiChatQuota,
  useMembershipLoading,
  useMembershipError,
} from '@/features/membership/store/membershipStore';

// ==================== Video Consultation Store ====================
export {
  // Store
  useVideoConsultationStore,
  default as videoConsultationStore,
  // Types
  type VideoConsultationState,
  type CallStatus,
  type CallQuality,
  type MeetingInfo,
  type LocalMediaState,
  type RemoteParticipant,
  // Selectors
  selectCurrentConsultation,
  selectConsultationId,
  selectConsultationStatus,
  selectIsCallActive,
  selectCallStatus,
  selectCallDuration,
  selectCallQuality,
  selectMeetingInfo,
  selectSelectedSlot,
  selectLocalMedia,
  selectRemoteParticipants,
  selectMicEnabled,
  selectCameraEnabled,
  selectScreenSharing,
  selectIsLoading as selectVideoConsultationIsLoading,
  selectError as selectVideoConsultationError,
  // Hooks
  useCurrentConsultation,
  useCallStatus,
  useIsCallActive,
  useCallDuration,
  useMeetingInfo,
  useLocalMedia,
  useRemoteParticipants,
  useMicEnabled,
  useCameraEnabled,
  useVideoConsultationLoading,
  useVideoConsultationError,
} from '@/features/video-consultation/store/videoConsultationStore';

// ==================== Re-export Types for Convenience ====================
export type { User } from '@/features/auth/types';
export type { MembershipTier, MembershipBenefits, UserMembership } from '@/features/membership/types';
export type { VideoConsultation, VideoConsultationStatus, VideoPaymentStatus } from '@/features/video-consultation/types';

// ==================== Store Utilities ====================

// 导入 store hooks 以便在 resetAllStores 中使用
import { useAuthStore } from '@/features/auth/store/authStore';
import { useMembershipStore } from '@/features/membership/store/membershipStore';
import { useVideoConsultationStore } from '@/features/video-consultation/store/videoConsultationStore';

import { useAppStore } from './appStore';

/**
 * 重置所有 Store 状态
 * 用于登出时清理所有状态
 */
export const resetAllStores = () => {
  // 重置 App Store
  useAppStore.getState().resetAll();
  
  // 重置 Auth Store
  useAuthStore.getState().reset();
  
  // 重置 Membership Store
  useMembershipStore.getState().reset();
  
  // 重置 Video Consultation Store
  useVideoConsultationStore.getState().reset();
};

/**
 * 清除所有持久化存储
 * 用于需要完全清除用户数据的场景
 */
export const clearAllPersistedStores = () => {
  // 清除 localStorage
  localStorage.removeItem('app-storage');
  localStorage.removeItem('auth-storage');
  localStorage.removeItem('membership-storage');
  
  // 清除 sessionStorage
  sessionStorage.removeItem('video-consultation-storage');
};

// ==================== Store Keys ====================

/** Store 持久化 Key 常量 */
export const STORE_KEYS = {
  APP: 'app-storage',
  AUTH: 'auth-storage',
  MEMBERSHIP: 'membership-storage',
  VIDEO_CONSULTATION: 'video-consultation-storage',
} as const;