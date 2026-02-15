/**
 * Calendar（法律日历）类型定义
 */

// ==================== 核心类型 ====================

/** 提醒状态 */
export type ReminderStatus = 'pending' | 'completed';

/** 重复类型 */
export type RepeatType = 'none' | 'daily' | 'weekly' | 'monthly' | 'yearly';

/** 日历提醒 */
export interface CalendarReminder {
  id: number;
  userId: number;
  title: string;
  note?: string;
  dueAt: string;
  remindAt?: string;
  isDone: boolean;
  doneAt?: string;
  createdAt: string;
  updatedAt: string;
  repeatType?: RepeatType;
}

/** 重复规则 */
export interface RepeatRule {
  type: RepeatType;
  interval?: number;
  endDate?: string;
  occurrences?: number;
}

/** 日历事件（用于视图展示） */
export interface CalendarEvent {
  id: number;
  title: string;
  date: string;
  isDone: boolean;
  reminder: CalendarReminder;
}

/** 日历视图类型 */
export type CalendarViewType = 'month' | 'week' | 'day';

// ==================== API 请求/响应类型 ====================

/** 创建提醒请求 */
export interface CreateReminderRequest {
  title: string;
  note?: string;
  dueAt: string;
  remindAt?: string;
  repeatType?: RepeatType;
}

/** 创建提醒响应 */
export interface CreateReminderResponse {
  id: number;
  title: string;
  note?: string;
  dueAt: string;
  remindAt?: string;
  isDone: boolean;
  doneAt?: string;
  createdAt: string;
  updatedAt: string;
}

/** 更新提醒请求 */
export interface UpdateReminderRequest {
  title?: string;
  note?: string;
  dueAt?: string;
  remindAt?: string;
  isDone?: boolean;
  repeatType?: RepeatType;
}

/** 更新提醒响应 */
export interface UpdateReminderResponse {
  id: number;
  title: string;
  note?: string;
  dueAt: string;
  remindAt?: string;
  isDone: boolean;
  doneAt?: string;
  createdAt: string;
  updatedAt: string;
}

/** 获取提醒列表请求 */
export interface GetReminderListRequest {
  page?: number;
  pageSize?: number;
  done?: boolean | null;
  fromAt?: string;
  toAt?: string;
}

/** 获取提醒列表响应 */
export interface GetReminderListResponse {
  items: CalendarReminder[];
  total: number;
}

/** 获取提醒详情请求 */
export interface GetReminderRequest {
  id: number;
}

/** 获取提醒详情响应 */
export interface GetReminderResponse {
  reminder: CalendarReminder;
}

/** 删除提醒响应 */
export interface DeleteReminderResponse {
  message: string;
}

// ==================== 组件 Props 类型 ====================

/** 日历视图组件 Props */
export interface CalendarViewProps {
  viewType: CalendarViewType;
  currentDate: Date;
  reminders: CalendarReminder[];
  onDateClick: (date: Date) => void;
  onEventClick: (reminder: CalendarReminder) => void;
}

/** 提醒列表组件 Props */
export interface ReminderListProps {
  reminders: CalendarReminder[];
  onEdit: (reminder: CalendarReminder) => void;
  onDelete: (id: number) => void;
  onToggleStatus: (id: number, isDone: boolean) => void;
  selectedDate?: Date;
}

/** 提醒卡片组件 Props */
export interface ReminderCardProps {
  reminder: CalendarReminder;
  onEdit: (reminder: CalendarReminder) => void;
  onDelete: (id: number) => void;
  onToggleStatus: (id: number, isDone: boolean) => void;
}

/** 提醒表单组件 Props */
export interface ReminderFormProps {
  initialData?: Partial<CalendarReminder>;
  onSubmit: (data: CreateReminderRequest | UpdateReminderRequest) => void;
  onCancel: () => void;
  isLoading?: boolean;
}

/** 提醒弹窗组件 Props */
export interface ReminderModalProps {
  isOpen: boolean;
  onClose: () => void;
  reminder?: CalendarReminder;
  mode: 'create' | 'edit';
  onSubmit: (data: CreateReminderRequest | UpdateReminderRequest) => void;
  isLoading?: boolean;
}

/** 日历事件组件 Props */
export interface CalendarEventProps {
  events: CalendarEvent[];
  onEventClick: (event: CalendarEvent) => void;
}