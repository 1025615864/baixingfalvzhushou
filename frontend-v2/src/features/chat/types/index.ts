// 消息角色
export type MessageRole = 'user' | 'assistant' | 'system';

// 消息状态
export type MessageStatus = 'pending' | 'streaming' | 'completed' | 'error';

// 聊天消息
export interface ChatMessage {
  id: string;
  role: MessageRole;
  content: string;
  timestamp: string;
  status?: MessageStatus;
  error?: string;
  metadata?: {
    sources?: string[];
    confidence?: number;
    suggestedQuestions?: string[];
  };
}

// 对话会话
export interface ChatSession {
  id: string;
  title: string;
  messages: ChatMessage[];
  createdAt: string;
  updatedAt: string;
  isActive: boolean;
}

// 发送消息请求
export interface SendMessageRequest {
  sessionId?: string;
  content: string;
  context?: Record<string, unknown>;
}

// 流式响应数据
export interface StreamChunk {
  type: 'content' | 'error' | 'done';
  data: string;
  metadata?: Record<string, unknown>;
}

// AI 模型配置
export interface AIModelConfig {
  model: string;
  temperature: number;
  maxTokens: number;
  topP: number;
}