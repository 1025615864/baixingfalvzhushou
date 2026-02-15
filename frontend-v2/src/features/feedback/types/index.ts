/**
 * 用户反馈功能类型定义
 */

/**
 * 反馈类型枚举
 */
export type FeedbackType = 'suggestion' | 'bug' | 'complaint' | 'other';

/**
 * 反馈状态枚举
 */
export type FeedbackStatus = 'open' | 'processing' | 'closed';

/**
 * 反馈类型标签配置
 */
export const FEEDBACK_TYPE_LABELS: Record<FeedbackType, { label: string; color: string }> = {
  suggestion: { label: '建议', color: 'bg-blue-100 text-blue-700' },
  bug: { label: 'Bug', color: 'bg-red-100 text-red-700' },
  complaint: { label: '投诉', color: 'bg-orange-100 text-orange-700' },
  other: { label: '其他', color: 'bg-gray-100 text-gray-700' },
};

/**
 * 反馈状态标签配置
 */
export const FEEDBACK_STATUS_LABELS: Record<FeedbackStatus, { label: string; color: string }> = {
  open: { label: '待处理', color: 'bg-yellow-100 text-yellow-700' },
  processing: { label: '处理中', color: 'bg-blue-100 text-blue-700' },
  closed: { label: '已解决', color: 'bg-green-100 text-green-700' },
};

/**
 * 反馈项接口
 */
export interface Feedback {
  /** 反馈ID */
  id: number;
  /** 用户ID */
  userId: number;
  /** 反馈类型 */
  type: FeedbackType;
  /** 反馈标题/主题 */
  subject: string;
  /** 反馈内容 */
  content: string;
  /** 反馈状态 */
  status: FeedbackStatus;
  /** 管理员回复 */
  adminReply: string | null;
  /** 管理员ID */
  adminId: number | null;
  /** 附件图片URL列表 */
  images?: string[];
  /** 联系方式 */
  contact?: string;
  /** 创建时间 */
  createdAt: string;
  /** 更新时间 */
  updatedAt: string;
}

/**
 * 创建反馈请求DTO
 */
export interface CreateFeedbackDTO {
  /** 反馈类型 */
  type: FeedbackType;
  /** 反馈标题 */
  subject: string;
  /** 反馈内容 */
  content: string;
  /** 附件图片URL列表 */
  images?: string[];
  /** 联系方式 */
  contact?: string;
}

/**
 * 更新反馈请求DTO（管理员）
 */
export interface UpdateFeedbackDTO {
  /** 反馈状态 */
  status?: FeedbackStatus;
  /** 管理员回复 */
  adminReply?: string;
  /** 管理员ID */
  adminId?: number | null;
}

/**
 * 反馈列表响应
 */
export interface FeedbackListResponse {
  /** 反馈列表 */
  items: Feedback[];
  /** 总数 */
  total: number;
  /** 当前页 */
  page: number;
  /** 每页数量 */
  pageSize: number;
}

/**
 * 反馈统计响应（管理员）
 */
export interface FeedbackStatsResponse {
  /** 总数 */
  total: number;
  /** 待处理数量 */
  open: number;
  /** 处理中数量 */
  processing: number;
  /** 已关闭数量 */
  closed: number;
  /** 未分配数量 */
  unassigned: number;
}

/**
 * 反馈查询参数
 */
export interface FeedbackQueryParams {
  /** 页码 */
  page?: number;
  /** 每页数量 */
  pageSize?: number;
  /** 状态筛选 */
  status?: FeedbackStatus;
  /** 关键词搜索 */
  keyword?: string;
}

/**
 * 获取反馈类型标签
 */
export function getFeedbackTypeLabel(type: FeedbackType): string {
  return FEEDBACK_TYPE_LABELS[type]?.label || '其他';
}

/**
 * 获取反馈类型样式
 */
export function getFeedbackTypeClass(type: FeedbackType): string {
  return FEEDBACK_TYPE_LABELS[type]?.color || 'bg-gray-100 text-gray-700';
}

/**
 * 获取反馈状态标签
 */
export function getFeedbackStatusLabel(status: FeedbackStatus): string {
  return FEEDBACK_STATUS_LABELS[status]?.label || '未知';
}

/**
 * 获取反馈状态样式
 */
export function getFeedbackStatusClass(status: FeedbackStatus): string {
  return FEEDBACK_STATUS_LABELS[status]?.color || 'bg-gray-100 text-gray-700';
}