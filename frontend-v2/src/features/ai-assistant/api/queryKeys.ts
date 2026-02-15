/**
 * AI Assistant（AI助手）Query Keys
 * 用于 React Query 的缓存管理
 */

/**
 * AI助手模块的基础 query key
 */
export const aiAssistantKeys = {
  all: ['ai-assistant'] as const,

  /** 咨询会话列表 */
  consultations: () => [...aiAssistantKeys.all, 'consultations'] as const,
  consultationList: (skip?: number, limit?: number, q?: string) =>
    [...aiAssistantKeys.consultations(), { skip, limit, q }] as const,

  /** 单个咨询会话详情 */
  consultation: (sessionId: string) =>
    [...aiAssistantKeys.all, 'consultation', sessionId] as const,

  /** 咨询会话导出数据 */
  consultationExport: (sessionId: string) =>
    [...aiAssistantKeys.consultation(sessionId), 'export'] as const,

  /** 分享链接 */
  shareLink: (sessionId: string) =>
    [...aiAssistantKeys.consultation(sessionId), 'share'] as const,

  /** 分享的咨询内容（公开访问） */
  sharedConsultation: (token: string) =>
    [...aiAssistantKeys.all, 'shared', token] as const,
} as const;

export default aiAssistantKeys;