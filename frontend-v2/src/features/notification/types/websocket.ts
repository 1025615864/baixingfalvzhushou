// ============================================
// WebSocket 类型定义
// ============================================

/**
 * WebSocket 连接状态枚举
 */
export enum WebSocketConnectionState {
  /** 连接中 */
  CONNECTING = 'connecting',
  /** 已连接 */
  CONNECTED = 'connected',
  /** 已断开 */
  DISCONNECTED = 'disconnected',
  /** 重连中 */
  RECONNECTING = 'reconnecting',
  /** 连接错误 */
  ERROR = 'error',
}

/**
 * 通知类型枚举
 */
export enum NotificationType {
  /** 系统通知 */
  SYSTEM = 'system',
  /** 聊天消息 */
  CHAT = 'chat',
  /** 订单更新 */
  ORDER = 'order',
  /** 咨询更新 */
  CONSULTATION = 'consultation',
  /** 论坛互动 */
  FORUM = 'forum',
  /** 支付通知 */
  PAYMENT = 'payment',
  /** 推广消息 */
  PROMOTION = 'promotion',
  /** 安全提醒 */
  SECURITY = 'security',
  /** 活动通知 */
  ACTIVITY = 'activity',
}

/**
 * 消息优先级
 */
export enum MessagePriority {
  /** 低优先级 */
  LOW = 'low',
  /** 普通优先级 */
  NORMAL = 'normal',
  /** 高优先级 */
  HIGH = 'high',
  /** 紧急 */
  URGENT = 'urgent',
}

/**
 * WebSocket 消息类型
 */
export enum WebSocketMessageType {
  /** 连接确认 */
  CONNECT = 'connect',
  /** 断开连接 */
  DISCONNECT = 'disconnect',
  /** 心跳 ping */
  PING = 'ping',
  /** 心跳 pong */
  PONG = 'pong',
  /** 通知消息 */
  NOTIFICATION = 'notification',
  /** 聊天消息 */
  CHAT_MESSAGE = 'chat_message',
  /** 订单更新 */
  ORDER_UPDATE = 'order_update',
  /** 系统广播 */
  BROADCAST = 'broadcast',
  /** 错误消息 */
  ERROR = 'error',
  /** 已读确认 */
  READ_RECEIPT = 'read_receipt',
  /** 打字状态 */
  TYPING = 'typing',
}

/**
 * 基础 WebSocket 消息结构
 */
export interface WebSocketMessageBase {
  /** 消息唯一ID */
  id: string;
  /** 消息类型 */
  type: WebSocketMessageType;
  /** 时间戳 */
  timestamp: number;
}

/**
 * 连接消息
 */
export interface ConnectMessage extends WebSocketMessageBase {
  type: WebSocketMessageType.CONNECT;
  /** 用户ID */
  userId: number;
  /** 设备信息 */
  deviceInfo?: string;
}

/**
 * 心跳消息
 */
export interface PingMessage extends WebSocketMessageBase {
  type: WebSocketMessageType.PING;
}

/**
 * 心跳响应消息
 */
export interface PongMessage extends WebSocketMessageBase {
  type: WebSocketMessageType.PONG;
}

/**
 * 通知消息数据结构
 */
export interface NotificationData {
  /** 通知ID */
  id: number;
  /** 通知类型 */
  type: NotificationType;
  /** 标题 */
  title: string;
  /** 内容 */
  content?: string;
  /** 链接 */
  link?: string;
  /** 优先级 */
  priority: MessagePriority;
  /** 是否已读 */
  isRead: boolean;
  /** 发送者ID */
  senderId?: number;
  /** 发送者名称 */
  senderName?: string;
  /** 发送者头像 */
  senderAvatar?: string;
  /** 关联业务ID */
  businessId?: string;
  /** 关联业务类型 */
  businessType?: string;
  /** 创建时间 */
  createdAt: string;
  /** 过期时间 */
  expireAt?: string;
  /** 附加数据 */
  extraData?: Record<string, unknown>;
}

/**
 * 通知消息
 */
export interface NotificationMessage extends WebSocketMessageBase {
  type: WebSocketMessageType.NOTIFICATION;
  /** 通知数据 */
  data: NotificationData;
}

/**
 * 聊天消息数据
 */
export interface ChatMessageData {
  /** 消息ID */
  id: string;
  /** 会话ID */
  conversationId: string;
  /** 发送者ID */
  senderId: number;
  /** 发送者名称 */
  senderName: string;
  /** 发送者头像 */
  senderAvatar?: string;
  /** 消息内容 */
  content: string;
  /** 消息类型 */
  messageType: 'text' | 'image' | 'file' | 'voice';
  /** 媒体URL */
  mediaUrl?: string;
  /** 创建时间 */
  createdAt: string;
  /** 是否已读 */
  isRead: boolean;
  /** 引用消息ID */
  replyTo?: string;
}

/**
 * 聊天消息
 */
export interface ChatMessage extends WebSocketMessageBase {
  type: WebSocketMessageType.CHAT_MESSAGE;
  /** 聊天数据 */
  data: ChatMessageData;
}

/**
 * 订单更新数据
 */
export interface OrderUpdateData {
  /** 订单ID */
  orderId: string;
  /** 订单状态 */
  status: string;
  /** 订单类型 */
  orderType: string;
  /** 金额 */
  amount?: number;
  /** 更新时间 */
  updatedAt: string;
  /** 描述 */
  description?: string;
}

/**
 * 订单更新消息
 */
export interface OrderUpdateMessage extends WebSocketMessageBase {
  type: WebSocketMessageType.ORDER_UPDATE;
  /** 订单数据 */
  data: OrderUpdateData;
}

/**
 * 系统广播消息
 */
export interface BroadcastMessage extends WebSocketMessageBase {
  type: WebSocketMessageType.BROADCAST;
  /** 广播标题 */
  title: string;
  /** 广播内容 */
  content: string;
  /** 广播范围 */
  scope: 'all' | 'user' | 'role';
  /** 目标ID列表 */
  targetIds?: number[];
}

/**
 * 错误消息
 */
export interface ErrorMessage extends WebSocketMessageBase {
  type: WebSocketMessageType.ERROR;
  /** 错误码 */
  code: string;
  /** 错误信息 */
  message: string;
  /** 详情 */
  details?: string;
}

/**
 * 已读回执
 */
export interface ReadReceiptMessage extends WebSocketMessageBase {
  type: WebSocketMessageType.READ_RECEIPT;
  /** 已读的消息ID列表 */
  messageIds: string[];
  /** 已读用户ID */
  readerId: number;
  /** 已读时间 */
  readAt: string;
}

/**
 * 打字状态
 */
export interface TypingMessage extends WebSocketMessageBase {
  type: WebSocketMessageType.TYPING;
  /** 会话ID */
  conversationId: string;
  /** 用户ID */
  userId: number;
  /** 用户名称 */
  userName: string;
  /** 是否正在输入 */
  isTyping: boolean;
}

/**
 * 联合类型：所有 WebSocket 消息
 */
export type WebSocketMessage =
  | ConnectMessage
  | PingMessage
  | PongMessage
  | NotificationMessage
  | ChatMessage
  | OrderUpdateMessage
  | BroadcastMessage
  | ErrorMessage
  | ReadReceiptMessage
  | TypingMessage;

/**
 * WebSocket 连接配置
 */
export interface WebSocketConfig {
  /** WebSocket 服务器URL */
  url: string;
  /** 重连间隔（毫秒） */
  reconnectInterval?: number;
  /** 最大重连次数 */
  maxReconnectAttempts?: number;
  /** 心跳间隔（毫秒） */
  heartbeatInterval?: number;
  /** 连接超时（毫秒） */
  connectionTimeout?: number;
  /** 自动重连 */
  autoReconnect?: boolean;
  /** 启用心跳 */
  enableHeartbeat?: boolean;
  /** 认证Token */
  token?: string;
  /** 自定义协议 */
  protocols?: string[];
  /** 连接成功后发送的初始消息 */
  initialMessage?: unknown;
}

/**
 * WebSocket 连接状态接口
 */
export interface WebSocketConnectionStatus {
  /** 当前状态 */
  state: WebSocketConnectionState;
  /** 是否已连接 */
  isConnected: boolean;
  /** 最后一次连接时间 */
  lastConnectedAt?: Date;
  /** 最后一次断开时间 */
  lastDisconnectedAt?: Date;
  /** 重连次数 */
  reconnectAttempts: number;
  /** 错误信息 */
  error?: Error;
  /** 延迟（毫秒） */
  latency?: number;
}

/**
 * WebSocket 事件处理器
 */
export interface WebSocketEventHandlers {
  /** 连接成功 */
  onConnect?: () => void;
  /** 连接断开 */
  onDisconnect?: (code: number, reason: string) => void;
  /** 连接错误 */
  onError?: (error: Error) => void;
  /** 收到消息 */
  onMessage?: (message: WebSocketMessage) => void;
  /** 收到通知 */
  onNotification?: (notification: NotificationData) => void;
  /** 收到聊天消息 */
  onChatMessage?: (message: ChatMessageData) => void;
  /** 订单更新 */
  onOrderUpdate?: (update: OrderUpdateData) => void;
  /** 开始重连 */
  onReconnecting?: (attempt: number) => void;
  /** 重连成功 */
  onReconnected?: () => void;
  /** 心跳超时 */
  onHeartbeatTimeout?: () => void;
}

/**
 * 消息队列项
 */
export interface QueuedMessage {
  /** 队列ID */
  id: string;
  /** 消息内容 */
  message: unknown;
  /** 入队时间 */
  enqueuedAt: number;
  /** 重试次数 */
  retryCount: number;
}

/**
 * 通知筛选条件
 */
export interface NotificationFilter {
  /** 类型筛选 */
  types?: NotificationType[];
  /** 是否已读 */
  isRead?: boolean;
  /** 开始时间 */
  startDate?: string;
  /** 结束时间 */
  endDate?: string;
  /** 优先级 */
  priorities?: MessagePriority[];
  /** 搜索关键词 */
  keyword?: string;
}

/**
 * 分页通知响应
 */
export interface PaginatedNotifications {
  /** 通知列表 */
  items: NotificationData[];
  /** 总数 */
  total: number;
  /** 当前页 */
  page: number;
  /** 每页数量 */
  pageSize: number;
  /** 是否有更多 */
  hasMore: boolean;
  /** 未读数量 */
  unreadCount: number;
}

/**
 * 通知操作类型
 */
export enum NotificationAction {
  /** 标记已读 */
  MARK_AS_READ = 'mark_as_read',
  /** 标记全部已读 */
  MARK_ALL_AS_READ = 'mark_all_as_read',
  /** 删除 */
  DELETE = 'delete',
  /** 清空全部 */
  CLEAR_ALL = 'clear_all',
}

/**
 * 实时通知配置
 */
export interface RealtimeNotificationConfig {
  /** 启用桌面通知 */
  enableDesktopNotification?: boolean;
  /** 启用声音 */
  enableSound?: boolean;
  /** 声音文件URL */
  soundUrl?: string;
  /** 最小通知间隔（毫秒） */
  minInterval?: number;
  /** 通知显示时长（毫秒） */
  displayDuration?: number;
  /** 最大显示数量 */
  maxDisplayCount?: number;
  /** 忽略的类别 */
  ignoredTypes?: NotificationType[];
}