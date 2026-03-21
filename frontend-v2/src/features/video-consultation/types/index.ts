/**
 * Video Consultation（视频咨询）类型定义
 */

// ==================== 核心类型 ====================

/** 视频咨询状态 */
export type VideoConsultationStatus = 
  | 'pending'      // 待确认
  | 'confirmed'    // 已确认
  | 'in_progress' // 进行中
  | 'completed'   // 已完成
  | 'cancelled';   // 已取消

/** 支付状态 */
export type VideoPaymentStatus = 
  | 'pending'  // 待支付
  | 'paid'     // 已支付
  | 'refunded'; // 已退款

// ==================== 实体类型 ====================

/** 视频咨询 */
export interface VideoConsultation {
  id: string;
  userId: string;
  lawyerId: string;
  subject: string;
  description?: string;
  category?: string;
  scheduledTime: string;
  durationMinutes: number;
  meetingRoomId?: string;
  meetingPassword?: string;
  meetingUrl?: string;
  status: VideoConsultationStatus;
  paymentStatus: VideoPaymentStatus;
  paymentAmount: number;
  isFree: boolean;
  discountRate: number;
  startedAt?: string;
  endedAt?: string;
  completedAt?: string;
  cancelledAt?: string;
  createdAt: string;
  updatedAt: string;
  lawyerName?: string;
}

// ==================== API 请求/响应类型 ====================

/** 创建视频咨询请求 */
export interface CreateVideoConsultationRequest {
  lawyerId: number;
  subject: string;
  description?: string;
  category?: string;
  scheduledTime: string;
}

/** 视频咨询列表响应 */
export interface VideoConsultationListResponse {
  items: VideoConsultation[];
  total: number;
  page: number;
  pageSize: number;
}

/** 视频咨询可用时段 */
export interface VideoSlot {
  scheduleId: number;
  date: string;
  startTime: string;
  endTime: string;
  consultationFee: number;
  availableCount: number;
}

/** 视频咨询可用时段列表响应 */
export interface VideoAvailableSlotsResponse {
  lawyerId: number;
  date: string;
  slots: VideoSlot[];
}

/** 视频咨询费用响应 */
export interface VideoConsultationFee {
  fee: number;
  duration: number;
  enabled: boolean;
}

/** 会员折扣响应 */
export interface MemberDiscount {
  tier: string;
  discountRate: number;
  freeMonthlyCount: number;
  isFree: boolean;
}

/** 用户使用情况响应 */
export interface UserUsage {
  yearMonth: string;
  freeUsed: number;
  paidCount: number;
  remainingFree: number;
  tier?: string;
}

// ==================== 组件 Props 类型 ====================

/** 视频咨询卡片组件 Props */
export interface VideoConsultationCardProps {
  consultation: VideoConsultation;
  onClick?: () => void;
  onJoin?: () => void;
  onCancel?: () => void;
}

/** 视频咨询预约表单 Props */
export interface VideoBookingFormProps {
  lawyerId: number;
  lawyerName?: string;
  fee: number;
  duration: number;
  memberDiscount?: MemberDiscount;
  usage?: UserUsage;
  onSubmit: (data: CreateVideoConsultationRequest) => void;
  onCancel?: () => void;
  loading?: boolean;
}

/** 时段选择组件 Props */
export interface SlotSelectorProps {
  lawyerId: number;
  date: string;
  slots: VideoSlot[];
  selectedSlot?: VideoSlot;
  onSelect: (slot: VideoSlot) => void;
  loading?: boolean;
}