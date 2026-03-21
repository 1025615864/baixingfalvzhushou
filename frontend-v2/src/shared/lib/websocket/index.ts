/**
 * WebSocket 服务 - 共享模块
 * 
 * 导出通知模块中的 WebSocket 服务，供全局复用
 * 
 * 功能：
 * - WebSocket 服务单例
 * - 断线自动重连（指数退避）
 * - 连接状态管理
 * - 心跳检测
 * - 消息队列（断线时缓存消息）
 * 
 * @see FR-005: WebSocket 优化
 */

// 从通知模块导出 WebSocket 服务
export {
  WebSocketService,
  createWebSocketService,
  getGlobalWebSocketService,
  setGlobalWebSocketService,
  initGlobalWebSocketService,
} from '@/features/notification/services/websocketService';

// 导出类型
export type {
  WebSocketConfig,
  WebSocketConnectionState,
  WebSocketConnectionStatus,
  WebSocketMessage,
  WebSocketMessageType,
  QueuedMessage,
  WebSocketEventHandlers,
} from '@/features/notification/types/websocket';