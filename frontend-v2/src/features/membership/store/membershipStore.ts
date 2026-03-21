/**
 * 会员状态管理 Store
 * 管理用户会员等级、权益、免费咨询次数等
 */

import { create } from 'zustand';
import { persist, createJSONStorage } from 'zustand/middleware';

import type {
  MembershipTier,
  MembershipBenefits,
  UserMembership,
} from '@/features/membership/types';

// ==================== 类型定义 ====================

/** 会员等级信息 */
export interface MembershipLevel {
  tier: MembershipTier;
  name: string;
  displayName: string;
  price: number;
  duration: 'month' | 'quarter' | 'year' | 'lifetime';
}

/** 会员使用配额 */
export interface MembershipQuota {
  /** AI 聊天 */
  aiChat: {
    limit: number;
    used: number;
    remaining: number;
  };
  /** 文档生成 */
  documentGenerate: {
    limit: number;
    used: number;
    remaining: number;
  };
  /** 视频咨询 */
  videoConsultation: {
    limit: number;
    used: number;
    remaining: number;
  };
  /** 合同审核 */
  contractReview: {
    limit: number;
    used: number;
    remaining: number;
  };
}

/** 会员状态 */
export interface MembershipState {
  // ========== 会员信息 ==========
  /** 当前会员等级 */
  currentLevel: MembershipTier;
  /** 会员详细信息 */
  membershipInfo: UserMembership | null;
  /** 会员权益 */
  benefits: MembershipBenefits | null;
  /** 是否为 VIP */
  isVip: boolean;
  /** 会员到期时间 */
  expiresAt: string | null;
  /** 是否自动续费 */
  autoRenew: boolean;

  // ========== 免费次数 ==========
  /** 免费视频咨询次数 */
  freeVideoConsultations: number;
  /** 免费文档审核次数 */
  freeDocumentReviews: number;
  /** 本月已用视频咨询次数 */
  usedVideoConsultations: number;
  /** 本月已用文档审核次数 */
  usedDocumentReviews: number;

  // ========== 配额 ==========
  /** 使用配额 */
  quota: MembershipQuota | null;

  // ========== 加载状态 ==========
  /** 是否加载中 */
  isLoading: boolean;
  /** 错误信息 */
  error: string | null;

  // ========== Actions ==========
  /** 设置会员信息 */
  setMembershipInfo: (info: UserMembership | null) => void;
  /** 设置会员等级 */
  setCurrentLevel: (level: MembershipTier) => void;
  /** 设置会员权益 */
  setBenefits: (benefits: MembershipBenefits | null) => void;
  /** 设置 VIP 状态 */
  setVipStatus: (isVip: boolean) => void;
  /** 设置到期时间 */
  setExpiresAt: (expiresAt: string | null) => void;
  /** 设置自动续费 */
  setAutoRenew: (autoRenew: boolean) => void;

  /** 设置免费视频咨询次数 */
  setFreeVideoConsultations: (count: number) => void;
  /** 设置免费文档审核次数 */
  setFreeDocumentReviews: (count: number) => void;
  /** 更新免费次数（批量） */
  updateFreeCounts: (video: number, document: number) => void;
  /** 使用一次视频咨询 */
  useVideoConsultation: () => void;
  /** 使用一次文档审核 */
  useDocumentReview: () => void;

  /** 设置配额 */
  setQuota: (quota: MembershipQuota | null) => void;
  /** 更新 AI 聊天配额 */
  updateAiChatQuota: (used: number, limit: number) => void;
  /** 更新文档生成配额 */
  updateDocumentQuota: (used: number, limit: number) => void;

  /** 设置加载状态 */
  setLoading: (isLoading: boolean) => void;
  /** 设置错误信息 */
  setError: (error: string | null) => void;

  /** 清除会员信息 */
  clearMembership: () => void;
  /** 重置为默认状态 */
  reset: () => void;
}

// ==================== 默认值 ====================

/** 默认会员配额 */
const defaultQuota: MembershipQuota = {
  aiChat: { limit: 10, used: 0, remaining: 10 },
  documentGenerate: { limit: 5, used: 0, remaining: 5 },
  videoConsultation: { limit: 0, used: 0, remaining: 0 },
  contractReview: { limit: 1, used: 0, remaining: 1 },
};

/** 初始状态 */
const initialState = {
  currentLevel: 'free' as MembershipTier,
  membershipInfo: null,
  benefits: null,
  isVip: false,
  expiresAt: null,
  autoRenew: false,
  freeVideoConsultations: 0,
  freeDocumentReviews: 0,
  usedVideoConsultations: 0,
  usedDocumentReviews: 0,
  quota: defaultQuota,
  isLoading: false,
  error: null,
};

// ==================== Store 实现 ====================

export const useMembershipStore = create<MembershipState>()(
  persist(
    (set, _get) => ({
      ...initialState,

      // ========== 会员信息 Actions ==========
      setMembershipInfo: (info) =>
        set({
          membershipInfo: info,
          currentLevel: info?.level ?? 'free',
          isVip: info?.isVip ?? false,
          expiresAt: info?.endDate ?? null,
          benefits: info?.benefits ?? null,
        }),

      setCurrentLevel: (level) =>
        set({ currentLevel: level }),

      setBenefits: (_benefits) =>
        set({ benefits: _benefits }),

      setVipStatus: (_isVip) =>
        set({ isVip: _isVip }),

      setExpiresAt: (_expiresAt) =>
        set({ expiresAt: _expiresAt }),

      setAutoRenew: (_autoRenew) =>
        set({ autoRenew: _autoRenew }),

      // ========== 免费次数 Actions ==========
      setFreeVideoConsultations: (count) =>
        set((state) => ({
          freeVideoConsultations: count,
          quota: state.quota
            ? {
                ...state.quota,
                videoConsultation: {
                  ...state.quota.videoConsultation,
                  limit: count,
                  remaining: Math.max(0, count - state.usedVideoConsultations),
                },
              }
            : null,
        })),

      setFreeDocumentReviews: (count) =>
        set((state) => ({
          freeDocumentReviews: count,
          quota: state.quota
            ? {
                ...state.quota,
                contractReview: {
                  ...state.quota.contractReview,
                  limit: count,
                  remaining: Math.max(0, count - state.usedDocumentReviews),
                },
              }
            : null,
        })),

      updateFreeCounts: (video, document) =>
        set((state) => ({
          freeVideoConsultations: video,
          freeDocumentReviews: document,
          quota: state.quota
            ? {
                ...state.quota,
                videoConsultation: {
                  ...state.quota.videoConsultation,
                  limit: video,
                  remaining: Math.max(0, video - state.usedVideoConsultations),
                },
                contractReview: {
                  ...state.quota.contractReview,
                  limit: document,
                  remaining: Math.max(0, document - state.usedDocumentReviews),
                },
              }
            : null,
        })),

      useVideoConsultation: () =>
        set((state) => {
          const newUsed = state.usedVideoConsultations + 1;
          return {
            usedVideoConsultations: newUsed,
            quota: state.quota
              ? {
                  ...state.quota,
                  videoConsultation: {
                    ...state.quota.videoConsultation,
                    used: newUsed,
                    remaining: Math.max(0, state.freeVideoConsultations - newUsed),
                  },
                }
              : null,
          };
        }),

      useDocumentReview: () =>
        set((state) => {
          const newUsed = state.usedDocumentReviews + 1;
          return {
            usedDocumentReviews: newUsed,
            quota: state.quota
              ? {
                  ...state.quota,
                  contractReview: {
                    ...state.quota.contractReview,
                    used: newUsed,
                    remaining: Math.max(0, state.freeDocumentReviews - newUsed),
                  },
                }
              : null,
          };
        }),

      // ========== 配额 Actions ==========
      setQuota: (quota) =>
        set({ quota }),

      updateAiChatQuota: (used, limit) =>
        set((state) => ({
          quota: state.quota
            ? {
                ...state.quota,
                aiChat: { limit, used, remaining: Math.max(0, limit - used) },
              }
            : null,
        })),

      updateDocumentQuota: (used, limit) =>
        set((state) => ({
          quota: state.quota
            ? {
                ...state.quota,
                documentGenerate: { limit, used, remaining: Math.max(0, limit - used) },
              }
            : null,
        })),

      // ========== 状态管理 Actions ==========
      setLoading: (_isLoading) =>
        set({ isLoading: _isLoading }),

      setError: (_error) =>
        set({ error: _error }),

      clearMembership: () =>
        set({
          ...initialState,
          quota: defaultQuota,
        }),

      reset: () =>
        set(initialState),
    }),
    {
      name: 'membership-storage',
      storage: createJSONStorage(() => localStorage),
      partialize: (state) => ({
        currentLevel: state.currentLevel,
        isVip: state.isVip,
        expiresAt: state.expiresAt,
        freeVideoConsultations: state.freeVideoConsultations,
        freeDocumentReviews: state.freeDocumentReviews,
      }),
    }
  )
);

// ==================== 选择器 ====================

/** 当前会员等级选择器 */
export const selectCurrentLevel = (state: MembershipState) => state.currentLevel;

/** 会员信息选择器 */
export const selectMembershipInfo = (state: MembershipState) => state.membershipInfo;

/** 会员权益选择器 */
export const selectBenefits = (state: MembershipState) => state.benefits;

/** 是否 VIP 选择器 */
export const selectIsVip = (state: MembershipState) => state.isVip;

/** 免费视频咨询次数选择器 */
export const selectFreeVideoConsultations = (state: MembershipState) =>
  state.freeVideoConsultations;

/** 免费文档审核次数选择器 */
export const selectFreeDocumentReviews = (state: MembershipState) =>
  state.freeDocumentReviews;

/** 配额选择器 */
export const selectQuota = (state: MembershipState) => state.quota;

/** AI 聊天配额选择器 */
export const selectAiChatQuota = (state: MembershipState) => state.quota?.aiChat;

/** 文档生成配额选择器 */
export const selectDocumentQuota = (state: MembershipState) =>
  state.quota?.documentGenerate;

/** 视频咨询配额选择器 */
export const selectVideoConsultationQuota = (state: MembershipState) =>
  state.quota?.videoConsultation;

/** 合同审核配额选择器 */
export const selectContractReviewQuota = (state: MembershipState) =>
  state.quota?.contractReview;

/** 加载状态选择器 */
export const selectIsLoading = (state: MembershipState) => state.isLoading;

/** 错误选择器 */
export const selectError = (state: MembershipState) => state.error;

// ==================== Hooks ====================

/** 获取当前会员等级 */
export const useMembershipLevel = () => useMembershipStore(selectCurrentLevel);

/** 获取会员信息 */
export const useMembershipInfoState = () => useMembershipStore(selectMembershipInfo);

/** 获取会员权益 */
export const useMembershipBenefits = () => useMembershipStore(selectBenefits);

/** 获取 VIP 状态 */
export const useMembershipVipStatus = () => useMembershipStore(selectIsVip);

/** 获取免费视频咨询次数 */
export const useFreeVideoConsultations = () =>
  useMembershipStore(selectFreeVideoConsultations);

/** 获取免费文档审核次数 */
export const useFreeDocumentReviews = () =>
  useMembershipStore(selectFreeDocumentReviews);

/** 获取配额 */
export const useMembershipQuota = () => useMembershipStore(selectQuota);

/** 获取 AI 聊天配额 */
export const useAiChatQuota = () => useMembershipStore(selectAiChatQuota);

/** 获取加载状态 */
export const useMembershipLoading = () => useMembershipStore(selectIsLoading);

/** 获取错误信息 */
export const useMembershipError = () => useMembershipStore(selectError);

export default useMembershipStore;