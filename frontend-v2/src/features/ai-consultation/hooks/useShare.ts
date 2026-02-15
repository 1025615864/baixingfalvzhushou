/**
 * AI咨询分享功能Hook
 */

import { useCallback } from 'react';
import { useMutation, useQuery } from '@tanstack/react-query';

import type {
  CreateShareRequest,
  ShareLinkResponse,
  SharedConsultationResponse,
} from '../types';
import {
  apiCreateShare,
  apiGetSharedConsultation,
} from '../api';

// ==================== Query Keys ====================

const SHARE_QUERY_KEYS = {
  share: (token: string) => ['ai-share', token] as const,
} as const;

// ==================== Hook 返回类型 ====================

/** 创建分享链接Hook返回类型 */
interface UseCreateShareReturn {
  /** 分享数据 */
  data: ShareLinkResponse | undefined;
  /** 是否加载中 */
  isLoading: boolean;
  /** 错误信息 */
  error: Error | null;
  /** 创建分享链接 */
  createShare: (request: CreateShareRequest) => Promise<ShareLinkResponse>;
}

/** 获取分享内容Hook返回类型 */
interface UseSharedConsultationReturn {
  /** 分享的咨询数据 */
  data: SharedConsultationResponse | undefined;
  /** 是否加载中 */
  isLoading: boolean;
  /** 错误信息 */
  error: Error | null;
}

// ==================== Hooks ====================

/**
 * 创建分享链接Hook
 */
export function useCreateShare(): UseCreateShareReturn {
  const mutation = useMutation<ShareLinkResponse, Error, CreateShareRequest>({
    mutationFn: apiCreateShare,
  });

  const createShare = useCallback(
    async (request: CreateShareRequest): Promise<ShareLinkResponse> => {
      return mutation.mutateAsync(request);
    },
    [mutation]
  );

  return {
    data: mutation.data,
    isLoading: mutation.isPending,
    error: mutation.error,
    createShare,
  };
}

/**
 * 获取分享的咨询内容Hook
 */
export function useSharedConsultation(token: string | undefined): UseSharedConsultationReturn {
  const { data, isLoading, error } = useQuery<SharedConsultationResponse>({
    queryKey: SHARE_QUERY_KEYS.share(token || ''),
    queryFn: () => apiGetSharedConsultation(token!),
    enabled: !!token,
    staleTime: 5 * 60 * 1000, // 5分钟缓存
  });

  return {
    data,
    isLoading,
    error,
  };
}

// ==================== 辅助函数 ====================

/**
 * 复制分享链接到剪贴板
 */
export async function copyShareLink(sharePath: string): Promise<boolean> {
  const fullUrl = `${window.location.origin}${sharePath}`;
  
  try {
    if (navigator.clipboard && window.isSecureContext) {
      await navigator.clipboard.writeText(fullUrl);
      return true;
    }
    
    // 降级方案
    const textArea = document.createElement('textarea');
    textArea.value = fullUrl;
    textArea.style.position = 'fixed';
    textArea.style.left = '-9999px';
    document.body.appendChild(textArea);
    textArea.select();
    
    try {
      document.execCommand('copy');
      document.body.removeChild(textArea);
      return true;
    } catch {
      document.body.removeChild(textArea);
      return false;
    }
  } catch {
    return false;
  }
}

/**
 * 生成分享页面URL
 */
export function generateShareUrl(sharePath: string): string {
  return `${window.location.origin}${sharePath}`;
}

/**
 * 格式化过期时间显示
 */
export function formatExpireTime(expiresAt: string): string {
  const expireDate = new Date(expiresAt);
  const now = new Date();
  const diffMs = expireDate.getTime() - now.getTime();
  const diffDays = Math.ceil(diffMs / (1000 * 60 * 60 * 24));
  
  if (diffDays <= 0) {
    return '已过期';
  }
  if (diffDays === 1) {
    return '1天后过期';
  }
  return `${diffDays}天后过期`;
}