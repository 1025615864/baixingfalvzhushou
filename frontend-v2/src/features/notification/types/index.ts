/**
 * 通知类型定义
 */

/** 通知类型枚举 */
export enum NotificationType {
  COMMENT_REPLY = 'comment_reply',
  POST_LIKE = 'post_like',
  POST_FAVORITE = 'post_favorite',
  POST_COMMENT = 'post_comment',
  SYSTEM = 'system',
  CONSULTATION = 'consultation',
  NEWS = 'news',
  ORDER = 'order',
}

/** 通知类型标签映射 */
export const NotificationTypeLabels: Record<NotificationType, string> = {
  [NotificationType.COMMENT_REPLY]: '评论回复',
  [NotificationType.POST_LIKE]: '点赞',
  [NotificationType.POST_FAVORITE]: '收藏',
  [NotificationType.POST_COMMENT]: '评论',
  [NotificationType.SYSTEM]: '系统通知',
  [NotificationType.CONSULTATION]: '咨询相关',
  [NotificationType.NEWS]: '新闻订阅',
  [NotificationType.ORDER]: '订单通知',
};

/** 通知类型图标映射 */
export const NotificationTypeIcons: Record<NotificationType, string> = {
  [NotificationType.COMMENT_REPLY]: 'MessageCircle',
  [NotificationType.POST_LIKE]: 'Heart',
  [NotificationType.POST_FAVORITE]: 'Bookmark',
  [NotificationType.POST_COMMENT]: 'MessageSquare',
  [NotificationType.SYSTEM]: 'Bell',
  [NotificationType.CONSULTATION]: 'Briefcase',
  [NotificationType.NEWS]: 'Newspaper',
  [NotificationType.ORDER]: 'ShoppingCart',
};

/** 通知类型颜色映射 */
export const NotificationTypeColors: Record<NotificationType, string> = {
  [NotificationType.COMMENT_REPLY]: 'text-blue-500 bg-blue-50',
  [NotificationType.POST_LIKE]: 'text-pink-500 bg-pink-50',
  [NotificationType.POST_FAVORITE]: 'text-yellow-500 bg-yellow-50',
  [NotificationType.POST_COMMENT]: 'text-green-500 bg-green-50',
  [NotificationType.SYSTEM]: 'text-purple-500 bg-purple-50',
  [NotificationType.CONSULTATION]: 'text-indigo-500 bg-indigo-50',
  [NotificationType.NEWS]: 'text-orange-500 bg-orange-50',
  [NotificationType.ORDER]: 'text-cyan-500 bg-cyan-50',
};

/** 通知数据对象 */
export interface Notification {
  /** 通知ID */
  id: number;
  /** 通知类型 */
  type: NotificationType;
  /** 标题 */
  title: string;
  /** 内容 */
  content: string | null;
  /** 跳转链接 */
  link: string | null;
  /** 是否已读 */
  is_read: boolean;
  /** 相关用户ID */
  related_user_id: number | null;
  /** 相关用户名称 */
  related_user_name: string | null;
  /** 创建时间 */
  created_at: string;
}

/** 通知列表响应 */
export interface NotificationListResponse {
  /** 通知列表 */
  items: Notification[];
  /** 总数 */
  total: number;
  /** 未读数量 */
  unread_count: number;
}

/** 未读数量响应 */
export interface UnreadCountResponse {
  /** 未读数量 */
  unread_count: number;
}

/** 通知类型统计响应 */
export interface NotificationTypesStatsResponse {
  /** 类型统计 */
  types: Record<string, number>;
  /** 类型标签 */
  type_labels: Record<string, string>;
}

/** 批量操作响应 */
export interface BatchOperationResponse {
  /** 消息 */
  message: string;
  /** 操作数量 */
  count: number;
}

/** 批量操作请求 */
export interface BatchIdsRequest {
  /** ID列表 */
  ids: number[];
}

/** 获取通知列表参数 */
export interface GetNotificationsParams {
  /** 页码 */
  page?: number;
  /** 每页数量 */
  page_size?: number;
  /** 仅显示未读 */
  unread_only?: boolean;
  /** 通知类型筛选 */
  notification_type?: NotificationType;
}

/** 通知设置 */
export interface NotificationSettings {
  /** 系统通知开关 */
  system_enabled: boolean;
  /** 咨询通知开关 */
  consultation_enabled: boolean;
  /** 评论回复通知开关 */
  comment_reply_enabled: boolean;
  /** 点赞通知开关 */
  like_enabled: boolean;
  /** 订单通知开关 */
  order_enabled: boolean;
  /** 新闻订阅通知开关 */
  news_enabled: boolean;
}

// ==================== 系统通知管理类型（管理员用） ====================

/** 系统通知目标类型 */
export type NotificationTargetType = 'all' | 'users' | 'lawyers' | 'admins' | 'specific';

/** 系统通知 */
export interface SystemNotification {
  id: string;
  title: string;
  content: string;
  targetType: NotificationTargetType;
  targetIds: string[] | null;
  sentCount: number;
  readCount: number;
  isPublished: boolean;
  publishedAt: string | null;
  expiresAt: string | null;
  createdBy: string;
  createdAt: string;
  updatedAt: string;
}

/** 创建系统通知请求 */
export interface CreateSystemNotificationRequest {
  title: string;
  content: string;
  targetType: NotificationTargetType;
  targetIds?: string[];
  expiresAt?: string;
}

/** 更新系统通知请求 */
export interface UpdateSystemNotificationRequest {
  title?: string;
  content?: string;
  targetType?: NotificationTargetType;
  targetIds?: string[];
  expiresAt?: string | null;
}

/** 获取系统通知列表请求 */
export interface GetSystemNotificationsRequest {
  page?: number;
  pageSize?: number;
  isPublished?: boolean;
  keyword?: string;
}

/** 获取系统通知列表响应 */
export interface GetSystemNotificationsResponse {
  items: SystemNotification[];
  total: number;
  page: number;
  pageSize: number;
}

/** 发布系统通知请求 */
export interface PublishSystemNotificationRequest {
  id: string;
}

/** 撤销系统通知请求 */
export interface RevokeSystemNotificationRequest {
  id: string;
}