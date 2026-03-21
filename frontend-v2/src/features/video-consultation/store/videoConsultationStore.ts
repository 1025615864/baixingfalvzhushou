/**
 * 视频咨询状态管理 Store
 * 管理当前咨询、通话状态、会议信息等
 */

import { create } from 'zustand';
import { persist, createJSONStorage } from 'zustand/middleware';

import type {
  VideoConsultation,
  VideoConsultationStatus,
  VideoPaymentStatus,
  VideoSlot,
} from '@/features/video-consultation/types';

// ==================== 类型定义 ====================

/** 通话状态 */
export type CallStatus = 'idle' | 'connecting' | 'connected' | 'disconnected' | 'ended';

/** 通话质量 */
export interface CallQuality {
  /** 网络延迟 (ms) */
  latency: number;
  /** 丢包率 (0-100) */
  packetLoss: number;
  /** 视频分辨率 */
  resolution: string;
  /** 帧率 */
  frameRate: number;
  /** 音频质量 (1-5) */
  audioQuality: number;
}

/** 会议信息 */
export interface MeetingInfo {
  /** 会议 ID */
  meetingId: string;
  /** 会议密码 */
  password?: string;
  /** 会议链接 */
  joinUrl?: string;
  /** 会议开始时间 */
  startTime: string;
  /** 会议时长 (分钟) */
  duration: number;
  /** 律师 ID */
  lawyerId: string;
  /** 律师姓名 */
  lawyerName?: string;
}

/** 本地媒体状态 */
export interface LocalMediaState {
  /** 麦克风是否开启 */
  micEnabled: boolean;
  /** 摄像头是否开启 */
  cameraEnabled: boolean;
  /** 屏幕共享是否开启 */
  screenSharing: boolean;
  /** 是否静音 */
  muted: boolean;
}

/** 远程参与者 */
export interface RemoteParticipant {
  /** 参与者 ID */
  id: string;
  /** 参与者名称 */
  name: string;
  /** 是否视频开启 */
  videoEnabled: boolean;
  /** 是否音频开启 */
  audioEnabled: boolean;
  /** 是否主持人 */
  isHost: boolean;
}

/** 视频咨询状态 */
export interface VideoConsultationState {
  // ========== 当前咨询 ==========
  /** 当前咨询 */
  currentConsultation: VideoConsultation | null;
  /** 咨询 ID */
  consultationId: string | null;
  /** 咨询状态 */
  consultationStatus: VideoConsultationStatus | null;
  /** 支付状态 */
  paymentStatus: VideoPaymentStatus | null;

  // ========== 通话状态 ==========
  /** 是否正在通话中 */
  isCallActive: boolean;
  /** 通话状态 */
  callStatus: CallStatus;
  /** 通话开始时间 */
  callStartTime: string | null;
  /** 通话时长 (秒) */
  callDuration: number;
  /** 通话质量 */
  callQuality: CallQuality | null;

  // ========== 会议信息 ==========
  /** 会议信息 */
  meetingInfo: MeetingInfo | null;
  /** 选中的时段 */
  selectedSlot: VideoSlot | null;

  // ========== 媒体状态 ==========
  /** 本地媒体状态 */
  localMedia: LocalMediaState;
  /** 远程参与者列表 */
  remoteParticipants: RemoteParticipant[];

  // ========== UI 状态 ==========
  /** 是否显示设置面板 */
  showSettings: boolean;
  /** 是否显示聊天面板 */
  showChat: boolean;
  /** 是否全屏 */
  isFullscreen: boolean;
  /** 是否正在加载 */
  isLoading: boolean;
  /** 错误信息 */
  error: string | null;

  // ========== Actions ==========
  /** 设置当前咨询 */
  setCurrentConsultation: (consultation: VideoConsultation | null) => void;
  /** 设置咨询 ID */
  setConsultationId: (id: string | null) => void;
  /** 设置咨询状态 */
  setConsultationStatus: (status: VideoConsultationStatus | null) => void;
  /** 设置支付状态 */
  setPaymentStatus: (status: VideoPaymentStatus | null) => void;

  /** 设置通话激活状态 */
  setCallActive: (active: boolean) => void;
  /** 设置通话状态 */
  setCallStatus: (status: CallStatus) => void;
  /** 开始通话 */
  startCall: () => void;
  /** 结束通话 */
  endCall: () => void;
  /** 更新通话时长 */
  updateCallDuration: (duration: number) => void;
  /** 设置通话质量 */
  setCallQuality: (quality: CallQuality | null) => void;

  /** 设置会议信息 */
  setMeetingInfo: (info: MeetingInfo | null) => void;
  /** 设置选中时段 */
  setSelectedSlot: (slot: VideoSlot | null) => void;

  /** 切换麦克风 */
  toggleMic: () => void;
  /** 切换摄像头 */
  toggleCamera: () => void;
  /** 切换屏幕共享 */
  toggleScreenShare: () => void;
  /** 设置静音 */
  setMuted: (muted: boolean) => void;
  /** 更新本地媒体状态 */
  updateLocalMedia: (state: Partial<LocalMediaState>) => void;

  /** 设置远程参与者 */
  setRemoteParticipants: (participants: RemoteParticipant[]) => void;
  /** 添加远程参与者 */
  addRemoteParticipant: (participant: RemoteParticipant) => void;
  /** 移除远程参与者 */
  removeRemoteParticipant: (participantId: string) => void;
  /** 更新远程参与者 */
  updateRemoteParticipant: (participantId: string, updates: Partial<RemoteParticipant>) => void;

  /** 切换设置面板 */
  toggleSettings: () => void;
  /** 切换聊天面板 */
  toggleChat: () => void;
  /** 切换全屏 */
  toggleFullscreen: () => void;
  /** 设置加载状态 */
  setLoading: (loading: boolean) => void;
  /** 设置错误信息 */
  setError: (error: string | null) => void;

  /** 重置所有状态 */
  reset: () => void;
  /** 重置通话状态 */
  resetCall: () => void;
}

// ==================== 默认值 ====================

/** 默认本地媒体状态 */
const defaultLocalMedia: LocalMediaState = {
  micEnabled: true,
  cameraEnabled: true,
  screenSharing: false,
  muted: false,
};

/** 初始状态 */
const initialState = {
  // 当前咨询
  currentConsultation: null,
  consultationId: null,
  consultationStatus: null,
  paymentStatus: null,

  // 通话状态
  isCallActive: false,
  callStatus: 'idle' as CallStatus,
  callStartTime: null,
  callDuration: 0,
  callQuality: null,

  // 会议信息
  meetingInfo: null,
  selectedSlot: null,

  // 媒体状态
  localMedia: defaultLocalMedia,
  remoteParticipants: [],

  // UI 状态
  showSettings: false,
  showChat: false,
  isFullscreen: false,
  isLoading: false,
  error: null,
};

// ==================== Store 实现 ====================

export const useVideoConsultationStore = create<VideoConsultationState>()(
  persist(
    (set, _get) => ({
      ...initialState,

      // ========== 咨询 Actions ==========
      setCurrentConsultation: (consultation) =>
        set({
          currentConsultation: consultation,
          consultationId: consultation?.id ?? null,
          consultationStatus: consultation?.status ?? null,
          paymentStatus: consultation?.paymentStatus ?? null,
        }),

      setConsultationId: (id) =>
        set({ consultationId: id }),

      setConsultationStatus: (status) =>
        set((state) => ({
          consultationStatus: status,
          currentConsultation: state.currentConsultation
            ? { ...state.currentConsultation, status: status! }
            : null,
        })),

      setPaymentStatus: (status) =>
        set((state) => ({
          paymentStatus: status,
          currentConsultation: state.currentConsultation
            ? { ...state.currentConsultation, paymentStatus: status! }
            : null,
        })),

      // ========== 通话 Actions ==========
      setCallActive: (active) =>
        set({ isCallActive: active }),

      setCallStatus: (status) =>
        set({ callStatus: status }),

      startCall: () =>
        set({
          isCallActive: true,
          callStatus: 'connecting',
          callStartTime: new Date().toISOString(),
          callDuration: 0,
        }),

      endCall: () =>
        set(() => ({
          isCallActive: false,
          callStatus: 'ended',
          callDuration: 0,
          callStartTime: null,
          localMedia: defaultLocalMedia,
          remoteParticipants: [],
        })),

      updateCallDuration: (duration) =>
        set({ callDuration: duration }),

      setCallQuality: (quality) =>
        set({ callQuality: quality }),

      // ========== 会议 Actions ==========
      setMeetingInfo: (info) =>
        set({ meetingInfo: info }),

      setSelectedSlot: (slot) =>
        set({ selectedSlot: slot }),

      // ========== 媒体 Actions ==========
      toggleMic: () =>
        set((state) => ({
          localMedia: {
            ...state.localMedia,
            micEnabled: !state.localMedia.micEnabled,
          },
        })),

      toggleCamera: () =>
        set((state) => ({
          localMedia: {
            ...state.localMedia,
            cameraEnabled: !state.localMedia.cameraEnabled,
          },
        })),

      toggleScreenShare: () =>
        set((state) => ({
          localMedia: {
            ...state.localMedia,
            screenSharing: !state.localMedia.screenSharing,
          },
        })),

      setMuted: (muted) =>
        set((state) => ({
          localMedia: { ...state.localMedia, muted },
        })),

      updateLocalMedia: (updates) =>
        set((state) => ({
          localMedia: { ...state.localMedia, ...updates },
        })),

      // ========== 参与者 Actions ==========
      setRemoteParticipants: (participants) =>
        set({ remoteParticipants: participants }),

      addRemoteParticipant: (participant) =>
        set((state) => ({
          remoteParticipants: [...state.remoteParticipants, participant],
        })),

      removeRemoteParticipant: (participantId) =>
        set((state) => ({
          remoteParticipants: state.remoteParticipants.filter(
            (p) => p.id !== participantId
          ),
        })),

      updateRemoteParticipant: (participantId, updates) =>
        set((state) => ({
          remoteParticipants: state.remoteParticipants.map((p) =>
            p.id === participantId ? { ...p, ...updates } : p
          ),
        })),

      // ========== UI Actions ==========
      toggleSettings: () =>
        set((state) => ({ showSettings: !state.showSettings })),

      toggleChat: () =>
        set((state) => ({ showChat: !state.showChat })),

      toggleFullscreen: () =>
        set((state) => ({ isFullscreen: !state.isFullscreen })),

      setLoading: (loading) =>
        set({ isLoading: loading }),

      setError: (error) =>
        set({ error }),

      // ========== 重置 Actions ==========
      reset: () =>
        set(initialState),

      resetCall: () =>
        set({
          isCallActive: false,
          callStatus: 'idle',
          callStartTime: null,
          callDuration: 0,
          callQuality: null,
          localMedia: defaultLocalMedia,
          remoteParticipants: [],
          showSettings: false,
          showChat: false,
          isFullscreen: false,
        }),

      _state: null,
    }),
    {
      name: 'video-consultation-storage',
      storage: createJSONStorage(() => sessionStorage), // 使用 sessionStorage，关闭浏览器后清除
      partialize: (state) => ({
        // 只保存必要的状态
        consultationId: state.consultationId,
        meetingInfo: state.meetingInfo,
      }),
    }
  )
);

// ==================== 选择器 ====================

/** 当前咨询选择器 */
export const selectCurrentConsultation = (state: VideoConsultationState) =>
  state.currentConsultation;

/** 咨询 ID 选择器 */
export const selectConsultationId = (state: VideoConsultationState) =>
  state.consultationId;

/** 咨询状态选择器 */
export const selectConsultationStatus = (state: VideoConsultationState) =>
  state.consultationStatus;

/** 是否通话中选择器 */
export const selectIsCallActive = (state: VideoConsultationState) =>
  state.isCallActive;

/** 通话状态选择器 */
export const selectCallStatus = (state: VideoConsultationState) =>
  state.callStatus;

/** 通话时长选择器 */
export const selectCallDuration = (state: VideoConsultationState) =>
  state.callDuration;

/** 通话质量选择器 */
export const selectCallQuality = (state: VideoConsultationState) =>
  state.callQuality;

/** 会议信息选择器 */
export const selectMeetingInfo = (state: VideoConsultationState) =>
  state.meetingInfo;

/** 选中时段选择器 */
export const selectSelectedSlot = (state: VideoConsultationState) =>
  state.selectedSlot;

/** 本地媒体状态选择器 */
export const selectLocalMedia = (state: VideoConsultationState) =>
  state.localMedia;

/** 远程参与者选择器 */
export const selectRemoteParticipants = (state: VideoConsultationState) =>
  state.remoteParticipants;

/** 麦克风状态选择器 */
export const selectMicEnabled = (state: VideoConsultationState) =>
  state.localMedia.micEnabled;

/** 摄像头状态选择器 */
export const selectCameraEnabled = (state: VideoConsultationState) =>
  state.localMedia.cameraEnabled;

/** 屏幕共享状态选择器 */
export const selectScreenSharing = (state: VideoConsultationState) =>
  state.localMedia.screenSharing;

/** 加载状态选择器 */
export const selectIsLoading = (state: VideoConsultationState) =>
  state.isLoading;

/** 错误选择器 */
export const selectError = (state: VideoConsultationState) =>
  state.error;

// ==================== Hooks ====================

/** 获取当前咨询 */
export const useCurrentConsultation = () =>
  useVideoConsultationStore(selectCurrentConsultation);

/** 获取通话状态 */
export const useCallStatus = () =>
  useVideoConsultationStore(selectCallStatus);

/** 获取是否通话中 */
export const useIsCallActive = () =>
  useVideoConsultationStore(selectIsCallActive);

/** 获取通话时长 */
export const useCallDuration = () =>
  useVideoConsultationStore(selectCallDuration);

/** 获取会议信息 */
export const useMeetingInfo = () =>
  useVideoConsultationStore(selectMeetingInfo);

/** 获取本地媒体状态 */
export const useLocalMedia = () =>
  useVideoConsultationStore(selectLocalMedia);

/** 获取远程参与者 */
export const useRemoteParticipants = () =>
  useVideoConsultationStore(selectRemoteParticipants);

/** 获取麦克风状态 */
export const useMicEnabled = () =>
  useVideoConsultationStore(selectMicEnabled);

/** 获取摄像头状态 */
export const useCameraEnabled = () =>
  useVideoConsultationStore(selectCameraEnabled);

/** 获取加载状态 */
export const useVideoConsultationLoading = () =>
  useVideoConsultationStore(selectIsLoading);

/** 获取错误信息 */
export const useVideoConsultationError = () =>
  useVideoConsultationStore(selectError);

export default useVideoConsultationStore;