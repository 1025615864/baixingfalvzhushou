/**
 * Consultation（咨询预约）类型定义
 */

// ==================== 核心类型 ====================

/** 咨询状态 */
export type ConsultationStatus = 
  | 'pending'      // 待处理
  | 'assigned'     // 已分配
  | 'in_progress'  // 进行中
  | 'completed'    // 已完成
  | 'cancelled';   // 已取消

/** 咨询分类 */
export type ConsultationCategory = 
  | 'legal'        // 法律咨询
  | 'contract'     // 合同审查
  | 'dispute'      // 纠纷调解
  | 'other';       // 其他

/** 发送者角色 */
export type SenderRole = 'user' | 'lawyer' | 'system';

// ==================== 实体类型 ====================

/** 咨询消息 */
export interface ConsultationMessage {
  id: string;
  consultationId: string;
  senderId: string;
  senderRole: SenderRole;
  content: string;
  createdAt: string;
  senderName?: string;
}

/** 咨询预约 */
export interface Consultation {
  id: string;
  userId: string;
  lawyerId: string;
  subject: string;
  description?: string;
  category?: string;
  contactPhone?: string;
  preferredTime?: string;
  status: ConsultationStatus;
  adminNote?: string;
  createdAt: string;
  updatedAt: string;
  lawyerName?: string;
  paymentOrderNo?: string;
  paymentStatus?: string;
  paymentAmount?: number;
  reviewId?: number;
  canReview: boolean;
}

// ==================== API 请求/响应类型 ====================

/** 创建咨询请求 */
export interface CreateConsultationRequest {
  lawyerId: string;
  subject: string;
  description?: string;
  category?: string;
  contactPhone?: string;
  preferredTime?: string;
}

/** 更新咨询请求 */
export interface UpdateConsultationRequest {
  status?: ConsultationStatus;
  adminNote?: string;
}

/** 发送消息请求 */
export interface SendMessageRequest {
  content: string;
  attachments?: File[];
}

/** 咨询列表响应 */
export interface ConsultationListResponse {
  items: Consultation[];
  total: number;
  page: number;
  pageSize: number;
}

/** 咨询消息列表响应 */
export interface ConsultationMessageListResponse {
  items: ConsultationMessage[];
  total: number;
  page: number;
  pageSize: number;
}

/** 取消咨询响应 */
export interface CancelConsultationResponse {
  success: boolean;
  message: string;
}

// ==================== 组件 Props 类型 ====================

/** 咨询列表组件 Props */
export interface ConsultationListProps {
  consultations: Consultation[];
  onSelect: (consultation: Consultation) => void;
  onCancel?: (id: string) => void;
  loading?: boolean;
}

/** 咨询卡片组件 Props */
export interface ConsultationCardProps {
  consultation: Consultation;
  onClick?: () => void;
  onCancel?: () => void;
  showActions?: boolean;
}

/** 咨询详情组件 Props */
export interface ConsultationDetailProps {
  consultation: Consultation;
  onSendMessage?: (content: string) => void;
  onClose?: () => void;
}

/** 消息列表组件 Props */
export interface MessageListProps {
  messages: ConsultationMessage[];
  currentUserId: string;
  loading?: boolean;
}

/** 消息气泡组件 Props */
export interface MessageBubbleProps {
  message: ConsultationMessage;
  isCurrentUser: boolean;
}

/** 发送消息表单 Props */
export interface SendMessageFormProps {
  onSubmit: (content: string) => void;
  loading?: boolean;
  disabled?: boolean;
}

/** 创建咨询表单 Props */
export interface CreateConsultationFormProps {
  lawyerId: string;
  lawyerName?: string;
  onSubmit: (data: CreateConsultationRequest) => void;
  onCancel?: () => void;
  loading?: boolean;
}

/** 咨询筛选条件 */
export interface ConsultationFilters {
  status?: ConsultationStatus;
  category?: ConsultationCategory;
  startDate?: string;
  endDate?: string;
  searchQuery?: string;
}

// ==================== 咨询模板管理类型（管理员用） ====================

/**
 * 咨询模板状态
 */
export type ConsultationTemplateStatus = 'draft' | 'published' | 'deprecated';

/**
 * 咨询模板
 */
export interface ConsultationTemplate {
  id: string;
  key: string;
  name: string;
  description: string;
  category: ConsultationCategory;
  questions: ConsultationQuestion[];
  status: ConsultationTemplateStatus;
  isDefault: boolean;
  usageCount: number;
  createdBy: string;
  createdAt: string;
  updatedAt: string;
  publishedAt: string | null;
}

/**
 * 咨询问题
 */
export interface ConsultationQuestion {
  id: string;
  type: 'text' | 'textarea' | 'select' | 'radio' | 'checkbox' | 'date' | 'number';
  label: string;
  placeholder?: string;
  required: boolean;
  options?: string[];
  validation?: {
    min?: number;
    max?: number;
    pattern?: string;
    message?: string;
  };
}

/**
 * 获取咨询模板列表请求
 */
export interface GetConsultationTemplatesRequest {
  page?: number;
  pageSize?: number;
  category?: ConsultationCategory;
  status?: ConsultationTemplateStatus;
  keyword?: string;
}

/**
 * 获取咨询模板列表响应
 */
export interface GetConsultationTemplatesResponse {
  items: ConsultationTemplate[];
  total: number;
  page: number;
  pageSize: number;
}

/**
 * 创建咨询模板请求
 */
export interface CreateConsultationTemplateRequest {
  key: string;
  name: string;
  description: string;
  category: ConsultationCategory;
  questions: ConsultationQuestion[];
  isDefault?: boolean;
}

/**
 * 更新咨询模板请求
 */
export interface UpdateConsultationTemplateRequest {
  name?: string;
  description?: string;
  category?: ConsultationCategory;
  questions?: ConsultationQuestion[];
  isDefault?: boolean;
}